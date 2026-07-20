# ESCALA-001: verification

Date: 2026-07-20
Fix commit: `435a7df`

## TDD Evidence

### RED

The expanded canonical-disposition specification was executed before the
validator changed:

```text
rai gate check gate-tests --scope tests/test_epic_closure_governance.py
9 failed, 1 passed
```

Failures covered the unchanged production regression, the new exact canonical
status expectations, acceptance of deferred/discarded states, and required
evidence phrases.

### GREEN

After synchronizing only the exact per-epic rules:

```text
rai gate check gate-tests --scope tests/test_epic_closure_governance.py
10 passed
```

The validator did not gain aliases or permissive status mapping. `Complete`, an
unknown status, missing `Backlog action`, and missing `no complete tag` remain
reported as errors.

## Repository Gates

Executed from commit `435a7df`:

| Gate | Result |
|---|---|
| `rai gate check gate-tests` | Pass |
| `rai gate check gate-lint` | Pass |
| `rai gate check gate-format` | Pass |
| `rai gate check gate-types` | Pass |

`rai gate check --all` was also executed. The four code gates remained green;
five context-dependent gates reported missing invocation context rather than a
product defect:

- architecture review for bugfix and story: no review context yet;
- remote sync: no backlog keys supplied;
- epic and story closure truth: no closure target supplied.

Those checks belong to their scoped review/closure phases. The bugfix
architecture review remains mandatory and is not recorded as passed or skipped
by this verification.

## Scope Integrity

- Seven legacy scope documents were not rewritten by the fix.
- The terminal-disposition index remains the canonical vocabulary source for
  this focused repair.
- The unrelated user-requested deletion of the reference-book PDF was preserved
  outside the bugfix commits.
