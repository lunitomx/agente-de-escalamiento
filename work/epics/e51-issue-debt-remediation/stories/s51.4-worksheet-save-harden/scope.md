# S51.4 Scope

## In Scope
- Add timestamped backup logic to `coaching.worksheet.run(action="save")` when overwriting an existing completed worksheet.
- Create `coaching/worksheet/tests/test_worksheet_save.py` with regression tests.

## Out of Scope
- Changing worksheet load/list/step behavior.
- UI confirmation dialogs.

## Done when
- Saving over a completed worksheet creates a deterministic timestamped backup.
- Tests prove backup creation and new data preservation.
- No unnecessary backups are created for in-progress saves.
- All existing tests pass.
