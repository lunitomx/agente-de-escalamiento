---
jira_key: ""
---

# S51.5: Governance Guardrails Tracked

## User Story
As a CI pipeline, I want `governance/guardrails.md` to be tracked in git, so that `tests/test_public_boundary.py` passes on a clean clone.

## Gherkin AC
Feature: Governance guardrails are versioned

Scenario: Clean clone has guardrails.md
  Given a fresh clone of the repository
  When I run the public boundary guardrail test
  Then it passes because guardrails.md is present

Scenario: guardrails.md is not ignored
  Given git check-ignore is run on governance/guardrails.md
  Then it reports the file is not ignored

## SbE Examples
- `git ls-files governance/guardrails.md` returns the file path.
- `uv run pytest tests/test_public_boundary.py::test_public_boundary_guardrail_replaces_attribution_rule` passes.
