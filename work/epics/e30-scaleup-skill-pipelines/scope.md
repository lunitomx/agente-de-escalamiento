# Epic Scope: E30 - ScaleUp Skill Pipeline Orchestration

**Status:** Complete

## Objective

Turn the existing ScaleUp skill catalog into explicit pipelines of skills, so each major business workflow has a documented sequence, quality gates, stop conditions, and evidence trail. This applies Emilio's guidance to the existing `scaleup-*` skills: do not make one giant skill; orchestrate small skills as a pipeline.

## Value

The user gets repeatable business coaching flows instead of one-off command routing. The system gets governance: every pipeline can be validated against real skill files and every artifact-producing flow can declare what it needs, what it produces, and where it stops.

## In Scope

- Inventory the current 39 `scaleup-*` skills.
- Reuse the E7 orchestration pattern for `scaleup-start` and `scaleup-close`.
- Define canonical pipelines for session, people, strategy, execution, cash, and quarterly review workflows.
- Create a declarative pipeline registry at `.raise/pipelines/scaleup.yaml`.
- Add a code validator that checks registry structure against the current skill catalog.
- Add tests proving the registry is valid and common drift is caught.
- Document implementation sequencing and gates in this scope.

## Out of Scope

- Rewriting every `scaleup-*` SKILL.md in this epic.
- Creating new business methodology content.
- Building a full runtime pipeline executor.
- Changing `.scaleup/my-company/` user data.
- Deleting or renaming existing skills.

## Gemba Findings

| Finding | Evidence | Implication |
|---|---|---|
| There are 39 `scaleup-*` skills. | `find .agents/skills -maxdepth 2 -name SKILL.md | rg '/scaleup-' | wc -l` | Registry must validate against a real catalog, not memory. |
| `scaleup-start` and `scaleup-close` already embody orchestration. | E7 S7.1 design and current SKILL.md files. | E30 should generalize the pattern, not invent a competing one. |
| Domain entrypoints route, but do not yet expose full pipelines. | `scaleup-cash`, `scaleup-strategy`, `scaleup-people`, `scaleup-execution` recommend next tools. | E30 should define canonical sequences and gates over existing domain skills. |
| RaiSE methodology already says pipeline should enforce phase ordering, gates, and traceability. | `.raise/rai/framework/methodology.yaml` rule "Pipeline Is The Only Entry Point". | Registry should make phase ordering and gates explicit. |

## Planned Stories

| ID | Story | Size | Depends | Purpose |
|---|---|---:|---|---|
| S30.1 | Pipeline registry contract | M | - | Define `.raise/pipelines/scaleup.yaml` with canonical workflows, phases, gates, stop conditions, model hints, and evidence. |
| S30.2 | Registry validator | M | S30.1 | Add code validation for missing skills, duplicate phases, malformed gates, and invalid pipeline references. |
| S30.3 | Domain entrypoint alignment | L | S30.1, S30.2 | Patch `scaleup-cash`, `scaleup-strategy`, `scaleup-people`, and `scaleup-execution` to reference their canonical pipelines without changing their user-facing commands. |
| S30.4 | Session pipeline alignment | S | S30.1, S30.2 | Confirm `scaleup-start` and `scaleup-close` match registry phases and document intentional inline vs subagent execution. |
| S30.5 | Pipeline docs and close audit | M | S30.1-S30.4 | Produce final audit proving every registry skill exists, every gate is named, and every core workflow has evidence. |

## Sequencing Strategy

Risk-first walking skeleton.

1. Freeze the registry contract first because every later change depends on the shape.
2. Validate the contract with code before touching skill prose.
3. Align one domain at a time to avoid silently changing behavior across all ScaleUp commands.
4. Close with an audit that checks registry, skill references, and documentation together.

## Implementation Plan

| Order | Story | Rationale | Verification |
|---:|---|---|---|
| 1 | S30.1 | Creates the single source of truth for pipelines. | Registry exists and covers session, people, strategy, execution, cash, and quarterly review. |
| 2 | S30.2 | Prevents bad orchestration from becoming documentation theater. | `validate_pipeline_registry` passes for current registry and fails for injected drift in tests. |
| 3 | S30.4 | Existing orchestration is the safest proof point. | Start/close registry phases match current skill design. |
| 4 | S30.3 | Domain entrypoints become pipeline-aware after the contract is proven. | Domain SKILL.md files reference canonical pipeline IDs and stop conditions. |
| 5 | S30.5 | Formal closure. | Final audit has zero missing skills and zero malformed phases. |

## Milestones

| Milestone | Stories | Success Criteria |
|---|---|---|
| M1 Registry Skeleton | S30.1-S30.2 | Registry and validator exist; tests pass. |
| M2 Existing Pipeline Alignment | S30.4 | Session start/close pipelines are documented as existing patterns. |
| M3 Domain Pipeline Adoption | S30.3 | Four domain entrypoints point to canonical pipelines. |
| M4 Epic Close | S30.5 | Final audit proves registry, docs, and skills agree. |

## Done Criteria

- [x] `.raise/pipelines/scaleup.yaml` lists canonical ScaleUp pipelines.
- [x] Every pipeline phase references an existing `scaleup-*` skill.
- [x] Every pipeline declares inputs, outputs, stop conditions, gates, and evidence.
- [x] Validator tests pass.
- [x] Domain entrypoints reference their pipeline IDs.
- [x] Final audit documents any remaining manual-only or future-runtime work.
- [x] Git status is reviewed before commit.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Registry becomes documentation only. | Medium | Add validator and tests in S30.2. |
| Runtime orchestration is overbuilt too early. | High | Keep runtime executor out of scope until registry proves value. |
| Existing users expect direct commands. | Medium | Keep current commands; add pipeline awareness without renaming skills. |

## Final Status

E30 is complete for the registry-and-alignment scope. Runtime execution remains intentionally deferred: the current deliverable is a validated pipeline contract over the existing ScaleUp skills, plus entrypoint documentation that makes those pipelines visible to users and future agents.

E32 reference: this is a trusted closure for the registry-and-alignment scope
only. Runtime runner work belongs to E31 and is not claimed by E30.
