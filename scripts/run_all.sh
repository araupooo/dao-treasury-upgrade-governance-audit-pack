#!/bin/bash
# run_all.sh — run the full measurement suite and write every output
# under pack/outputs/ (raw logs are kept unedited).
# Usage: run_all.sh [workdir] [log-prefix]
# workdir defaults to <task>/work. log-prefix (default "") is prepended to
# every output filename; scripts/clean_reproduce.sh passes "fresh-clone-"
# so a reproduction run never overwrites the shipped outputs.
set -u
PACK="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${1:-$PACK/../work}"
PREFIX="${2:-}"
OUT="$PACK/outputs"
FIX="$PACK/fixtures"
mkdir -p "$OUT" "$FIX" "$WORK"
LOG="$OUT/${PREFIX}run-all.log"

{
echo "run_all: pack=$PACK work=$WORK out=$OUT prefix=$PREFIX"
echo "run_all: date $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "run_all: python $(python3 --version 2>&1)"
echo "=== fetch_treasury ==="
python3 "$PACK/scripts/fetch_treasury.py" "$OUT" "$FIX" || { echo "FATAL: fetch_treasury failed"; exit 1; }
echo "=== audit_proposals ==="
python3 "$PACK/scripts/audit_proposals.py" "$OUT" "$FIX" || { echo "FATAL: audit_proposals failed"; exit 1; }
echo "=== score_findings ==="
python3 "$PACK/scripts/score_findings.py" "$PACK" || { echo "FATAL: score_findings failed"; exit 1; }
echo "=== make_index ==="
python3 "$PACK/scripts/make_index.py" "$PACK" || { echo "FATAL: make_index failed"; exit 1; }
echo "=== make_sha256sums ==="
bash "$PACK/scripts/make_sha256sums.sh" "$PACK" || { echo "FATAL: make_sha256sums failed"; exit 1; }
echo "run_all: DONE — outputs in $OUT"
ls -l "$OUT"
} 2>&1 | tee "$LOG"
# tee preserves the pipeline exit status poorly; re-check the log tail.
grep -q "run_all: DONE" "$LOG" || { echo "run_all: FAILED (see $LOG)"; exit 1; }
