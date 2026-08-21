---
jira_key: ""
---

# S51.4: Worksheet Save Hardening

## User Story
As a user, I want completed worksheets to be backed up before overwrite, so that I never lose prior work.

## Gherkin AC
Feature: Worksheet save protects completed data

Scenario: Saving over a completed worksheet creates a backup
  Given a worksheet is already completed
  When I call worksheet save again
  Then a timestamped backup exists and the new data is saved

Scenario: Saving an in-progress worksheet does not create unnecessary backups
  Given a worksheet is in progress
  When I save a step
  Then no backup is created

## SbE Examples
- Existing file: `.escala/my-company/worksheets/test-ws.yaml` with status `completed`
- Backup pattern: `.escala/my-company/worksheets/test-ws-20260821-120000.yaml`
