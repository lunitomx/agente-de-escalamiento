# Epic Scope: E7 — Agent Intelligence

## Objective

Darle al agente ScaleUp memoria persistente, continuidad de sesión, gestión de tareas y alineación estratégica — que se comporte como un coach real que recuerda, da seguimiento y personaliza.

## In Scope

- Session lifecycle: cargar contexto al abrir, guardar estado al cerrar
- Persistent memory: perfil de empresa, scores de diagnóstico, worksheets completados, historial de sesiones
- SMART annual goal como filtro estratégico para todas las recomendaciones
- Task board en markdown (TODO/DOING/DONE) vinculado a decisiones
- Accountability loop automático al iniciar sesión
- Company knowledge graph con hechos específicos de la empresa

## Out of Scope

- Coaching logic o facilitación de worksheets (E8)
- Exportación o dashboards (E9)
- Modificación de la ontología de conocimiento (E6 cerrado)
- Interfaz gráfica — todo es conversacional via Claude Code
- Integración con servicios externos (APIs, bases de datos)

## Planned Stories

| ID | Story | Size | Status | Depends |
|----|-------|------|--------|---------|
| S7.1 | Session lifecycle — context loader + session log | M | pending | — |
| S7.2 | Persistent memory — YAML source of truth + markdown views | M | pending | S7.1 |
| S7.3 | SMART annual goal como filtro estratégico | S | pending | S7.2 |
| S7.4 | Task board — kanban con metadata y links a ontología | M | pending | S7.2 |
| S7.5 | Accountability loop — auto-review al iniciar sesión | M | pending | S7.1, S7.4 |
| S7.6 | Company knowledge graph (hechos de la empresa) | S | pending | S7.2 |

Critical path: S7.1 → S7.2 → S7.4 → S7.5

## Dependencies

- E6 Knowledge Ontology (DONE) — memory system referencia nodos de ontología para vincular tareas a metodología

## Done Criteria

- [ ] Agente recuerda contexto de empresa entre sesiones sin re-preguntar
- [ ] Session start carga contexto completo en < 5 segundos
- [ ] Task board persiste entre sesiones, trackea decisión por tarea
- [ ] Meta anual visible en toda interacción de coaching
- [ ] Accountability loop se activa automáticamente al iniciar sesión
- [ ] Knowledge graph de empresa almacena hechos estructurados
