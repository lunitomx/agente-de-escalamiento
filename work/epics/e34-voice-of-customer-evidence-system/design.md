# E34 Design: Voice of Customer Evidence System

## Existing State

- Draft E20 described customer voice capture but never implemented it.
- Draft E19 described strategy prompt hardening but depends on better evidence
  inputs to avoid assumption-driven strategy.
- Existing ScaleUp strategy skills are present under `.agents/skills`, but the
  repo does not yet have a dedicated customer evidence contract or library.

## Target Contract

The first implementation should create a small validated evidence record rather
than a broad platform.

Required fields:

- `id`
- `source_type`
- `source_label`
- `captured_at`
- `context`
- `quote`
- `customer_segment`
- `evidence_tags`
- `review_status`
- `notes`

The contract must distinguish real customer evidence from fixtures or examples.
Strategy stories may use fixtures for tests, but closure must state whether
real evidence was available.

## Strategy Handoff

Core Customer, Brand Promise, positioning, and Strategy Canvas outputs should
consume evidence by id. If evidence is missing, the flow should say so and ask
for it instead of generating unsupported claims.

## Decisions

| Decision | Rationale |
|---|---|
| Evidence contract before prompt edits. | Prompt hardening without evidence would repeat the E19 risk: polished guidance without stronger proof. |
| Local library before external integrations. | CRM/review imports add noise before the schema and validation rules are stable. |
| Preserve uncertainty. | Customer voice can be incomplete; the system should not fill missing source/context/date fields with guesses. |

## Open Questions For S34.1

- Should evidence records live under `work/evidence/`, `.raise/evidence/`, or a
  package-level data directory?
- Which minimum fields should be required for real closure versus test fixtures?
- Which current strategy skill should consume the evidence first?

