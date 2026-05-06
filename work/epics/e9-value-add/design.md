# Epic Design: E9 — Value-Add Features

## Architecture

Mismo patrón E8: **core Python (`coaching/{skill}/`) + adapter SKILL.md delgado**.

| Componente | Core Python | Adapter SKILL.md |
|------------|-------------|------------------|
| Export | `coaching/export/` | `.claude/skills/scaleup-export/` |
| Pulse | `coaching/pulse/` | `.claude/skills/scaleup-pulse/` |
| Dashboard | `coaching/dashboard/` | `.claude/skills/scaleup-dashboard/` |
| Summary | `coaching/summary/` | Integrado en `scaleup-close` |

### Data Sources

Cada core module lee de:
- `.scaleup/agent/memory/company-profile.yaml` — scores, focus, coaching level
- `.scaleup/my-company/tasks.md` — task board
- `.scaleup/my-company/sessions/` — historial de sesiones
- `.scaleup/my-company/worksheets/` — worksheets completados
- `.scaleup/my-company/annual-goal.md` — SMART goal

## Story Decomposition

### S9.1 — Action Plan Export (`/scaleup-export`)

Genera documento markdown listo para compartir con:
- Diagnóstico actual (scores)
- Meta anual (SMART goal)
- Prioridades activas
- Tareas abiertas
- Próximos pasos sugeridos por el router

**Core:** `coaching/export/` — agrega datos, genera markdown formateado  
**Adapter:** `.claude/skills/scaleup-export/SKILL.md`  
**Quality gate:** Valida que todos los campos requeridos existan

### S9.2 — Quarterly Pulse (`/scaleup-pulse`)

Re-diagnóstico rápido de 5 preguntas (1 por decisión + 1 overall):
1. People: "¿Tu equipo está más alineado que hace 3 meses?"
2. Strategy: "¿Tu estrategia es más clara ahora?"
3. Execution: "¿Ejecutas con más disciplina?"
4. Cash: "¿Tu salud de cash mejoró?"
5. Overall: "¿Estás más cerca de tu meta anual?"

Cada respuesta: -1 (peor), 0 (igual), +1 (mejor). Compara vs pulse anterior. Detecta tendencias (improving/stalling/regressing).

**Core:** `coaching/pulse/`  
**Adapter:** `.claude/skills/scaleup-pulse/SKILL.md`  
**Quality gate:** Valida formato de respuestas, detecta tendencias

### S9.3 — Progress Dashboard (`/scaleup-dashboard`)

Extiende S8.4 con histórico:
- Scores actuales (de S8.4)
- Trajectory: línea de tiempo de scores (extraídos de session logs)
- Wins: decisiones que mejoraron desde el último diagnóstico
- Atención: decisiones que empeoraron o se estancaron

**Core:** `coaching/dashboard/` (extiende `coaching/progress/`)  
**Adapter:** `.claude/skills/scaleup-dashboard/SKILL.md`

### S9.4 — Coaching Session Summary

Auto-generado en `/scaleup-close`:
- Duración de la sesión
- Decisiones trabajadas
- Worksheets completados
- Tareas creadas/completadas
- Score changes (si aplica)
- Próximos pasos

Se appendea a `.scaleup/my-company/sessions/YYYY-MM-DD.md`.

**Core:** `coaching/summary/`  
**Integración:** Se invoca desde `scaleup-close` orchestrator

## Risks

| Risk | Mitigation |
|------|-----------|
| Dashboard duplica S8.4 Progress Tracker | S9.3 extiende, no reemplaza. S8.4 es "estado actual", S9.3 es "histórico" |
| Pulse puede sentirse repetitivo | Solo 5 preguntas, < 5 minutos. Enfatizar comparación con anterior |
| Summary requiere datos de sesión que el LLM debe capturar | El core recibe los datos como contexto; no deduce nada |
