# Pinned public endpoints, block heights, and proposal IDs

All data sources are public and need no API key or private credential.
The toolkit fails loudly (non-zero exit) if a primary endpoint is
unreachable after retries; the fallback endpoint is tried only for the
Cosmos Hub LCD.

## Endpoints

| Chain | Primary LCD | Fallback LCD | Status at build time |
|---|---|---|---|
| Cosmos Hub (cosmoshub-4) | https://rest.cosmos.directory/cosmoshub | https://lcd-cosmoshub.keplr.app | Primary OK; fallback OK |
| Osmosis (osmosis-1) | https://rest.cosmos.directory/osmosis | — (none verified) | Primary OK |

Dropped: `https://cosmoshub-api.publicnode.com` and
`https://osmosis-api.publicnode.com` returned empty responses from this
environment and are not used.

Rate limiting observed on cosmos.directory (HTTP 403 after rapid bursts).
The client sends a `User-Agent` header, waits 0.5 s between requests, and
retries 403/429/5xx with exponential backoff (5 s → 80 s, 5 attempts).

## Pinned snapshot heights (2026-11-12/13)

| Chain | Current height at fetch | Historical height | Note |
|---|---|---|---|
| Cosmos Hub | 33,847,624 (2026-11-12 18:08:35 UTC) | 33,746,800 | ~100,824 blocks (~7 days) earlier; uatom pool balance compared across the two heights |
| Osmosis | 74,934,511 (2026-11-12 18:08:44 UTC) | 74,800,000 | Snapshot height served by the LCD; height 74,900,000 is pruned ("version does not exist") |

Heights are recorded in the fetch outputs; a reproduction run will show
later heights and slightly different balances, which is expected. The
comparison script checks the pinned, height-independent values exactly
(params, thresholds, finalized tallies, IBC denom hashes) and checks live
balances only for presence and sane magnitude.

## Proposals audited (6)

| Chain | Proposal | Title | Status at fetch |
|---|---|---|---|
| Cosmos Hub | 1061 | Gaia v29.1.0 upgrade | VOTING_PERIOD (ends 2026-11-17T11:57:22Z) |
| Cosmos Hub | 1060 | Migrate Community Pool USDC.n to USDC.inj via a Community Multisig | PASSED |
| Cosmos Hub | 1058 | Move the 1,227,121 ATOM recovered after the Neutron exploit to the Neutron recovery multisig | PASSED |
| Osmosis | 1067 | CosmWasm Pinning Update - November 2026 | VOTING_PERIOD (ends 2026-11-14T17:20:59Z) |
| Osmosis | 1066 | Signal a 10% Minimum Validator Commission | VOTING_PERIOD (ends 2026-11-14T15:34:57Z) |
| Osmosis | 1057 | Burn Community Pool OSMO to Reach 100 Million Burned | PASSED |

## Treasury records pinned

- Cosmos Hub recovery multisig: `cosmos1z8pq5cn7tdrwwzlwm0e44fgq07e43ner6vph64`
  (LegacyAminoPubKey, threshold 4 of 6; balance 136,746 uatom at fetch).
- Cosmos Hub USDC migration multisig (DAODAO): `cosmos1amny2nf23uauu79lzp299tvh9v4a62uuxvh8xyj7qavrm0adztsq5sz864`
  (4-of-6 per proposal 1060 text; CosmWasm contract account — auth-module
  record shows no pubkey / sequence 0).
- Neutron recovery multisig (recipient in proposal 1058):
  `neutron1yr29fd7uzdjp2jsq8hrta8mvyd6ex7vumn0shy` (not queried; Neutron
  LCD is outside this pack's scope — stated limitation).
- Osmosis burn address (proposal 1057):
  `osmo1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqmcn030`.
- IBC denoms: USDC.n on Hub `ibc/F663521BF1836B00F5F177680F74BFB9A8B5654A694D0D2BC249E03CF2509013`
  (transfer/channel-536/uusdc); USDC.inj on Hub
  `ibc/E107DB3E8AABB49C87CB737A1ABBFDBA9803ECAE05E295D8D7A0B1A7FE83706C`
  (transfer/channel-220/erc20:0xa00C59fF5a080D2b954d0c75e46E22a0c371235a).
  Both hashes were recomputed locally with sha256 and match the proposal
  text exactly (see `outputs/treasury-cosmoshub.json`, `ibc_denoms`).

## Endpoints that do NOT work on this LCD (documented limitations)

- `/ibc/apps/transfer/v1/denom_traces/{hash}` → `{"code": 12, "message": "Not Implemented"}`.
- `/cosmos/tx/v1beta1/txs?events=...` → `{"code": 13, "message": "query cannot be empty"}`.
  Transaction-level confirmation of individual transfers is therefore not
  available from this LCD; flows are reconciled from proposal messages and
  pool balances instead.
- `/cosmos/gov/v1/proposals/{id}/votes` returns an empty list for
  finalized proposals on both LCDs tried (gov v1 and v1beta1). Per-voter
  concentration is computed only for proposals still in their voting
  period.
- `/cosmos/mint/v1beta1/inflation` on Osmosis → `{"code": 12, "message": "Not Implemented"}`
  (Osmosis minting is complete; inflation is 0 as returned by
  `/osmosis/mint/v1beta1/inflation`).
