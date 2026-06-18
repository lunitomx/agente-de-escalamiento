# Epic Scope: E32 — Closure Evidence Repair

**Status:** Complete
**Completed:** 2026-06-18

## Objective

Repair the governance truth for suspicious epic closures so closed work is backed by independent evidence, incomplete product work is not presented as complete, and legacy tags are treated as historical signals rather than source-of-truth proof.

## In Scope

- Audit and repair E10, E11, E19, E22, E23, E24, E29, E30, and E31.
- Add an automated governance check for contradictory closure status and open Done Criteria.
- Create a single truth matrix with evidence, contradictions, corrected status, required follow-up, and tag action.
- Add E29 closure retrospective evidence without reopening E29.
- Preserve existing implementation behavior; this epic is governance/documentation plus validation only.

## Out of Scope

- Implementing parser/API/schema work left open in E19.
- Implementing E24 cron, auto-patch, or post-session automation.
- Closing E31 while S31.3 remains pending.
- Deleting or rewriting historical tags without human review.
- Touching unrelated dirty files.

## Planned Stories

| ID | Story | Size | Purpose |
|---|---|---:|---|
| S32.1 | Closure evidence repair | M | Add audit validator, repair suspicious artifacts, and document the corrected truth matrix. |

## Done Criteria

- [x] `audit-matrix.md` lists claimed status, independent evidence, contradictions, corrected status, required follow-up, and tag action for every audited epic.
- [x] E10, E11, E19, E22, E23, E24, E29, E30, and E31 scopes no longer contradict their corrected status.
- [x] Automated governance test fails for `Complete` plus open Done Criteria unless the epic is explicitly partial, absorbed, descoped, legacy, or backlog.
- [x] E29 has retrospective evidence declaring its repair boundaries.
- [x] E31 remains active and is explicitly not taggable as complete.
- [x] Existing unrelated dirty files remain untouched.

## Repair Policy

- Do not invent implementation evidence.
- If proof is missing, mark the item partial/backlog instead of checking the box.
- Prefer additive tag documentation over tag deletion.
- Product follow-up is captured as backlog/future work, not silently closed.

## Progress

| Story | Status | Notes |
|---|---|---|
| S32.1 | Complete | Governance repair and closure validator. |

## Final Status

Complete as governance repair. E32 did not implement old product work; it made
the closure record truthful and added an automated guard against the same class
of false-complete drift.
