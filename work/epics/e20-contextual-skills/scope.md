# Epic Scope: E20 — Contextual Skills (Grafo → Dashboards)

**Status:** Complete
**Dependencies:** E19 (grafo poblado)
**Tamaño:** L

## In Scope
- API wrapper en server.py: GET /api/knowledge/context?tool=power-of-one
- Cada dashboard (22 total) puede mostrar contexto relevante del libro
- Skills de coaching pueden consultar "dame principios de Harnish sobre X"
- Panel lateral en dashboards con "Contexto de Scaling Up"
- Los 4 módulos (Cash, Strategy, People, Execution) tienen acceso al contexto de su sección del libro

## Out of Scope
- Ingestar nuevos libros o fuentes (E19)
- Crear agente conversacional (E21)
- Modificar el parser del libro

## Dependencias
- E19 (grafo poblado con entidades y relaciones)
- E18 (server, API routing, dashboards)
- HTML/JS de dashboards existentes

## Done Criteria
- [ ] GET /api/knowledge/context?tool=X devuelve entidades, relaciones y hechos relevantes
- [ ] Panel de contexto visible en los 22 dashboards
- [ ] Skills pueden consultar contexto por categoría (cash, strategy, people, execution)
- [ ] Tests de integración: cada dashboard recibe contexto correcto

## Implementation Plan

> Added by rai-epic-plan — 2026-05-29

### Story Sequence

| Order | Story | Size | Dependencies | Milestone | Rationale |
|:-----:|-------|:----:|--------------|-----------|-----------|
| 1 | S20.1 — Knowledge Context API | M | Ninguna | M1 | Base de todo — endpoint que conecta dashboards con el grafo de E19 |
| 2 | S20.2 — Dashboard Context Panel | L | S20.1 | M1-M2 | Panel lateral en los 22 dashboards, filtrando por módulo |
| 3 | S20.3 — Coaching Skill Helper | S | S20.1 | M2 | Función que skills de coaching usan para obtener contexto |
| 4 | S20.4 — Integration Tests | S | S20.1-S20.3 | M2 | Validación contra done criteria |

### Milestones

| Milestone | Stories | Success Criteria |
|-----------|---------|------------------|
| **M1: Walking Skeleton** | S20.1, S20.2 (1-2 dashboards) | Endpoint funcional, un dashboard muestra contexto del libro |
| **M2: Feature Complete** | S20.2 (resto), S20.3, S20.4 | Los 22 dashboards con panel, skills consultan, tests pasan |

### Progress Tracking

| Story | Size | Status | Actual | Velocity | Notes |
|-------|:----:|:------:|:------:|:--------:|-------|
| S20.1 — Knowledge Context API | M | Done | — | — | Test coverage + param validation added |
| S20.2 — Dashboard Context Panel | L | Done | — | — | Panel + JS + 23 dashboards with includes |
| S20.3 — Coaching Skill Helper | S | Done | — | — | scaling_context.py module created |
| S20.4 — Integration Tests | S | Done | — | — | 6 tests — scaling_context + dashboard includes |

### Sequencing Risks

| Risk | L/I | Mitigation |
|------|:---:|------------|
| Grafo de E19 no poblado o schema distinto al esperado | H/M | Verificar estado real del grafo antes de empezar S20.1 |
| 22 dashboards tienen HTML inconsistente | M/M | Crear componente reutilizable, adaptar por módulo |
| Skills de coaching no existen aún como módulo importable | L/L | Helper como función standalone, no como skill plugin |