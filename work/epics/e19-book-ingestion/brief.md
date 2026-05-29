# Epic Brief: E19 — Book Ingestion & Knowledge Graph

## Visión
Convertir `scaling_up_llamaparse.md` (el libro completo de Verne Harnish) en un grafo de conocimiento navegable dentro de Escala. Cada concepto, herramienta, métrica y hábito del libro pasa a ser una entidad con relaciones y hechos.

## Por qué separada
Sin el libro en el grafo, no hay base para nada más. Esta épica es el pipeline de datos puro — no toca skills ni crea agentes.

## Lo que NO es
- No modifica dashboards existentes (E20)
- No crea el board member (E21)
- No es "subir el libro y ya" — es estructurarlo

## Deliverables
- Parser del libro que extrae: capítulos, conceptos clave, herramientas, métricas, hábitos, principios
- Grafo de conocimiento con entidades y relaciones
- API de consulta al grafo
- Tests de integridad (cada concepto del libro mapeado a una entidad)
