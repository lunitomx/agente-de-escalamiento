# S52.2: Save/Load Implementation

## Problem
No functions exist to persist or restore `WelcomeState` to/from disk.

## Root Cause
`coaching/welcome/conversation.py` is pure in-memory logic. Persistence was not part of the original implementation.

## Goal
Add `save_welcome_state(base_path, state, authorized)` and `load_welcome_state(base_path)` with clear error handling.

## Acceptance Criteria
- [ ] `save_welcome_state` writes YAML only when `authorized=True`.
- [ ] `load_welcome_state` returns `None` when no saved state exists.
- [ ] Saved state is human-readable YAML.
- [ ] Tests cover save, load, missing file, and unauthorized save.
- [ ] All existing tests pass.

## Tasks
1. Add persistence functions to `coaching/welcome/conversation.py` or a new module.
2. Write unit tests.
3. Run gates.

## Related
- GitHub issue #8
- S52.1
