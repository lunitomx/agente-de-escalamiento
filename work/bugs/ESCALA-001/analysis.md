# ESCALA-001: analysis

## Method: git bisect plus contract diff

The regression followed a known governance-document change, so the analysis used
`git bisect` in an isolated temporary clone and then compared the validator
contract with the changed scope artifacts.

### Root Cause

Commit `c9b119d024470bbf431bd649c4b6a9f2a2954f41` introduced a more precise
terminal-disposition vocabulary in seven legacy epic scopes without updating the
exact-string contract in `validators/epic_closure.py` or its regression tests.

The validator models each epic with one literal `expected_status` and literal
`required_phrases`. It therefore cannot distinguish the shared governance
meaning "not complete and not active" from the particular disposition used to
express it. The new scopes remain fail-closed, but their canonical labels changed:

- `Partial` / `Partial/Backlog` became `Deferred/Backlog` for E19 Book, E23, and E24.
- `required follow-up` became `Backlog action` for those deferred scopes.
- `Backlog/Not Completed` became `Superseded/Discarded` or
  `Deprecated/Discarded` for the four draft scopes.

No validator or test file changed in the introducing commit. The documents and
the executable governance contract consequently drifted in the same commit.

### Evidence

- Current reproduction: `2 failed, 2 passed`, with 10 errors: six across E19
  Book/E23/E24 and four across the E19-E22 backlog drafts.
- The exact parent `c9b119d^` passes the focused module: `4 passed`.
- Isolated `git bisect` identifies `c9b119d` as the first bad commit.
- `git diff c9b119d^ c9b119d -- validators/epic_closure.py
  tests/test_epic_closure_governance.py` is empty.
- The new scopes still prohibit false completion: deferred scopes say they must
  not be counted as unqualified complete, and discarded drafts retain the
  `no complete tag` evidence plus an explicit successor or deprecation.

### Fix Approaches

1. **Restore the legacy document tokens.** Change the seven scopes back to
   `Partial`, `Partial/Backlog`, or `Backlog/Not Completed` and restore
   `required follow-up`. This is the smallest diff, but it erases the deliberate
   distinction between deferred work and ideas already superseded or discarded;
   it also conflicts with the terminal-disposition index.
2. **Synchronize the executable contract to the canonical terminal
   dispositions (recommended).** Keep the truthful scope language, update each
   rule to its exact canonical status and evidence phrase, and add regression
   cases proving that `Complete`, unknown dispositions, missing backlog action,
   and missing `no complete tag` remain rejected. This repairs the mismatch
   without treating several aliases as universally interchangeable.

### Recommended Fix Approach

Use approach 2 as a focused compatibility repair. Defer a broader structured
closure-schema migration to E36, where the governance vocabulary can become a
single typed source of truth rather than expanding this prerequisite bug.
