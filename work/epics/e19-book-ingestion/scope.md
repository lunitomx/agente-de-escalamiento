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
