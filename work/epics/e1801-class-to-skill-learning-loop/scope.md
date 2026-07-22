# Epic Scope: E1801 — Class-to-Skill Learning Loop

**Status:** Complete

## Objective

Transformar clases, transcripts y prompts docentes en un flujo que detecta patrones, decisiones y mejoras concretas para los skills del agente Escala.

## In Scope

- Ingesta de transcript y materiales de clase
- Extracción de patrones repetibles, decisiones y reglas
- Detección de oportunidades de mejora por skill
- Mapeo clase → skill → cambio sugerido
- Formato de salida listo para revisión humana

## Out of Scope

- Escritura automática de skills sin revisión
- Entrenamiento de modelos
- Integraciones externas complejas
- UI nueva para edición visual de skills

## Planned Stories

| ID | Story | Size | Depends |
|----|-------|------|---------|
| S18.1 | Class intake + source bundling | M | — |
| S18.2 | Pattern extraction from transcript and prompts | M | S18.1 |
| S18.3 | Skill delta suggestions | L | S18.2 |
| S18.4 | Reviewable learning report per class | S | S18.3 |

## Dependencies

- Skill source files y materiales de clase
- Flujo existente de transcripts y prompts
- Criterios de calidad del agente Escala

## Done Criteria

- [x] Cada clase nueva puede producir un reporte reusable
- [x] El reporte muestra patrones, decisiones y oportunidades de mejora
- [x] Cada sugerencia apunta a un skill específico
- [x] La trazabilidad hacia la clase fuente queda clara

## Implementation Plan

> Added by `/rai-epic-plan` — 2026-06-02

### Story Sequence

| Order | Story | Size | Dependencies | Milestone | Rationale |
|:-----:|-------|:----:|--------------|-----------|-----------|
| 1 | S18.1 | M | None | M1 | Primero se necesita un contenedor confiable que amarre transcript, prompts y metadatos antes de intentar interpretar nada. |
| 2 | S18.2 | M | S18.1 | M1 | Con el bundle ya estable, se puede extraer patrones y decisiones sin perder trazabilidad. |
| 3 | S18.3 | L | S18.2 | M2 | Las sugerencias por skill dependen de tener señales ya clasificadas; aquí nace el valor estratégico. |
| 4 | S18.4 | S | S18.3 | M2 | El reporte final solo tiene sentido cuando el mapeo y la evidencia ya existen. |

### Milestones

| Milestone | Stories | Target | Success Criteria |
|-----------|---------|--------|------------------|
| **M1: Walking Skeleton** | S18.1, S18.2 | After first implementation slice | Existe un bundle de clase y ya produce patrones y decisiones con trazabilidad mínima. |
| **M2: Core MVP** | S18.3, S18.4 | After second implementation slice | El sistema ya propone deltas por skill y los entrega en un reporte legible y revisable. |
| **M3: Feature Complete** | — | Not planned in this first pass | Reservado para ampliaciones futuras, como automatización parcial o scoring más fino. |
| **M4: Epic Complete** | — | When done criteria are met | El learning loop funciona de extremo a extremo y el reporte sirve como insumo de mejora real. |

### Parallel Work Streams

No hay paralelización significativa en la primera versión porque el flujo es deliberadamente lineal: primero bundle, luego extracción, luego mapeo, luego reporte. La única posibilidad de trabajo paralelo sería preparar plantillas de reporte mientras se afina la extracción, pero no se recomienda como dependencia formal.

### Progress Tracking

| Story | Size | Status | Actual | Velocity | Notes |
|-------|:----:|:------:|:------:|:--------:|-------|
| S18.1 | Class intake + source bundling | M | ✔ Done | — | — | Merged to main |
| S18.2 | M | Pending | — | — | Pattern extraction and drift detection |
| S18.3 | L | Pending | — | — | Skill-specific recommendations |
| S18.4 | S | Pending | — | — | Reviewable class report |

### Sequencing Risks

| Risk | L/I | Mitigation |
|------|:---:|------------|
| Transcript incompleto o ruidoso | H/M | Mantener evidencia enlazada y tratar el output como sugerencia revisable, no como verdad absoluta. |
| Mezclar intención docente con intención de producto | M/H | Separar explícitamente hechos, interpretación y recomendación en el reporte. |
| Crear salida útil pero demasiado manual | M/M | Diseñar desde el inicio una estructura que luego pueda automatizarse sin rehacer el modelo de datos. |

## Next Step

Una vez aceptado el plan, el siguiente paso natural es `/rai-story-design` para S18.1.
