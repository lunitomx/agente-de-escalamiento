---
epic_id: E49
title: Experiencia diagnostica y evidencia accionable
status: complete
closure_disposition: complete
closed: 2026-08-27
---

# Epic E49: Experiencia diagnóstica y evidencia accionable para Escala — Scope

> **Status:** COMPLETE — S49.1–S49.7, retrospective and local acceptance verified
> **Release:** REL-TBD (diagnostic experience)
> **Created:** 2026-08-19
> **Design:** `design.md`

## Objective

Make Escala's first diagnostic interaction feel like a coach-led conversation
while still producing an evidence-backed, inspectable result. A user should be
able to reach an early useful insight, optionally deepen the evidence, and
receive a local artifact that names the focus, proves it with response-level
evidence, and gives a bounded 90-day action route.

**Value:** Escala keeps its strongest differentiator — adaptive local coaching
— and closes the current gap against the observed Accelerator deliverable:
structured baseline, funnel/context evidence, explainable bottleneck, and an
actionable handoff.

## Stories (7 stories, 18 SP estimated)

| ID | Story | Size | Status | Description |
|----|-------|:----:|:------:|-------------|
| S49.1 | Canonical diagnostic evidence contract | S | **Done** (2026-08-19) | Define typed evidence, provenance, freshness, confidence, N/A, and answer IDs without changing the four-decision backbone. |
| S49.2 | Conversational welcome walking skeleton | M | **Done** (2026-08-19) | Route one question at a time from first concern to provisional focus and next step. |
| S49.3 | Optional evidence pack and source adapters | M | **Done** (2026-08-19) | Deepen only when useful; accept conversation, files, CRM exports, and estimates with explicit source status. |
| S49.4 | Explainable scoring and bottleneck evidence | M | **Done** (2026-08-19) | Score four decisions, exclude N/A from denominators, expose uncertainty, and link the focus to supporting answers. |
| S49.5 | Diagnostic result and 90-day action route | M | **Done** (2026-08-19) | Produce local Markdown/machine-readable output with scorecard, funnel, evidence, owner, metric, and bounded route. |
| S49.6 | Prefill, freshness, and privacy lifecycle | S | **Done** (2026-08-19) | Reuse eligible profile/OPSP facts with source/freshness confirmation and local retention/export controls. |
| S49.7 | Dogfood comparison and acceptance evidence | S | **Done** (2026-08-19) | Compare the new flow with the current baseline and observed Accelerator strengths using time, completion, actionability, and trust measures. |

**Total:** 7 stories, 18 SP (S=2, M=3)

## Scope

**In scope (MUST):**

- Conversational welcome state and routing that preserves one-question-at-a-time
  behavior.
- Evidence contract covering the four Decisions, optional owner context,
  company calibration, commercial funnel, qualitative context, provenance,
  freshness, confidence, and N/A.
- Optional evidence deepening and source-flexible ingestion without a single
  mandatory form.
- Explainable scoring and bottleneck selection with response-level evidence.
- Local result artifact and bounded 90-day route.
- Tests and dogfood evidence for the experience and output contract.

**In scope (SHOULD):**

- OPSP/profile prefill with visible source and freshness.
- Reuse of existing dashboard/export renderers where the contract fits.
- A small redacted benchmark fixture derived from the structural VisionHub
  observation.

**Out of scope:**

- Hosted storage, telemetry, or external submission → preserve E36/E37 local
  authority and inbox boundaries.
- Rebuilding every specialist skill → follow-on stories after E49 evidence.
- A universal survey builder → parking lot; use explicit diagnostic contracts.
- A fifth scored pillar → revisit only with product-owner evidence.
- Visual polish/radar charts before the contract and result semantics are
  accepted → parking lot.

## Done Criteria

**Per story:**

- [x] TDD evidence exists for changed logic and boundary conditions.
- [x] Scoped type, lint, format, and test gates for changed surfaces pass;
  full-suite baseline failures unrelated to E49 are recorded in the epic
  retrospective.
- [x] Local data authority and redaction rules remain intact.
- [x] Story artifact names the contract and evidence used.

**Epic complete:**

- [x] All stories S49.1–S49.7 complete.
- [x] A synthetic/dogfood user reaches a provisional insight before deepening.
- [x] Optional evidence produces a result with scores, confidence, evidence
  links, N/A handling, and a 90-day route.
- [x] No seller/no applicable cases do not depress scores through fake zeros.
- [x] Prefilled facts display source/freshness and require confirmation when
  stale or inferred.
- [x] Output is locally persisted and exportable without telemetry or hosted
  transmission.
- [x] Comparison receipt records completion time, abandonment, evidence
  coverage, actionability, and user trust; no raw personal data is committed.
- [x] Epic retrospective done and merged to `main`.

**Closure re-verification (2026-08-27):** the current full suite passes
(`1242 passed, 2 skipped`) with Pyright, Ruff check and Ruff format check. The
acceptance remains scoped to the local coaching engine; production UI and a
longitudinal human-outcome study remain explicitly outside E49.

## Dependencies

```
S49.1 (contract)
  ├──> S49.2 (conversation skeleton) ──┐
  ├──> S49.3 (evidence pack) ───────────┼──> S49.4 (scoring/evidence)
  └──> S49.6 (prefill/lifecycle) ──────┘          │
                                                  ├──> S49.5 (result/route)
                                                  └──> S49.7 (dogfood/acceptance)
```

**External:** Existing `coaching/welcome`, `coaching/diagnose`, export,
dashboard, profile/OPSP, and local-ingestion contracts; no external service.

## Architecture

| Decision | ADR | Summary |
|----------|-----|---------|
| D1 | E49-1 | Two-speed diagnostic: conversation first, optional evidence deepening second. |
| D2 | E49-1 | Four Decisions remain canonical; owner/system is contextual, not a fifth score. |
| D3 | E49-1 | Every score and route claim carries answer IDs, provenance, freshness, confidence, and N/A semantics. |
| D4 | E49-1 | Local-first artifacts; no hosted submission or telemetry. |

> Problem Brief: `brief.md`
> Evidence: `evidence/visionhub-2026-08-19.md`

## Risks

| Risk | L/I | Mitigation |
|------|:---:|------------|
| “Optional” evidence grows into another long form | M/H | Set a minimum evidence budget, route by pain, and measure time-to-first-value. |
| Scores look precise while inputs are estimates or stale | M/H | Store provenance/freshness/confidence and show uncertainty in the result. |
| New contract forks current profile/diagnose/export models | M/H | S49.1 maps existing consumers first; adapters preserve backward compatibility. |
| Local privacy boundary is weakened by convenience integrations | L/H | Fail closed on hosted transmission; reuse E36/E37 authority and inbox rules. |
| Benchmark comparison becomes opinion-led | M/M | Use a redacted fixture and comparable measures, not raw personal answers or one satisfaction score. |

## Parking Lot

- Full visual radar/interactive report → after result semantics are validated.
- Cross-company benchmarking or facilitator multi-tenant portal → separate
  product decision and privacy review.
- Generic survey/form builder → reject unless three independent diagnostics
  prove the abstraction necessary.
- Fifth scored pillar for owner sustainability → revisit only with longitudinal
  evidence.

### Machine

```yaml
modules_affected:
  - path: coaching/welcome/
    change: modify
  - path: coaching/diagnose/
    change: modify
  - path: coaching/export/
    change: extend
  - path: escala_server/executive/
    change: inspect/extend only if existing contract requires it
  - path: validators/
    change: add evidence and result validation
  - path: tests/
    change: add contract, edge-case, and dogfood fixtures
decisions:
  - id: D1
    choice: "two-speed conversation plus optional evidence pack"
    rationale: "retain Escala's adaptive value while closing Accelerator's evidence gap"
    constraint: "no mandatory eight-block wall"
  - id: D2
    choice: "four Decisions remain canonical"
    rationale: "the Four Decisions are Escala's product backbone; owner context is useful but not a new pillar"
    constraint: "owner/system signals cannot silently change pillar scores"
  - id: D3
    choice: "explainability is part of the output contract"
    rationale: "a bottleneck without response-level evidence is not trustworthy"
    constraint: "scores and routes reference answer IDs and uncertainty"
  - id: D4
    choice: "local-first persistence and export"
    rationale: "company data authority and privacy are product invariants"
    constraint: "no telemetry or hosted submission in E49"
constraints:
  - "N/A excludes an item from its denominator; it is never coerced to zero"
  - "prefill is not fact until source/freshness is visible and confirmed"
  - "no story creates a generic survey framework"
```

## Implementation Plan

> Added by `/rai-epic-plan` — 2026-08-19

### Story Sequence

| Order | Story | Size | Dependencies | Milestone | Rationale |
|:-----:|-------|:----:|--------------|-----------|-----------|
| 1 | S49.1 | S | None | M1 | Contract and edge semantics are the highest-leverage uncertainty; prove N/A, provenance, freshness, confidence, and backward-compatible keys first. |
| 2 | S49.2 | M | S49.1 | M1 | Walking skeleton proves a user can reach provisional value without a form wall. |
| 3 | S49.3 | M | S49.1 | M2 | Adds targeted evidence only after the conversational path and source contract exist. |
| 4 | S49.4 | M | S49.1, S49.3 | M2 | Makes scores and bottleneck selection explainable using the evidence gathered. |
| 5 | S49.6 | S | S49.1 | M2 | Runs in parallel with S49.3/S49.4; prevents stale prefill and privacy drift before output work. |
| 6 | S49.5 | M | S49.2, S49.4, S49.6 | M3 | Integrates the stable result contract into the local artifact and 90-day route. |
| 7 | S49.7 | S | S49.5 | M4 | Validates the end-to-end experience against the redacted benchmark and dogfood measures. |

**Critical path:** S49.1 → S49.2 → S49.3 → S49.4 → S49.5 → S49.7.

**Parallel opportunity:** S49.6 may run after S49.1 while S49.3 and S49.4 are
underway, provided both streams consume the same contract and do not create
parallel persistence.

### Milestones

| Milestone | Stories | Target | Success Criteria |
|-----------|---------|--------|------------------|
| **M1: Walking Skeleton** | S49.1, S49.2 | After contract + first flow | A synthetic user reaches a provisional focus and next action in one-question-at-a-time interaction; existing profile/diagnose consumers remain green. |
| **M2: Evidence MVP** | +S49.3, S49.4, S49.6 | After evidence semantics | Targeted funnel/context/profile evidence produces scores with coverage, confidence, N/A behavior, and supporting answer IDs. |
| **M3: Result Handoff** | +S49.5 | After output integration | Local Markdown/machine-readable result contains focus, evidence, owner, metric, and bounded 90-day route. |
| **M4: Epic Complete** | +S49.7 | After dogfood | Comparable receipt shows first-value time, completion, evidence coverage, actionability, and trust; done criteria met and retro complete. |

### Parallel Work Streams

```text
Time →
Stream 1 (Critical): S49.1 ─► S49.2 ─► S49.3 ─► S49.4 ─► S49.5 ─► S49.7
                              │                    ▲
Stream 2 (Parallel):          └────── S49.6 ──────┘
```

**Merge points:**

- After S49.1: conversation, evidence, and lifecycle may split.
- Before S49.5: scoring and lifecycle must agree on the same result contract.
- Before S49.7: all user-facing output paths must be exercised end to end.

### Progress Tracking

| Story | Size | Status | Actual | Velocity | Notes |
|-------|:----:|:------:|:------:|:--------:|-------|
| S49.1 | S | **Done** | 2026-08-19 | — | Contract, tests, AR/QR, and retrospective merged; global closure gate has unrelated baseline failures. |
| S49.2 | M | **Done** | 2026-08-19 | — | Walking skeleton, AR/QR, and retrospective merged. |
| S49.3 | M | **Done** | 2026-08-19 | — | Typed funnel/intake, AR/QR, and retrospective merged. |
| S49.4 | M | **Done** | 2026-08-19 | — | Explainable scores, AR/QR, and retrospective merged. |
| S49.5 | M | **Done** | 2026-08-19 | — | Local Markdown/JSON result, AR/QR, and retrospective merged. |
| S49.6 | S | **Done** | 2026-08-19 | — | Pure prefill/confirmation, AR/QR, and retrospective merged. |
| S49.7 | S | **Done** | 2026-08-19 | — | Synthetic E2E path, skill integration, and acceptance receipt merged. |

### Sequencing Risks

| Risk | L/I | Mitigation |
|------|:---:|------------|
| Contract becomes a speculative universal model | M/H | Require two concrete consumers in S49.1 and reject unused fields. |
| Conversation and evidence paths drift into two authorities | M/H | One contract, one local persistence boundary, and integration gate before S49.5. |
| Dogfood measures are not comparable to the external benchmark | M/M | Compare structural capabilities and normalized measures; do not copy raw personal data. |
