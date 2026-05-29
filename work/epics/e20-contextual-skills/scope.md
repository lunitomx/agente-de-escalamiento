# Epic Scope: E20 — Contextual Skills (Grafo → Dashboards)

**Status:** Draft
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
