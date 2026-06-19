# E34 Story Map: Voice of Customer Evidence System

**Status:** Planned
**Planning date:** 2026-06-18

## Delivery Strategy

Build the evidence spine before touching strategy prompts. The first three
stories establish the data contract and mapping behavior. Prompt hardening only
starts after strategy outputs can cite evidence records.

## Story Sequence

| Seq | Story | Purpose | Primary Output | Gate |
|---|---|---|---|---|
| 1 | S34.1 Evidence intake schema | Define what counts as usable customer evidence. | Typed evidence record + validation tests. | Incomplete records fail validation. |
| 2 | S34.2 Testimonial normalization | Convert raw quotes/notes into evidence records without inventing missing data. | Normalizer + fixture cases. | Missing source/context remains explicit. |
| 3 | S34.3 Voice-to-strategy mapping | Make evidence useful for Core Customer, Brand Promise, and positioning. | Mapping layer with cited evidence ids. | Strategy inputs cite evidence or report gaps. |
| 4 | S34.4 Strategy prompt hardening | Absorb E19 by updating Prompt 0-4 behavior around evidence. | Strategy skill updates + prompt checks. | Prompts require evidence before claims. |
| 5 | S34.5 Evidence library handoff | Make the system reusable by future skills/pipelines. | Library docs, handoff examples, pipeline note. | Consumers can load/cite evidence without draft folders. |

## S34.1 — Evidence Intake Schema

### User Story

As a ScaleUp operator, I want a strict evidence record format so customer voice
can be captured with enough provenance to support strategic decisions.

### In Scope

- Define the local storage location for evidence fixtures and records.
- Define required fields: id, source type, source label, captured date, context,
  quote/content, customer segment, evidence tags, review status.
- Add validation for real records versus synthetic fixtures.
- Add test fixtures for valid, incomplete, and fixture-labeled evidence.

### Out of Scope

- CRM import/export.
- Audio transcription.
- Strategy mapping logic.

### Acceptance Criteria

- Given a complete customer evidence record, validation passes.
- Given a record without source, context, or date, validation fails or marks it
  unusable for strategy claims.
- Given a synthetic fixture, the record is explicitly labeled as fixture data.

### Likely Files

- `validators/voice_of_customer.py`
- `tests/test_voice_of_customer.py`
- `tests/fixtures/voice_of_customer/*.yaml`
- `work/epics/e34-voice-of-customer-evidence-system/stories/s34.1-*`

### Verification

- `rai gate check gate-tests --scope tests/test_voice_of_customer.py`
- `rai gate check gate-lint`
- `rai gate check gate-format`
- `rai gate check gate-types`

## S34.2 — Testimonial Normalization

### User Story

As a ScaleUp operator, I want raw quotes and notes normalized into evidence
records so customer voice is reusable without losing source context.

### In Scope

- Normalize raw text snippets into the S34.1 evidence contract.
- Preserve unknown fields as unknown instead of guessing.
- Detect duplicate or near-duplicate quotes by stable id/source metadata.
- Keep raw quote text separate from interpretation.

### Out of Scope

- Sentiment scoring.
- Bulk external review scraping.
- Strategy recommendation generation.

### Acceptance Criteria

- Given raw quote input with source/context/date, a valid evidence record is
  produced.
- Given raw quote input missing context, the output is reviewable but not valid
  for strategy claims.
- Given duplicate quote/source pairs, duplicates are detected or rejected.

### Likely Files

- `validators/voice_of_customer.py`
- `tests/test_voice_of_customer.py`
- `tests/fixtures/voice_of_customer/raw_quotes.yaml`

### Verification

- `rai gate check gate-tests --scope tests/test_voice_of_customer.py`
- `rai gate check gate-lint`
- `rai gate check gate-format`
- `rai gate check gate-types`

## S34.3 — Voice-To-Strategy Mapping

### User Story

As a strategy facilitator, I want customer evidence mapped into Core Customer,
Brand Promise, and positioning inputs so strategic claims are traceable.

### In Scope

- Define mapping categories for customer segment, desired outcome, pain,
  promised value, objection, proof, and language to reuse.
- Generate strategy input summaries that cite evidence ids.
- Flag claims that do not have enough evidence.
- Preserve uncertainty when evidence is thin or contradictory.

### Out of Scope

- Final strategy prose generation.
- UI dashboards.
- Automated customer segmentation beyond evidence tags.

### Acceptance Criteria

- Given evidence records with relevant tags, mapping produces cited strategy
  inputs.
- Given insufficient evidence, mapping returns explicit gaps instead of claims.
- Given contradictory evidence, mapping keeps both sides visible for review.

### Likely Files

- `validators/voice_of_customer.py`
- `tests/test_voice_of_customer_mapping.py`
- `tests/fixtures/voice_of_customer/strategy_mapping.yaml`

### Verification

- `rai gate check gate-tests --scope tests/test_voice_of_customer_mapping.py`
- `rai gate check gate-lint`
- `rai gate check gate-format`
- `rai gate check gate-types`

## S34.4 — Strategy Prompt Hardening

### User Story

As a ScaleUp user, I want strategy prompts to ask for and use customer evidence
before forming Core Customer, Brand Promise, or Strategy Canvas outputs.

### In Scope

- Update Prompt 0-4 behavior in the relevant strategy skills.
- Preserve one-question-per-turn interaction.
- Add evidence requirements to Core Customer and Brand Promise guidance.
- Make unsupported claims ask for evidence instead of inventing it.

### Out of Scope

- Full course rewrite.
- New strategy framework.
- Visual redesign.

### Acceptance Criteria

- Prompt guidance requires customer evidence before strategy claims.
- Prompt flow still advances one question at a time.
- Strategy Canvas handoff references evidence-backed inputs.
- Existing strategy skill commands remain recognizable.

### Likely Files

- `.agents/skills/scaleup-strategy*/SKILL.md`
- `.claude/skills/scaleup-strategy*/SKILL.md` if mirrored skill docs are still canonical in this repo
- `tests/test_voice_of_customer_mapping.py`

### Verification

- `rai gate check gate-tests --scope tests/test_voice_of_customer_mapping.py`
- `rai gate check gate-lint`
- `rai gate check gate-format`
- `rai gate check gate-types`

## S34.5 — Evidence Library Handoff

### User Story

As a future skill author, I want a reusable evidence library contract so other
skills can load and cite Voice of Customer records consistently.

### In Scope

- Document the evidence library contract and storage convention.
- Add examples for strategy consumption.
- Add a handoff note for future pipeline registry integration.
- Record what real evidence versus fixtures was used in the epic.

### Out of Scope

- Building a runtime pipeline executor.
- Publishing external docs.
- Migrating historical customer data.

### Acceptance Criteria

- A future story can find the evidence contract without reading E19/E20 drafts.
- Example consumers show how to cite evidence ids.
- Epic close can distinguish real evidence from fixtures.

### Likely Files

- `docs/` or `.raise/` evidence contract location chosen in S34.1
- `work/epics/e34-voice-of-customer-evidence-system/retrospective.md`
- `work/epics/e34-voice-of-customer-evidence-system/final-audit.md`

### Verification

- `rai gate check gate-tests --scope tests/test_voice_of_customer.py`
- `rai gate check gate-tests --scope tests/test_voice_of_customer_mapping.py`
- `rai gate check gate-lint`
- `rai gate check gate-format`
- `rai gate check gate-types`

## Cross-Story Risks

| Risk | Mitigation |
|---|---|
| No real customer evidence is available during implementation. | Use fixtures only for RED/GREEN tests and block complete closure until real/synthetic status is explicit. |
| Prompt updates outrun the evidence contract. | Do not start S34.4 until S34.1-S34.3 are done. |
| Evidence records become too complex. | Start with required provenance and review fields only; defer CRM/sentiment fields. |

## Definition Of Ready For First Story

- Confirm storage location for evidence fixtures/records.
- Confirm first strategy consumer: Core Customer, Brand Promise, or Strategy
  Canvas.
- Provide at least one real or representative customer quote for fixture design.

