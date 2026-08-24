# Epic Scope: E9 — Value-Add Features

**Status:** Complete — follow-up required for summary
**Audited:** 2026-08-24

## Objective

Entregar exportación, pulse diagnóstico, dashboard histórico y resumen de sesión — features que hacen el coaching tangible y compartible con el equipo del empresario.

**Arquitectura:** Mismo patrón cross-platform que E8 — core Python en `coaching/` + adapters SKILL.md delgados.

## In Scope

- `/scaleup-export` — documento markdown compartible con diagnóstico, metas, tareas, próximos pasos
- `/scaleup-pulse` — re-diagnóstico rápido de 5 preguntas + comparación vs anterior + detección de tendencias
- `/scaleup-dashboard` — scores históricos con trayectoria, wins, áreas de atención
- `/scaleup-summary` — resumen auto-generado al cerrar sesión (qué se discutió, qué se creó, qué sigue)

## Out of Scope

- Modificación de la ontología (E6 cerrado)
- Skills de coaching (E8 cerrado)
- Interfaz gráfica
- Integración con servicios externos

## Planned Stories

| ID | Story | Size | Status | Depends |
|----|-------|------|--------|---------|
| S9.1 | Action Plan Export — `/scaleup-export` | M | **done** ✓ | E8 |
| S9.2 | Quarterly Pulse — `/scaleup-pulse` | M | **done** ✓ | S9.1 |
| S9.3 | Progress Dashboard — `/scaleup-dashboard` | M | **done** ✓ | S9.2 |
| S9.4 | Coaching Session Summary — auto-generado al cerrar sesión | S | **done** ✓ | E7, E8 |

## Dependencies

- E8 Coaching Engine (DONE) — dashboard y pulse usan datos de metodología; export necesita task board y diagnosis
- E7 Agent Intelligence (DONE) — session logs, task board, company profile
- Core Python structure en `coaching/` (E8)

## Cross-Platform

Mismo patrón E8: core Python en `coaching/{skill}/` + adapter SKILL.md en `.claude/skills/scaleup-{skill}/`. Todos los módulos invocables standalone vía stdin JSON.

## Done Criteria

- [x] Export produce documento markdown limpio y compartible
- [x] Pulse re-diagnóstico y comparación histórica entregados
- [x] Dashboard muestra progresión histórica de scores
- [x] Resumen automático restaurado en `coaching/summary/`, cubierto por pruebas e incluido en la distribución
- [x] Cada story tuvo core Python + adapter SKILL.md + quality gate al cierre

### Audit Note — 2026-08-24

La retrospectiva de E9 es correcta como registro histórico. El estado actual
cambió después: E13 eliminó la fuente duplicada y dejó el port de summary en su
parking lot. Restaurar summary es deuda técnica, no una reapertura de E9.

### Follow-up Verification — 2026-08-24

El contrato fue portado a la ruta canónica `coaching/summary/`. Conserva engine,
formatter, API `run(context)` y CLI `python -m coaching.summary`; una
re-ejecución ya no duplica la sección. El instalador vuelve a copiar el módulo a
Claude y Hermes, y las pruebas ejercitan el validador real de E9.
