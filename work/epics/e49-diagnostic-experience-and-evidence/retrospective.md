# Epic Retrospective: E49 Experiencia diagnóstica y evidencia accionable para Escala

**Completed:** 2026-08-19
**Duration:** 1 calendar day (started 2026-08-19)
**Stories:** 7 stories delivered

---

## Summary

E49 turned the VisionHub comparison into a local-first Escala diagnostic path:
one-question conversational routing, typed evidence with provenance and N/A
semantics, explainable four-decision scoring, profile/OPSP confirmation, and a
bounded Markdown + JSON result with a 90-day route. A synthetic end-to-end
receipt proves the path without real company data, network calls, or telemetry.

The epic deliberately adopted the benchmark's evidence and handoff strengths
without copying its mandatory eight-block questionnaire. Production UI,
longitudinal outcome, and human dogfood timing remain separate gates rather than
being implied by the synthetic receipt.

## Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Stories Delivered | 7 | S49.1–S49.7 all merged locally to `main` |
| Story Points | 18 SP | 2 S + 5 M stories as scoped |
| Tests Added | 31 | Contract, conversation, intake, scoring, prefill, result, and acceptance |
| Scoped E49 Tests | 66 passed | Welcome + diagnose + export + synthetic acceptance |
| Full Suite | 1127 passed, 2 failed, 2 skipped | Entry-point failure cleared after editable local install; two remaining server-start failures are pre-existing HTTP/DNS behavior outside E49 changed surfaces |
| Average Velocity | Not measured | RaiSE calibration/pattern writes hit readonly shared DB |
| Calendar Days | 1 | Same-day implementation and local integration |

### Story Breakdown

| Story | Size | SP | Velocity | Key Learning |
|-------|:----:|:--:|:--------:|--------------|
| S49.1 | S | 2 | — | N/A, provenance, freshness, and confidence must be typed at the boundary. |
| S49.2 | M | 3 | — | One-turn routing needs a separate internal route and user-facing prompt. |
| S49.3 | M | 3 | — | Optional evidence is useful when normalized; a generic form is not. |
| S49.4 | M | 3 | — | A bottleneck claim needs denominator, coverage, confidence, and evidence IDs. |
| S49.5 | M | 3 | — | Markdown and JSON must derive from one result object. |
| S49.6 | S | 2 | — | Prefill is inference until explicit confirmation; stale is not current. |
| S49.7 | S | 2 | — | Synthetic acceptance proves the local path, not production UX outcomes. |

## What Went Well

- The real VisionHub run supplied concrete design evidence instead of a vague
  competitive opinion.
- Existing `coaching.evidence` and local authority boundaries were reused; no
  second database or hosted integration was introduced.
- TDD caught important semantic failures: fake zero/N/A handling, Commercial
  reporting versus canonical Decisions, invalid funnel values, and prompt
  command leakage.
- Every story has a scope, design, plan, progress, review, and retrospective;
  story branches were merged locally with no-ff and removed after merge.
- The acceptance receipt explicitly separates implemented capability from
  deferred UI/longitudinal proof.

## What Could Be Improved

- The RaiSE pipeline/backlog database was readonly for this checkout, so
  pattern reinforcement, calibration, and external backlog registration could
  not be persisted; the failures are recorded rather than fabricated as green.
- The checkout initially lacked its ignored local `.raise/manifest.yaml`; it was
  reconstructed from the existing S48 worktree manifests, which allowed
  lint/format/type gates and the entry-point check to run locally. It is not a
  tracked release artifact.
- The full suite still has two unrelated baseline failures: HTTP server
  resilience tests cannot observe startup because `HTTPServer.server_bind`
  blocks in `socket.getfqdn` under this environment. The entry-point failure was
  environment-only and now passes after installing the editable package.
- Human dogfood timing, abandonment, and trust feedback should be captured in a
  follow-on approved session before claiming UX superiority.
- Compatibility dictionary access on `FunnelMetrics` should be removed after
  all consumers migrate to the typed model.

## Patterns Discovered

| ID | Pattern | Context |
|----|---------|---------|
| Pending RaiSE DB write | Diagnostic evidence must distinguish `not_applicable` and `unknown` from numeric scores, and every recommendation-supporting fact needs provenance, freshness, confidence, and a safe local or redacted reference. | S49.1–S49.6; CLI pattern persistence was blocked by readonly DB. |
| E49-local-result | One typed result object should feed every local renderer; route claims remain bounded and evidence-linked. | S49.5–S49.7. |

## Process Insights

- A live competitor walkthrough is useful only when converted into structural
  acceptance evidence and explicit no-go decisions.
- Scoped gates can prove an epic's changed surfaces while the full repository
  remains unhealthy; both truths must be reported separately.
- RAISE story closure is valuable even without external Jira because the
  branch/commit/artifact trail still makes the product change inspectable.

## Artifacts

- **Scope:** `work/epics/e49-diagnostic-experience-and-evidence/scope.md`
- **Stories:** `work/epics/e49-diagnostic-experience-and-evidence/stories/`
- **ADR:** `work/epics/e49-diagnostic-experience-and-evidence/adr-e49-1-two-speed-diagnostic-contract.md`
- **Benchmark evidence:** `work/epics/e49-diagnostic-experience-and-evidence/evidence/visionhub-2026-08-19.md`
- **Acceptance receipt:** `work/epics/e49-diagnostic-experience-and-evidence/evidence/e49-acceptance-2026-08-19.md`
- **Tests:** 31 new tests; 66 scoped E49 tests passing

## Release Impact

**Release:** REL-TBD (diagnostic experience)
**Epic progress:** E49 complete locally; external release/MR remains a separate
authority gate.

## Next Steps

- Run an approved human dogfood session and capture actual first-value time,
  abandonment, trust, and usefulness feedback.
- Remove the temporary `FunnelMetrics.__getitem__` compatibility shim after
  consumer migration.
- Resolve the unrelated server startup/DNS behavior in the owning E27
  bugfix/epic, not in E49.
- Register/push the epic when a writable backlog and release authority are
  available.
