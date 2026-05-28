# Epic Scope: E14 — Cash Dashboards

## Objective
Crear dashboards visuales para las herramientas de la decisión Cash del sistema Escala. Cada herramienta existente como skill debe tener su representación visual — no solo texto guiado, sino gráficas, semáforos, medidores y tableros interactivos.

## In Scope
- S14.1 — CASh: Cash Acceleration Strategies visual board (4 ciclos × 3 estrategias)
- S14.2 — Power of One: Dashboard visual de 7 variables con impacto en Cash Flow & EBIT
- S14.3 — Recurring Revenue: Jerarquía visual + Value Assessment (None/Weak/Solid/Exceptional)
- S14.4 — Fundability: Radar chart de 8 criterios de mejora

## Out of Scope
- Conexión a datos financieros reales (API bancaria/contabilidad)
- Exportación a PDF/Excel
- Traducción a otros idiomas

## Dependencies
- Sistema Escala base funcional (skills cash existentes)
- Framework de visualización aún por definir

## Status: implement

## Implementation Plan

### Story Sequence

| Pos | Story | Tamaño | Estrategia | Habilita |
|-----|-------|--------|-----------|---------|
| 1 | S14.1 — CASh Board | M | Walking skeleton — resuelve framework, establece patrón grid + semáforo | Patrón base reutilizable |
| 2 | S14.2 — Power of One | L | Risk-first — lógica de cálculo más compleja (7 vars, Current vs Adjusted) | Motor de cálculo |
| 3 | S14.4 — Fundability Radar | M | Risk-first — introduce librería de charts (radar), dependencia nueva | Patrón chart |
| 4 | S14.3 — Recurring Revenue | M | Quick win — jerarquía + badges, aprovecha todo lo establecido | Cierre épic |

**Ruta crítica:** S14.1 → S14.2 → S14.4 → S14.3 (secuencial — todas dependen del framework de S14.1)

**Oportunidades paralelas:** Ninguna en esta épica. El framework de visualización debe quedar probado en S14.1 antes de continuar.

### Milestones

| Milestone | Stories | Criterio de éxito |
|-----------|---------|------------------|
| M1: Walking Skeleton | S14.1 | CASh Board renderizado, framework definido, grid + semáforos funcionando |
| M2: Core MVP | S14.1 + S14.2 | Los 2 dashboards de mayor valor analítico listos y responsivos |
| M3: Feature Complete | S14.1–S14.4 | Suite visual de Cash completa — los 4 dashboards funcionando |
| M4: Epic Complete | Todas + review | Done criteria cumplidos, retrospectiva escrita, listo para close |

### Sequencing Risks

| Riesgo | Impacto | Mitigación |
|--------|---------|-----------|
| Framework de visualización no probado | Alto — bloquea todas las stories | S14.1 resuelve esto primero; si el framework elegido no escala, pivotamos antes de S14.2 |
| Librería de radar chart incompatible con el framework | Medio — solo afecta S14.4 | S14.4 se aborda en pos 3 cuando el framework ya es estable; cambio de librería no afecta otras stories |
| Complejidad de cálculo de Power of One subestimada | Medio — puede inflar S14.2 | Atacar S14.2 cuando el framework está fresco; si se infla, se puede dividir la historia |

### Progress Tracking

| Story | Tamaño | Status | Actual | Velocity | Notes |
|-------|--------|--------|--------|----------|-------|
| S14.1 — CASh Board | M | Pending | — | — | Walking skeleton, define framework |
| S14.2 — Power of One | L | Pending | — | — | Depende de S14.1 |
| S14.4 — Fundability Radar | M | Pending | — | — | Introduce chart library |
| S14.3 — Recurring Revenue | M | Pending | — | — | Cierre, más simple |
