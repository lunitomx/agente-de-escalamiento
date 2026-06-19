# E35 Design: Skill Golden Cases & Drift Gates

## Existing State

- E30 validates pipeline registry structure and skill references.
- E31 records guided pipeline run evidence.
- E32 validates closure evidence and prevents false complete status.
- Draft E22 proposed broader validation/drift governance but did not implement
  golden cases or release gates.

## Target Contract

Golden cases should be deterministic fixtures with expected properties, not
full-output prose snapshots.

Recommended fixture fields:

- `case_id`
- `skill`
- `input_context`
- `expected_sections`
- `required_methodology_terms`
- `forbidden_claim_patterns`
- `citation_or_evidence_required`
- `notes`

Expected properties should be narrow enough to survive harmless wording changes
and strict enough to catch methodological drift.

## Drift Gate Behavior

The gate should fail when:

- a required methodology section disappears;
- a skill makes claims that require evidence but cites none;
- output shape changes in a way that breaks downstream consumption;
- expected golden cases are changed without a version/changelog note.

## Decisions

| Decision | Rationale |
|---|---|
| Behavior properties over prose snapshots. | Full snapshots are noisy and invite false positives. |
| Small core set first. | The fixture contract needs proof before broad coverage. |
| Complement existing validators. | Registry, runner, and closure checks already exist; E35 should not duplicate them. |

## Open Questions For S35.1

- Should fixtures live under `tests/fixtures/skills/` or `.raise/golden-cases/`?
- Which four skills are the first core set: strategy, cash, people, execution,
  or session start/close?
- Should release integration use `rai gate check` directly or a standalone
  validator that later becomes a gate?

