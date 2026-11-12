# Findings and remediation report — DAO treasury and upgrade-governance audit

Chains: Cosmos Hub (cosmoshub-4) and Osmosis (osmosis-1). Snapshot:
Cosmos Hub height 33,847,852 (2026-11-12 18:30 UTC); Osmosis height
74,936,465 (2026-11-12 18:36 UTC). Severity rubric:
`configs/rubric.md`. Every finding is scored by
`scripts/score_findings.py` and its evidence pointers are validated
against `outputs/` and `fixtures/`. Totals: 12 findings — 4 Medium,
4 Low, 4 Info; no Critical, no High.

## Summary table

| ID | Severity | Title | Amount at risk |
|---|---|---|---|
| F-01 | Medium | No post-passage execution timelock on either chain | Hub pool 11,548,584.08 ATOM; Osmosis pool 63,780,813.94 OSMO |
| F-02 | Medium | Per-vote records for finalized proposals are not retrievable from public LCDs | n/a (verification gap) |
| F-03 | Medium | USDC migration multisig threshold is not independently verifiable from the public LCD | 566,067.055810 USDC.n sent; 566,068.055810 USDC.inj returned |
| F-04 | Info | USDC.n to USDC.inj migration reconciles, with a +1.000000 USDC difference | 566,067.055810 USDC.n; delta +1.000000 USDC.inj |
| F-05 | Medium | Emergency powers are off-governance: chain halt and state change preceded the vote | 1,227,121.374688 ATOM moved by state change |
| F-06 | Low | Validator-set concentration is high on both chains | Hub bonded 343.73M ATOM; Osmosis bonded 155.28M OSMO |
| F-07 | Low | Voting-stake concentration in live votes is high (Gini ~0.88–0.90) | n/a (governance concentration) |
| F-08 | Low | Osmosis community pool is static: no issuance or tax inflow in params | Osmosis pool 63,780,813.94 OSMO; 11,104.00 ION |
| F-09 | Low | Gaia v29.1.0 upgrade executes about 24.6 hours after voting ends | n/a (upgrade timing) |
| F-10 | Info | Osmosis proposal 1066 is a non-binding signal with no executable message | n/a |
| F-11 | Info | Cosmos Hub proposal 1061 turnout is below quorum at the snapshot (vote still open) | n/a |
| F-12 | Info | Osmosis community-pool burn of 55,500,000 OSMO executed as specified | 55,500,000 OSMO |

## Findings

### F-01 — Medium — No post-passage execution timelock on either chain

Neither chain has a post-passage timelock parameter in its governance
module. A passed proposal executes at EndBlock on passage (or at its
scheduled upgrade height for software upgrades). The voting period
(7 days Cosmos Hub, 5 days Osmosis; 3 days / 1 day expedited) is the
only delay between a vote closing and funds moving or code activating.
A passed community-pool spend therefore moves funds immediately, with
no window for a second look, a veto by an external guardian, or an
operator opt-out.

Evidence: `outputs/treasury-cosmoshub.json` (`gov_params`),
`outputs/treasury-osmosis.json` (`gov_params`),
`outputs/proposals-cosmoshub.json` proposal 1061
`timelock.post_passage_execution_timelock_s` = 0,
`outputs/proposals-osmosis.json` proposal 1067 same field = 0.

Remediation: governance proposal to add an execution delay for
treasury spends and upgrades (a timelock module or a mandatory delay
parameter in the gov module), with the delay published in gov params.
Re-check: rerun `fetch_treasury.py` and confirm a timelock parameter
appears in gov params and that the proposal outputs record a non-zero
`post_passage_execution_timelock_s`.

### F-02 — Medium — Per-vote records for finalized proposals are not retrievable from public LCDs

The votes endpoint returns an empty list for every finalized proposal
checked (Cosmos Hub 1060 and 1058; Osmosis 1057), on two independent
LCD providers and both gov v1 and v1beta1, while it returns full vote
lists for proposals still in their voting period (865, 497, and 506
votes). Independent per-voter verification of passed proposals — who
voted, with how much stake — is therefore impossible from public LCD
data alone; only the aggregate tally survives.

Evidence: `outputs/proposals-cosmoshub.json` proposals 1060 and 1058
(`votes_fetched` = 0, `votes_available` = false);
`outputs/proposals-osmosis.json` proposal 1057 (same).

Remediation: publish per-vote records for finalized proposals through
a public indexer or an archived endpoint, and record the archive URL
in the proposal metadata. Re-check: rerun `audit_proposals.py` and
confirm `votes_fetched` > 0 for finalized proposals.

### F-03 — Medium — USDC migration multisig threshold is not independently verifiable from the public LCD

Proposal 1060 states the recipient is a 4-of-6 DAODAO multisig, but
the threshold cannot be confirmed from on-chain account state via the
public LCD: the auth module returns a BaseAccount with no pubkey and
sequence 0 (expected for a CosmWasm contract account), and CosmWasm
smart-contract queries (`threshold`, `list_voters`) against the
contract return HTTP 500 from this LCD. The contract itself exists
on-chain (code_id 179, created at block 33,506,400, admin is itself),
but its voter set and threshold were not retrievable here. The 4-of-6
claim therefore rests on the proposal text alone.

Evidence: `outputs/treasury-cosmoshub.json` (`multisigs` — recipient
`cosmos1amny2nf23uauu79lzp299tvh9v4a62uuxvh8xyj7qavrm0adztsq5sz864`,
`threshold_onchain` null, `wasm_contract_info` present).

Remediation: publish the multisig's voter set and threshold from the
contract state (e.g. a DAODAO page link or a contract-query result) in
the proposal's forum thread, and require future multisig mandates to
include a verifiable contract-state citation. Re-check: query the
contract's threshold from an LCD that serves wasm smart queries and
compare with the proposal text.

### F-04 — Info — USDC.n to USDC.inj migration reconciles, with a +1.000000 USDC difference

Proposal 1060 sent 566,067.055810 USDC.n from the community pool to
the migration multisig. The pool no longer holds any USDC.n (denom
`ibc/F663521BF...` absent), and now holds 566,068.055810 USDC.inj
(denom `ibc/E107DB3E...`, hash verified locally by sha256 recomputation
against the proposal's claimed trace paths). The return exceeds the
sent amount by exactly 1.000000 USDC. The proposal text states
proceeds are 1:1 less gas/relayer fees, which would reduce rather than
increase the amount, so the +1 USDC is an unexplained top-up — small,
in the pool's favour, and not a loss. Transaction-level confirmation
of the individual legs was not available (the LCD's tx-search endpoint
is unimplemented), so reconciliation rests on the two pool balances.

Evidence: `outputs/treasury-cosmoshub.json` (`ibc_denoms` —
`hash_matches_claim` true for both denoms;
`community_pool_spends_recent` — proposal 1060).

Remediation: no action required beyond the multisig publishing the
transaction hashes for each migration leg in the forum thread, as the
proposal promises, so the +1 USDC top-up is explained on the record.

### F-05 — Medium — Emergency powers are off-governance: chain halt and state change preceded the vote

No pause, halt, or emergency message type exists in the governance
parameters or in any audited proposal's messages on either chain. Yet
the September 2026 Neutron incident was handled by validators halting
the Cosmos Hub at block 33,086,740 and restarting on Gaia v28.3.0
with a one-time state change at height 33,086,741 that moved
1,227,121.374688 ATOM to a 4-of-6 recovery multisig — all before
proposal 1058, which merely ratified the mandate afterwards. The
recovery multisig itself is verified on-chain (LegacyAminoPubKey
threshold 4 of 6; balance now 136,746 uatom, sequence 2), but the
halt/restart authority that created it is uncodified social consensus
among validators, not an on-chain power with a defined threshold or
scope.

Evidence: `outputs/proposals-cosmoshub.json` proposal 1058
(`emergency_powers`, empty `messages` — a text proposal);
`outputs/treasury-cosmoshub.json` (`multisigs` — recovery multisig
`cosmos1z8pq5cn7tdrwwzlwm0e44fgq07e43ner6vph64`, threshold 4,
6 signer keys, sequence 2).

Remediation: codify emergency authority in a governance proposal: who
may halt the chain, under what conditions, what state changes are
permitted, and the deadline for retrospective ratification. Re-check:
confirm a published emergency procedure exists in Hub documentation
and that future halt events cite it.

### F-06 — Low — Validator-set concentration is high on both chains

Osmosis caps its active set at 30 validators (`max_validators` = 30,
verified in staking params); the top 4 hold 37.37% and the top 10
hold 60.77% of bonded stake (HHI 0.05570). On the Cosmos Hub (180
validators) the top 1 holds 19.03%, top 4 hold 38.15%, and top 10 hold
56.56% (HHI 0.05855). A coordinated top-4 set is close to a blocking
minority on either chain, and on Osmosis only 30 entities share all
validation.

Evidence: `outputs/treasury-cosmoshub.json` and
`outputs/treasury-osmosis.json` (`validator_concentration`,
`staking_params`).

Remediation: monitor top-N shares each quarter with this toolkit;
consider raising Osmosis `max_validators` and reviewing Hub
minimum-commission / delegation-program incentives that entrench the
top set. Re-check: rerun `fetch_treasury.py` and compare
`validator_concentration` top4/top10 shares.

### F-07 — Low — Voting-stake concentration in live votes is high (Gini ~0.88–0.90)

Delegation-weighted concentration over all fetched voters: Cosmos Hub
1061 (864 voters with stake) top-1 10.59%, top-4 26.34%, top-10
39.37%, HHI 0.02689, Gini 0.8779. Osmosis 1067 (494 voters) top-1
9.36%, top-4 31.18%, top-10 56.34%, HHI 0.03940, Gini 0.8968.
Osmosis 1066 (503 voters) top-1 9.62%, top-4 32.05%, top-10 57.90%,
HHI 0.04109, Gini 0.8998. The top 10 voters command a majority of the
voting stake on Osmosis live votes. Stake is measured at fetch time
(snapshot), not at vote time.

Evidence: `outputs/proposals-cosmoshub.json` proposal 1061
(`vote_concentration`); `outputs/proposals-osmosis.json` proposals
1067 and 1066 (same).

Remediation: no on-chain fix is available from this finding alone;
track the metric per proposal with this toolkit and flag any vote
where the top-4 share exceeds the veto threshold (33.4%). Re-check:
rerun `audit_proposals.py` while votes are live.

### F-08 — Low — Osmosis community pool is static: no issuance or tax inflow in params

Osmosis `community_tax` is 0 and mint inflation is 0 (the mint
endpoint returns "Not Implemented"; `/osmosis/mint/v1beta1/inflation`
returns 0). Measured over 136,465 blocks the uosmo pool balance moved
by only +0.506633 OSMO (63,780,813.94 OSMO at height 74,934,511). The
pool is therefore funded by protocol revenue (e.g. taker fees), not by
issuance or a staking-reward tax, so its sustainability depends on fee
flow that is not visible in the governance parameters.

Evidence: `outputs/treasury-osmosis.json` (`bond_pool_change`,
`distribution_params`, `inflation`).

Remediation: document the pool's revenue sources and their recent
rates in Osmosis documentation, so spend proposals can be sized
against real inflow. Re-check: rerun `fetch_treasury.py` over a longer
block span and compare `bond_pool_change`.

### F-09 — Low — Gaia v29.1.0 upgrade executes about 24.6 hours after voting ends

Proposal 1061 schedules the upgrade at height 33,935,300. At the
measured average block interval of 5.68 s over the last 1,000 blocks,
that height is reached about 496,336 s after the fetch, i.e. about
88,455 s (24.6 hours) after voting ends (2026-11-17T11:57:22Z).
Combined with F-01 (no timelock), operators have under a day between
a passing vote and a mandatory binary switch.

Evidence: `outputs/proposals-cosmoshub.json` proposal 1061
(`timelock` — `upgrade_height` 33,935,300, `blocks_to_upgrade_height`
87,351, `avg_block_interval_s_measured` 5.68,
`voting_end_to_upgrade_seconds_estimate` 88,455).

Remediation: schedule future upgrades at least one full voting period
after the earliest possible passage, or add a post-passage delay (see
F-01). Re-check: rerun `audit_proposals.py` and read
`timelock.voting_end_to_upgrade_seconds_estimate`.

### F-10 — Info — Osmosis proposal 1066 is a non-binding signal with no executable message

Proposal 1066 ("Signal a 10% Minimum Validator Commission") contains
no messages. Whatever the vote outcome, no parameter changes on-chain;
a separate parameter-change proposal is required to enforce a minimum
commission. The vote is a sentiment signal only, and its 99.28% yes
share of counted votes at fetch does not itself change any rule.

Evidence: `outputs/proposals-osmosis.json` proposal 1066 (`messages`
empty, `quorum_evaluation`).

Remediation: none for the audit; a follow-up parameter-change
proposal is needed if the signal is to be enforced. Re-check: look for
a parameter-change proposal citing 1066.

### F-11 — Info — Cosmos Hub proposal 1061 turnout is below quorum at the snapshot (vote still open)

At fetch time (height 33,847,852, 2026-11-12 18:30 UTC) proposal 1061
has 38.44% turnout against a 40% quorum, with 100.00% yes share of
counted votes and 0 veto. Voting ends 2026-11-17T11:57:22Z, so the
outcome is still open: if turnout does not reach 40%, the upgrade
fails despite unanimous yes votes. This is a snapshot observation, not
a weakness.

Evidence: `outputs/proposals-cosmoshub.json` proposal 1061
(`quorum_evaluation`).

Remediation: none; re-check after voting ends by rerunning
`audit_proposals.py`.

### F-12 — Info — Osmosis community-pool burn of 55,500,000 OSMO executed as specified

Proposal 1057 (passed, turnout 66.35%, yes share 99.98%) sent
55,500,000,000,000 uosmo (55,500,000 OSMO) from the community pool to
the burn address `osmo1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqmcn030`. The
spend message, recipient, and amount in the on-chain proposal match
the proposal title ("Burn Community Pool OSMO to Reach 100 Million
Burned"). The burn address balance itself was not queried (outside
the audited surface), so the burn is confirmed at the
proposal-message level, not at the recipient-balance level.

Evidence: `outputs/treasury-osmosis.json`
(`community_pool_spends_recent` — proposal 1057).

Remediation: none; for full confirmation, query the burn address
balance in a follow-up run.

## Robustness checks performed

- Re-fetch at a second (historical) height for both pools: Hub
  +25,072.36 ATOM over 101,052 blocks; Osmosis +0.51 OSMO over
  136,465 blocks. Both deltas are consistent with the chains'
  parameters (Hub: 2% community tax, 10% inflation; Osmosis: 0 tax,
  0 inflation).
- The toolkit fails loudly on unreachable endpoints: during the build
  run the primary Hub LCD returned HTTP 500 for the community-pool
  query and the script fell back to the keplr LCD and logged the
  failure; a persistent failure exits non-zero after 5 retries with
  exponential backoff.
- IBC denom identities were verified by independent local sha256
  recomputation, not by trusting the proposal text.
- The CosmWasm smart-query path for the DAODAO multisig was attempted
  (`threshold`, `list_voters`) and returned HTTP 500; the failure is
  recorded as finding F-03 rather than silently skipped.
