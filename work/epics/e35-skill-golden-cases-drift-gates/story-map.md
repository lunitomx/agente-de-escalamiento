# E35 Story Map: Skill Golden Cases & Drift Gates

**Status:** Complete
**Planning date:** 2026-06-18
**Closed:** 2026-06-18

## Closure Note

E35 closed as a deterministic release-check implementation. It does not provide
a native `rai gate` id, live model evaluation, or semantic scoring.

## Delivery Strategy

Prove a small deterministic behavior-gate before expanding coverage. E35 should
test methodology-critical properties, not prose snapshots, and it must reuse the
existing E30/E31/E32 validation surfaces instead of duplicating them.

## Story Sequence

| Seq | Story | Purpose | Primary Output | Gate |
|---|---|---|---|---|
| 1 | S35.1 Golden case fixture contract | Define what a skill behavior case means. | Fixture schema + validator. | Bad fixtures fail with actionable errors. |
| 2 | S35.2 Core skill golden cases | Add first representative cases. | Strategy/cash/people/execution fixtures. | Cases cover required methodology properties. |
| 3 | S35.3 Drift check implementation | Detect behavior regressions. | Drift validator + tests. | Injected drift fails deterministically. |
| 4 | S35.4 Prompt/version changelog | Track accepted behavior changes. | Changelog contract + validation. | Changed expectations require rationale. |
| 5 | S35.5 Release check integration | Make results visible before release. | Script/checklist integration. | Release review cites golden-case status. |

## S35.1 — Golden Case Fixture Contract

### User Story

As a skill maintainer, I want a fixture format for expected skill behavior so
methodological drift can be detected without comparing full prose snapshots.

### In Scope

- Define fixture fields: case id, skill, input context, expected sections,
  required methodology terms, forbidden claim patterns, evidence requirement,
  and notes.
- Validate fixture completeness and skill references.
- Add positive and negative fixture examples.

### Out of Scope

- Running live LLM calls.
- Creating golden cases for every skill.
- Release gate integration.

### Acceptance Criteria

- Given a complete fixture for an existing skill, validation passes.
- Given a fixture referencing a missing skill, validation fails.
- Given a fixture without expected properties, validation fails.

### Likely Files

- `validators/skill_golden_cases.py`
- `tests/test_skill_golden_cases.py`
- `tests/fixtures/skill_golden_cases/*.yaml`

### Verification

- `rai gate check gate-tests --scope tests/test_skill_golden_cases.py`
- `rai gate check gate-lint`
- `rai gate check gate-format`
- `rai gate check gate-types`

## S35.2 — Core Skill Golden Cases

### User Story

As a ScaleUp reviewer, I want initial golden cases for the highest-value skills
so behavior drift is visible in strategy, cash, people, and execution workflows.

### In Scope

- Add golden cases for selected `scaleup-strategy`, `scaleup-cash`,
  `scaleup-people`, and `scaleup-execution` skills.
- Define expected methodology properties for each selected skill.
- Include at least one evidence-required case where unsupported claims are
  forbidden.

### Out of Scope

- Exhaustive coverage of all skills.
- Large example transcript datasets.
- UI reporting.

### Acceptance Criteria

- Each selected skill has at least one golden case.
- Each case declares expected sections and prohibited weak behavior.
- Cases are deterministic and do not require external services.

### Likely Files

- `tests/fixtures/skill_golden_cases/scaleup_strategy.yaml`
- `tests/fixtures/skill_golden_cases/scaleup_cash.yaml`
- `tests/fixtures/skill_golden_cases/scaleup_people.yaml`
- `tests/fixtures/skill_golden_cases/scaleup_execution.yaml`
- `tests/test_skill_golden_cases.py`

### Verification

- `rai gate check gate-tests --scope tests/test_skill_golden_cases.py`
- `rai gate check gate-lint`
- `rai gate check gate-format`
- `rai gate check gate-types`

## S35.3 — Drift Check Implementation

### User Story

As a release reviewer, I want a drift check that fails when skill behavior loses
required methodology, unsupported-claim controls, or expected output shape.

### In Scope

- Implement deterministic drift checks over fixture properties.
- Detect missing required sections.
- Detect forbidden claim patterns.
- Detect missing evidence/citation behavior where required.
- Add deliberate regression tests.

### Out of Scope

- Semantic grading by a model.
- Full text snapshot comparison.
- Pipeline registry validation already owned by E30.

### Acceptance Criteria

- Given an output missing a required section, the drift check fails.
- Given an output with forbidden unsupported claims, the drift check fails.
- Given a compliant output, the drift check passes.

### Likely Files

- `validators/skill_golden_cases.py`
- `tests/test_skill_golden_case_drift.py`
- `tests/fixtures/skill_golden_cases/outputs/*.md`

### Verification

- `rai gate check gate-tests --scope tests/test_skill_golden_case_drift.py`
- `rai gate check gate-tests --scope tests/test_skill_golden_cases.py`
- `rai gate check gate-lint`
- `rai gate check gate-format`
- `rai gate check gate-types`

## S35.4 — Prompt/Version Changelog

### User Story

As a maintainer, I want expected behavior changes to carry rationale so golden
case updates do not hide unreviewed methodological drift.

### In Scope

- Define changelog fields for changed skill, case id, reason, reviewer, and
  expected behavior change.
- Require changelog entry when fixture expectations change.
- Document accepted change flow.

### Out of Scope

- Release automation.
- External approval workflow.
- Historical reconstruction of all prior prompt changes.

### Acceptance Criteria

- Fixture expectation changes without changelog evidence fail validation.
- Changelog entries explain the intended behavior change.
- Accepted changes remain auditable after the story closes.

### Likely Files

- `.raise/skill-golden-cases/changelog.md` or equivalent selected path
- `validators/skill_golden_cases.py`
- `tests/test_skill_golden_case_changelog.py`

### Verification

- `rai gate check gate-tests --scope tests/test_skill_golden_case_changelog.py`
- `rai gate check gate-lint`
- `rai gate check gate-format`
- `rai gate check gate-types`

## S35.5 — Release Check Integration

### User Story

As a release reviewer, I want golden-case status visible in release checks so
skill changes cannot ship without deterministic behavior evidence.

### In Scope

- Add a release checklist entry for golden-case validation.
- Document when the gate is required.
- Record sample passing/failing report output.
- Confirm the gate complements E30/E31/E32 rather than duplicating them.
- Document that the implementation is a versioned script/checklist, not a
  native `rai gate` id.

### Out of Scope

- Automatic release promotion.
- CI provider configuration unless already present.
- Generic dashboard.

### Acceptance Criteria

- Release review can cite golden-case pass/fail status.
- Release check output names failed cases and why they failed.
- Documentation states how this differs from pipeline registry, runner, and
  closure gates.

### Likely Files

- `scripts/check_skill_golden_cases.py`
- `.raise/release/skill-golden-cases.md`
- `validators/skill_golden_cases.py`
- `tests/test_skill_golden_case_gate.py`
- `work/epics/e35-skill-golden-cases-drift-gates/final-audit.md`

### Verification

- `rai gate check gate-tests --scope tests/test_skill_golden_case_gate.py`
- `rai gate check gate-lint`
- `rai gate check gate-format`
- `rai gate check gate-types`

## Cross-Story Risks

| Risk | Mitigation |
|---|---|
| Golden cases become brittle prose snapshots. | Validate required properties and forbidden patterns, not full paragraphs. |
| Scope expands into generic LLM evaluation. | Keep first version deterministic and fixture-based. |
| Gate duplicates E30/E31/E32. | Each story must state which existing gate it complements and what behavior gap it covers. |

## Definition Of Ready For First Story

- Confirm fixture storage path.
- Confirm first four skills to cover.
- Confirmed in S35.5: release integration is a standalone versioned check
  because no project-local native `rai gate` registry was found.
