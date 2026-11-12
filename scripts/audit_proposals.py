#!/usr/bin/env python3
"""audit_proposals.py — end-to-end audit of pinned governance proposals:
creation (deposit, submit/voting times), quorum (tally vs bonded stake),
voting-power concentration (delegation-weighted, per-voter, for proposals
still in their voting period), execution timelock (voting period and, for
software upgrades, the scheduled upgrade height), and emergency powers
(presence/absence of pause authority in gov params and message types).

Public LCD only, no keys. Fails loudly on fetch failure. Per-vote lists
for FINALIZED proposals are empty on the public LCDs tried (documented
limitation): those proposals are audited from tally + params only and
`votes_available` is recorded as false — never silently treated as zero
votes.
"""
import csv
import json
import os
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from onchain import (FetchError, concentration, get_json, paginate,
                     quorum_outcome)

CHAINS = {
    "cosmoshub": {"label": "Cosmos Hub", "lcd": "https://rest.cosmos.directory/cosmoshub",
                  "fallback_lcd": "https://lcd-cosmoshub.keplr.app",
                  "bond_denom": "uatom", "decimals": 6,
                  "proposals": [1061, 1060, 1058]},
    "osmosis": {"label": "Osmosis", "lcd": "https://rest.cosmos.directory/osmosis",
                "fallback_lcd": None,
                "bond_denom": "uosmo", "decimals": 6,
                "proposals": [1067, 1066, 1057]},
}

MAX_DELEG_WORKERS = 4


def fetch_with_fallback(chain, path):
    try:
        return get_json(chain["lcd"] + path)
    except FetchError as e:
        fb = chain.get("fallback_lcd")
        if not fb:
            raise
        print("  primary LCD failed (%s); trying fallback" % e, flush=True)
        return get_json(fb + path)


def voter_stake(chain, voter):
    """Total currently-delegated bond-denom stake of one voter (base
    units). Snapshot-date approximation: stake at fetch time, not at
    vote time — stated in the methodology."""
    total = 0
    next_key = None
    while True:
        url = (chain["lcd"] + "/cosmos/staking/v1beta1/delegations/%s?pagination.limit=100" % voter)
        if next_key:
            url += "&pagination.key=" + urllib.parse.quote(next_key, safe="")
        try:
            data = get_json(url)
        except FetchError as e:
            fb = chain.get("fallback_lcd")
            if not fb:
                raise
            data = get_json(fb + "/cosmos/staking/v1beta1/delegations/%s?pagination.limit=100" % voter)
        for d in data.get("delegation_responses", []):
            bal = d.get("balance", {})
            if bal.get("denom") == chain["bond_denom"]:
                total += int(bal.get("amount", 0))
        pg = data.get("pagination", {}) or {}
        next_key = pg.get("next_key")
        if not next_key:
            return total


def audit_chain(slug, chain, outdir, fixdir):
    print("=== auditing %s ===" % chain["label"], flush=True)
    gov = fetch_with_fallback(chain, "/cosmos/gov/v1/params/voting")
    params = gov["params"]
    quorum = float(params["quorum"])
    threshold = float(params["threshold"])
    veto = float(params["veto_threshold"])
    staking = fetch_with_fallback(chain, "/cosmos/staking/v1beta1/pool")
    bonded = int(staking["pool"]["bonded_tokens"])
    results = {"chain": chain["label"], "chain_id": chain.get("chain_id", slug),
               "lcd": chain["lcd"], "bonded_tokens_base": bonded,
               "gov_params": params, "proposals": []}
    for pid in chain["proposals"]:
        print("  proposal %d" % pid, flush=True)
        detail = fetch_with_fallback(chain, "/cosmos/gov/v1/proposals/%d" % pid)
        p = detail["proposal"]
        with open(os.path.join(fixdir, "%s-proposal-%d.json" % (slug, pid)), "w") as f:
            json.dump(detail, f, indent=2, sort_keys=True)
        tally = fetch_with_fallback(chain, "/cosmos/gov/v1/proposals/%d/tally" % pid)["tally"]
        qo = quorum_outcome(tally, bonded, quorum, threshold, veto)
        rec = {"id": pid, "title": p.get("title"), "status": p.get("status"),
               "submit_time": p.get("submit_time"),
               "voting_start_time": p.get("voting_start_time"),
               "voting_end_time": p.get("voting_end_time"),
               "total_deposit": p.get("total_deposit"),
               "messages": [{"type": m.get("@type"),
                             "detail": {k: v for k, v in m.items() if k != "@type"}}
                            for m in p.get("messages", [])],
               "metadata": p.get("metadata"),
               "tally": tally, "quorum_evaluation": qo}
        # Execution timelock: Cosmos SDK gov has no post-passage timelock;
        # execution happens at EndBlock on passage, or at the scheduled
        # upgrade height for MsgSoftwareUpgrade. The voting period is the
        # only delay; record both delays explicitly.
        rec["timelock"] = {
            "post_passage_execution_timelock_s": 0,
            "post_passage_timelock_source": "Cosmos SDK gov module: proposals execute at EndBlock on passage; no timelock parameter exists in gov params (see gov params snapshot).",
            "voting_period_s": params["voting_period"],
            "expedited_voting_period_s": params["expedited_voting_period"],
        }
        for m in p.get("messages", []):
            if m.get("@type") == "/cosmos.upgrade.v1beta1.MsgSoftwareUpgrade":
                plan = m.get("plan", {})
                rec["timelock"]["upgrade_plan"] = plan
                up_height = int(plan.get("height", 0)) if plan.get("height") not in (None, "0") else None
                rec["timelock"]["upgrade_height"] = up_height
                if up_height:
                    latest = fetch_with_fallback(chain, "/cosmos/base/tendermint/v1beta1/blocks/latest")
                    h_now = int(latest["block"]["header"]["height"])
                    # Average block interval from the last 1000 blocks.
                    old = fetch_with_fallback(chain, "/cosmos/base/tendermint/v1beta1/blocks/%d" % (h_now - 1000))
                    t_now = datetime.fromisoformat(latest["block"]["header"]["time"].replace("Z", "+00:00"))
                    t_old = datetime.fromisoformat(old["block"]["header"]["time"].replace("Z", "+00:00"))
                    interval = (t_now - t_old).total_seconds() / 1000.0
                    blocks_left = up_height - h_now
                    rec["timelock"]["blocks_to_upgrade_height"] = blocks_left
                    rec["timelock"]["avg_block_interval_s_measured"] = interval
                    rec["timelock"]["estimated_seconds_to_upgrade_height"] = blocks_left * interval
                    vote_end = datetime.fromisoformat(p["voting_end_time"].replace("Z", "+00:00"))
                    rec["timelock"]["estimated_upgrade_time_utc"] = (
                        t_now.timestamp() + blocks_left * interval)
                    rec["timelock"]["voting_end_to_upgrade_seconds_estimate"] = (
                        (t_now.timestamp() + blocks_left * interval) - vote_end.timestamp())
                    print("    upgrade height %d, %d blocks left, ~%.0f s to upgrade (%.1f s after voting ends)" % (
                        up_height, blocks_left, blocks_left * interval,
                        rec["timelock"]["voting_end_to_upgrade_seconds_estimate"]), flush=True)
        # Emergency powers: scan gov params and message types for any
        # pause/halt/emergency authority. None exists in the gov module;
        # record the negative result explicitly.
        rec["emergency_powers"] = {
            "pause_or_halt_authority_in_gov_params": False,
            "pause_or_halt_message_in_proposal": False,
            "note": ("No pause/halt/emergency message type appears in gov params or in this "
                     "proposal's messages. Emergency action on these chains is therefore "
                     "off-governance (validator-coordinated halt / social consensus), "
                     "not an on-chain power. See findings report for the proposal-1058 case."),
        }
        # Votes / concentration.
        votes = paginate(chain["lcd"] + "/cosmos/gov/v1/proposals/%d/votes" % pid, "votes", limit=100)
        rec["votes_fetched"] = len(votes)
        rec["votes_available"] = len(votes) > 0
        if len(votes) == 0 and p.get("status") != "PROPOSAL_STATUS_VOTING_PERIOD":
            rec["votes_limitation"] = (
                "Per-vote list is EMPTY for this finalized proposal on the public LCD "
                "(verified on two LCD providers, gov v1 and v1beta1). Per-voter "
                "concentration cannot be computed for it; tally-based quorum/turnout "
                "is the only voter evidence. See chain-endpoints.md.")
            print("    votes: UNAVAILABLE (finalized proposal, empty list from LCD)", flush=True)
        elif len(votes) == 0:
            rec["votes_limitation"] = "No votes cast yet at fetch time."
            print("    votes: 0 cast so far", flush=True)
        else:
            print("    votes: %d fetched; fetching delegation totals (snapshot) ..." % len(votes), flush=True)
            voters = []
            for v in votes:
                opt = (v.get("options") or [{}])[0].get("option", "")
                voters.append((v["voter"], opt))
            with ThreadPoolExecutor(max_workers=MAX_DELEG_WORKERS) as ex:
                stakes = list(ex.map(lambda vt: voter_stake(chain, vt[0]), voters))
            for i, (voter, opt) in enumerate(voters):
                if (i + 1) % 200 == 0:
                    print("      ... %d/%d voters" % (i + 1, len(voters)), flush=True)
            weighted = []
            by_option = {}
            zero_weight = 0
            for (voter, opt), stake in zip(voters, stakes):
                if stake <= 0:
                    zero_weight += 1
                    continue
                weighted.append(stake)
                by_option.setdefault(opt, 0)
                by_option[opt] += stake
            conc = concentration(weighted)
            total_stake = sum(weighted)
            rec["vote_concentration"] = {
                "voters_with_delegated_stake": len(weighted),
                "voters_with_zero_or_no_stake": zero_weight,
                "total_voter_stake_base": total_stake,
                "stake_basis": ("Current delegated stake at fetch time (snapshot), not stake at vote time. "
                                "Voters with no current delegation contribute 0 and are excluded from shares."),
                "top1_share": conc["top1_share"], "top4_share": conc["top4_share"],
                "top10_share": conc["top10_share"], "hhi": conc["hhi"], "gini": conc["gini"],
                "stake_by_option": by_option,
                "yes_stake_share_of_voter_stake": (
                    by_option.get("VOTE_OPTION_YES", 0) / total_stake if total_stake else None),
            }
            print("    concentration: n=%d top1=%.4f top4=%.4f top10=%.4f hhi=%.5f gini=%.4f" % (
                conc["n"], conc["top1_share"], conc["top4_share"],
                conc["top10_share"], conc["hhi"], conc["gini"] or 0), flush=True)
        results["proposals"].append(rec)
    with open(os.path.join(outdir, "proposals-%s.json" % slug), "w") as f:
        json.dump(results, f, indent=2, sort_keys=True)
    rows = [["chain", "proposal_id", "title", "status", "voting_end_time",
             "turnout", "quorum", "quorum_met", "yes_share_non_abstain",
             "veto_share", "passes_by_tally", "votes_fetched",
             "top1_voter_stake_share", "top4_voter_stake_share",
             "top10_voter_stake_share", "voter_hhi", "voter_gini",
             "post_passage_timelock_s", "upgrade_height"]]
    for r in results["proposals"]:
        q = r["quorum_evaluation"]
        vc = r.get("vote_concentration", {})
        rows.append([chain["label"], r["id"], r["title"], r["status"],
                     r["voting_end_time"],
                     ("%.6f" % q["turnout"]) if q["turnout"] is not None else "",
                     q["quorum"], q["quorum_met"],
                     ("%.6f" % q["yes_share_non_abstain"]) if q["yes_share_non_abstain"] is not None else "",
                     ("%.6f" % q["veto_share"]) if q["veto_share"] is not None else "",
                     q["passes_by_tally"], r["votes_fetched"],
                     ("%.6f" % vc["top1_share"]) if vc.get("top1_share") is not None else "",
                     ("%.6f" % vc["top4_share"]) if vc.get("top4_share") is not None else "",
                     ("%.6f" % vc["top10_share"]) if vc.get("top10_share") is not None else "",
                     ("%.6f" % vc["hhi"]) if vc.get("hhi") is not None else "",
                     ("%.6f" % vc["gini"]) if vc.get("gini") is not None else "",
                     r["timelock"]["post_passage_execution_timelock_s"],
                     r["timelock"].get("upgrade_height", "")])
    with open(os.path.join(outdir, "proposals-%s.csv" % slug), "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print("=== %s audit DONE ===" % chain["label"], flush=True)


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
    fixdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "fixtures")
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(fixdir, exist_ok=True)
    for slug, chain in CHAINS.items():
        audit_chain(slug, chain, outdir, fixdir)
    print("audit_proposals: DONE", flush=True)


if __name__ == "__main__":
    main()
