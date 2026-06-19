# E34 Retrospective: Voice of Customer Evidence System

**Status:** Complete
**Date:** 2026-06-19

## Summary

E34 revived the valuable E20 Voice of Customer idea and absorbed the useful
part of E19 as evidence-first strategy prompt hardening. The delivered system
creates a local evidence contract, normalizes raw quotes, maps approved evidence
into cited strategy inputs, and updates strategy prompts to avoid unsupported
claims.

## Story Outcomes

| Story | Status | Evidence |
|---|---|---|
| S34.1 | Complete | Evidence schema, validation tests, retrospective. |
| S34.2 | Complete | Raw quote normalization, duplicate handling, retrospective. |
| S34.3 | Complete | Strategy mapping with inputs/gaps/contradictions, retrospective. |
| S34.4 | Complete | Strategy prompt hardening and mirror tests, retrospective. |
| S34.5 | Complete | Canonical handoff, final audit, epic retrospective. |

## Delivered

- `validators/voice_of_customer.py`
- `tests/test_voice_of_customer.py`
- `tests/test_voice_of_customer_mapping.py`
- `tests/test_strategy_voice_of_customer_prompting.py`
- `tests/test_voice_of_customer_handoff.py`
- `.raise/evidence/voice-of-customer.md`
- Updated strategy skill docs in `.agents` and `.claude`
- `final-audit.md`

## What Changed

- Strategy claims now have an evidence path: raw quote -> evidence record ->
  strategy input -> cited prompt guidance.
- Draft and fixture evidence cannot silently become strategy-usable.
- Missing evidence becomes a gap and a one-question follow-up, not an invented
  claim.

## Risks And Boundaries

- Real customer evidence was not collected in this implementation.
- Fixture data remains test-only evidence.
- Production evidence storage is not implemented.
- E35 remains separate: it will handle golden cases and drift gates for skill
  behavior, not VoC evidence capture.

## Closure Decision

E34 can close for the local contract, validation, mapping, prompt hardening, and
handoff scope. It must not be cited as proof that real customer interviews have
been collected.

