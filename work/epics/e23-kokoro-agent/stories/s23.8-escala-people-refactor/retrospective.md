---
story_id: s23.8
title: "escala-people refactor — Agent-based People Skill"
status: complete
merged_at: 2026-05-30
---

## Resumen

Se creó `escala-agent/skills/escala-people/SKILL.md` — skill agent-based que consolida:

- FACChart completo (identificar funciones, asignar accountables, KPIs)
- Core Values Discovery (5 preguntas Lencioni/Collins, validación)
- Topgrading (Job Scorecard, entrevista cronológica, TORC)
- Generación de organigrama HTML bajo demanda
- Guardado en `memoria/analisis/people/`

## Cambios clave

| Antes | Ahora |
|-------|-------|
| 4 skills separados (people, fac, values, topgrading) | Un skill que cubre todo People |
| Leía archivos del servidor | El LLM guía la conversación |
| Guardaba en `work/people/` | Guarda en `~/.escala/memoria/analisis/people/` |
