# S51.5: Governance Guardrails Tracked

## Problem
`tests/test_public_boundary.py::test_public_boundary_guardrail_replaces_attribution_rule` reads `governance/guardrails.md`, but the file is ignored by `.gitignore` (`governance/`) and therefore not tracked. A clean clone will fail this test.

## Root Cause
`.gitignore` contains a blanket `governance/` rule that prevents new governance files from being tracked, even though several governance files are already tracked and the test depends on `guardrails.md`.

## Goal
Make `governance/guardrails.md` part of the repository so the boundary test is reproducible on any clone.

## Acceptance Criteria
- [ ] `governance/guardrails.md` is tracked in git.
- [ ] `git status --short governance/guardrails.md` shows nothing on a clean clone after checkout.
- [ ] `uv run pytest tests/test_public_boundary.py::test_public_boundary_guardrail_replaces_attribution_rule` passes in a fresh clone.
- [ ] No unintended governance files are added to git.

## Tasks
1. Decide strategy: force-track `guardrails.md` only, or refine `.gitignore`.
2. Apply the strategy.
3. Verify in a clean environment or with `git check-ignore`.
4. Run gates.

## Related
- Parking lot item from E47
