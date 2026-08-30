---
epic_id: E60
title: Corpus People verificado
status: in_progress
depends_on: [E58]
---

# Scope E60

## Objetivo

Extraer y revisar el dominio People con suficiente fidelidad para que futuras intervenciones asignen accountability, desarrollen al líder y creen artefactos sin inventar hechos personales ni convertir referencias parciales en metodologías completas.

## Dentro

- Inventario de conceptos, herramientas, acciones, warnings, métricas, preguntas y formularios People.
- Extracción/revisión separada de OPPP, FACe, PACe y demás unidades explícitas.
- Validación visual de columnas, campos y relaciones espaciales de growth tools.
- Etiquetas de sensibilidad y límites de estado para datos personales.
- Etiquetado de contenido externo con alcance incompleto.

## Fuera

- Crear scorecards o decisiones de personal autónomas.
- Implementar Topgrading, Lean u otros sistemas más allá de lo que una fuente autorizada respalde.
- Construir los procedimientos de FACe/PACe; eso espera E69.

## Historias y secuencia

| Orden | Historia | Entrega verificable |
|---:|---|---|
| 1 | S60.1 Inventario | Unidades People clasificadas contra el manifiesto. |
| 2 | S60.2 Candidatos/revisión | Pares extractor-auditor con cola de revisión. |
| 3 | S60.3 Formularios | Recibo de comparación visual y semántica. |
| 4 | S60.4 Externos/sensibilidad | Reglas de estado y límites de alcance verificables. |

## Criterios de terminación

- 100% del dominio People clasificado o excluido justificadamente.
- Toda regla, cifra y campo obligatorio tiene evidencia.
- Ningún ejemplo se generaliza y ningún método externo se vende como completo.
- No hay críticos abiertos en el reporte de fidelidad.

## Estado de evidencia

- S60.1, S60.2 y S60.4 tienen evidencia privada trazable; candidatos sin promoción canónica hasta revisión independiente.
- La inspección visual privada `s60.3-visual-layout-review-2026-08-30.json` confirmó la topología de OPPP, FACe y PACe contra una copia pública de la edición v20/03. El activo se eliminó; sólo queda el recibo privado validable conforme a `visual-layout-review-protocol.md`.

## Handoff y riesgos

Entrega nodos a E64 y contratos de información sensible a E44/E65/E69. No reemplaza el consentimiento de E52 ni el onboarding de E55.
