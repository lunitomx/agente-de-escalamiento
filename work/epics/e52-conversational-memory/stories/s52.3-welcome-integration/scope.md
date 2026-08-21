# S52.3 Scope

## In Scope
- Update `escala-welcome/SKILL.md` to describe persistence authorization and continuation flow.
- Update `coaching/welcome/__init__.py` to load saved state when starting (if fresh and user confirms).
- Add acceptance test for cross-session continuity.

## Out of Scope
- Modifying the core conversation logic in `conversation.py`.
- Hosted or cloud persistence.

## Done when
- SKILL.md describes when and how state is saved/loaded.
- A test proves returning user continuity.
- All existing tests pass.
