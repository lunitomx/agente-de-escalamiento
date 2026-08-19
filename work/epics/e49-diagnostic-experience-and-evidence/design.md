---
epic_id: "E49"
grounded_in: "Gemba of coaching/welcome, coaching/diagnose, coaching/export, escala_server/executive, validators, tests, escala-skills/escala-welcome, escala-skills/escala-diagnose, and redacted VisionHub run evidence"
---

# Epic Design: Experiencia diagnóstica y evidencia accionable para Escala

## Design stance

The observed Accelerator result is a useful benchmark for evidence and handoff,
not a UX template. E49 therefore keeps a conversational front door and adds a
bounded diagnostic evidence layer only when the user's situation needs it.

## Affected Surface (Gemba)

| Module/File | Current State | Changes |
|-------------|---------------|---------|
| `escala-skills/escala-welcome/SKILL.md` | Defines one-question conversational welcome, maturity profiles, source discovery, and <10-minute first value. | Make the evidence-deepening decision and provisional-result contract explicit without exposing commands. |
| `escala-skills/escala-diagnose/SKILL.md` | Adapter asks 5 questions per Decision (20 total), invokes core Python, and routes to the lowest score. | Route from welcome, accept evidence IDs/provenance, distinguish N/A, and present explainable output. |
| `coaching/welcome/engine.py` | Minimal profile builder: name, industry, employees, stage, optional revenue/years/location/description, empty four scores. | Preserve backward compatibility while accepting typed intake/evidence references through a narrow contract. |
| `coaching/diagnose/engine.py` | Scores four integer decisions 1–5 and chooses the minimum. | Add evidence-aware scoring metadata, N/A denominator handling, confidence, ties, and response-linked focus. |
| `coaching/export/` | Existing export boundary for local reports. | Add a diagnostic result renderer only after the result contract is stable. |
| `escala_server/executive/` | Existing onboarding/diagnostic/persistence/cockpit surfaces. | Reuse existing profile/session boundaries; do not create a parallel authority. |
| `validators/` and `tests/` | Validation and test fixtures exist for welcome, diagnose, export, memory, and server behavior. | Add contract, edge-case, redaction, and benchmark fixtures before consumer changes. |
| `work/epics/e49-diagnostic-experience-and-evidence/evidence/` | New redacted benchmark evidence. | Keep source observations and privacy exclusions auditable without copying raw answers. |

## Target Components

| Component | Responsibility | Key Interface |
|-----------|---------------|---------------|
| `DiagnosticEvidence` | One fact or answer with identity, value, source, freshness, confidence, and applicability. | `DiagnosticEvidence(id, value, source, captured_at, freshness, confidence, applicability)` |
| `DiagnosticIntake` | Aggregate company context, four-decision answers, optional owner context, funnel, and open prompts. | `DiagnosticIntake(company, answers, funnel, context, evidence)` |
| `DiagnosticScore` | Explain a decision score and denominator. | `DiagnosticScore(decision, value, answered, applicable, confidence, supporting_evidence_ids)` |
| `DiagnosticResult` | Stable result contract for preview, export, and dashboards. | `DiagnosticResult(scores, focus, evidence, route, provenance, generated_at)` |
| `WelcomeRouter` | Select conversation, fast diagnostic, or evidence deepening based on user intent and available data. | `next_turn(message, state) -> Turn` |
| `EvidencePackBuilder` | Collect only the evidence needed for the selected route and normalize sources. | `build(request, sources) -> DiagnosticIntake` |
| `ResultRenderer` | Render a local Markdown/machine-readable artifact with claims and citations to answer IDs. | `render(result, format) -> artifact` |

These names are design-level contracts, not permission to create a framework
before a story proves a consumer. S49.1 should fit them into the existing dict
and Pydantic conventions rather than adding wrappers that have one consumer.

## Key Contracts

### 1. Applicability and denominator

```text
applicability ∈ {applicable, not_applicable, unknown}
answer_status ∈ {fact, estimate, inference, unanswered}
confidence ∈ {low, medium, high}
```

`not_applicable` items are excluded from the denominator and visible in the
result. `unknown` is not silently scored; the result reports coverage and may
ask one clarifying question. No-seller cases therefore cannot become fake zero
scores.

### 2. Provenance and freshness

Every imported or prefilled value carries:

```text
source_kind ∈ {conversation, user_file, crm_export, profile, opsp, estimate}
source_ref: local relative reference or redacted label
captured_at: ISO-8601 timestamp
freshness: current | stale | unknown
```

Prefill is shown as “proposed” until the user confirms it. External URLs may be
stored as references, but the product does not fetch or transmit company data
to fulfill this contract.

### 3. Explainable focus

`focus` must include the selected Decision, the selection rule, coverage,
confidence, and at least one supporting evidence ID. Ties are retained rather
than hidden. A route recommendation cannot claim more certainty than its
lowest-confidence supporting evidence.

### 4. Two-speed interaction

The minimum path is:

```text
concern → maturity/context → provisional focus → first recommendation
```

The deep path is entered only when the user or coach needs proof:

```text
focus → targeted evidence pack → explainable result → 90-day route
```

The UI/agent must never reveal skill names or commands to a business user.

### 5. Local artifact

The result is persisted under the existing local authority and can be rendered
to Markdown plus a machine-readable representation. No story may add automatic
telemetry, hosted submission, or a second database authority.

## Migration Path

1. Add the evidence contract and fixtures without changing the current welcome
   or diagnose output.
2. Adapt `coaching/diagnose` to emit richer metadata while preserving existing
   `scores`, `focus`, `summary`, and `labels` keys for current consumers.
3. Add the conversational router and optional evidence path behind the current
   skill entry points.
4. Add result rendering and validators after scoring semantics are accepted.
5. Run the benchmark/dogfood comparison, then promote the new path as the
   default only if the leading metrics pass.

## Architecture Review (design-time)

### Critical

None. The design does not require a hosted service, a new database, or a new
generic survey framework.

### Recommended

- Keep `DiagnosticEvidence` and `DiagnosticResult` in the smallest existing
  domain module that has two real consumers; do not create a new package in
  S49.1 solely to satisfy a diagram.
- Treat result rendering as a consumer of the contract, not as the place where
  scoring rules live.
- Reuse local ingestion/profile authority rather than allowing each source
  adapter to persist its own facts.

### Questions for product-owner review

1. What is the minimum evidence budget for a deep path before it stops feeling
   conversational?
2. Should a provisional result be persisted immediately, or only after the user
   confirms the focus and next action?
3. Which existing export format is the first acceptance target: Markdown only,
   or Markdown plus JSON/YAML in the same story?

### Verdict

**PASS WITH QUESTIONS** — proportional for a seven-story product epic, provided
S49.1 proves the contract before consumer expansion and the questions above are
answered at the design gate.
