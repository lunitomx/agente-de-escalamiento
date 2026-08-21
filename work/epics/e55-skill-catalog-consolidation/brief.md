# E55: Skill Catalog Consolidation (Proposal)

## Objective
Address the high-priority parking lot item from E47: consolidate the `escala-*` / `scaleup-*` skill catalog. There are 39 `scaleup-*` and 69 `escala-*` unique skill names, with duplicates across agent mirrors (`.agents`, `.claude`, `.cursor`, `.github/agents`, `.roo`, `.windsurf`, etc.).

## Status
**Proposal / Epic.** Requires an audit and a decision pass before implementation stories.

## Scope (Draft)
1. Audit all skills and group by function.
2. Apply the Bitter Pill criterion: "Would a model with real memory make this skill unnecessary?"
3. For each group, decide: keep canonical `escala-*`, merge into core Python, or delete.
4. Decide mirror strategy: auto-sync from `escala-skills/`, delete mirrors, or keep manual.

## Success Criteria (Draft)
- Each business function is covered by exactly one canonical skill or core module.
- Agent mirrors are either auto-generated or removed.
- No `scaleup-*` skill remains if an equivalent `escala-*` skill exists.

## Next Step
Run `/rai-epic-predesign-evidence` and `/rai-epic-design` before creating stories.

## Related
- Parking lot item from E47
