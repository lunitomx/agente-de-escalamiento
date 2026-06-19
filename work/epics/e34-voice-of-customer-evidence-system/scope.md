# Epic Scope: E34 — Voice of Customer Evidence System

**Status:** Planned
**Created:** 2026-06-18
**Renumbers:** E20 Voice of Customer & Evidence Capture
**Absorbs:** E19 Strategy Core Skills as S34.4 strategy hardening

## Objective

Create a reusable Voice of Customer evidence system that captures real customer
quotes, context, and source metadata before ScaleUp defines Core Customer,
Brand Promise, positioning, or Strategy Canvas recommendations.

## Value

The system should make strategic claims auditable. Instead of asking the agent
to invent or polish promises first, it forces the workflow to gather evidence,
normalize it, and cite it when producing strategy outputs.

## In Scope

- Evidence intake schema for quotes, testimonials, audio notes, source, context,
  date, and review state.
- Testimonial normalization rules that preserve uncertainty and provenance.
- Mapping rules from customer voice to Core Customer, Brand Promise, and
  positioning inputs.
- A reusable local evidence library for strategy skills.
- Strategy prompt hardening from draft E19: Prompt 0-4 sequence, one question
  per turn, Strategy Canvas update flow, and evidence-first guidance.

## Out of Scope

- CRM or sales pipeline implementation.
- Automated external review scraping.
- Advanced statistical sentiment analysis.
- New visual dashboard before the evidence contract is validated.
- Rewriting the full strategy curriculum.

## Gemba Findings

| Finding | Evidence | Decision |
|---|---|---|
| Draft E20 contains the strongest unrealized value. | `work/epics/e20-voice-of-customer-evidence-capture/scope.md` defines customer evidence capture but has no implementation or retrospective. | Renumber as E34 and restart with fresh story artifacts. |
| Draft E19 is valuable but too small as a standalone epic. | `work/epics/e19-strategy-core-skills/scope.md` focuses Prompt 0-4 and Strategy Canvas hardening. | Absorb as S34.4 after the evidence contract exists. |
| Existing strategy skills exist, but no VoC evidence contract was found. | `.agents/skills/scaleup-strategy*` exists; repo search found no implemented customer evidence library. | Build the evidence contract before prompt edits. |

## Planned Stories

| ID | Story | Size | Depends | Description |
|----|-------|------|---------|-------------|
| S34.1 | Evidence intake schema | M | - | Define typed evidence records, source metadata, confidence/review fields, and validation fixtures. |
| S34.2 | Testimonial normalization | M | S34.1 | Normalize raw quotes/notes into evidence records without inventing missing context. |
| S34.3 | Voice-to-strategy mapping | M | S34.2 | Map evidence into Core Customer, Brand Promise, and positioning inputs with citations. |
| S34.4 | Strategy prompt hardening | M | S34.3 | Absorb E19 by refining Prompt 0-4 flow to require evidence before strategic recommendations. |
| S34.5 | Evidence library handoff | S | S34.3, S34.4 | Provide a reusable local library/contract that strategy skills can consume and audit. |

## Dependencies

- Existing ScaleUp strategy skills under `.agents/skills/scaleup-strategy*`.
- Real or representative customer evidence supplied by the operator.
- Existing pipeline registry conventions from E30/E31 if the flow is exposed as
  a governed pipeline later.

## Done Criteria

- [ ] Evidence records are validated with source, context, date, and review
      status.
- [ ] Strategy outputs cite evidence records or explicitly state missing
      evidence.
- [ ] Prompt 0-4 hardening is implemented as story work, not claimed from the
      old E19 draft.
- [ ] Tests or validators prove evidence-free claims are blocked or flagged.
- [ ] Epic retrospective records what evidence was real, synthetic fixture, or
      still missing.

## Implementation Plan

Detailed story scopes, acceptance criteria, expected files, and gates live in
`story-map.md`. This scope remains the epic-level source of truth.

| Seq | Story | Rationale | Exit Evidence |
|---|---|---|---|
| 1 | S34.1 | Contract first; downstream logic needs stable fields. | Schema/tests reject incomplete records. |
| 2 | S34.2 | Raw customer voice must be normalized before mapping. | Fixture conversion preserves source/context. |
| 3 | S34.3 | Core value appears when evidence drives strategy inputs. | Mapping output cites evidence ids. |
| 4 | S34.4 | Prompt hardening is useful only after evidence is available. | Strategy prompts require/cite evidence. |
| 5 | S34.5 | Make the result reusable by other skills and future pipelines. | Library/handoff docs and tests exist. |

## Milestones

| Milestone | Stories | Success Criteria |
|---|---|---|
| M1 Evidence Contract | S34.1, S34.2 | Customer voice can be captured and normalized with provenance. |
| M2 Strategy Use | S34.3, S34.4 | Core Customer and Brand Promise flows consume cited evidence. |
| M3 Reusable System | S34.5 | Evidence library can be reused without reading old draft folders. |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Evidence source data is unavailable. | Medium | High | Allow representative fixtures, but label them as fixtures and block product closure until real evidence is available. |
| Prompt hardening turns into full course rewrite. | Medium | Medium | Keep S34.4 bounded to Prompt 0-4 and Strategy Canvas handoff. |
| The agent treats weak anecdotes as proof. | Medium | High | Require source/context/date/review status and preserve uncertainty. |

## Tag Action

No complete tag exists or should exist for E34 until implementation stories,
tests, and retrospective are complete. Old E20/E19 draft folders remain source
context only.
