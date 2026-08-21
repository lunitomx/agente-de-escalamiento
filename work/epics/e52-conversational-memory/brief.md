# E52: Conversational Memory Persistence

## Objective
Make the E49 conversational welcome (`escala-welcome`) remember authorized context across sessions, so returning users do not have to restart onboarding from scratch.

## Scope
1. S52.1 — Design the persistence contract for `WelcomeState` and user-authorized memory.
2. S52.2 — Implement save/load functions for conversational state.
3. S52.3 — Integrate persistence into `escala-welcome` and verify with tests.

## Success Criteria
- A user can authorize memory persistence during onboarding.
- A later session loads the saved state and continues the conversation where it left off.
- No state is persisted without explicit authorization.
- All existing tests pass.

## Methodology
RAISE story pipeline, TDD, gates, regression tests.
