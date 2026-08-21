# S51.4: Worksheet Save Hardening

## Problem
GitHub issue #4 reported that `worksheet save` ignored `base_path` and silently overwrote worksheets, risking data loss across businesses. `base_path` is now honored, but there is still no backup when a completed worksheet is overwritten.

## Root Cause
`coaching/worksheet/__init__.py::run(action="save")` calls `write_yaml(state_path, completed_data)` directly. If a file already exists at `state_path`, it is replaced without a backup or confirmation.

## Goal
Protect completed worksheets from accidental overwrite by creating a timestamped backup before writing.

## Acceptance Criteria
- [ ] When `save` overwrites an existing completed worksheet, a timestamped backup is created alongside it.
- [ ] The backup path is deterministic and parseable.
- [ ] A regression test proves the backup is created and the new data is written.
- [ ] No-op saves do not create unnecessary backups.
- [ ] All existing tests pass.

## Tasks
1. Add backup logic to `coaching/worksheet/__init__.py` save path.
2. Create `coaching/worksheet/tests/test_worksheet_save.py`.
3. Run gates.

## Related
- GitHub issue #4
