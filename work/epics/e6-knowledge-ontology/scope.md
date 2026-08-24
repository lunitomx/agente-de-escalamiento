# Epic Scope: E6 — Knowledge Ontology

**Status:** Complete
**Audited:** 2026-08-24

## Objective

Convertir el contenido extraído de Scaling Up (LlamaParse) en una ontología de dominio estructurada — el "cerebro" del agente. Retrieval determinístico, sin vectores, puro archivos.

## In Scope

- Schema de ontología: tipos de nodo, tipos de relación, formato YAML
- Reconstrucción completa de `.scaleup/knowledge/` con contenido LlamaParse
- Población de las 4 decisiones (People, Strategy, Execution, Cash)
- Relaciones cross-decisión y registro de worksheets
- Motor de retrieval determinístico (traversal simbólico)
- Los 15 worksheets reales con metadata y tracking de completitud

## Out of Scope

- Coaching logic o prompts de facilitación (E8)
- Embeddings, vectores, o RAG
- Interfaz de usuario o visualización del grafo
- Modificación de skills existentes
- Session management o memoria persistente (E7)

## Planned Stories

| ID | Story | Size |
|----|-------|------|
| S6.1 | Ontology schema design — tipos de nodo, relaciones, formato YAML | M | done |
| S6.2 | People decision — ontology population desde LlamaParse | M | done ✓ — 17 nodes, ~75m |
| S6.3 | Strategy decision — ontology population desde LlamaParse | M | done ✓ — 18 nodes, ~55m |
| S6.4 | Execution decision — ontology population desde LlamaParse | M | done ✓ — 18 nodes, ~50m |
| S6.5 | Cash decision — ontology population desde LlamaParse | M | done ✓ — 17 nodes, ~45m |
| S6.6 | Cross-decision relationships + worksheet registry | S | done ✓ — 12 edges, 15 worksheets, 79 IDs |
| S6.7 | Deterministic retrieval engine | M | done ✓ — KnowledgeGraph, 301 edges, all queries verified |

## Done Criteria

- [x] Aproximadamente 70 metodologías representadas como nodos con relaciones
- [x] 15 worksheets registrados con metadata (decisión, prerequisitos, outputs)
- [x] Grafo almacenado en `.scaleup/knowledge/` como archivos YAML inspeccionables
- [x] Retrieval engine retorna nodos relevantes para consultas por decisión y etapa
- [x] Zero dependencias externas — puro file-based
- [x] Contenido reconstruido desde LlamaParse

### Audit Note — 2026-08-24

El objetivo original decía 34 worksheets. S6.6 verificó que el inventario real
es 15 y dejó la corrección solicitada en su retrospectiva. El registro actual
`.scaleup/knowledge/registry/worksheets.yaml` confirma 15.
