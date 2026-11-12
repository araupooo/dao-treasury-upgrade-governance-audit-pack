#!/usr/bin/env python3
"""fetch_treasury.py — reconstruct treasury balances, flows, multisig
thresholds, and timelock parameters for Cosmos Hub and Osmosis from
public LCD endpoints only (no API keys, no private credentials).

Usage: fetch_treasury.py [outdir] [fixturesdir]
Writes (per chain):
  outputs/treasury-<chain>.json   full structured record
  outputs/treasury-<chain>.csv   headline balances/flows table
  fixtures/<chain>-proposal-<id>.json  raw proposal JSON as fetched
  fixtures/<chain>-gov-params.json, <chain>-validators.json (snapshots)
Fails loudly (exit 1) if any primary fetch fails.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from onchain import (FetchError, concentration, from_base_units, get_json,
                     get_json_optional, ibc_denom_hash, paginate)

CHAINS = {
    "cosmoshub": {
        "label": "Cosmos Hub",
        "chain_id": "cosmoshub-4",
        "lcd": "https://rest.cosmos.directory/cosmoshub",
        "fallback_lcd": "https://lcd-cosmoshub.keplr.app",
        "bond_denom": "uatom",
        "bond_decimals": 6,
        "hist_height": 33746800,
        "spend_scan_limit": 40,
        "multisigs": [
            {"address": "cosmos1z8pq5cn7tdrwwzlwm0e44fgq07e43ner6vph64",
             "role": "Neutron-exploit recovery multisig (proposal 1058)",
             "expected_threshold": 4, "expected_signers": 6},
            {"address": "cosmos1amny2nf23uauu79lzp299tvh9v4a62uuxvh8xyj7qavrm0adztsq5sz864",
             "role": "USDC.n -> USDC.inj migration multisig, DAODAO (proposal 1060)",
             "expected_threshold": 4, "expected_signers": 6},
        ],
        "ibc_denoms": [
            {"label": "USDC.n (Noble)", "path": "transfer/channel-536/uusdc",
             "claimed": "F663521BF1836B00F5F177680F74BFB9A8B5654A694D0D2BC249E03CF2509013"},
            {"label": "USDC.inj (Injective)", "path": "transfer/channel-220/erc20:0xa00C59fF5a080D2b954d0c75e46E22a0c371235a",
             "claimed": "E107DB3E8AABB49C87CB737A1ABBFDBA9803ECAE05E295D8D7A0B1A7FE83706C"},
        ],
    },
    "osmosis": {
        "label": "Osmosis",
        "chain_id": "osmosis-1",
        "lcd": "https://rest.cosmos.directory/osmosis",
        "fallback_lcd": None,
        "bond_denom": "uosmo",
        "bond_decimals": 6,
        "hist_height": 74800000,
        "spend_scan_limit": 40,
        "multisigs": [],
        "ibc_denoms": [],
    },
}

# Proposals whose full JSON is snapshotted as fixtures (audited end to end
# by audit_proposals.py as well).
PINNED_PROPOSALS = {
    "cosmoshub": [1061, 1060, 1058],
    "osmosis": [1067, 1066, 1057],
}


def fetch_with_fallback(chain, path, height=None):
    try:
        return get_json(chain["lcd"] + path, height=height)
    except FetchError as e:
        fb = chain.get("fallback_lcd")
        if not fb:
            raise
        print("  primary LCD failed (%s); trying fallback %s" % (e, fb), flush=True)
        return get_json(fb + path, height=height)


def pool_amount(pool, denom):
    for c in pool:
        if c["denom"] == denom:
            return c["amount"]
    return None


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
    fixdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "fixtures")
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(fixdir, exist_ok=True)
    from datetime import datetime, timezone
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for slug, ch in CHAINS.items():
        print("=== %s (%s) ===" % (ch["label"], ch["chain_id"]), flush=True)
        rec = {"chain": ch["label"], "chain_id": ch["chain_id"],
               "lcd": ch["lcd"], "fetched_at_utc": fetched_at}

        latest = fetch_with_fallback(ch, "/cosmos/base/tendermint/v1beta1/blocks/latest")
        header = latest["block"]["header"]
        height = int(header["height"])
        rec["latest_height"] = height
        rec["latest_block_time"] = header["time"]
        print("  latest height %d at %s" % (height, header["time"]), flush=True)

        gov = fetch_with_fallback(ch, "/cosmos/gov/v1/params/voting")
        params = gov["params"]
        rec["gov_params"] = params
        with open(os.path.join(fixdir, "%s-gov-params.json" % slug), "w") as f:
            json.dump(params, f, indent=2, sort_keys=True)
        print("  voting_period=%s quorum=%s threshold=%s veto=%s expedited=%s/%s" % (
            params["voting_period"], params["quorum"], params["threshold"],
            params["veto_threshold"], params["expedited_voting_period"],
            params["expedited_threshold"]), flush=True)

        dist = fetch_with_fallback(ch, "/cosmos/distribution/v1beta1/params")
        rec["distribution_params"] = dist["params"]
        mint = get_json_optional(ch["lcd"] + "/cosmos/mint/v1beta1/inflation")
        if mint is None and slug == "osmosis":
            mint = get_json_optional(ch["lcd"] + "/osmosis/mint/v1beta1/inflation")
        rec["inflation"] = (mint or {}).get("inflation")
        print("  community_tax=%s inflation=%s" % (
            dist["params"]["community_tax"], rec["inflation"]), flush=True)

        staking = fetch_with_fallback(ch, "/cosmos/staking/v1beta1/pool")
        rec["staking_pool"] = staking["pool"]
        bonded = int(staking["pool"]["bonded_tokens"])
        rec["bonded_tokens_base"] = bonded
        print("  bonded=%d %s (%.2fM whole)" % (bonded, ch["bond_denom"],
              from_base_units(bonded, ch["bond_decimals"]) / 1e6), flush=True)

        spar = fetch_with_fallback(ch, "/cosmos/staking/v1beta1/params")
        rec["staking_params"] = spar["params"]

        validators = paginate(ch["lcd"] + "/cosmos/staking/v1beta1/validators?status=BOND_STATUS_BONDED",
                              "validators", limit=200)
        with open(os.path.join(fixdir, "%s-validators.json" % slug), "w") as f:
            json.dump([{"operator_address": v["operator_address"],
                        "moniker": v.get("description", {}).get("moniker"),
                        "tokens": v["tokens"], "status": v["status"]}
                       for v in validators], f, indent=2)
        vconc = concentration([int(v["tokens"]) for v in validators])
        rec["validator_concentration"] = vconc
        print("  validators bonded=%d top1=%.4f top4=%.4f top10=%.4f hhi=%.5f" % (
            vconc["n"], vconc["top1_share"], vconc["top4_share"],
            vconc["top10_share"], vconc["hhi"]), flush=True)

        pool_now = fetch_with_fallback(ch, "/cosmos/distribution/v1beta1/community_pool")
        rec["community_pool_now"] = pool_now["pool"]
        rec["community_pool_now_height"] = height
        pool_hist = fetch_with_fallback(ch, "/cosmos/distribution/v1beta1/community_pool",
                                        height=ch["hist_height"])
        rec["community_pool_hist"] = pool_hist["pool"]
        rec["community_pool_hist_height"] = ch["hist_height"]
        now_amt = pool_amount(pool_now["pool"], ch["bond_denom"])
        hist_amt = pool_amount(pool_hist["pool"], ch["bond_denom"])
        delta = None
        if now_amt is not None and hist_amt is not None:
            delta = float(now_amt) - float(hist_amt)
        rec["bond_pool_change"] = {"denom": ch["bond_denom"],
            "now_base": now_amt, "hist_base": hist_amt,
            "delta_base": ("%.6f" % delta) if delta is not None else None,
            "delta_whole": (delta / 10 ** ch["bond_decimals"]) if delta is not None else None,
            "blocks_span": height - ch["hist_height"]}
        print("  pool %s now=%s hist@%d=%s delta=%.2f whole over %d blocks" % (
            ch["bond_denom"], now_amt, ch["hist_height"], hist_amt,
            rec["bond_pool_change"]["delta_whole"] or 0,
            height - ch["hist_height"]), flush=True)

        # IBC denom hash verification (local sha256 recomputation).
        rec["ibc_denoms"] = []
        pool_by_denom = {c["denom"]: c["amount"] for c in pool_now["pool"]}
        for d in ch["ibc_denoms"]:
            h = ibc_denom_hash(d["path"])
            denom = "ibc/" + h
            rec["ibc_denoms"].append({
                "label": d["label"], "trace_path": d["path"],
                "computed_hash": h, "claimed_hash": d["claimed"],
                "hash_matches_claim": h == d["claimed"],
                "pool_balance_base": pool_by_denom.get(denom),
                "present_in_pool_now": denom in pool_by_denom})
            print("  ibc %s hash_match=%s pool_balance=%s" % (
                d["label"], h == d["claimed"], pool_by_denom.get(denom)), flush=True)

        # Multisig accounts: threshold via auth module (LegacyAminoPubKey).
        rec["multisigs"] = []
        for m in ch["multisigs"]:
            acct = fetch_with_fallback(ch, "/cosmos/auth/v1beta1/accounts/" + m["address"])
            bal = fetch_with_fallback(ch, "/cosmos/bank/v1beta1/balances/" + m["address"])
            a = acct.get("account", {})
            pk = a.get("pub_key") or {}
            entry = {"address": m["address"], "role": m["role"],
                     "account_type": a.get("@type"),
                     "account_number": a.get("account_number"),
                     "sequence": a.get("sequence"),
                     "pubkey_type": pk.get("@type"),
                     "threshold_onchain": pk.get("threshold"),
                     "signer_keys_onchain": len(pk.get("public_keys", [])) if pk.get("public_keys") else None,
                     "expected_threshold": m["expected_threshold"],
                     "expected_signers": m["expected_signers"],
                     "threshold_verifiable_onchain": pk.get("threshold") is not None,
                     "balances": bal.get("balances", [])}
            rec["multisigs"].append(entry)
            print("  multisig %s threshold_onchain=%s signers_onchain=%s seq=%s balances=%s" % (
                m["address"][:20], pk.get("threshold"),
                entry["signer_keys_onchain"], a.get("sequence"),
                [(b["denom"][:12], b["amount"]) for b in bal.get("balances", [])]), flush=True)
            # CosmWasm contract info attempt (DAODAO multisig is a contract
            # account; the auth module carries no pubkey for it).
            info = get_json_optional(ch["lcd"] + "/cosmwasm/wasm/v1/contract/" + m["address"])
            entry["wasm_contract_info"] = info
            print("  wasm contract info available: %s" % (info is not None), flush=True)

        # Community-pool spend proposals: scan the most recent proposals.
        listing = fetch_with_fallback(
            ch, "/cosmos/gov/v1/proposals?pagination.limit=%d&pagination.reverse=true"
            % ch["spend_scan_limit"])
        spends = []
        for p in listing.get("proposals", []):
            msgs = [mm for mm in p.get("messages", [])
                    if "MsgCommunityPoolSpend" in mm.get("@type", "")]
            if not msgs:
                continue
            detail = fetch_with_fallback(ch, "/cosmos/gov/v1/proposals/" + p["id"])
            dp = detail["proposal"]
            with open(os.path.join(fixdir, "%s-proposal-%s.json" % (slug, p["id"])), "w") as f:
                json.dump(detail, f, indent=2, sort_keys=True)
            for mm in dp.get("messages", []):
                if "MsgCommunityPoolSpend" not in mm.get("@type", ""):
                    continue
                spends.append({"proposal_id": p["id"], "title": dp.get("title"),
                               "status": dp.get("status"),
                               "submit_time": dp.get("submit_time"),
                               "voting_end_time": dp.get("voting_end_time"),
                               "recipient": mm.get("recipient"),
                               "amount": mm.get("amount")})
                print("  spend prop %s [%s] %s -> %s %s" % (
                    p["id"], dp.get("status"), dp.get("title"),
                    mm.get("recipient"), mm.get("amount")), flush=True)
        rec["community_pool_spends_recent"] = spends

        # Snapshot the pinned audit proposals as fixtures.
        for pid in PINNED_PROPOSALS[slug]:
            detail = fetch_with_fallback(ch, "/cosmos/gov/v1/proposals/%d" % pid)
            with open(os.path.join(fixdir, "%s-proposal-%d.json" % (slug, pid)), "w") as f:
                json.dump(detail, f, indent=2, sort_keys=True)

        with open(os.path.join(outdir, "treasury-%s.json" % slug), "w") as f:
            json.dump(rec, f, indent=2, sort_keys=True)

        # Headline CSV.
        rows = [["metric", "value"]]
        rows.append(["chain", ch["label"]])
        rows.append(["latest_height", height])
        rows.append(["latest_block_time_utc", header["time"]])
        rows.append(["bonded_tokens_whole", "%.6f" % from_base_units(bonded, ch["bond_decimals"])])
        rows.append(["community_pool_%s_now_base" % ch["bond_denom"], now_amt])
        rows.append(["community_pool_%s_now_whole" % ch["bond_denom"],
                     "%.6f" % from_base_units(int(float(now_amt)), ch["bond_decimals"]) if now_amt else ""])
        rows.append(["community_pool_%s_hist_base@%d" % (ch["bond_denom"], ch["hist_height"]), hist_amt])
        rows.append(["pool_delta_whole_over_%d_blocks" % (height - ch["hist_height"]),
                     "%.6f" % rec["bond_pool_change"]["delta_whole"] if delta is not None else ""])
        rows.append(["voting_period_s", params["voting_period"]])
        rows.append(["quorum", params["quorum"]])
        rows.append(["threshold", params["threshold"]])
        rows.append(["veto_threshold", params["veto_threshold"]])
        rows.append(["expedited_voting_period_s", params["expedited_voting_period"]])
        rows.append(["expedited_threshold", params["expedited_threshold"]])
        rows.append(["community_tax", dist["params"]["community_tax"]])
        rows.append(["inflation", rec["inflation"]])
        rows.append(["validators_bonded_count", vconc["n"]])
        rows.append(["validator_top4_share", "%.6f" % vconc["top4_share"]])
        rows.append(["validator_top10_share", "%.6f" % vconc["top10_share"]])
        rows.append(["validator_hhi", "%.6f" % vconc["hhi"]])
        rows.append(["max_validators", spar["params"]["max_validators"]])
        for s in spends:
            for a in s["amount"]:
                rows.append(["spend_prop_%s_%s" % (s["proposal_id"], a["denom"][:24]),
                             "%s to %s [%s]" % (a["amount"], s["recipient"], s["status"])])
        with open(os.path.join(outdir, "treasury-%s.csv" % slug), "w", newline="") as f:
            csv.writer(f).writerows(rows)
        print("=== %s DONE ===" % ch["label"], flush=True)

    print("fetch_treasury: DONE", flush=True)


if __name__ == "__main__":
    main()
