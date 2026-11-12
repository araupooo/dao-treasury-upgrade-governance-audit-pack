# Decision memo — DAO treasury and upgrade-governance audit

## Question

Can a reviewer independently verify, from public data alone, that the
Cosmos Hub and Osmosis treasuries are governed safely — that spends are
authorised, traceable, and reversible in effect, and that protocol
upgrades cannot activate without a real vote and a usable preparation
window?

## Answer in brief

Mostly yes for the flows that were checked, with four Medium gaps that
should be closed before the next large spend or upgrade:

1. **No execution timelock.** A passed spend moves funds immediately
   (F-01). Add a delay.
2. **Finalized votes are unverifiable per-voter.** Only aggregate
   tallies survive in public LCD data (F-02). Publish an archive.
3. **The USDC migration multisig's threshold is unverified.**
   The migration itself reconciled, but its 4-of-6 claim rests on the
   proposal text (F-03, F-04).
4. **Emergency authority is uncodified.** The Hub halt and the
   1,227,121 ATOM state change happened before any vote (F-05).

No Critical or High findings. No funds were found missing or
misdirected in any audited flow.

## Evidence base (primary sources)

- **On-chain records** (public LCD, no key): Cosmos Hub gov params —
  voting period 604800 s, quorum 0.40, threshold 0.50, veto 0.334,
  expedited 259200 s / 0.667; Osmosis gov params — voting period
  432000 s, quorum 0.30, threshold 0.50, veto 0.334, expedited
  86400 s / 0.80. Community pools at pinned heights: Hub
  11,548,584.08 ATOM at height 33,847,852 (2026-11-12 18:30 UTC);
  Osmosis 63,780,813.94 OSMO at height 74,936,465. Tallies and
  proposal messages for six proposals (Hub 1061, 1060, 1058; Osmosis
  1067, 1066, 1057). Recovery multisig account
  (`cosmos1z8pq5cn7tdrwwzlwm0e44fgq07e43ner6vph64`): LegacyAminoPubKey
  threshold 4 of 6, balance 136,746 uatom, sequence 2. Full JSON in
  `outputs/` and `fixtures/`.
- **Proposal texts** (on-chain, in the proposal JSON): 1060 states
  the 566,067.055810 USDC.n spend, the 4-of-6 DAODAO multisig with six
  named members, and the 1:1 return promise; 1058 states the halt at
  block 33,086,740, the restart state change at height 33,086,741,
  and the 1,227,121.374688 ATOM mandate. See `fixtures/`.
- **Independent checks performed by the pack**: IBC denom hashes
  recomputed locally with sha256 and matched to the proposal claims
  exactly; pool balances compared across two pinned heights per chain;
  validator and voter concentration computed from fetched stake data.
- **Protocol documentation**: Cosmos SDK governance module
  (https://docs.cosmos.network/), Cosmos Hub docs
  (https://hub.cosmos.network/), Osmosis docs
  (https://docs.osmosis.zone/), Gaia v29.1.0 release
  (https://github.com/cosmos/gaia/releases/tag/v29.1.0), Injective
  USDC documentation
  (https://docs.injective.network/developers-defi/usdc-stablecoin),
  Circle's Noble USDC wind-down notice
  (https://www.circle.com/blog/circle-is-discontinuing-support-for-usdc-and-cctp-v1-on-noble).
  Full list: `docs/citations.md`.

## Findings that support the decisions below

| Decision | Supporting findings | Evidence |
|---|---|---|
| Adopt the USDC.inj migration as complete; no clawback | F-04 (reconciled, +1 USDC in pool's favour) | Pool holds 566,068,055,810 USDC.inj; USDC.n absent; hashes verified |
| Require a timelock before the next large treasury spend | F-01, F-09 (upgrade 24.6 h after vote end) | Gov params; proposal 1061 timelock estimate |
| Publish finalized per-vote records | F-02 | Empty votes lists for 1060, 1058, 1057 on two LCDs |
| Require contract-state proof for future multisig mandates | F-03 | Auth module: no pubkey; wasm smart queries HTTP 500 |
| Codify emergency halt/restart authority | F-05 | Proposal 1058 text; no pause authority in gov params |
| Treat the 1066 commission signal as non-binding until a parameter proposal passes | F-10 | Proposal 1066 has no messages |
| Note Osmosis pool sustainability depends on fee revenue, not issuance | F-08 | community_tax 0, inflation 0, pool delta +0.51 OSMO / 136,465 blocks |

## Recommendations (ordered)

1. **Timelock (F-01, F-09).** Propose a post-passage execution delay
   for `MsgCommunityPoolSpend` and `MsgSoftwareUpgrade` on both
   chains, sized at no less than one voting period, and schedule
   upgrades at least one voting period after the earliest possible
   passage. Until then, treat any expedited treasury proposal as
   high-attention: the expedited window is 3 days on the Hub and 1
   day on Osmosis.
2. **Vote archive (F-02).** Stand up a public per-vote archive for
   finalized proposals (indexer or pruned-node snapshot) and link it
   from proposal metadata. Without it, no passed vote can ever be
   re-audited voter by voter.
3. **Multisig proof (F-03).** Future multisig mandates must cite the
   contract state (voter set, threshold, code id) from a queryable
   endpoint, not only the proposal text. The DAODAO multisig for
   proposal 1060 should publish its migration transaction hashes, as
   the proposal promises, to close the +1 USDC observation (F-04).
4. **Emergency procedure (F-05).** Publish a written emergency
   procedure: who may halt, what state changes are allowed, and the
   ratification deadline. The 1058 precedent — halt first, vote
   later — worked, but it worked on trust, and trust is not a
   control.
5. **Concentration watch (F-06, F-07).** Re-run this toolkit
   quarterly. Flag any live vote where the top-4 voter share exceeds
   the 33.4% veto threshold, and any quarter where Osmosis top-10
   validator share rises above 65%.

## What this memo does NOT claim

- It does not claim the Neutron recovery multisig's onward transfer
  to Neutron was verified: the recipient
  (`neutron1yr29fd7uzdjp2jsq8hrta8mvyd6ex7vumn0shy`) lives on Neutron
  and was not queried (see `docs/methodology.md`, limitation 6).
- It does not claim transaction-level proof of the USDC migration
  legs: the LCD's tx-search endpoint is unimplemented, so the
  reconciliation rests on proposal messages plus pool balances
  (limitation 2).
- It does not claim voter-stake figures are exact at vote time: they
  are fetch-time snapshots (limitation 4).
- Turnout and tallies for the three in-voting proposals (Hub 1061,
  Osmosis 1067, 1066) are snapshots as of 2026-11-12 ~18:30–18:48 UTC
  and will have moved since.
