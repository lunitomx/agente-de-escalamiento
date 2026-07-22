---
epic_id: "E38"
title: "Cash and Financial Intelligence"
status: "in_progress"
created: "2026-07-22"
mission: "escala-local-v2-plan-maestro-2607202112"
---

# Epic Scope: E38 — Cash and Financial Intelligence

## Objective

Construir la inteligencia financiera local de ESCALA sobre los contratos de
E37: el empresario entrega sus workbooks tal como los usa, el sistema perfila
hojas y estructuras, pregunta lo que no puede determinar, reconstruye vistas
financieras cuando hay soporte suficiente y explica cada resultado con
procedencia, supuestos, confianza y límites.

## Architectural Invariants

1. Runtime, SQLite, ledger de fuentes y estado canónico permanecen en la
   máquina del instalador.
2. La carpeta ordinaria local/Drive/OneDrive solo intercambia documentos; no
   contiene la autoridad financiera ni una SQLite sincronizada.
3. No se escribe sobre el workbook original y no se promociona un perfil a
   hecho financiero sin confirmación explícita.
4. Toda cifra derivada conserva `source_id`, workbook, hoja, celda/rango,
   transformación, periodo, moneda, unidad y nivel de confianza cuando estén
   disponibles.
5. Faltantes, inconsistencias, datos vencidos y mappings ambiguos bloquean una
   recomendación sobreconfiada y producen preguntas accionables.
6. Todo reporte visual se genera localmente y puede descargarse como artefacto
   seguro sin llamadas cloud.

## In Scope

- Perfilado financiero de workbooks existentes por hojas, tablas, fórmulas,
  periodos, monedas y unidades.
- Mapeo guiado de columnas/cuentas con preguntas ante ambigüedad material.
- Reconstrucción trazable de P&L, balance y vista de flujo de efectivo cuando
  los datos permiten derivarlos.
- Procedencia por workbook/hoja/celda o rango y notas de transformación.
- Análisis de cash-conversion-cycle y Power-of-One con supuestos visibles.
- Escenarios comparables, freshness/confidence y bloqueo de recomendaciones
  ante evidencia incompleta o inconsistente.
- Reporte visual local de cash con hallazgos, preguntas, escenarios y descarga.

## Out of Scope

- Revisión diaria/semanal de transcripts y coordinación de equipo (E39).
- Diagnóstico 0–100, cockpit ejecutivo y estrategia (E40).
- Instalador multiplataforma, actualización y rollback (E41).
- Calificación end-to-end, catálogo funcional y PDF español (E42).
- APIs cloud, OAuth, multi-writer, contabilidad fiscal, auditoría profesional,
  OCR universal o pronósticos sin datos confirmados.

## Planned Stories

| ID | Story | Size | Depends on | Outcome |
|---|---|:---:|---|---|
| S38.1 | Workbook Understanding | M | E37 | El workbook real se perfila sin plantilla y los mappings ambiguos generan preguntas antes de calcular. |
| S38.2 | Financial Statement Reconstruction | L | S38.1 | P&L, balance y flujo se reconstruyen solo con soporte suficiente y cada cifra conserva procedencia y transformación. |
| S38.3 | Cash Decision Coaching | L | S38.2 | CCC, Power-of-One y escenarios comparables muestran inputs, supuestos, freshness, confianza y límites. |
| S38.4 | Visual Cash Evidence | M | S38.2, S38.3 | Un reporte visual local permite ver hallazgos, preguntas, escenarios y descargar evidencia sin runtime hospedado. |

## Progress

- [x] S38.1 Workbook Understanding — merged `25a7d83` / `daec3fb`; gates
  tests, lint, format and types PASS.
- [x] S38.2 Financial Statement Reconstruction — merged `8d185bd` / `40c7730`;
  gates tests, lint, format and types PASS.
- [x] S38.3 Cash Decision Coaching — merged `d43930e` / `74ba85e`; gates tests,
  lint, format and types PASS.
- [ ] S38.4 Visual Cash Evidence

## Master Requirements Owned

| Requirement | Acceptance proof |
|---|---|
| REQ-E38-001 | Workbooks reales perfilados por hojas, tablas, fórmulas, periodos, monedas y unidades sin plantilla fija. |
| REQ-E38-002 | Mappings financieros ambiguos producen preguntas específicas y permanecen sin resolver hasta respuesta del dueño. |
| REQ-E38-003 | P&L, balance y flujo se reconstruyen cuando hay soporte; lo no derivable queda explícito. |
| REQ-E38-004 | Cada cifra conserva workbook, hoja, celda/rango y transformación. |
| REQ-E38-005 | CCC y Power-of-One usan inputs validados, supuestos visibles y comparación de escenarios. |
| REQ-E38-006 | Faltantes, inconsistencias, stale/low-confidence bloquean recomendaciones sobreconfiadas. |
| REQ-E38-007 | Existe un reporte visual local con hallazgos, preguntas, escenarios y evidencia descargable. |

## Done Criteria

- [ ] Las cuatro stories completan el ciclo RaiSE y se integran en `main` con
      tests, lint, formato y tipos PASS.
- [ ] Los siete requisitos E38 tienen artefacto y receipt exactos en el ledger
      maestro; ninguno se declara `proved` por presencia de código.
- [ ] Una empresa sintética entrega un workbook no adaptado, responde una
      aclaración y obtiene statements trazables o estados explícitos de no
      derivabilidad.
- [ ] Un caso negativo demuestra que un mapping ambiguo, stale, faltante o
      inconsistente detiene la recomendación y no muta el workbook original.
- [ ] CCC, Power-of-One y escenarios muestran supuestos, confidence,
      freshness, procedencia y diferencias comparables.
- [ ] El reporte visual se genera localmente, es determinista/redacted y no
      usa APIs cloud, OAuth, SQLite sincronizada ni rutas absolutas.
- [ ] E39-E40 pueden consumir perfiles/derivaciones sin duplicar el contrato
      de autoridad, procedencia o preguntas.

## Acceptance Evidence

- Fixtures de workbooks CSV/XLSX con hojas, periodos, monedas, unidades,
  fórmulas, faltantes y mappings deliberadamente ambiguos.
- Receipts JSON/Markdown deterministas por perfil, derivación, escenario y
  reporte; nunca incluyen contenido sensible ni rutas de máquina.
- Pruebas de no mutación del workbook/original y de no escritura prematura en
  estado canónico.
- Qualification local con empresa sintética y matriz negativa de confianza,
  freshness y consistencia.
- Revisión de compatibilidad de rutas macOS/Windows; la ejecución nativa de
  Windows se comprobará en E41/E42 cuando exista el instalador.
- Ledger maestro actualizado únicamente después de gates específicos
  `gate-req-e38-001`…`gate-req-e38-007`.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Workbooks tienen fórmulas/formatos fuera del parser local | High | Capability report, `provider_unavailable` y límites explícitos; nunca inferir silenciosamente. |
| Se confunde una cuenta con otra | High | Mapping ordinal, preguntas, confirmación y estado unresolved. |
| Statements parecen exactos aunque falten datos | High | Provenance por cifra, confidence/freshness y bloqueo fail-closed. |
| Escenarios de cash dan falsa precisión | High | Inputs/supuestos visibles, sensibilidad acotada y no recommendation cuando la base es insuficiente. |
| Visualización filtra datos del empresario | High | Artefactos redacted, rutas relativas, local-only y pruebas de no filtración. |

## Implementation Plan

1. S38.1 comienza por el seam de perfilado y preguntas, reutilizando la
   identidad/procedencia de E37 sin duplicar ingestión.
2. S38.2 construye el walking skeleton de derivación con un pequeño modelo de
   cuentas y trazabilidad; no intenta cubrir contabilidad universal.
3. S38.3 añade cálculos CCC/Power-of-One y escenarios detrás de validación y
   confidence/freshness.
4. S38.4 integra la salida en un reporte visual local y ejecuta la
   qualification sintética; los siete receipts maestros se producen al cierre
   de la épica.

No se ejecutará trabajo financiero en paralelo hasta que S38.1 tenga un
contrato de mapping y preguntas que impida que S38.2 invente correspondencias.
