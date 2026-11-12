#!/bin/bash
# verify_digests.sh — verify every file in pack/SHA256SUMS. Exit non-zero
# on any mismatch or missing file. Usage: verify_digests.sh [packdir]
set -u
PACK="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$PACK"
[ -f SHA256SUMS ] || { echo "FATAL: SHA256SUMS missing"; exit 1; }
sha256sum -c SHA256SUMS
