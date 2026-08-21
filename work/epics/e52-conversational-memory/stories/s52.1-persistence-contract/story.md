---
jira_key: ""
---

# S52.1: Persistence Contract Design

## User Story
As a returning user, I want my authorized onboarding context to persist, so that the next session can continue where I left off.

## Gherkin AC
Feature: Conversational state persistence contract

Scenario: Authorized state is persisted
  Given the user explicitly authorizes memory
  When the welcome conversation ends
  Then WelcomeState and derived facts are written to disk

Scenario: Unauthorized state is not persisted
  Given the user does not authorize memory
  When the welcome conversation ends
  Then no state file is created

## SbE Examples
- Authorized save produces `.escala/agent/memory/welcome-state.yaml`.
- Declined save leaves no welcome-state file.
