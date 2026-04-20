# Epic Scope: E6 — Knowledge Ontology

## Objective

Convertir el contenido extraído de Scaling Up (LlamaParse) en una ontología de dominio estructurada — el "cerebro" del agente. Retrieval determinístico, sin vectores, puro archivos.

## In Scope

- Schema de ontología: tipos de nodo, tipos de relación, formato YAML
- Reconstrucción completa de `.scaleup/knowledge/` con contenido LlamaParse
- Población de las 4 decisiones (People, Strategy, Execution, Cash)
- Relaciones cross-decisión y registro de worksheets
- Motor de retrieval determinístico (traversal simbólico)
- Los 34 worksheets con metadata y tracking de completitud

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
| S6.4 | Execution decision — ontology population desde LlamaParse | M |
| S6.5 | Cash decision — ontology population desde LlamaParse | M |
| S6.6 | Cross-decision relationships + worksheet registry | S |
| S6.7 | Deterministic retrieval engine | M |

## Done Criteria

- [ ] 68 metodologías representadas como nodos con relaciones
- [ ] 34 worksheets registrados con metadata (decisión, prerequisitos, outputs)
- [ ] Grafo almacenado en `.scaleup/knowledge/` como archivos YAML inspeccionables
- [ ] Retrieval engine retorna nodos relevantes para cualquier (decisión, etapa)
- [ ] Zero dependencias externas — puro file-based
- [ ] Todo el contenido viene de LlamaParse (no del OCR viejo)
