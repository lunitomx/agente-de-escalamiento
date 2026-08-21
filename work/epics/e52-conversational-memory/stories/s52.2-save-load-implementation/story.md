---
jira_key: ""
---

# S52.2: Save/Load Implementation

## User Story
As the welcome module, I want save/load functions, so that authorized WelcomeState can be persisted and restored.

## Gherkin AC
Feature: WelcomeState persistence functions

Scenario: Save authorized state
  Given a WelcomeState and explicit authorization
  When save_welcome_state is called
  Then the state is written to `.escala/agent/memory/welcome-state.yaml`

Scenario: Refuse unauthorized save
  Given a WelcomeState without authorization
  When save_welcome_state is called
  Then nothing is written

Scenario: Load existing state
  Given a valid welcome-state.yaml exists
  When load_welcome_state is called
  Then the WelcomeState is returned

Scenario: Missing state returns None
  Given no welcome-state.yaml exists
  When load_welcome_state is called
  Then None is returned
