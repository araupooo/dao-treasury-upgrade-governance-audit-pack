#!/usr/bin/env python3
"""compare_reproduce.py — compare a fresh-environment run against the
shipped outputs. Checks PINNED values exactly (they must not move):
gov params, multisig thresholds, IBC denom hashes, finalized-proposal
tallies, historical-height pool balances, validator-set concentration
(allowing a small tolerance for validator-set churn), and finding
scores. Live values (latest height, current pool balances, in-voting
tallies and vote counts) are checked only for presence and sane
magnitude, never for equality — they move between runs by design.

Usage: compare_reproduce.py <shipped-packdir> <fresh-packdir>
The fresh run's outputs carry the "fresh-clone-" prefix.
Exit 0 on match, 1 on any pinned mismatch.
"""
import json
import os
import sys

FAILURES = []


def check(cond, msg):
    print(("  OK   " if cond else "  FAIL ") + msg)
    if not cond:
        FAILURES.append(msg)


def load(d, name):
    with open(os.path.join(d, name)) as f:
        return json.load(f)


def main():
    shipped, fresh = sys.argv[1], sys.argv[2]
    so, fo = os.path.join(shipped, "outputs"), os.path.join(fresh, "outputs")
    print("compare_reproduce: shipped=%s fresh=%s" % (shipped, fresh))
    for slug in ("cosmoshub", "osmosis"):
        print("== %s ==" % slug)
        s = load(so, "treasury-%s.json" % slug)
        f = load(fo, "treasury-%s.json" % slug)
        check(s["chain_id"] == f["chain_id"], "%s chain_id" % slug)
        check(s["gov_params"] == f["gov_params"], "%s gov params identical" % slug)
        check(s["distribution_params"] == f["distribution_params"], "%s distribution params identical" % slug)
        check(s["staking_params"] == f["staking_params"], "%s staking params identical" % slug)
        check(s["community_pool_hist"] == f["community_pool_hist"],
              "%s historical-height pool identical" % slug)
        check(s["community_pool_hist_height"] == f["community_pool_hist_height"],
              "%s historical height identical" % slug)
        for sd, fd in zip(s["ibc_denoms"], f["ibc_denoms"]):
            check(sd == fd, "%s ibc denom %s identical" % (slug, sd["label"]))
        for sm, fm in zip(s["multisigs"], f["multisigs"]):
            check(sm["threshold_onchain"] == fm["threshold_onchain"],
                  "%s multisig %s threshold identical" % (slug, sm["address"][:16]))
            check(sm["signer_keys_onchain"] == fm["signer_keys_onchain"],
                  "%s multisig %s signer count identical" % (slug, sm["address"][:16]))
        check(abs(s["validator_concentration"]["hhi"] - f["validator_concentration"]["hhi"]) < 0.01,
              "%s validator HHI within 0.01 (%.5f vs %.5f)" % (
                  slug, s["validator_concentration"]["hhi"], f["validator_concentration"]["hhi"]))
        check(abs(s["validator_concentration"]["top4_share"] - f["validator_concentration"]["top4_share"]) < 0.02,
              "%s validator top4 share within 0.02" % slug)
        # Live values: presence + sanity only.
        check(f["latest_height"] >= s["latest_height"], "%s fresh height >= shipped height" % slug)
        check(isinstance(f["community_pool_now"], list) and len(f["community_pool_now"]) > 0,
              "%s fresh current pool non-empty" % slug)
        check(len(f["community_pool_spends_recent"]) >= len(s["community_pool_spends_recent"]),
              "%s fresh spend list at least as long" % slug)

        sp = load(so, "proposals-%s.json" % slug)
        fp = load(fo, "proposals-%s.json" % slug)
        for sr, fr in zip(sp["proposals"], fp["proposals"]):
            check(sr["id"] == fr["id"], "%s proposal %s id" % (slug, sr["id"]))
            if sr["status"] in ("PROPOSAL_STATUS_PASSED", "PROPOSAL_STATUS_REJECTED"):
                check(sr["tally"] == fr["tally"], "%s proposal %s finalized tally identical" % (slug, sr["id"]))
                # Quorum evaluation: tally-derived fields must match
                # exactly; turnout depends on live bonded stake, which
                # moves between runs, so it is checked within 0.005.
                sq, fq = sr["quorum_evaluation"], fr["quorum_evaluation"]
                qe_same = all(sq[k] == fq[k] for k in
                              ("yes", "no", "abstain", "veto", "total_voted",
                               "quorum", "quorum_met", "yes_share_non_abstain",
                               "veto_share", "passes_by_tally"))
                check(qe_same and abs(sq["turnout"] - fq["turnout"]) < 0.005,
                      "%s proposal %s finalized quorum evaluation identical (turnout %.6f vs %.6f)" % (
                          slug, sr["id"], sq["turnout"], fq["turnout"]))
            else:
                check(fr["votes_fetched"] >= 0, "%s proposal %s voting: votes fetched present" % (slug, sr["id"]))
                check(fr["tally"]["yes_count"] is not None, "%s proposal %s voting: tally present" % (slug, sr["id"]))
            check(sr["timelock"]["post_passage_execution_timelock_s"] ==
                  fr["timelock"]["post_passage_execution_timelock_s"],
                  "%s proposal %s timelock identical" % (slug, sr["id"]))
    sf = load(so, "findings-scored.json")
    ff = load(fo, "findings-scored.json")
    check(len(sf) == len(ff), "findings count identical")
    for a, b in zip(sf, ff):
        check(a["id"] == b["id"] and a["severity"] == b["severity"],
              "finding %s severity identical" % a["id"])
    print("compare_reproduce: %d failure(s)" % len(FAILURES))
    for m in FAILURES:
        print("  FAILED: " + m)
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
