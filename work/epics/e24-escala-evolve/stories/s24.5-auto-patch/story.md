---
story_id: s24.5
title: "Auto-patch con aprobación — El agente se modifica a sí mismo"
epic: e24
type: code
status: started
created: 2026-05-30
---

## Acceptance Criteria

- [ ] `escala-evolve` skill updated with auto-patch flow (generate diff → present → wait → apply → rollback)
- [ ] Process: propuesta → aprueba? → aplica → registra en changelog
- [ ] Rollback: guarda backup del SKILL.md antes de modificar
- [ ] Siempre pide confirmación explícita antes de aplicar
