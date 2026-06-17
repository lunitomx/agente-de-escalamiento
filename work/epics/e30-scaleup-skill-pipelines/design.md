# E30 Design - ScaleUp Skill Pipeline Orchestration

## Design Premise

Emilio's direction is not "make bigger skills." It is "think pipeline": a complete artifact should be produced by a sequence of small skills, each with bounded context, explicit gate, and an independent inference budget.

For ScaleUp, the raw material already exists: 39 `scaleup-*` skills. E30 adds the orchestration contract above them.

## Existing Pattern To Reuse

E7 S7.1 established the orchestration rule:

- An orchestrator sequences phases.
- Sub-skills do substantive work.
- Quality gates are code-based where possible.
- The orchestrator passes minimal context forward.

Current state has a pragmatic variant: `scaleup-start` inlines simple file-read phases while preserving sub-skill names for future expansion. E30 accepts both execution modes as long as the registry declares them.

## Target Component

### `.raise/pipelines/scaleup.yaml`

Declarative registry of canonical ScaleUp workflows:

- `id`: stable pipeline identifier.
- `entrypoint`: user-facing skill that starts or represents the workflow.
- `intent`: what business artifact or decision the pipeline serves.
- `inputs`: required starting context.
- `phases`: ordered skill sequence.
- `gates`: quality checks and stop conditions.
- `outputs`: expected artifacts or decisions.
- `evidence`: what proves the pipeline ran or can be audited.

### `validators/pipelines.py`

Code gate for the registry:

- Registry file exists and parses as YAML.
- Every pipeline has required keys.
- Every phase has a unique `id`.
- Every referenced skill exists in `.agents/skills/<skill>/SKILL.md`.
- Every phase declares output, evidence, and inference budget.
- Gate names are unique and reference known phases when applicable.

### `tests/test_pipeline_registry.py`

Regression tests:

- Current registry validates.
- Missing skill is caught.
- Duplicate phase IDs are caught.
- Missing gate name is caught.

## Canonical Pipelines

| Pipeline | Entrypoint | Existing skills sequenced |
|---|---|---|
| `scaleup-session-start` | `scaleup-start` | `scaleup-start-load-profile`, `scaleup-start-load-sessions`, `scaleup-start-load-tasks`, `scaleup-start-present` |
| `scaleup-session-close` | `scaleup-close` | `scaleup-close-capture`, `scaleup-close-log`, `scaleup-close-sync` plus summary module gate |
| `scaleup-people-development` | `scaleup-people` | `scaleup-people-fac`, `scaleup-people-values`, `scaleup-people-topgrading` |
| `scaleup-strategy-development` | `scaleup-strategy` | `scaleup-strategy-swot`, `scaleup-strategy-opsp`, `scaleup-strategy-7strata`, `scaleup-context-add` |
| `scaleup-execution-system` | `scaleup-execution` | `scaleup-execution-rockefeller`, `scaleup-execution-rhythms`, `scaleup-execution-priorities`, `scaleup-task-add` |
| `scaleup-cash-acceleration-system` | `scaleup-cash` | `scaleup-cash-ccc`, `scaleup-cash-power1`, `scaleup-cash-acceleration`, `scaleup-task-add` |
| `scaleup-quarterly-review` | `scaleup-pulse` | `scaleup-diagnose`, `scaleup-pulse`, `scaleup-progress`, `scaleup-dashboard`, `scaleup-export` |

## Execution Modes

| Mode | Use When | Example |
|---|---|---|
| `inline` | Phase is simple file read or formatting and current skill already embeds it. | `scaleup-start-load-profile` inside `scaleup-start`. |
| `subskill` | Phase benefits from separate context, richer reasoning, or independent output. | Domain worksheets like `scaleup-cash-ccc`. |
| `code_gate` | Validation is deterministic. | `validate_session_log`, `validate_pipeline_registry`. |
| `manual_gate` | Human review or business decision is required. | Choose top cash acceleration moves. |

## Key Decisions

### D1: Registry before runtime executor

Build a validated registry first. A runtime executor is not useful until the team agrees on pipeline shape, phase metadata, and gates.

### D2: Existing skills remain the unit of work

E30 does not rename or collapse skills. Pipelines compose them.

### D3: Domain entrypoints become pipeline-aware routers

`scaleup-cash`, `scaleup-strategy`, `scaleup-people`, and `scaleup-execution` should continue to work as familiar commands, but they should reference canonical pipeline IDs and explain stop/resume behavior.

### D4: Gates must be explicit

A phase without a gate can exist, but the pipeline must say why. Ambiguous "looks good" checks are not enough.

## Verification Strategy

1. Static validation of registry.
2. Unit tests for drift detection.
3. Grep check that domain entrypoints reference pipeline IDs after S30.3.
4. Final E30 audit documenting what is declarative now and what remains future runtime work.

