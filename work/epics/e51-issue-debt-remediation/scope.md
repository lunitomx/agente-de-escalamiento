# E51 Scope

## In Scope
- Remove or align the orphaned `coaching/welcome/engine.py` so the welcome contract is unambiguous.
- Repoint `.escala/knowledge/**/*.md` references in `escala-skills/*` to the real `conocimiento/**/*.yaml` files.
- Create `.escala/agent/sub-agents/{strategy,people,execution,cash}.md` and `.escala/knowledge/{strategy,people,execution}/overview.md` with content derived from `conocimiento/decisions/*.yaml`.
- Add timestamped backup to `coaching.worksheet.run(action="save")` when overwriting an existing completed worksheet.
- Force-track `governance/guardrails.md` in git.

## Out of Scope
- Changing the conversational E49 welcome flow (that is E52).
- Onboarding multifuente / conciliación financiera (issue #9, shaped initiative).
- Full skill-catalog consolidation (E55).
- Hosted/multi-writer runtime, cloud APIs, psychological inference (rejected in parking lot).

## Risks
- SKILL.md edits can break agent mirrors if they are not regenerated from `escala-skills/`.
- Adding backup logic must not break existing worksheet consumers.

## Stories
- S51.1: Welcome engine cleanup
- S51.2: Knowledge references repair
- S51.3: Sub-agents and overviews
- S51.4: Worksheet save hardening
- S51.5: Governance guardrails tracked
