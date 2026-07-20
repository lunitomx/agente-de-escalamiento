# Architecture Review: ESCALA-001 (scope: bugfix)

Date: 2026-07-20
Base: `c9b119d`
Reviewed head: `0bdbf43`
Language: Python

## Design Intent

Keep the seven truthful terminal dispositions introduced by `c9b119d`, update
the exact executable rules that consume them, and preserve fail-closed behavior.
A broader typed source of truth is explicitly deferred to E36.

## Scope Reviewed

- `validators/epic_closure.py`
- `tests/test_epic_closure_governance.py`
- the bug scope, analysis, plan, verification, and retrospective artifacts

The code-context query returned no ranked symbols. The graph query returned no
relevant established `PAT-E-*` pattern for closure status contracts, so the
review used the approved bug design, `PAT-L-1267`, and the existing validator
shape as its comparison baseline.

## Critical (fix before merge)

None.

## Recommended (simplify in E36)

1. **H9 / L5 — status vocabulary still has two physical sources.**
   `validators/epic_closure.py:35-128` repeats values held in the audited
   Markdown scopes. This duplication caused ESCALA-001. Removing it inside this
   prerequisite would expand the fix into a schema migration, so the approved
   proportional action is to keep exact rules now and create one typed source of
   truth in E36.

## Questions (human judgment)

1. **H7 / L5 — explicit tests versus a fixture helper.**
   `tests/test_epic_closure_governance.py:65-192` repeats temporary-scope setup.
   A helper would reduce lines, but the explicit cases make each governance
   posture independently auditable. Recommendation: retain the explicit cases
   until E36 introduces a typed status matrix, then parameterize from that
   matrix.
2. **L2 — deferral boundary.** Is it acceptable to close this bug with semantic
   duplication still present, provided E36 owns the single-source migration?
   Gate 2 already approved this boundary; Gate 3 should confirm it remains the
   intended close posture.

## Observations

- **H1-H8:** no new protocol, wrapper, public API, dependency, configuration,
  or delegation layer was added.
- **H10-H12:** the validator retains one responsibility and no new import fan-in.
- **AG1-AG6:** no authorization, clone amplification, unresolved symbols,
  secrets, vulnerability surface, or prompt-literal production branches were
  introduced.
- **L1-L5:** the implementation matches the approved route 2 and does not build
  the deferred E36 schema prematurely.
- `validators/epic_closure.py:153-175` remains fail-closed: an unexpected status
  or missing evidence produces an error.
- `tests/test_epic_closure_governance.py:22-62` still proves that `Complete` is
  rejected for deferred and discarded records.

## Verdict

**PASS — Gate 3 confirmed by the user on 2026-07-20.**

The implementation is necessary and proportional for the prerequisite bug. No
code change is required before merge; the remaining question concerns ownership
of the broader single-source migration, not correctness of this repair.

The user authorized uninterrupted execution of routine local PASS gates and
accepted that the broader single-source migration remains owned by E36. Future
pauses are reserved for material scope decisions, critical findings,
destructive actions, external publication/push, or credentials.
