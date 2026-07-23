---
epic_id: "E40"
title: "Executive Cockpit and Coaching"
grounded_in: "Gemba of coaching/{welcome,diagnose,router,progress}, escala_server/workspace/authority.py, escala_server/meetings, escala_server/financial, escala-skills/escala-strategy-opsp/SKILL.md"
---

# Epic Design: Executive Cockpit and Coaching

## Gemba findings

- `coaching.welcome` and `coaching.diagnose` already provide a useful conversational baseline, but they persist unvalidated YAML with scores 1–5, use wall-clock dates and do not retain provenance, unknowns or evidence freshness. E40 adds a strict local seam instead of silently changing those legacy commands.
- `coaching.router` already establishes the four-decision routing vocabulary (`people`, `strategy`, `execution`, `cash`) and the command mapping. E40 will expose the same mapping through typed routing and use a 0–100 score scale.
- `coaching.dashboard` is a read-only Markdown progress view over legacy `.escala` files. It is not an executive cockpit: it has no drill-down contract, source IDs or local artifact authority. E40 adds a bounded HTML/JSON cockpit writer.
- E37 `WorkspaceConfig`/`validate_workspace` owns the installer-machine and exchange boundary. E40 must call it before every state/artifact write and must keep derived state under `data_root`.
- E38 and E39 expose financial/meeting evidence with source IDs and redacted receipts. E40 consumes those IDs as evidence references; it does not parse or copy their source content.
- The strategy skill and OPSP skill define the conversational sections (purpose, BHAG, sandbox, brand promise, Profit per X, annual/quarterly priorities). E40 stores those sections as a typed partial plan and keeps missing answers unresolved.

## Target components

| Component | Responsibility | Key interface |
|-----------|---------------|---------------|
| `escala_server/executive/models.py` | Closed Pydantic contracts for profile, evidence, diagnosis, cockpit, strategy, routing and execution | `CompanyProfile`, `DecisionAssessment`, `ExecutiveDiagnostic`, `ExecutiveCockpit`, `StrategyPlan`, `ExecutionState` |
| `escala_server/executive/onboarding.py` | Validate supplied profile answers, preserve unknowns and create bounded material questions | `build_company_profile(answers)` |
| `escala_server/executive/diagnostic.py` | Aggregate evidence-backed 0–100 scores, freshness, blockers and next questions | `build_diagnostic(answers, evidence)` |
| `escala_server/executive/cockpit.py` | Select pain, build drill-down and render/write deterministic local visual artifacts | `build_cockpit`, `render_cockpit_html`, `write_cockpit` |
| `escala_server/executive/coaching.py` | Build partial OPSP/vision and route to existing four-decision skills without unsupported claims | `build_strategy_plan`, `route_coaching` |
| `escala_server/executive/persistence.py` | Atomically persist/query derived state and execution continuity below `data_root` | `save_state`, `load_state`, `save_execution_state` |
| `tests/test_e40_executive_cockpit.py` | Synthetic positive and negative qualification across all requirements | deterministic fixture, path/redaction/authority tests |
| `validators/e40_gates.py` | Eight fail-closed requirement gates | `gate-req-e40-001` … `gate-req-e40-008` |
| `scripts/qualify_e40.py` | Run the synthetic entrepreneur and emit exact ledger receipts | `main()` |

## Key contracts

```python
def build_company_profile(
    answers: tuple[ProfileAnswer, ...],
) -> OnboardingResult: ...

def build_diagnostic(
    answers: tuple[DiagnosticAnswer, ...],
    evidence: tuple[EvidenceItem, ...] = (),
) -> ExecutiveDiagnostic: ...

def build_cockpit(
    diagnostic: ExecutiveDiagnostic,
    strategy: StrategyPlan | None = None,
    execution: ExecutionState | None = None,
) -> ExecutiveCockpit: ...

def build_strategy_plan(
    answers: tuple[StrategyAnswer, ...],
) -> StrategyPlan: ...

def route_coaching(
    request: CoachingRequest,
    diagnostic: ExecutiveDiagnostic,
) -> CoachingRoute: ...

def save_state(config: WorkspaceConfig, state: ExecutiveState) -> StateReceipt: ...
def load_state(config: WorkspaceConfig) -> ExecutiveState | None: ...
def write_cockpit(config: WorkspaceConfig, cockpit: ExecutiveCockpit) -> CockpitArtifact: ...
```

All models are immutable/closed (`extra="forbid"`, `frozen=True`). Evidence references contain only stable `source_id`, relative locator, freshness and confidence; receipts never contain machine paths or source text. Unknowns are first-class values, and routing returns `supported=False` when a material answer is absent.

## Data flow

`owner answers + E37/E38/E39 evidence references → validated profile → diagnostic 0–100 → cockpit drill-down → strategy/routing → local execution state/report`

The only write path is `data_root/.escala-executive/`. The exchange remains read-only and no module calls a network client or writes SQLite.

## Decisions

### D1 — Derived executive state is JSON below validated `data_root`

The existing SQLite authority remains untouched; E40 stores a deterministic, atomic JSON snapshot for derived executive contracts so a fresh install can inspect/export it without placing state in a synced folder. A later migration may map this state to the authoritative SQLite schema, but that is not required for E40.

### D2 — Scores require supplied evidence or explicit owner answers

An answer without a source is still attributable to the owner only when explicitly marked `owner_input`; missing/ambiguous answers produce `unknown` and questions. The engine never transforms missing input into a negative score or a claim about a person.

### D3 — Local HTML is the visual surface

The cockpit is rendered as escaped, deterministic HTML with accessible labels and a JSON mirror. It is opened from the filesystem; no HTTP server, cloud endpoint or browser automation is part of E40.

## Negative matrix

- incomplete onboarding → unresolved required-field questions, no fabricated value;
- score without evidence/owner attribution → `evidence_limited` and no supported recommendation;
- missing trend/source → freshness `unknown`, not regression;
- exchange/database overlap → `validate_workspace` fails before any write;
- path-like/source-text values in receipt → redaction test fails closed;
- unsupported explicit coaching request → `supported=False` plus clarifying question.

## Testing strategy

- Unit: strict model validation, profile unknowns, score aggregation, pain tie-breaks, strategy unresolved fields, routing, persistence round trip and HTML escaping.
- Integration: synthetic `Nopal Foods` owner answers + E38/E39 source IDs → profile, four scores, cockpit, OPSP, route, persisted state and local artifact.
- Negative: no answers, missing evidence, unknown strategy fields, invalid score ranges, exchange SQLite/overlap, source/path leakage, deterministic rerun.
- Qualification: `scripts/qualify_e40.py` writes eight requirement artifacts/receipts and `master-acceptance-e40.json`.

## Migration and compatibility

Existing `/escala-welcome`, `/escala-diagnose`, `/escala-dashboard` and `/escala-progress` remain compatible. E40 is a typed, local composition seam; no existing command is removed or silently reinterpreted.
