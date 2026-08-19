---
epic_id: "E49"
title: "Experiencia diagnóstica y evidencia accionable para Escala"
status: "draft"
created: "2026-08-19"
---

# Epic Brief: Experiencia diagnóstica y evidencia accionable para Escala

## Hypothesis

For business leaders who need clarity before committing to a coaching path,
Escala's conversational welcome can become a two-speed diagnostic experience:
first it asks one useful question at a time and routes to the real pain, then it
offers a bounded evidence pack when quantitative or qualitative proof is needed.
Unlike the observed Accelerator flow (a long linear questionnaire whose value is
mostly revealed at the end), Escala will preserve the relationship and speed of
conversation while producing a traceable diagnosis, bottleneck evidence, and a
90-day action route.

## Evidence Baseline

On 2026-08-19 we completed a real, user-authorized run of the VisionHub
Accelerator diagnostic in Chrome. Its strongest product signals were:

- explicit promise of the final deliverable before intake;
- company calibration, five operating pillars, owner context, funnel numbers,
  open strategy prompts, and prefilled one-page-plan fields;
- a final result with global score, pillar scores, evidence rows for the
  bottleneck, funnel conversion, candidate metrics, quarterly route, and
  accountability prompts.

Its main experience costs were the fixed eight-block progression, repeated
Likert grids, hidden value until the end, and ambiguous treatment of
not-applicable commercial questions. Raw personal answers are intentionally not
stored in this repository; the structural evidence is summarized in
`evidence/visionhub-2026-08-19.md`.

## Success Metrics

- **Leading:** a synthetic or dogfood user can reach a provisional insight in
  one conversational path, add an optional evidence pack, and see exactly
  which answers support the proposed focus.
- **Lagging:** compared with the current Escala baseline, completion and
  actionable-output rates improve without making the first interaction feel
  like a questionnaire; every generated result includes a next action, owner,
  metric, confidence, and provenance.

## Appetite

M — 7 stories. The epic is intentionally bounded to the diagnostic experience
and its output contract; it does not redesign every specialist skill.

## Scope Boundaries

### In (MUST)

- Define one canonical diagnostic evidence contract for company context,
  People/Strategy/Execution/Cash signals, optional owner context, funnel data,
  qualitative prompts, provenance, freshness, confidence, and N/A handling.
- Preserve Escala's conversational, one-question-at-a-time welcome and route
  users to value before requesting deep evidence.
- Add an optional, source-flexible evidence pack that can accept facts from
  conversation, files, CRM exports, or user estimates without forcing one
  form-shaped workflow.
- Generate an explainable result with scores, uncertainty, bottleneck evidence,
  and a bounded 90-day route with owners and metrics.
- Validate the result against the observed Accelerator strengths and against
  Escala's local-first/no-telemetry boundary.

### In (SHOULD)

- Prefill eligible fields from the existing company profile/OPSP while showing
  source and freshness and asking the user to confirm stale or inferred facts.
- Produce a local Markdown plus machine-readable artifact that existing
  export/dashboard consumers can reuse.
- Add a compact dogfood comparison report with time-to-first-value,
  abandonment, evidence coverage, and user-rated usefulness.

### No-Gos

- Recreate the eight-block Accelerator questionnaire or make every field
  mandatory.
- Add a fifth scored business pillar; owner/system sustainability remains an
  optional contextual signal unless later evidence justifies a new decision.
- Send company data to a hosted service, add telemetry, or change the local
  authority boundary.
- Build a generic survey/form framework or redesign all specialist skills in
  this epic.

### Rabbit Holes

- Perfecting a radar-chart UI before the evidence and scoring contract is
  trustworthy.
- Adding more questions when a missing source, confidence, or denominator is
  the real problem.
- Treating a prefilled plan as current fact without freshness and user
  confirmation.
- Ranking Escala against Accelerator on a single satisfaction opinion instead
  of comparable completion and actionability evidence.
