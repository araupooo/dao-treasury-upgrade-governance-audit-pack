# Primary sources

Every measured claim in this pack links to one of the sources below.
On-chain records are cited by chain, height, and proposal ID; the
corresponding raw JSON is stored under `fixtures/` or `outputs/`.

## On-chain records (fetched live, public LCD, no key)

- Cosmos Hub LCD (primary): https://rest.cosmos.directory/cosmoshub
- Cosmos Hub LCD (fallback): https://lcd-cosmoshub.keplr.app
- Osmosis LCD (primary): https://rest.cosmos.directory/osmosis
- Cosmos Hub gov params (voting period 604800s, quorum 0.40, threshold
  0.50, veto 0.334, expedited 259200s / 0.667):
  `/cosmos/gov/v1/params/voting` — snapshot `fixtures/cosmoshub-gov-params.json`
- Osmosis gov params (voting period 432000s, quorum 0.30, threshold
  0.50, veto 0.334, expedited 86400s / 0.80):
  `/cosmos/gov/v1/params/voting` — snapshot `fixtures/osmosis-gov-params.json`
- Cosmos Hub community pool, heights 33,847,624 and 33,746,800:
  `/cosmos/distribution/v1beta1/community_pool` — `outputs/treasury-cosmoshub.json`
- Osmosis community pool, heights 74,934,511 and 74,800,000:
  `/cosmos/distribution/v1beta1/community_pool` — `outputs/treasury-osmosis.json`
- Proposals (full JSON in `fixtures/`): Cosmos Hub 1061, 1060, 1058;
  Osmosis 1067, 1066, 1057 — `/cosmos/gov/v1/proposals/{id}`
- Tallies: `/cosmos/gov/v1/proposals/{id}/tally` — `outputs/proposals-*.json`
- Votes (in-voting proposals only): `/cosmos/gov/v1/proposals/{id}/votes`
- Recovery multisig account (threshold 4 of 6, 6 pubkeys):
  `/cosmos/auth/v1beta1/accounts/cosmos1z8pq5cn7tdrwwzlwm0e44fgq07e43ner6vph64`
- USDC migration multisig account (no pubkey on record, sequence 0):
  `/cosmos/auth/v1beta1/accounts/cosmos1amny2nf23uauu79lzp299tvh9v4a62uuxvh8xyj7qavrm0adztsq5sz864`
- Staking pools and params: `/cosmos/staking/v1beta1/pool`,
  `/cosmos/staking/v1beta1/params` (Osmosis max_validators 30; Hub 180)
- Validator sets: `/cosmos/staking/v1beta1/validators?status=BOND_STATUS_BONDED`
  — snapshots `fixtures/cosmoshub-validators.json`, `fixtures/osmosis-validators.json`

## Protocol documentation

- Cosmos SDK governance module (voting period, quorum, threshold, veto,
  deposit, expedited proposals; proposals execute on passage, no
  post-passage timelock parameter): https://docs.cosmos.network/
- Cosmos Hub documentation: https://hub.cosmos.network/
- Osmosis documentation (governance, community pool, minting):
  https://docs.osmosis.zone/
- Gaia v29.1.0 release (upgrade binaries and checksums referenced by
  proposal 1061): https://github.com/cosmos/gaia/releases/tag/v29.1.0
- Injective USDC documentation (USDC.inj: native Circle issuance,
  bank denom `erc20:0xa00C59fF5a080D2b954d0c75e46E22a0c371235a`,
  6 decimals): https://docs.injective.network/developers-defi/usdc-stablecoin
- Cosmos Hub chain-registry asset list entry for USDC.inj:
  https://github.com/cosmos/chain-registry/blob/master/cosmoshub/assetlist.json
- Circle: discontinuing support for USDC and CCTP V1 on Noble:
  https://www.circle.com/blog/circle-is-discontinuing-support-for-usdc-and-cctp-v1-on-noble
- Circle: native USDC and CCTP on Injective (May 7, 2026):
  https://www.circle.com/blog/now-available-native-usdc-cctp-on-injective
- Circle USDC contract addresses:
  https://developers.circle.com/stablecoins/usdc-contract-addresses

## Governance forum records

- Proposal 1058 discussion (Neutron recovery multisig, halt at block
  33,086,740, restart state change at height 33,086,741):
  https://forum.cosmos.network/t/discussion-move-the-1-227-121-atom-recovered-after-the-neutron-exploit-to-the-neutron-recovery-multisig
- Cosmos Hub forum (general): https://forum.cosmos.network/
- Osmosis governance forum (Commonwealth):
  https://commonwealth.im/osmosis/discussions
- Proposal 1060 DAODAO page (multisig members and proposals):
  https://daodao.zone/dao/cosmos1amny2nf23uauu79lzp299tvh9v4a62uuxvh8xyj7qavrm0adztsq5sz864/proposals

## Notes on sources NOT used

- PublicNode LCDs (`cosmoshub-api.publicnode.com`,
  `osmosis-api.publicnode.com`) returned empty responses from this
  environment and were dropped; see `configs/chain-endpoints.md`.
- No block explorer, indexer, or analytics service requiring an API key
  was used; the pack reruns with public endpoints only.
