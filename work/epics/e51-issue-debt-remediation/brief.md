# E51: Issue Debt Remediation

## Objective
Close the open GitHub issues #1-#4 that still have real residue in `main`, plus the `governance/guardrails.md` tracking gap found in the parking lot. Each fix must be verified with a regression test before the story closes.

## Scope
1. S51.1 — Clean up the orphaned `coaching/welcome/engine.py` and unify the welcome contract (#1 residual).
2. S51.2 — Repair broken knowledge references in 8+ `escala-skills` SKILL.md files (#2).
3. S51.3 — Create the missing 4 sub-agent personas and 3 decision overviews (#3).
4. S51.4 — Harden `worksheet save` with timestamped backup before overwriting a completed worksheet (#4).
5. S51.5 — Make `governance/guardrails.md` tracked in git so `tests/test_public_boundary.py` passes on a clean clone.

## Success Criteria
- `gh issue view 1 2 3 4` no longer describes reproducible defects on `main`.
- All changed SKILL.md files reference files that exist.
- `worksheet save` never loses a previously completed worksheet.
- `uv run pytest tests/test_public_boundary.py coaching/worksheet/tests/ coaching/welcome/tests/` passes.

## Methodology
RAISE story pipeline, TDD, gates, regression tests. Each story is a standalone branch merged to `main`.
