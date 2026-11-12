# Methodology

## Scope

Two live DAOs/protocols, chosen because their treasury balances, treasury
flows, and full proposal lifecycles are all fetchable from public,
no-key endpoints:

- **Cosmos Hub (cosmoshub-4)** — community pool, governance parameters,
  proposals, staking set.
- **Osmosis (osmosis-1)** — same surface, different parameters
  (5-day voting period, 30% quorum, 30-validator active set).

Six proposals were audited end to end (creation, quorum, voting-power
concentration, execution timelock, emergency powers): Cosmos Hub 1061,
1060, 1058; Osmosis 1067, 1066, 1057.

## Data sources and tools

- Public Cosmos SDK LCD (REST) endpoints only — `rest.cosmos.directory`
  (primary) and `lcd-cosmoshub.keplr.app` (Hub fallback). No API key, no
  private credential, no authenticated service anywhere in the toolkit.
- `scripts/fetch_treasury.py` — balances, parameters, validator set,
  multisig accounts, IBC denom verification, recent community-pool
  spends.
- `scripts/audit_proposals.py` — proposal detail, tally, per-vote lists,
  delegation-weighted concentration, timelock and emergency-power
  assessment.
- `scripts/score_findings.py` — applies `configs/rubric.md` and validates
  every evidence pointer.
- `src/onchain.py` — the only HTTP client: retries 403/429/5xx with
  exponential backoff, waits 0.5 s between requests, and raises
  (fail-loud) after 5 attempts so a broken endpoint can never silently
  produce an empty result.

## Measurements

- **Treasury balance**: `/cosmos/distribution/v1beta1/community_pool` at
  the current height and at a pinned historical height
  (header `x-cosmos-block-height`). The delta over the block span is the
  measured net inflow over that window.
- **Inflows**: community tax
  (`/cosmos/distribution/v1beta1/params`) and mint inflation
  (`/cosmos/mint/v1beta1/inflation`). On Osmosis the mint endpoint
  returns "Not Implemented" and `/osmosis/mint/v1beta1/inflation`
  returns 0 — the pool is funded by protocol revenue, not issuance.
- **Outflows**: every `MsgCommunityPoolSpend` in the most recent 40
  proposals per chain, with recipient, amount, and status, plus the
  full proposal JSON snapshotted under `fixtures/`.
- **Multisig threshold**: `/cosmos/auth/v1beta1/accounts/{address}` —
  `LegacyAminoPubKey.threshold` and the count of `public_keys`. For
  CosmWasm multisig (DAODAO) accounts the auth module carries no pubkey;
  the threshold is then taken from the proposal text and flagged as
  not independently verifiable from the auth module.
- **IBC denom identity**: recomputed locally as
  `sha256("transfer/{channel}/{base_denom}")` and compared with the
  denom claimed in the proposal text and with the denom present in the
  community pool.
- **Quorum / turnout**: tally
  (`/cosmos/gov/v1/proposals/{id}/tally`) evaluated against the bonded
  stake (`/cosmos/staking/v1beta1/pool`) and the on-chain quorum,
  threshold, and veto parameters. Turnout = total voted / bonded.
  Pass condition: turnout >= quorum, yes > threshold of
  (yes + no + veto), veto < veto_threshold of all votes.
- **Voting-power concentration**: for proposals still in their voting
  period, every vote is fetched (paginated) and each voter's current
  total delegated bond-denom stake is fetched
  (`/cosmos/staking/v1beta1/delegations/{voter}`). Top-1/4/10 shares,
  Herfindahl-Hirschman Index, and Gini are computed over those stakes.
  Stake is measured at fetch time (snapshot), not at vote time — this is
  an approximation and is stated wherever the numbers appear.
- **Execution timelock**: Cosmos SDK governance has no post-passage
  timelock parameter; proposals execute at EndBlock on passage, or at
  the scheduled upgrade height for `MsgSoftwareUpgrade`. The voting
  period is therefore the only delay, and it is recorded as such. For
  upgrades, the seconds between voting end and the upgrade height are
  estimated from the measured average block interval over the last
  1,000 blocks.
- **Emergency powers**: assessed by scanning gov parameters and every
  message type in the audited proposals for pause/halt/emergency
  authority. None exists in the gov module on either chain; emergency
  action is therefore off-governance (validator-coordinated halt and
  social consensus), documented with the proposal-1058 case.

## Known limitations (all verified, none assumed)

1. Per-vote lists for **finalized** proposals return empty from the
   public LCDs (verified on two providers, gov v1 and v1beta1).
   Per-voter concentration is therefore computed only for proposals
   still in their voting period; finalized proposals are audited from
   tally + parameters only.
2. The IBC denom-trace endpoint and the transaction-search endpoint are
   not implemented on the public LCD used, so individual transfer
   transactions cannot be fetched from it. Flows are reconciled from
   proposal messages plus pool balances instead (e.g. the proposal-1060
   return leg is confirmed by the pool holding 566,068,055,810 USDC.inj
   after sending 566,067,055,810 USDC.n).
3. Historical pool queries only work at snapshot heights kept by the
   LCD node (Osmosis height 74,900,000 is pruned; 74,800,000 works).
4. Voter stake is a fetch-time snapshot, not stake at vote time.
5. The DAODAO multisig threshold (4-of-6) is documented in the
   proposal text; the auth module carries no pubkey for that contract
   account, so the threshold is not independently verifiable from
   on-chain account state via this LCD. The CosmWasm contract query
   was attempted and its result is recorded in the treasury output.
6. The Neutron recovery multisig (proposal 1058 recipient) lives on
   Neutron; its balance and signers were not queried (outside the two
   chains' LCD scope) and are reported from the proposal text only.

## Reproduction

See `README.md`. `scripts/clean_reproduce.sh` runs the whole toolkit
in a fresh copy and compares every pinned value exactly; live values
(current height, current balances, in-voting tallies) are checked for
presence and sane magnitude only, because they move between runs.
