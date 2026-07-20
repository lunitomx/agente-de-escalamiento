# ESCALA-001: plan

## Approved Approach

Synchronize the executable governance contract with the canonical terminal
dispositions introduced by `c9b119d`, while adding fail-closed regression tests.
Do not restore the old document vocabulary and do not introduce permissive
status aliases.

## Tasks

### T1: Specify the canonical terminal-disposition contract (RED)

- Update the focused tests so the seven canonical statuses and their required
  evidence are the expected contract.
- Add negative cases for `Complete`, an unknown disposition, a missing
  `Backlog action`, and a missing `no complete tag` statement.
- Verify: `uv run pytest tests/test_epic_closure_governance.py -q` — the new
  assertions fail against the old executable contract.
- Commit intent: `test(ESCALA-001): specify terminal disposition contract`.

### T2: Synchronize the validator rules (GREEN)

- Set E19 Book, E23, and E24 to the exact `deferred/backlog` contract and
  require `Governance correction` plus `Backlog action`.
- Set the four draft scopes to their exact `superseded/discarded` or
  `deprecated/discarded` disposition and require `Backlog Closure Review`,
  `Current backlog action`, and `no complete tag`.
- Keep unknown and `complete` states rejected; do not broaden normalization or
  allow aliases.
- Verify: `uv run pytest tests/test_epic_closure_governance.py -q` — all focused
  tests pass.
- Commit: `fix(ESCALA-001): align terminal disposition gates`.

### T3: Run repository gates and record the repair

- Run the full test, format, lint, and type-check commands from the manifest.
- Force-add only the ignored bug artifacts; preserve the unrelated book-PDF
  deletion without staging it in this bugfix.
- Verify:
  - `uv run pytest --tb=short`
  - `uv run ruff format --check`
  - `uv run ruff check`
  - `uv run pyright`
- Commit: `bug(ESCALA-001): record governance repair evidence`.

## Commit-Gate Adaptation

The repository forbids every commit while any test is red. Because this branch
starts with the production regression already failing, T1 cannot be committed
as a standalone RED snapshot. T1 remains an explicit RED checkpoint; T1 and T2
will be committed together only after GREEN. This preserves both TDD order and
the stronger repository invariant that every commit is test-passing.
