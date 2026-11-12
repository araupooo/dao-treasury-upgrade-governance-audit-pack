#!/bin/bash
# clean_reproduce.sh — fresh-environment reproduction check.
# Copies the pack (scripts, src, configs, findings.json) to a temp dir,
# runs the full toolkit there with log prefix "fresh-clone-", then runs
# compare_reproduce.py against the shipped outputs. Exits non-zero on
# any mismatch in the pinned values or on any toolkit failure.
# Live values (current height, current pool balances, in-voting tallies)
# legitimately move between runs; the comparison script checks only
# pinned, height-independent values exactly.
set -u
PACK="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d /tmp/dao-audit-repro-XXXXXX)"
echo "clean_reproduce: temp dir $TMP"
mkdir -p "$TMP/pack"
cp -r "$PACK/scripts" "$PACK/src" "$PACK/configs" "$PACK/findings.json" "$TMP/pack/"
cd "$TMP/pack"
bash scripts/run_all.sh "$TMP/work" "fresh-clone-" || { echo "clean_reproduce: FATAL — toolkit failed in fresh copy"; exit 1; }
python3 "$PACK/scripts/compare_reproduce.py" "$PACK" "$TMP/pack" || { echo "clean_reproduce: FATAL — comparison failed"; exit 1; }
echo "clean_reproduce: OK — fresh-environment run matches pinned values"
echo "clean_reproduce: temp dir kept at $TMP for inspection"
