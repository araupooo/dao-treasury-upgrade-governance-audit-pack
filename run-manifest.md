# Run manifest

## Shipped run (primary evidence)

- Date: 2026-11-12 18:30–18:48 UTC (2026-11-13 01:30–01:48 WIB)
- Commands run (in order):
  1. `python3 scripts/fetch_treasury.py outputs fixtures` — exit 0
     (~6 min). One primary-LCD HTTP 500 on the Hub community-pool
     query; the script fell back to the keplr LCD and logged it.
  2. `python3 scripts/audit_proposals.py outputs fixtures` — exit 0
     (~11 min). A first attempt failed with HTTP 400 on a votes
     pagination key containing `+`; fixed by URL-encoding pagination
     keys in `src/onchain.py` and `scripts/audit_proposals.py`, then
     rerun clean.
  3. `python3 scripts/score_findings.py .` — exit 0; 12 findings
     (4 Medium, 4 Low, 4 Info), all evidence pointers validated.
  4. `python3 scripts/make_index.py .` — exit 0 (after fixing a
     `bond_denom` key lookup in the generator).
- Pinned heights at fetch: Cosmos Hub 33,847,852 (18:30 UTC);
  Osmosis 74,936,465 (18:36 UTC). Historical heights: Hub 33,746,800;
  Osmosis 74,800,000.
- Environment: this VM — Python 3.12.3 (standard library only),
  4 CPUs, ~483 MB RAM available at build time. No API keys, no
  private credentials used anywhere.

## Fresh-environment reproduction

- `scripts/clean_reproduce.sh` copies the pack to a temp dir and runs
  the full toolkit there, then `compare_reproduce.py` checks every
  pinned value.
- Attempt 1: FAILED during Hub proposal 1061 delegation fetching —
  `URLError` on both LCDs (primary + fallback) after 5 retries,
  coinciding with a runtime restart; both LCDs probed healthy (HTTP
  200) immediately after. Assessed as a transient outage, not a pack
  defect. Log: `work/clean-reproduce.log`.
- Attempt 2: toolkit completed exit 0 (temp dir
  `/tmp/dao-audit-repro-IYVzcT`). Comparison initially reported 3
  failures — all on finalized proposals' quorum evaluations, caused by
  bonded stake moving between runs (turnout differed by 0.000004).
  Root cause was an over-strict comparison, not a data mismatch:
  `compare_reproduce.py` was corrected to compare tally-derived
  quorum fields exactly and allow turnout within 0.005.
- Comparison re-run with the corrected script against the attempt-2
  fresh outputs: **0 failures**. All pinned values verified:
  gov params, distribution params, staking params, historical-height
  pool balances, IBC denom hashes, multisig thresholds and signer
  counts, validator HHI/top-4 within tolerance, finalized tallies,
  timelocks, finding severities. Log: `work/clean-reproduce-2.log`.

## Files shipped

See `SHA256SUMS` (verified with `bash scripts/verify_digests.sh`).
