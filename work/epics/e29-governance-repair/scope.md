# Epic Scope: E29 — Governance Repair for Epic Closure Truth

**Status:** Complete

## Objective

Repair closure truth for the recently audited epic set so completed epics have unambiguous evidence, draft scopes are not misclassified as complete, and pipeline/skill/gate governance is visible without relying on memory or tag-number inference.

## In Scope

- Reconcile the 20 audited items against tracked files, close commits, tags, retrospectives, story artifacts, and ignored local drafts.
- Fix contradictory closure records, especially E25.
- Add canonical slug-based tags for completed epics that currently rely on ambiguous or missing number-only tags.
- Add or patch `Pipeline / Skills / Gates` sections where the implementation is complete but governance evidence is incomplete.
- Reclassify ignored local draft scopes as backlog/future/cancelled; do not close them as if they were completed.
- Produce a final closure audit proving the repaired state.

## Out of Scope

- Implementing unfinished product functionality from draft scopes.
- Deleting ignored draft scopes without explicit decision.
- Rewriting historical implementation commits.
- Closing the current RaiSE session.
- Broad refactors outside governance artifacts and tags.

## Critical Findings From Pre-Audit

| Finding | Impact |
|---|---|
| E25 said `COMPLETE`, but its scope still said `Draft` and its retrospective had conflicting story counts. | Formal close was not trustworthy until docs were reconciled. |
| E18 Class-to-Skill claims `epic/e18-complete`, but that tag points to E18 Escala Server. | Tag evidence is false/ambiguous for that epic. |
| E19 Strategy Core, E20 Voice of Customer, E21 Transcript Intelligence, E22 Validation Drift are ignored local drafts, not tracked completed epics. | They must not be counted as finalizadas. |
| E15-E17 have close commits and retrospectives but no `epic/eN-complete` tags. | Completion is evidenced but not tag-addressable. |
| E18-E22 use number-only tags where multiple local directories share the same number. | Future audits can misclassify again. |

## Planned Stories

| ID | Story | Size | Depends | Purpose |
|---|---|---:|---|---|
| S29.1 | Canonical audit inventory | M | — | Freeze truth in `audit-matrix.md`; verify git-tracked vs ignored vs tagged evidence. |
| S29.2 | E25 contradiction repair | S | S29.1 | Patch E25 scope/retrospective so closure, story count, and done criteria agree. |
| S29.3 | Draft-scope reclassification | M | S29.1 | For ignored E19/E20/E21/E22 drafts, decide and document: backlog, cancelled, or renumbered future epic. |
| S29.4 | Canonical tag repair | M | S29.1, S29.2, S29.3 | Add slug-based canonical tags and legacy tag notes for E9-E25 as needed. |
| S29.5 | Pipeline / Skills / Gates documentation | L | S29.1 | Add standard governance section to all DOC_REPAIR/CONTRADICTORY_CLOSE completed epics. |
| S29.6 | Final closure re-audit | M | S29.2-S29.5 | Re-run checks and write `final-closure-audit.md` with pass/fail evidence. |

## Sequencing Strategy

Risk-first.

1. Freeze evidence before editing so we do not repair the wrong thing.
2. Fix E25 first because it has a direct contradiction inside closure artifacts.
3. Reclassify ignored draft scopes before tagging; otherwise tags could bless non-work.
4. Add canonical tags only after the target commit/path is known.
5. Patch pipeline/gate documentation last, after the closure target set is clean.

## Milestones

| Milestone | Stories | Success Criteria |
|---|---|---|
| M1 Truth Freeze | S29.1 | Every audited item classified as SOLID, DOC_REPAIR, CONTRADICTORY_CLOSE, or NOT_COMPLETED_SCOPE with file/commit evidence. |
| M2 Closure Corrections | S29.2-S29.3 | E25 contradiction removed; ignored draft scopes no longer listed as complete. |
| M3 Tag & Governance Repair | S29.4-S29.5 | Canonical tags exist; completed epics document pipeline/skills/gates or explicitly state why not applicable. |
| M4 Formal Re-Audit | S29.6 | `final-closure-audit.md` shows zero contradictory closes, zero draft scopes counted as complete, zero ambiguous tags without canonical replacement. |

## Done Criteria

- [x] `audit-matrix.md` is complete and cites evidence for each audited item.
- [x] E25 scope and retrospective agree on status, stories, and done criteria.
- [x] Ignored local draft scopes are explicitly classified and excluded from completed epic counts.
- [x] Completed epics with duplicate numbers have canonical slug tags.
- [x] Completed epics missing tags have canonical slug tags.
- [x] Every completed audited epic has `Pipeline / Skills / Gates` or an explicit "not applicable" rationale.
- [x] `final-closure-audit.md` proves the repaired state.
- [x] `git status --short` is reviewed before any commit.

## Repair Policy

- Do not invent missing implementation evidence.
- Do not close ignored draft scopes unless implementation evidence is found.
- Do not delete draft scopes without explicit user approval.
- Prefer additive canonical tags over deleting legacy tags.
- When evidence is reconstructed, label it `reconstructed` and cite source commits.

## Final Status

Complete as governance repair. Product work from ignored draft scopes was not implemented or closed; those drafts were explicitly reclassified as backlog candidates.

Closure retrospective evidence: `work/epics/e29-governance-repair/retrospective.md`
documents the repair boundaries and residual risks added by E32.
