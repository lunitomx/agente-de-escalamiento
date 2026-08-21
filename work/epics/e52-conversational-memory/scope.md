# E52 Scope

## In Scope
- Define what parts of `WelcomeState` and derived facts are persisted.
- Add explicit authorization step before persistence.
- Implement `save_welcome_state` / `load_welcome_state` in `coaching/welcome/`.
- Update `escala-welcome/SKILL.md` to use persistence.
- Tests covering save, load, authorization, and empty-state fallback.

## Out of Scope
- Cross-device sync or cloud storage (local-only invariant).
- Persisting raw user messages verbatim.
- Onboarding multifuente / financial reconciliation (issue #9, E53).

## Risks
- Over-persisting could leak context between users on a shared machine.
- Loading stale state without freshness checks could confuse users.

## Stories
- S52.1: Persistence contract design
- S52.2: Save/load implementation
- S52.3: Welcome integration
