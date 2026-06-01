---
story_id: s24.1
title: "escala-evolve — Skill de auto-mejora"
epic: e24
type: code
status: started
created: 2026-05-30
---

## Acceptance Criteria

- [ ] `escala-agent/skills/escala-evolve/SKILL.md` exists
- [ ] Skill can scan `~/.escala/memoria/` and detect patterns (skill usage, missing data, score trends, repeated recommendations)
- [ ] Detects at least 3 pattern types: frequency, gaps, trends
- [ ] Generates improvement proposals with evidence
- [ ] Saves analysis to `memoria/evolucion/` with YAML frontmatter
