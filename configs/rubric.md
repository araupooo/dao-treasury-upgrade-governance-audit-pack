# Severity rubric — DAO treasury and upgrade-governance findings

Scored **before** findings are written; `scripts/score_findings.py` applies
this rubric mechanically and rejects any finding whose evidence pointer is
missing from the pack outputs. Each finding carries exactly one severity.

## Severity levels

| Level | Definition (all conditions are evaluated on the measured evidence) |
|---|---|
| **Critical** | Directly exploitable path to loss or irreversible control of treasury funds or protocol upgrades, demonstrable from on-chain records, with no governance check in the path. |
| **High** | A plausible path to loss, irreversible control, or silent governance capture (e.g. quorum reachable by a small coordinated set, an unaudited emergency power, a spend with no return leg) that requires one additional condition beyond what is measured (e.g. collusion, a key compromise, an unobserved off-chain step). |
| **Medium** | A material governance or treasury weakness that does not by itself move funds: missing timelock, unverifiable threshold, unrecorded emergency authority, or a verification gap that prevents independent confirmation of a material flow. Remediation is a concrete on-chain or process change. |
| **Low** | A transparency, hygiene, or minor-parameter issue: ambiguous records, non-binding votes, small unexplained deltas, or a parameter that is weaker than peers but still inside the governance check. No funds at risk from the issue alone. |
| **Info** | A verified observation about the system's design or state that is not a weakness: confirmed reconciliations, parameters that match documented policy, or measurements that close a question. |

## Scoring rules

1. **Evidence strength gates severity.** A finding rated High or Critical must
   cite an on-chain record (proposal, tally, balance, account, or block
   height) fetched by a pack script and stored under `outputs/` or
   `fixtures/`. A finding whose only source is a forum post or documentation
   is capped at Medium.
2. **Funds at risk scale the level.** Any finding touching an amount is
   scored with that amount stated in the finding (base units and whole
   tokens). Amounts above 100,000 whole tokens raise the level by one step
   from the base definition, unless the flow is fully reconciled (then the
   finding is Info).
3. **No silent upgrades.** A finding may not be downgraded because "the
   community is trusted" — trust in named signers is not a control.
4. **Unverifiable is a finding, not an absence.** When a material control
   (multisig threshold, return leg, per-voter tally) cannot be verified from
   public data, that is recorded as a Medium finding with the exact endpoint
   and response that failed, not omitted.
5. **Reproducibility.** Every numeric claim in a finding must be traceable
   to a named output file and line/command in `outputs/` or `fixtures/`.

## Remediation guidance

Each finding carries remediation guidance naming: (a) the concrete change
(on-chain parameter, proposal type, contract query, or publication step),
(b) who can make it (governance proposal, signers, or chain maintainers),
and (c) how a reviewer re-checks it with the pack toolkit.
