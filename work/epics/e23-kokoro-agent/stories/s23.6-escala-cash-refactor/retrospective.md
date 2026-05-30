---
story_id: s23.6
title: "escala-cash refactor — Agent-based Cash Skill"
status: complete
merged_at: 2026-05-30
---

## Resumen

Se creó `escala-agent/skills/escala-cash/SKILL.md` — skill agent-based que reemplaza la dependencia del servidor `escala_server/cash/`. El LLM usa su propia inteligencia para:

- Entrevistar al usuario en lenguaje humano
- Calcular CCC (DSO/DIO/DPO) con base 365 días
- Calcular Power of One con las 7 palancas
- Guardar análisis en `memoria/analisis/cash/` con frontmatter YAML
- Generar dashboards HTML con Chart.js bajo demanda

## Cambios clave respecto al anterior

| Antes (server-dependent) | Ahora (agent-based) |
|--------------------------|---------------------|
| Llamaba `POST /api/cash/power-of-one` | El LLM calcula usando fórmulas exactas |
| Guardaba en `work/cash/` | Guarda en `~/.escala/memoria/analisis/cash/` |
| Dashboard HTML fijo en servidor | HTML generado por el agente bajo demanda |
| 3 skills separados (cash, ccc, power1) | Un solo skill que cubre todo Cash |
| Sliders en UI | Botones +1/-1 explicados en documentación |

## Patrones extraídos

- PAT-2026-05-30-1: Skills agent-based deben tener fórmulas exactas embebidas y referencias a benchmarks
- PAT-2026-05-30-2: Cada skill debe especificar "en lenguaje humano" qué términos usar
