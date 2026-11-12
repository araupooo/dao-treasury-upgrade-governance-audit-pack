#!/usr/bin/env python3
"""score_findings.py — apply the documented severity rubric
(configs/rubric.md) to the authored findings (findings.json) and emit
scored outputs.

Validation (fail-loud, exit 1):
  - every finding has exactly one severity from the rubric levels;
  - every evidence pointer names a file that exists under outputs/ or
    fixtures/ and, where a JSON key path is given (file.json:a.b.c),
    that key exists in the file;
  - High/Critical findings must cite an on-chain record (a JSON output
    produced by fetch_treasury.py or audit_proposals.py), per rubric
    rule 1.
Usage: score_findings.py [packdir]
Writes outputs/findings-scored.json and outputs/findings-scored.csv.
"""
import csv
import json
import os
import sys

LEVELS = ["Critical", "High", "Medium", "Low", "Info"]


def key_exists(data, path):
    cur = data
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return False
    return True


def main():
    packdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..")
    outdir = os.path.join(packdir, "outputs")
    fixdir = os.path.join(packdir, "fixtures")
    src = os.path.join(packdir, "findings.json")
    with open(src) as f:
        findings = json.load(f)
    scored = []
    for fd in findings:
        fid = fd.get("id", "?")
        sev = fd.get("severity")
        assert sev in LEVELS, "%s: severity %r not in rubric levels %s" % (fid, sev, LEVELS)
        assert fd.get("title") and fd.get("description") and fd.get("remediation"), \
            "%s: missing title/description/remediation" % fid
        ev = fd.get("evidence", [])
        assert ev, "%s: no evidence pointers" % fid
        onchain_cited = False
        for ptr in ev:
            if ":" in ptr and ptr.endswith(".json"):
                pass
            parts = ptr.split(":", 1)
            rel = parts[0]
            path = os.path.join(outdir, rel) if os.path.exists(os.path.join(outdir, rel)) \
                else os.path.join(fixdir, rel)
            assert os.path.exists(path), "%s: evidence file missing: %s" % (fid, rel)
            if rel.startswith("treasury-") or rel.startswith("proposals-"):
                onchain_cited = True
            if len(parts) == 2 and rel.endswith(".json"):
                with open(path) as f:
                    data = json.load(f)
                assert key_exists(data, parts[1]), \
                    "%s: evidence key missing: %s in %s" % (fid, parts[1], rel)
        if sev in ("High", "Critical"):
            assert onchain_cited, \
                "%s: rubric rule 1 — High/Critical findings must cite an on-chain record (treasury-*.json or proposals-*.json)" % fid
        scored.append(fd)
        print("  %s [%s] evidence=%d pointers OK" % (fid, sev, len(ev)), flush=True)
    with open(os.path.join(outdir, "findings-scored.json"), "w") as f:
        json.dump(scored, f, indent=2, sort_keys=True)
    rows = [["id", "severity", "title", "amount_at_risk", "evidence_count"]]
    for fd in scored:
        rows.append([fd["id"], fd["severity"], fd["title"],
                     fd.get("amount_at_risk", ""), len(fd["evidence"])])
    with open(os.path.join(outdir, "findings-scored.csv"), "w", newline="") as f:
        csv.writer(f).writerows(rows)
    from collections import Counter
    print("score_findings: DONE — %d findings: %s" % (
        len(scored), dict(Counter(fd["severity"] for fd in scored))), flush=True)


if __name__ == "__main__":
    main()
