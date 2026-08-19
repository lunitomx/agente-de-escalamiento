# E49 acceptance receipt — 2026-08-19

## Run provenance

- Repository: local ESCALA checkout on `main` after S49.1–S49.6 merges
- Input: synthetic concern and synthetic evidence only
- External calls: none
- Raw personal/company data: none
- Acceptance test: `tests/test_e49_acceptance.py`

## Observable path

```text
begin_welcome
  → respond_to_welcome(concrete concern)
  → build_diagnostic_intake(evidence + funnel)
  → score_diagnostic()
  → build_diagnostic_result()
  → run_diagnostic()
  → local Markdown + JSON artifacts
```

## Acceptance results

| Measure | Evidence | Result |
|---|---|---|
| First useful route | Synthetic concern is routed after one user response (1 turn to route) | PASS |
| Completion / abandonment | 1/1 synthetic runs completed; 0/1 abandoned | PASS (synthetic proxy) |
| Evidence coverage | Scorecard includes coverage, confidence, and evidence IDs | PASS |
| N/A semantics | Contract excludes `not_applicable` from denominator | PASS |
| Actionability | Result contains no more than two route actions with metric slots | PASS |
| Local trust | Artifacts written under `.escala/`; no network path | PASS |
| Machine handoff | Dated Markdown and JSON created from one result object | PASS |
| Targeted tests | Welcome + diagnose + export + E49 acceptance | 65 passed |
| Lint / format / type | Ruff check, Ruff format check, Pyright | PASS |

## Benchmark comparison

### Implemented from the observed Accelerator strengths

- Result promise is represented by a local scorecard and handoff artifact.
- Funnel/context evidence can be supplied without making a long form mandatory.
- Focus recommendations cite evidence IDs, coverage, confidence, and a rule.
- A bounded route includes actions, owners, and metrics instead of generic topics.
- Profile/OPSP prefill carries source/freshness and requires confirmation.

### Deliberately not copied

- Eight-block mandatory questionnaire.
- Hidden value until the final button.
- Fake zero for not-applicable commercial questions.
- Hosted submission, telemetry, or a second data authority.

### Remaining gap

The synthetic path proves the contract and local artifact, not a production UI or
longitudinal user outcome. The next validation must be a human dogfood session
with timing and trust feedback; that is not silently claimed by this receipt.

## Verdict

**E49 acceptance: PASS for the scoped local coaching engine and skill contract.**
Production deployment, live UI, and longitudinal outcome remain separate gates.
