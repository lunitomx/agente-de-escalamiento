# S52.3: Welcome Integration

## Problem
Even with save/load functions, `escala-welcome` will not use them unless the SKILL.md and conversation flow are updated.

## Root Cause
The conversational skill flow was designed stateless.

## Goal
Integrate persistence into the welcome flow: ask for authorization, save at end of turn, and load on start.

## Acceptance Criteria
- [ ] `escala-welcome/SKILL.md` describes when and how state is persisted.
- [ ] Returning users are offered to continue from saved state when it exists and is fresh.
- [ ] Users can decline persistence and start fresh.
- [ ] Regression test proves cross-session continuity.
- [ ] All existing tests pass.

## Tasks
1. Update `escala-welcome/SKILL.md` flow.
2. Update `coaching/welcome/__init__.py` or conversation entry points to load state.
3. Add acceptance test.
4. Run gates.

## Related
- GitHub issue #8
- S52.2
