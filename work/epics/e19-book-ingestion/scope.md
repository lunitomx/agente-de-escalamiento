# Epic Scope: E19 — Book Ingestion & Knowledge Graph

**Status:** Draft
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
- [ ] Parser extrae capítulos, conceptos, herramientas, métricas y hábitos
- [ ] Mínimo 30 entidades creadas en el grafo
- [ ] Mínimo 50 relaciones entre entidades
- [ ] API de consulta funcional: GET /api/knowledge/search?q=concepto
- [ ] Tests: cada capítulo del libro verificado contra entidades
- [ ] Documentación del esquema del grafo

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
| S19.3 — Relationship Builder | M | Pending | — | — | Conecta entidades con relaciones semánticas |
| S19.4 — Knowledge API | M | Pending | — | — | Endpoints de consulta al grafo |
| S19.5 — Integrity Tests | S | Pending | — | — | Cobertura contra el libro fuente |
