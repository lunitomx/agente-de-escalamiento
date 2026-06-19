# E35 Brief: Skill Golden Cases & Drift Gates

**Status:** Planned
**Created:** 2026-06-18
**Source draft:** E22 Validation, Drift Control & Governance

## Hypothesis

If core ScaleUp skills have golden cases and methodological drift gates, changes
can be reviewed against expected behavior before release instead of relying only
on registry or closure governance.

E30, E31, and E32 already cover pipeline registry validation, guided runner
evidence, and closure truth. E35 focuses only on the remaining valuable gap:
golden cases for skill behavior and release-time drift checks.

## Success Metrics

- Core skills have fixture-based golden cases with expected output properties.
- Drift checks detect missing methodology sections, unsupported claims, and
  output-shape regressions.
- Release gates can cite golden-case results before publishing skill changes.
- Version/change notes explain why expected behavior changed.
- E35 does not duplicate E30 registry validation, E31 runner evidence, or E32
  closure governance.

## Appetite

Medium. Build a focused validation layer for behavior-critical skills. Do not
build a generic eval platform.

## Rabbit Holes

- Revalidating pipeline registry structure already covered by E30.
- Expanding into model-quality scoring without deterministic fixtures.
- Automating release promotion without human review.
- Creating golden cases for every skill before proving the contract on a small
  core set.

