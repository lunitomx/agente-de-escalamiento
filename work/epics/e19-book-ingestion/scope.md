# Epic Scope: E19 — Book Ingestion & Knowledge Graph

**Status:** Complete
**Dependencies:** E18 (infraestructura base)
**Tamaño:** XL

## In Scope
- Parser del `scaling_up_llamaparse.md` para extraer:
  - Capítulos y secciones
  - Conceptos clave: "Power of One", "Rockefeller Habits", "Cash Conversion Cycle", etc.
  - Herramientas: FACe, PACe, OPPP, One-Page Strategic Plan, etc.
  - Métricas: Revenue per Employee, Net Promoter Score, etc.
  - Hábitos: Daily Huddle, Weekly Meeting, Quarterly Planning
  - Principios: "Keep Things Simple", "No Surprises", etc.
- Ingestar en el grafo entidad-relación (S18.9) como:
  - Entidades (con type, name, properties del libro)
  - Relaciones (contiene, se_evalua_con, pertenece_a, etc.)
  - Hechos (citas textuales, definiciones, pasos de implementación)
- API de consulta: "dame todo lo que Harnish dice sobre cash flow"
- Tests: cada capítulo del libro mapeado a entidades verificables

## Out of Scope
- Modificar skills o dashboards existentes (E20)
- Crear agente board member (E21)
- Ingestar otros libros o fuentes
- NLP o embeddings

## Dependencias
- `scaling_up_llamaparse.md` (ya existe en el repo)
- GraphEngine de S18.9
- MemoryEngine de S18.9

## Done Criteria
- [x] Parser extrae capítulos, conceptos, herramientas, métricas y hábitos
- [x] 42 entidades creadas en el grafo (mínimo: 30)
- [x] 59 relaciones creadas (mínimo: 50)
- [x] API funcional: search, entity lookup y context
- [x] 406 capítulos parseados y 12 integrity tests cubren las 4 decisiones
- [x] Esquema formal documentado en `escala_server/data/SCHEMA.md`

### Audit Note — 2026-08-24

La redacción original pedía verificar cada capítulo contra entidades. La
evidencia de cierre demuestra 406 capítulos parseados y cobertura de integridad
por las cuatro decisiones, no una aserción individual por capítulo. E19
permanece cerrada; la documentación quedó registrada como deuda en ese corte.

### Follow-up Verification — 2026-08-24

`escala_server/data/SCHEMA.md` documenta el artefacto JSON, invariantes,
enumeraciones, proyección SQLite, side effects de memoria, respuestas HTTP y
reglas de cambio. También registra explícitamente qué provenance se pierde al
ingerir para que E21 no dependa de garantías inexistentes.

## Implementation Plan

> Added by rai-epic-plan — 2026-05-29

### Story Sequence

| Order | Story | Size | Dependencies | Milestone | Rationale |
|:-----:|-------|:----:|--------------|-----------|-----------|
| 1 | S19.1 — Book Parser | L | Ninguna | M1 | Primero hay que extraer los datos del libro antes de poder ingestarlos |
| 2 | S19.2 — Entity Ingest | M | S19.1 | M1 | Las entidades se crean desde los datos parseados |
| 3 | S19.3 — Relationship Builder | M | S19.2 | M1 | Las relaciones conectan entidades que ya existen |
| 4 | S19.4 — Knowledge API | M | S19.2, S19.3 | M2 | API sobre entidades y relaciones ya pobladas |
| 5 | S19.5 — Integrity Tests | S | S19.1-S19.4 | M2 | Validación final contra el libro fuente |

### Milestones

| Milestone | Stories | Success Criteria |
|-----------|---------|------------------|
| **M1: Data Pipeline** | S19.1, S19.2, S19.3 | Libro parseado, 30+ entidades, 50+ relaciones en el grafo |
| **M2: Access & Verify** | S19.4, S19.5 | API funcional, tests de cobertura pasando |

### Progress Tracking

| Story | Size | Status | Actual | Velocity | Notes |
|-------|:----:|:------:|:------:|:--------:|-------|
| S19.1 — Book Parser | L | Done | — | — | Extrae chapters, concepts, tools, metrics, habits, principles |
| S19.2 — Entity Ingest | M | Done | — | — | Crea entidades en GraphEngine con propiedades |
| S19.3 — Relationship Builder | M | Done (via S19.2) | — | — | Superseded — relaciones ingeridas en S19.2 |
| S19.4 — Knowledge API | M | Done | — | — | Endpoints de consulta al grafo |
| S19.5 — Integrity Tests | S | Done | — | — | Cobertura contra el libro fuente |
