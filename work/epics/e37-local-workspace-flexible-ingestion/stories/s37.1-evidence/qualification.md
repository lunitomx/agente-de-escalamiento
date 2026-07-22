# S37.1 Local Workspace Qualification

## Qualified source

- Story: `S37.1`
- Epic: `E37`
- Source commit: `f14ad924479cd3ecfa9e5b2d74055df072217299`
- Observed platform: `macos`

## Automated gates

- Focused authority tests: `12` passing.
- Full repository tests: `860` collected and passing.
- `uv run ruff check`: PASS.
- `uv run ruff format --check`: PASS.
- `uv run pyright`: PASS with `0` errors, `0` warnings and `0` informations.

## Manual local flow

An isolated temporary workspace ran the real `daos.schema.init_db_for_workspace`
adapter twice:

1. A valid local database target produced a passing authority receipt and
   created SQLite under the local data root.
2. A database target inside the exchange produced `fail` with the stable code
   `authoritative_sqlite_sync_forbidden`.
3. The invalid run did not create a database, WAL or journal in the exchange;
   before/after filesystem listings were identical.
4. The JSON receipt contained no temporary root, database filename or raw error.
5. No network, OAuth, Drive API, OneDrive API, telemetry or hosted service was
   invoked.

The qualification also found and fixed a macOS false positive where the system
`/var` symlink was incorrectly treated as a symlink inside the user exchange.
The guard now stops at the declared exchange boundary and has a regression
fixture for a direct exchange target.

## Truth boundary

This is evidence for S37.1 implementation, not proof that the whole product or
E37 is complete. `REQ-E37-001` and `REQ-E37-002` are ready for exact master
ledger receipts after story review/close. The master ledger remains truthfully
`unproved` until those requirement-specific gate receipts are committed; no
plan, checkbox or local test count is promoted automatically.
