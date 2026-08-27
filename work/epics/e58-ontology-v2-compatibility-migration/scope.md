---
epic_id: E58
title: Ontología v2 trazable y migración de compatibilidad
status: active
depends_on: [E57, E6]
---

# Scope E58

## Objetivo

Evolucionar la ontología existente de E6 a una autoridad canónica con procedencia, evidencia, revisión, aliases y relaciones tipadas, sin romper los consumidores actuales ni crear una segunda verdad.

## Dentro

- JSON Schema para nodo, relación, evidencia, candidate, review decision y alias.
- Clases: decisión, framework, principio, herramienta, artefacto, procedimiento, paso, regla, warning, métrica, rol, rutina, horizonte, ejemplo, referencia externa y dimensión personal.
- Seis orígenes: `source-explicit`, `source-synthesis`, `historical-example`, `external-reference`, `company-local`, `model-hypothesis`.
- Migración de los IDs, aliases y relaciones existentes de `conocimiento/`.
- Cola de revisión para ambigüedades o candidatos rechazados.
- Generadores de vistas YAML compatibles y SQLite de consulta derivado.
- Validadores de unicidad, relación, evidencia, aliases y autoridad única.

## Fuera

- Poblar exhaustivamente todos los dominios; eso es E59-E63.
- Reemplazar E55 como autoridad de hechos de empresa.
- Hacer de SQLite una fuente de verdad o sincronizarlo.
- Cambiar la metodología de cara al empresario.

## Historias y secuencia

| Orden | Historia | Entrega verificable |
|---:|---|---|
| 1 | S58.1 Schema y vocabulario | Done — contrato v2 privado, schema y vocabulario deterministas. |
| 2 | S58.2 Origen/evidencia/revisión | Done — cola tipada, evidencia de aprobación y recibo seguro. |
| 3 | S58.3 Migración E6 | Done — mapa 82/78/4 con hashes y disposición explícita, sin promoción falsa. |
| 4 | S58.4 Vistas derivadas | YAML/SQLite regenerables desde la autoridad v2. |
| 5 | S58.5 Integridad | Suite que bloquea huérfanos, duplicados y evidencia inválida. |

## Criterios de terminación

- Cero referencias, IDs, aliases o relaciones rotas en la migración.
- Toda vista indica versión y procedencia de generación.
- Los consumidores de retrieval existentes pasan sin regresiones.
- Candidate y review queue distinguen trabajo no aprobado de conocimiento canónico.
- Ninguna relación normativa se puede promover sin evidencia válida.

## Dependencias y handoff

Consume el manifiesto de E57 y migra E6. Entrega el contrato para las pasadas paralelas E59-E63 y, después, para E64.

## Riesgos y no-gos

- No duplicar `conocimiento/` en una raíz paralela.
- No reducir evidencia a una cita libre sin locator verificable.
- No forzar términos distintos a un alias si su diferencia permanece ambigua.
