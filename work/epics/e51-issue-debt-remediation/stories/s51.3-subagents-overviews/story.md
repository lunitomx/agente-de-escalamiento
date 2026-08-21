---
jira_key: ""
---

# S51.3: Sub-Agents and Decision Overviews

## User Story
As a decision skill, I want a sub-agent persona and a domain overview, so that I can coach the user with consistent context and routing.

## Gherkin AC
Feature: Decision skills have required context files

Scenario: Strategy skill loads its sub-agent
  Given escala-strategy is invoked
  When it reads `.escala/agent/sub-agents/strategy.md`
  Then the file exists and defines the strategy coaching persona

Scenario: People skill loads its overview
  Given escala-people is invoked
  When it reads `.escala/knowledge/people/overview.md`
  Then the file exists and summarizes the people decision domain

## SbE Examples
- `.escala/agent/sub-agents/cash.md` → coaching persona for Cash
- `.escala/knowledge/execution/overview.md` → overview of Execution domain
