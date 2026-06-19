# Epic Scope: E35 — Skill Golden Cases & Drift Gates

**Status:** Complete
**Created:** 2026-06-18
**Renumbers and narrows:** E22 Validation, Drift Control & Governance
**Depends on context from:** E30, E31, E32

## Objective

Create focused golden cases and drift gates for core ScaleUp skills so
methodological behavior can be tested before release.

## Value

E30 made pipelines valid, E31 made them runnable with evidence, and E32 made
closure truth auditable. The remaining gap is behavioral: a skill can still
drift methodologically while passing structural validation. E35 adds focused
golden cases and release gates for that gap.

## In Scope

- Golden case fixture contract for selected core skills.
- Expected output properties for methodology-critical behavior.
- Drift checks for missing required sections, unsupported claims, and changed
  output shape.
- Prompt/version changelog that explains accepted behavior changes.
- Release gate checklist that cites golden-case results.

## Out of Scope

- Rebuilding `.raise/pipelines/scaleup.yaml` validation from E30.
- Rebuilding guided run evidence from E31.
- Rebuilding closure evidence governance from E32.
- Generic LLM eval platform or model scoring.
- Automatic release promotion without human review.

## Gemba Findings

| Finding | Evidence | Decision |
|---|---|---|
| Structural pipeline validation already exists. | `validators/pipelines.py`, `tests/test_pipeline_registry.py`, E30 final audit. | Do not duplicate registry checks. |
| Guided runtime evidence already exists. | `validators/pipeline_runner.py`, `tests/test_pipeline_runner.py`, E31 retrospective. | Golden cases should complement runner evidence, not replace it. |
| Closure truth validation already exists. | `validators/epic_closure.py`, `tests/test_epic_closure_governance.py`, E32 retrospective. | E35 should focus on skill behavior drift, not closure status. |
| Draft E22 still names a valuable missing gap. | `work/epics/e22-validation-drift-governance/scope.md` includes golden outputs and release gates. | Renumber as E35 with narrower scope. |

## Planned Stories

| ID | Story | Size | Depends | Description |
|----|-------|------|---------|-------------|
| S35.1 | Golden case fixture contract | M | - | Define fixture format, expected properties, and pass/fail reporting for skill behavior cases. |
| S35.2 | Core skill golden cases | M | S35.1 | Add initial cases for strategy, cash, people, and execution skills. |
| S35.3 | Drift check implementation | M | S35.1, S35.2 | Detect missing methodology sections, unsupported claims, and output-shape regressions. |
| S35.4 | Prompt/version changelog | S | S35.3 | Record accepted behavior changes with rationale and expected-case updates. |
| S35.5 | Release gate integration | S | S35.3, S35.4 | Add a release checklist/gate that cites golden-case results. |

## Dependencies

- Existing skill catalog under `.agents/skills/scaleup-*`.
- Existing pipeline registry and runner from E30/E31.
- Closure governance validator from E32 as a pattern for lightweight
  documentary gates.

## Done Criteria

- [x] A golden case fixture format exists and is documented.
- [x] At least the selected core skills have golden cases.
- [x] Drift checks fail on deliberate methodology/output regressions.
- [x] Accepted behavior changes require prompt/version changelog updates.
- [x] Release gate evidence can be cited without relying on old E22 draft
      status.

## Implementation Plan

Detailed story scopes, acceptance criteria, expected files, and gates live in
`story-map.md`. This scope remains the epic-level source of truth.

| Seq | Story | Rationale | Exit Evidence |
|---|---|---|---|
| 1 | S35.1 | Contract first; tests need stable fixture semantics. | Fixture schema/docs and failing/passing examples. |
| 2 | S35.2 | Fixtures must cover representative core workflows. | Initial golden case set for selected skills. |
| 3 | S35.3 | Drift gate delivers the main value. | Tests fail on injected drift and pass current behavior. |
| 4 | S35.4 | Expected behavior changes need reviewable history. | Changelog required for accepted updates. |
| 5 | S35.5 | Release workflow must make results visible. | Gate/checklist cites golden-case report. |

## Milestones

| Milestone | Stories | Success Criteria |
|---|---|---|
| M1 Golden Contract | S35.1 | Fixture format can represent expected behavior. |
| M2 Core Coverage | S35.2, S35.3 | Selected skills have drift checks with deliberate failure cases. |
| M3 Release Integration | S35.4, S35.5 | Release review cites golden-case status and accepted changes. |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Golden cases become brittle snapshots. | Medium | Medium | Validate expected properties, not whole prose blobs. |
| Scope drifts into generic eval tooling. | Medium | High | Keep first pass deterministic and fixture-based. |
| Existing pipeline gates are duplicated. | Low | Medium | Explicitly reuse E30/E31/E32 and test only behavior gaps. |

## Tag Action

No complete tag exists or should exist for E35 until stories, tests, release
gate evidence, and retrospective are complete. Old E22 remains a superseded
draft source only.

## Progress

| Story | Status | Evidence |
|---|---|---|
| S35.1 Golden case fixture contract | Complete | `validators/skill_golden_cases.py`, `tests/test_skill_golden_cases.py`, `stories/s35.1-retrospective.md`; gates passed for scoped tests, lint, format, and types. |
| S35.2 Core skill golden cases | Complete | `tests/fixtures/skill_golden_cases/core/*.yaml`, `tests/test_skill_golden_cases.py`, `stories/s35.2-retrospective.md`; gates passed for scoped tests, lint, format, and types. |
| S35.3 Drift check implementation | Complete | `validators/skill_golden_cases.py`, `tests/test_skill_golden_case_drift.py`, `tests/fixtures/skill_golden_cases/outputs/*.md`; gates passed for drift tests, fixture tests, lint, format, and types. |
| S35.4 Prompt/version changelog | Complete | `.raise/skill-golden-cases/changelog.yaml`, `tests/test_skill_golden_case_changelog.py`, `validators/skill_golden_cases.py`; gates passed for changelog, drift, fixture, lint, format, and types. |
| S35.5 Release gate integration | Complete | `scripts/check_skill_golden_cases.py`, `.raise/release/skill-golden-cases.md`, `tests/test_skill_golden_case_gate.py`; release check reports `status: pass`. |
