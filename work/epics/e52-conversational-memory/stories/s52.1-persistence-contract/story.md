# S52.1: Persistence Contract Design

## Problem
Issue #8 reports that after a long conversational onboarding, the context memory is empty in a later session. `WelcomeState` is serializable but never saved.

## Root Cause
There is no contract defining what to persist, where to store it, or when persistence is authorized.

## Goal
Define a minimal, explicit persistence contract for conversational onboarding.

## Acceptance Criteria
- [ ] Document the decision on what fields of `WelcomeState` are persisted.
- [ ] Document the storage path (e.g., `.escala/agent/memory/welcome-state.yaml`).
- [ ] Document the authorization rule: state is only persisted after explicit user consent.
- [ ] Document freshness/invalidation behavior.
- [ ] Design reviewed and approved before implementation.

## Tasks
1. Analyze `WelcomeState` fields and decide what is safe/useful to persist.
2. Draft the contract in the story scope doc.
3. Review against local-only and privacy constraints.
4. Hand off to S52.2.

## Related
- GitHub issue #8
