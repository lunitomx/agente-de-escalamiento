---
epic_id: E58
title: Ontología v2 trazable y migración de compatibilidad
status: active
depends_on: [E57, E6]
---

# E58 — Ontología v2 trazable y migración de compatibilidad

## Resultado

`conocimiento/` pasa de YAML curado sin procedencia a una única ontología versionada, validable y compatible con los consumidores actuales.

## Historias

| ID | Historia | Termina cuando |
|---|---|---|
| S58.1 | Schema y vocabulario | JSON Schema define nodos, relaciones, evidencia, aliases, procedencia y estados de revisión. |
| S58.2 | Tipos de origen y evidencia | Soporta `source-explicit`, `source-synthesis`, `historical-example`, `external-reference`, `company-local` y `model-hypothesis`. |
| S58.3 | Migración de activos E6 | Los 78 IDs/aliases existentes migran sin romper retrieval ni consumidores. |
| S58.4 | Vistas derivadas | YAML de compatibilidad y SQLite de consulta se generan desde la ontología, sin convertirse en segunda autoridad. |
| S58.5 | Integridad | IDs únicos, relaciones válidas, evidencia obligatoria cuando aplique y cola explícita de revisión. |

## Cierre

- Cero nodos, aliases o edges rotos.
- Una sola autoridad canónica; todas las vistas son generadas.
- Suite actual de conocimiento y consumidores pasa completa.
