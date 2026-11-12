#!/bin/bash
# make_sha256sums.sh — (re)generate pack/SHA256SUMS over every shipped
# file except SHA256SUMS itself. Run from anywhere; pack dir is $1.
set -eu
PACK="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$PACK"
find . -type f ! -name SHA256SUMS ! -path "./.git/*" -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
echo "SHA256SUMS: $(wc -l < SHA256SUMS) files"
