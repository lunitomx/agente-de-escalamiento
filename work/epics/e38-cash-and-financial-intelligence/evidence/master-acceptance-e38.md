# E38 Master Acceptance Receipt

- status: pass
- fixture: synthetic-nopal-foods
- requirements_proved: REQ-E38-001 … REQ-E38-007

## Proof

- REQ-E38-001: Perfiló workbook flexible por estructura, periodo, moneda, unidad y formulas.
- REQ-E38-002: Mapping ambiguo genero pregunta ordinal y se resolvio solo tras respuesta.
- REQ-E38-003: P&L, balance y cash-flow view se reconstruyeron con derivaciones explicitas.
- REQ-E38-004: Figures conservaron source_id, workbook relativo, hoja, celda y transformation.
- REQ-E38-005: CCC, Power-of-One y escenario price-plus-one compartieron inputs y assumptions.
- REQ-E38-006: Caso stale quedo blocked y sin recommendations.
- REQ-E38-007: Reporte HTML/Markdown/JSON local fue determinista y uso paths relativos.

## Negative matrix

- ambiguous mappings remain unresolved until owner answer
- formulas without cached values are not facts
- stale/mixed-confidence/mixed-currency inputs block recommendations
- source workbook is not mutated

## Authority

- runtime/data authority: installer_machine
- team exchange: ordinary_filesystem_documents_only
- authoritative SQLite sync: forbidden
