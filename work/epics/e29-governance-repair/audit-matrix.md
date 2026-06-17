# E29 Governance Repair — Audit Matrix

Date: 2026-06-16
Scope: last 20 items previously treated as completed epics during pipeline/governance audit.

## Classification Rules

- SOLID: scope, retrospective, story evidence, and tag/commit evidence agree.
- DOC_REPAIR: implementation likely complete, but governance docs have missing or stale fields.
- CONTRADICTORY_CLOSE: closure evidence exists but conflicts with scope/retrospective facts.
- NOT_COMPLETED_SCOPE: local scope exists, but there is no tracked implementation/close evidence. Do not count as completed.
- AMBIGUOUS_LEGACY_TAG: tag name is number-only and can collide with another local directory using the same epic number.

## Findings

| Item | Current Classification | Evidence | Problem | Required Repair |
|---|---|---|---|---|
| E25 Escala Live | CONTRADICTORY_CLOSE | `epic/e25-complete`; tracked story retros; later commit `3794689 docs(e25): S25.5 done — epic complete` | Original finding: `scope.md` said `Status: Draft` and had unchecked done criteria; `retrospective.md` reported conflicting story counts. | Patch scope to `Complete`; check done criteria; fix retrospective story count and S25.5 row; document canonical closure commit after tag. Consider moving/retagging `epic/e25-complete` or adding `epic/e25-escala-live-complete` at true final commit `3794689`. |
| E24 Escala Evolve | DOC_REPAIR | `epic/e24-complete`; 5 tracked story retros; retrospective says 5/5 | Good closure evidence. Pipeline/gates are light in epic-level docs. | Add `Pipeline / Skills / Gates` section; record evolve loop gates: proposal states, approval, backup, diff, rollback. |
| E23 Kokoro Agent | DOC_REPAIR | `epic/e23-complete`; 11/11 in scope and retro; commits S23.1-S23.11 | Good closure evidence. Story files only exist for S23.6-S23.11; S23.1-S23.5 are tracked in scope/commits but not full story docs. | Add evidence table for S23.1-S23.5 commits; add `Pipeline / Skills / Gates`; optionally create short reconstructed story retros for S23.1-S23.5 or mark "scope-tracked only". |
| E22 Full System Audit / Verne Audit | SOLID_WITH_ABSORPTIONS | `epic/e22-complete`; retro says 9 done, 3 absorbed/descoped; scope status complete | This is the real E22 closed by the tag. Absorptions are documented but need cross-links to E23/E24/E25 evidence. | Add absorption evidence links: S22.10 -> E25/S25.6, S22.11 -> E23/S23.6, S22.12 -> E25/S25.7 or explicit descoped note. Add canonical tag `epic/e22-verne-audit-complete`. |
| E22 Validation Drift Governance | NOT_COMPLETED_SCOPE | ignored local files only (`!!` in `git status --ignored`); no `git ls-files`; no git log for directory | Was incorrectly pulled into completed set because number E22 matched `epic/e22-complete`. It is not tracked and not closed. | Do not close. Decide: delete ignored draft, move to backlog as future E30+, or formalize as new active epic. If kept, renumber to avoid collision. |
| E21 Verne Board Member | DOC_REPAIR | `epic/e21-complete`; retro status complete; 6 stories tracked; 28 tests in retro | Real E21 closed by tag. Good evidence. | Add canonical tag `epic/e21-verne-board-member-complete`; add `Pipeline / Skills / Gates`; verify S21.6 story has retrospective or mark missing. |
| E21 Transcript Intelligence | NOT_COMPLETED_SCOPE | ignored local files only; no `git ls-files`; no git log for directory | Was incorrectly pulled into completed set because number E21 matched Verne Board Member tag. | Do not close. Decide: delete ignored draft, move to backlog, or renumber as future epic. |
| E20 Contextual Skills | DOC_REPAIR | `epic/e20-complete`; scope complete; retro complete; 4 story retros | Real E20 closed by tag. Strong pipeline wording already present. | Add canonical tag `epic/e20-contextual-skills-complete`; add explicit `Pipeline / Skills / Gates` section if not already enough; update legacy tag note. |
| E20 Voice of Customer Evidence Capture | NOT_COMPLETED_SCOPE | ignored local files only; no `git ls-files`; no git log for directory | Was incorrectly pulled into completed set because number E20 matched Contextual Skills tag. | Do not close. Decide future backlog or delete ignored draft. |
| E19 Book Ingestion | DOC_REPAIR | `epic/e19-complete`; retro; scope status complete; story evidence | Real E19 closed by tag. Scope has unchecked done criterion despite retrospective saying integrity tests exist. | Check done criteria in scope; add canonical tag `epic/e19-book-ingestion-complete`; add `Pipeline / Skills / Gates`. |
| E19 Strategy Core Skills | NOT_COMPLETED_SCOPE | ignored local files only; no `git ls-files`; no git log for directory | Was incorrectly pulled into completed set because number E19 matched Book Ingestion tag. | Do not close. Decide future backlog or delete ignored draft. |
| E18 Escala Server | DOC_REPAIR | `epic/e18-complete`; retro; 12 story retros; scope status complete | Real E18 closed by tag. Strong evidence. | Add canonical tag `epic/e18-escala-server-complete`; add legacy tag note. |
| E18 Class-to-Skill Learning Loop | CONTRADICTORY_CLOSE | tracked retro and story evidence; retro claims tag `epic/e18-complete`; git shows that tag points to E18 Escala Server close commit, not this epic | It is complete by docs/commits, but its tag claim is false/ambiguous. | Add canonical tag `epic/e18-class-to-skill-learning-loop-complete` at close commit `d857799`; update retrospective tag section to mark `epic/e18-complete` as invalid legacy collision. |
| E17 Execution Dashboards | DOC_REPAIR | commit `555e913 epic(e17): close...`; retro complete; scope complete | Closed without `epic/e17-complete` tag. No explicit pipeline/gate docs. | Add tag `epic/e17-execution-dashboards-complete`; add `Pipeline / Skills / Gates`; note manual/dashboard verification model. |
| E16 People Dashboards | DOC_REPAIR | commit `e008ea4 epic(e16): close...`; retro complete; scope complete | Closed without `epic/e16-complete` tag. No explicit gate docs. | Add tag `epic/e16-people-dashboards-complete`; add `Pipeline / Skills / Gates`; note manual/dashboard verification model. |
| E15 Strategy Dashboards | DOC_REPAIR | commit `cc921a3 epic(e15): close...`; retro complete; scope complete | Closed without `epic/e15-complete` tag. No explicit gate docs. | Add tag `epic/e15-strategy-dashboards-complete`; add `Pipeline / Skills / Gates`; note manual/dashboard verification model. |
| E14 Cash Dashboards | SOLID | `epic/e14-complete`; scope/retro/story evidence; AR/QR fix commits | Solid closure. | Optional canonical slug tag `epic/e14-cash-dashboards-complete`; no urgent doc repair. |
| E11 Agente de Escalamiento | DOC_REPAIR | commit `9453f24 epic(e11): close...`; retrospective complete | Closed without local `epic/e11-complete` tag. Strong retro. | Add canonical tag `epic/e11-agente-escalamiento-complete`; add `Pipeline / Skills / Gates` focused on migration script + grep verification. |
| E10 Cross-Platform Distribution | SOLID | `epic/e10-complete`; retro; compatibility matrix; tests | Solid closure; known shallow Hermes adapter risk is documented. | Optional slug tag `epic/e10-cross-platform-distribution-complete`; no urgent repair. |
| E9 Value Add | SOLID | `epic/e9-complete`; retro/story evidence | Solid closure. | Optional slug tag `epic/e9-value-add-complete`; no urgent repair. |

## High-Risk Truth Corrections

1. The number-only tags are not enough when multiple local epic folders share the same number.
2. Four ignored local draft scopes were incorrectly treated as completed epics. They must not be closed without implementation evidence.
3. E25's formal close had internal contradictions and required document repair before being trusted.
4. E18 Class-to-Skill has real completion evidence but points to the wrong legacy tag.

## Repair Status

| Item | Repair Result |
|---|---|
| E25 Escala Live | Repaired. Scope is complete, done criteria checked, retrospective story count fixed to 8/8, canonical tag added at true final closure commit. |
| E24 Escala Evolve | Repaired. Pipeline / Skills / Gates section added; canonical tag added. |
| E23 Kokoro Agent | Repaired. Pipeline / Skills / Gates section added; canonical tag added. |
| E22 Full System Audit / Verne Audit | Repaired. Pipeline / Skills / Gates and absorption evidence added; canonical tag added. |
| E22 Validation Drift Governance | Reclassified as not completed. No close performed. |
| E21 Verne Board Member | Repaired. Pipeline / Skills / Gates section added; canonical tag added. |
| E21 Transcript Intelligence | Reclassified as not completed. No close performed. |
| E20 Contextual Skills | Repaired. Pipeline / Skills / Gates section added; canonical tag added. |
| E20 Voice of Customer Evidence Capture | Reclassified as not completed. No close performed. |
| E19 Book Ingestion | Repaired. Done criterion checked, closure evidence added, Pipeline / Skills / Gates section added, canonical tag added. |
| E19 Strategy Core Skills | Reclassified as not completed. No close performed. |
| E18 Escala Server | Repaired. Pipeline / Skills / Gates section added; canonical tag added. |
| E18 Class-to-Skill Learning Loop | Repaired. Legacy tag collision documented, Pipeline / Skills / Gates section added, canonical tag added. |
| E17 Execution Dashboards | Repaired. Pipeline / Skills / Gates section added; canonical tag added. |
| E16 People Dashboards | Repaired. Pipeline / Skills / Gates section added; canonical tag added. |
| E15 Strategy Dashboards | Repaired. Pipeline / Skills / Gates section added; canonical tag added. |
| E14 Cash Dashboards | Repaired for consistency. Pipeline / Skills / Gates section added; canonical tag added. |
| E11 Agente de Escalamiento | Repaired. Pipeline / Skills / Gates section added; canonical tag added. |
| E10 Cross-Platform Distribution | Repaired for consistency. Pipeline / Skills / Gates section added; canonical tag added. |
| E9 Value Add | Repaired for consistency. Pipeline / Skills / Gates section added; canonical tag added. |
