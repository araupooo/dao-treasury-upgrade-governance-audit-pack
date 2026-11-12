# Evidence index

Maps every material claim to the script output or primary source that
backs it. Files live under `outputs/` (unedited run outputs) and
`fixtures/` (snapshots exactly as fetched).

## Treasury

| Claim | Evidence |
|---|---|
| Hub pool 11,548,584.08 ATOM at height 33,847,852 | `outputs/treasury-cosmoshub.json` (`community_pool_now`, `latest_height`), `outputs/treasury-cosmoshub.csv` |
| Hub pool +25,072.36 ATOM over 101,052 blocks (hist height 33,746,800) | `outputs/treasury-cosmoshub.json` (`bond_pool_change`) |
| Osmosis pool 63,780,813.94 OSMO, 11,104.00 ION at height 74,936,465 | `outputs/treasury-osmosis.json` (`community_pool_now`) |
| Osmosis pool +0.51 OSMO over 136,465 blocks (hist height 74,800,000) | `outputs/treasury-osmosis.json` (`bond_pool_change`) |
| Hub gov params (7d vote, 40% quorum, 50% threshold, 33.4% veto, 3d expedited) | `fixtures/cosmoshub-gov-params.json`, `outputs/treasury-cosmoshub.json` (`gov_params`) |
| Osmosis gov params (5d vote, 30% quorum, 50% threshold, 33.4% veto, 1d expedited) | `fixtures/osmosis-gov-params.json`, `outputs/treasury-osmosis.json` (`gov_params`) |
| Hub community_tax 2%, inflation 10%; bonded 343.73M ATOM | `outputs/treasury-cosmoshub.json` |
| Osmosis community_tax 0, inflation 0; bonded 155.28M OSMO | `outputs/treasury-osmosis.json` |
| Hub validator concentration top1 19.03% / top4 38.15% / top10 56.56%, HHI 0.05855 | `outputs/treasury-cosmoshub.json` (`validator_concentration`), `fixtures/cosmoshub-validators.json` |
| Osmosis validator concentration top1 13.52% / top4 37.37% / top10 60.77%, HHI 0.05570; max_validators 30 | `outputs/treasury-osmosis.json` (`validator_concentration`, `staking_params`), `fixtures/osmosis-validators.json` |
| Recovery multisig threshold 4 of 6, balance 136,746 uatom, sequence 2 | `outputs/treasury-cosmoshub.json` (`multisigs`) |
| DAODAO multisig: no pubkey on record, sequence 0, zero balance; contract code_id 179, created block 33,506,400 | `outputs/treasury-cosmoshub.json` (`multisigs`, `wasm_contract_info`) |
| IBC denom hashes match proposal claims (USDC.n, USDC.inj) | `outputs/treasury-cosmoshub.json` (`ibc_denoms`, `hash_matches_claim` true) |
| USDC.inj pool balance 566,068,055,810; USDC.n absent from pool | `outputs/treasury-cosmoshub.json` (`ibc_denoms`, `community_pool_now`) |
| Recent community-pool spends (Hub 1060, 1056, 1054, 1043, 1022; Osmosis 1057, 1055, 1049, 1044, 1042) | `outputs/treasury-cosmoshub.json` / `outputs/treasury-osmosis.json` (`community_pool_spends_recent`), `fixtures/*-proposal-*.json` |

## Proposals

| Claim | Evidence |
|---|---|
| Hub 1061: upgrade height 33,935,300; ~88,455 s after voting end; turnout 38.44% (below 40% quorum) at snapshot; 865 votes; voter top10 39.37%, HHI 0.02689, Gini 0.8779 | `outputs/proposals-cosmoshub.json` (proposal 1061), `fixtures/cosmoshub-proposal-1061.json` |
| Hub 1060: passed; turnout 53.02%; yes 99.98%; votes unavailable | `outputs/proposals-cosmoshub.json` (proposal 1060), `fixtures/cosmoshub-proposal-1060.json` |
| Hub 1058: passed; turnout 58.56%; yes 99.72%; text proposal (no messages); votes unavailable | `outputs/proposals-cosmoshub.json` (proposal 1058), `fixtures/cosmoshub-proposal-1058.json` |
| Osmosis 1067: 497 votes; turnout 56.66%; voter top10 56.34%, HHI 0.03940, Gini 0.8968 | `outputs/proposals-osmosis.json` (proposal 1067), `fixtures/osmosis-proposal-1067.json` |
| Osmosis 1066: 506 votes; turnout 54.41%; yes 99.28%; no messages; voter top10 57.90%, HHI 0.04109, Gini 0.8998 | `outputs/proposals-osmosis.json` (proposal 1066), `fixtures/osmosis-proposal-1066.json` |
| Osmosis 1057: passed; turnout 66.35%; yes 99.98%; votes unavailable | `outputs/proposals-osmosis.json` (proposal 1057), `fixtures/osmosis-proposal-1057.json` |
| No post-passage timelock on either chain (0 s) | `outputs/proposals-cosmoshub.json`, `outputs/proposals-osmosis.json` (`timelock`) |
| No pause/halt authority in gov params or proposal messages | `outputs/proposals-cosmoshub.json`, `outputs/proposals-osmosis.json` (`emergency_powers`) |

## Findings

| Claim | Evidence |
|---|---|
| 12 findings scored (4 Medium, 4 Low, 4 Info) with validated evidence pointers | `outputs/findings-scored.json`, `outputs/findings-scored.csv`, `findings.json` |
| Full finding texts with remediation | `docs/findings-report.md` |
| Decisions and recommendations | `docs/decision-memo.md` |

## Primary sources

See `docs/citations.md` for the full list (on-chain endpoints,
protocol documentation, governance forum records).
