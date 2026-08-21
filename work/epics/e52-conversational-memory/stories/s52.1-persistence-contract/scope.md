# S52.1 Scope

## In Scope
- Define the persistence contract for `WelcomeState`:
  - Storage path: `.escala/agent/memory/welcome-state.yaml`
  - Fields persisted: phase, profile, concern, area, next_action, returning, previous_focus
  - Authorization: explicit user consent required
  - Freshness: timestamp + max age before prompting to confirm
- Produce the contract document as a design artifact.

## Out of Scope
- Implementation of save/load functions (S52.2).
- SKILL.md flow changes (S52.3).

## Done when
- Contract document is reviewed and committed.
- S52.2 has a clear implementation spec.
