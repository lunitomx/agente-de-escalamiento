# Epic Brief: E6 — Knowledge Ontology

## Hypothesis

Si convertimos el contenido extraído de Scaling Up (68 metodologías, 34 worksheets, 23 coaching prompts) en una ontología de dominio estructurada con retrieval determinístico, entonces el agente podrá dar respuestas precisas y metodológicamente correctas sin depender de RAG ni embeddings.

## Success Metrics

| Metric | Target |
|--------|--------|
| Metodologías representadas | 68/68 como nodos de ontología |
| Worksheets registrados | 34/34 con metadata (decisión, prerequisitos, outputs) |
| Retrieval accuracy | Dado (decisión, etapa), retorna nodos relevantes |
| Dependencias externas | Zero — puro file-based |
| Fuente de datos | LlamaParse content (no OCR viejo) |

## Appetite

7 stories, tamaño total L. Contenido denso — requiere leer y estructurar todo el material parseado de LlamaParse. Sin código complejo — YAML/JSON para el grafo, markdown para documentación.

## Rabbit Holes

- No construir un motor de queries complejo — traversal simple sobre archivos YAML
- No embeddings ni vectores — retrieval determinístico simbólico
- No reescribir el contenido — estructurar y apuntar al contenido existente
- No implementar coaching logic — eso es E8
- El contenido en `.scaleup/knowledge/` actual (OCR malo) se descarta y reconstruye desde LlamaParse
