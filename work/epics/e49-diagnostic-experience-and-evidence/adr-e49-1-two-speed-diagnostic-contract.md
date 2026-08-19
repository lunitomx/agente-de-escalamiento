---
adr_id: "E49-1"
epic: "E49"
title: "Two-speed local-first diagnostic contract"
status: "proposed"
created: "2026-08-19"
---

# ADR E49-1: Two-speed local-first diagnostic contract

## Context

The observed Accelerator diagnostic proves the value of structured baseline,
funnel evidence, open strategy prompts, bottleneck evidence, and a quarterly
handoff. Its fixed eight-block flow also creates survey fatigue and hides value
until the end. Escala already promises a conversational, adaptive, local-first
welcome, but its current profile and four-decision scoring contracts do not yet
carry enough evidence for an equivalent result.

## Decision

1. Escala uses a **two-speed diagnostic**: conversation and provisional focus
   first; targeted evidence deepening only when it increases decision quality.
2. People, Strategy, Execution, and Cash remain the canonical scored decisions.
   Owner/system sustainability is contextual and non-scoring in E49.
3. Every scored answer and imported fact carries applicability, status,
   provenance, freshness, confidence, and a stable evidence ID.
4. Not-applicable items are excluded from denominators; unknown items remain
   visible as coverage gaps.
5. Results are local artifacts and may be rendered for existing consumers;
   E49 adds no hosted submission, telemetry, or second data authority.

## Alternatives Considered

### Copy the Accelerator questionnaire

Rejected. It would import the primary UX weakness — a long mandatory wall — and
would conflict with Escala's conversational product promise.

### Keep the current 20-question diagnose unchanged

Rejected as the complete answer. It preserves speed but cannot explain a
bottleneck with funnel/context evidence or integrate profile/OPSP freshness.

### Build a generic survey framework

Rejected. E49 needs one diagnostic contract and two consumers first; a generic
framework would be speculative abstraction.

## Consequences

### Positive

- Faster first value without giving up evidence quality.
- Bottleneck claims become inspectable rather than opaque.
- N/A, stale, and estimated data stop masquerading as precise facts.
- Existing local-first and four-decision boundaries remain intact.

### Costs and constraints

- Two interaction paths require more acceptance coverage than a single form.
- Result consumers must understand coverage and confidence, not just a number.
- The team must resist adding questions when a provenance or source gap is the
  actual defect.

## Revisit Conditions

Revisit only after dogfood evidence shows the two-speed path cannot reach a
trustworthy result within the agreed evidence budget, or if the product owner
explicitly changes the local-first or Four Decisions boundaries.
