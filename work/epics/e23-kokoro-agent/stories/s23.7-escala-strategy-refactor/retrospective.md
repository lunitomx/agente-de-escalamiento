---
story_id: s23.7
title: "escala-strategy refactor — Agent-based Strategy Skill"
status: complete
merged_at: 2026-05-30
---

## Resumen

Se creó `escala-agent/skills/escala-strategy/SKILL.md` — skill agent-based que consolida:

- OPSP completo (Core Values, Purpose, BHAG, Sandbox, Brand Promise, Profit per X, Metas Anuales, Plan Trimestral)
- 7 Estratos de Estrategia
- SWOT/SWT Analysis
- Generación de HTML visual bajo demanda
- Guardado en `memoria/analisis/strategy/`

## Cambios clave

| Antes | Ahora |
|-------|-------|
| 4 skills separados (strategy, opsp, 7strata, swot) | Un skill que cubre todo Strategy |
| Leía archivos del servidor | El LLM guía la conversación |
| Guardaba en `work/strategy/` | Guarda en `~/.escala/memoria/analisis/strategy/` |
| Sin generación de HTML | HTML visual bajo demanda |
