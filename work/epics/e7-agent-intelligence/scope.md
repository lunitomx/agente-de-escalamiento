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

## Implementation Plan

### Sequencing Strategy: Walking Skeleton

S7.1 establece la arquitectura de orquestación (pipeline de sesión). Todo lo demás se monta sobre ese esqueleto. Risk-first: el patrón de orquestación con subagentes es nuevo — probarlo temprano.

### Sequence

| # | Story | Rationale | Enables |
|---|-------|-----------|---------|
| 1 | **S7.1** Session lifecycle | Walking skeleton — establece pipeline de orquestación, session log, context loader. Prueba el patrón de subagentes. | S7.2, S7.5 |
| 2 | **S7.2** Persistent memory | YAML source of truth — sin esto no hay datos que cargar ni persistir. Unifica el storage dual. | S7.3, S7.4, S7.6 |
| 3 | **S7.4** Task board | Prerequisito del accountability loop. CRUD de tareas con metadata de ontología. | S7.5 |
| 4 | **S7.3** SMART annual goal | Parallelizable con S7.4 pero depende de S7.2. Filtro estratégico para recomendaciones. | — |
| 5 | **S7.5** Accountability loop | Se integra dentro del session start (review phase). Necesita tasks + sessions. | — |
| 6 | **S7.6** Company knowledge graph | Valor incremental — extiende el perfil con hechos estructurados. Puede empezar después de S7.2. | — |

### Parallel Opportunities

```
         S7.1
          ↓
         S7.2
        ↙    ↘
     S7.4    S7.3 ← parallel
     S7.4    S7.6 ← parallel (after S7.2)
        ↘
         S7.5
```

S7.3 y S7.6 son independientes entre sí y de S7.4. Pueden ejecutarse en paralelo si hay tiempo.

### Milestones

**M1: Walking Skeleton (S7.1)**
- `/scaleup-start` orquesta 3 sub-skills como subagentes
- `/scaleup-close` escribe session log con frontmatter YAML
- Al menos 1 quality gate en código (Python)
- Criterio: ejecutar start → close y verificar que session log se creó correctamente

**M2: Core MVP (S7.1 + S7.2 + S7.4)**
- Agente carga contexto de empresa al iniciar sesión
- Tasks se crean, mueven y listan con links a ontología
- Markdown views se generan desde YAML
- Criterio: sesión completa start-to-close con perfil, tasks y log persistidos

**M3: Feature Complete (all stories)**
- Accountability loop funcional en session start
- SMART goal filtra recomendaciones
- Company knowledge graph almacena hechos
- Criterio: done criteria del epic todos verificados

### Progress Tracking

| Story | Size | Status | Started | Completed | Notes |
|-------|------|--------|---------|-----------|-------|
| S7.1 | M | pending | — | — | — |
| S7.2 | M | pending | — | — | — |
| S7.4 | M | pending | — | — | — |
| S7.3 | S | pending | — | — | — |
| S7.5 | M | pending | — | — | — |
| S7.6 | S | pending | — | — | — |

### Sequencing Risks

| Risk | Mitigation |
|------|-----------|
| Patrón de orquestación con subagentes es nuevo — puede no funcionar como esperamos | S7.1 es walking skeleton, lo probamos primero. Si falla, pivotamos antes de construir encima |
| Subagent overhead para operaciones simples (leer un YAML) | Regla: si un paso es < 20 líneas de lógica, inline en el orquestador |
| Quality gates en Python requieren que el usuario tenga Python instalado | Mantener gates simples — solo PyYAML como dependencia (ya requerida por E6) |

## Done Criteria

- [ ] Agente recuerda contexto de empresa entre sesiones sin re-preguntar
- [ ] Session start carga contexto completo en < 5 segundos
- [ ] Task board persiste entre sesiones, trackea decisión por tarea
- [ ] Meta anual visible en toda interacción de coaching
- [ ] Accountability loop se activa automáticamente al iniciar sesión
- [ ] Knowledge graph de empresa almacena hechos estructurados
