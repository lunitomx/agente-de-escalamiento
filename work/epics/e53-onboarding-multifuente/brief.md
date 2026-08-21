# E53: Onboarding Multifuente y Conciliación (Proposal)

## Objective
Address GitHub issue #9: when a real company shares conversations, spreadsheets, catalogs, and platform exports, ESCALA must build traceable evidence and reconcile metrics that look the same but are not before diagnosing or recommending.

## Status
**Proposal / Shaped Initiative.** This issue is too large for direct stories. It needs a design phase that defines the fact contract, evidence dashboard, adaptive onboarding flow, financial reconciliation model, entity resolution rules, and decision map.

## Scope (Draft)
1. Fact contract with provenance (metric, period, date basis, source, confidence, comparability).
2. Evidence dashboard shown before diagnosis.
3. Adaptive onboarding of the 4 decisions based on authorized facts.
4. Native financial reconciliation model (platform spend, invoicing, card settlement, accounting, inventory, sales collection, attributable income).
5. Conservative entity resolution for buyers/customers.
6. Decision map and parking lot from findings.

## Success Criteria (Draft)
- A persisted fact retains source, period, definition, temporal basis, confidence, and comparability status.
- The dashboard can exist before scores and clearly shows known, pending, and non-comparable data.
- Reconciliation flow prevents comparing metrics of different nature without explicit warning.

## Next Step
Run `/rai-initiative-shaped` or `/rai-problem-shape` to produce `treatment.md` + `mvp-spec.md` before creating stories.

## Related
- GitHub issue #9
