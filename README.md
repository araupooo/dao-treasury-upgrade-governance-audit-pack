# DAO Treasury and Upgrade-Governance Audit Pack

A consolidated, third-party-rerunnable evidence pack covering DAO
treasury flows and protocol-upgrade governance for two live DAOs:
**Cosmos Hub (cosmoshub-4)** and **Osmosis (osmosis-1)**. Six proposals
audited end to end (creation, quorum, voting-power concentration,
execution timelock, emergency powers); twelve severity-rated findings
with remediation guidance; a primary-source decision memo.

## What is in here

- `scripts/` — `fetch_treasury.py`, `audit_proposals.py`,
  `score_findings.py`, `run_all.sh`, `clean_reproduce.sh`,
  `compare_reproduce.py`, `verify_digests.sh`, `make_sha256sums.sh`,
  `make_index.py`
- `src/onchain.py` — public-LCD client (retries with exponential
  backoff, fail-loud) and concentration statistics
- `configs/` — `rubric.md` (severity rubric), `chain-endpoints.md`
  (pinned endpoints, heights, proposal IDs)
- `findings.json` — authored findings with evidence pointers (validated
  by `score_findings.py`)
- `outputs/` — unedited run logs, treasury/proposal JSON + CSV,
  findings-scored JSON + CSV
- `fixtures/` — proposal and parameter snapshots exactly as fetched
- `docs/` — `methodology.md`, `citations.md`, `evidence-index.md`,
  `findings-report.md`, `decision-memo.md`, `index.html`
- `SHA256SUMS` — digests of every shipped file

## Headline numbers (snapshot 2026-11-12 ~18:30–18:48 UTC)

- Cosmos Hub community pool: **11,548,584.08 ATOM** at height
  33,847,852 (+25,072.36 ATOM over the prior 101,052 blocks).
  Osmosis pool: **63,780,813.94 OSMO** at height 74,936,465
  (+0.51 OSMO over 136,465 blocks).
- USDC migration (Hub proposal 1060) reconciles: 566,067.055810 USDC.n
  out, **566,068.055810 USDC.inj** back (+1.000000 USDC).
- Recovery multisig (Hub proposal 1058): threshold **4 of 6 verified
  on-chain**; balance now 136,746 uatom (the 1,227,121.37 ATOM has
  moved on).
- Findings: **12 total — 4 Medium, 4 Low, 4 Info; no Critical, no
  High.** Headline gaps: no post-passage execution timelock on either
  chain; per-vote records for finalized proposals not retrievable from
  public LCDs; DAODAO multisig threshold not independently verifiable
  from the public LCD; emergency halt/restart authority uncodified.

## Reproduction (no API key, no private credential needed)

Requirements: Python 3.10+ (standard library only), `bash`, `sha256sum`,
`curl` (optional). The toolkit only talks to public LCD endpoints.

```bash
# Full run (about 15–20 minutes; most of it is polite 0.5 s gaps and
# LCD rate-limit backoff while fetching ~1,900 voter delegation records)
bash scripts/run_all.sh

# Verify file digests
bash scripts/verify_digests.sh

# Fresh-environment reproduction check (copies the pack to a temp dir,
# reruns everything, compares every pinned value exactly)
bash scripts/clean_reproduce.sh
```

Outputs land in `outputs/` (run logs are kept unedited). A reproduction
run writes `fresh-clone-*` prefixed files so shipped outputs are never
overwritten.

## Notes for the reviewer

- Live values move between runs (current height, current pool balances,
  tallies and vote counts for the three in-voting proposals). The
  comparison script checks pinned values exactly (gov params,
  thresholds, IBC denom hashes, finalized tallies, historical-height
  pool balances) and live values for presence and sane magnitude only.
- Voter-stake concentration uses each voter's **current** delegated
  stake (snapshot at fetch time), not stake at vote time.
- Per-vote lists for **finalized** proposals return empty from the
  public LCDs (verified on two providers); see finding F-02 and
  `docs/methodology.md` for the full limitations list.
- The public LCD rate-limits bursts (HTTP 403/500). The client retries
  with exponential backoff and falls back to the keplr LCD for the Hub;
  a persistent failure exits non-zero rather than producing empty
  results.
