---
jira_key: ""
---

# S52.3: Welcome Integration

## User Story
As a returning user, I want escala-welcome to load my saved state and continue the conversation, so that I do not restart onboarding from scratch.

## Gherkin AC
Feature: Welcome uses persisted state

Scenario: Returning user with fresh state is offered continuation
  Given a saved welcome state exists and is fresh
  When escala-welcome starts
  Then the agent asks whether to continue

Scenario: User declines persistence
  Given a fresh conversation
  When the user declines to save memory
  Then no state file is written

Scenario: User authorizes persistence
  Given a fresh conversation
  When the user authorizes memory
  Then state is saved and can be loaded later

## SbE Examples
- Saved state with area="cash" → "¿Continuamos con Cash?"
- No saved state → normal first-contact question.
