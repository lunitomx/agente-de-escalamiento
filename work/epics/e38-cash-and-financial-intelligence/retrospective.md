# Retrospectiva de épica: E38 — Cash and Financial Intelligence

**Completada:** 2026-07-22
**Duración:** 1 día (2026-07-22 → 2026-07-22)
**Stories:** 4 entregadas

## Resumen

E38 añade la primera capa de inteligencia financiera local de ESCALA sobre los
workbooks reales que ya produce el empresario. El sistema perfila CSV/TSV/XLSX,
pregunta antes de aceptar mappings ambiguos, reconstruye vistas de P&L, balance
y flujo con procedencia, y calcula CCC/Power-of-One y escenarios solo cuando la
calidad de la evidencia lo permite. La salida es un reporte HTML/Markdown/JSON
determinista y local; no hay runtime hospedado, OAuth, telemetría ni SQLite
sincronizada.

## Cierre de alcance, compromiso por compromiso

### Historias

- S38.1 Workbook Understanding: completa en `25a7d83` y retrospectiva
  `daec3fb`.
- S38.2 Financial Statement Reconstruction: completa en `8d185bd` y
  retrospectiva `40c7730`.
- S38.3 Cash Decision Coaching: completa en `d43930e` y retrospectiva
  `74ba85e`.
- S38.4 Visual Cash Evidence: completa en `7b63bd5` y retrospectiva
  `d5fa276`.

### In scope

1. Perfilado por hojas, tablas, fórmulas, periodos, monedas y unidades:
   implementado en `escala_server/financial/profiling.py` y probado por
   `REQ-E38-001`.
2. Mapeo guiado y preguntas ante ambigüedad: implementado con
   `MappingQuestion`/`MappingAnswer` y probado por `REQ-E38-002`.
3. P&L, balance y flujo trazables: implementado en `statements.py` y probado
   por `REQ-E38-003` y `REQ-E38-004`.
4. CCC y Power-of-One con supuestos: implementado en `cash_decision.py` y
   probado por `REQ-E38-005`.
5. Escenarios comparables y bloqueo por evidencia incompleta: probado por
   `REQ-E38-006`.
6. Reporte visual descargable local: implementado en `report.py` y probado por
   `REQ-E38-007`.

No hubo compromisos de eliminación incumplidos. El motor Power-of-One V1 se
conservó deliberadamente porque otras rutas lo consumen; E38 lo encapsula
detrás de inputs validados y no duplica ni elimina ese contrato legado.

### Done when

- Las cuatro stories completan el ciclo RaiSE y están integradas en `main`.
- Los siete requisitos tienen JSON y receipt exactos en el ledger maestro.
- La qualification sintética de Nopal Foods cubre workbook no adaptado,
  aclaración del dueño, statements trazables y estados no derivables.
- La matriz negativa cubre mapping ambiguo, fórmula sin caché, stale, baja
  confianza, moneda mezclada y no mutación del workbook.
- CCC, Power-of-One y escenarios exponen supuestos, confianza, freshness,
  procedencia y deltas.
- El reporte es local, determinista, redacted en sus receipts y usa rutas
  relativas.
- E39 y E40 tienen un contrato financiero consumible sin mover la autoridad.

La comprobación exacta del ledger reporta **7/7 requisitos E38 proved, 0
blockers**. La misión completa permanece abierta por E39–E42.

## Métricas y evidencia

| Métrica | Resultado | Evidencia |
|---|---:|---|
| Stories entregadas | 4/4 | `scope.md` y retrospectivas por story |
| Requisitos E38 probados | 7/7 | `evidence/REQ-E38-00*.json` + receipts |
| Tests nuevos E38 | 13 | `tests/test_e38_financial_intelligence.py` |
| Suite completa | 901 pass, 2 skipped | `uv run rai gate check gate-tests` |
| Gates E38 | 7/7 PASS | `gate-req-e38-001` … `gate-req-e38-007` |
| Lint / formato / tipos | PASS | `gate-lint`, `gate-format`, `gate-types` |
| Qualification | PASS | `scripts/qualify_e38.py`, Nopal Foods |

El receipt maestro y sus hashes se encuentran en
`evidence/master-acceptance-e38.json` y `.md`. La readiness exacta fue
verificada con `scripts/check_master_acceptance.py --epic E38`.

## Qué funcionó bien

- Perfil antes de derivar: ninguna ambigüedad se convierte en hecho sin
  respuesta explícita del dueño.
- Procedencia compuesta por cifra: workbook relativo, hoja, celda/rango,
  periodo, moneda, unidad, transformación, confidence y freshness.
- Fail-closed real: los casos stale, moneda mezclada y fórmula sin valor
  almacenado bloquean o marcan no derivable y no generan recomendaciones.
- El reporte separa datos privados de receipts redacted y es repetible sin red.
- La qualification usa datos sintéticos y deja una ruta clara para pruebas con
  empresarios sin usar información real en el repositorio.

## Qué mejorar / límites conocidos

- El lector XLSX es intencionalmente acotado: no promete macros, cifrado,
  evaluación universal de fórmulas, OCR ni contabilidad fiscal. Esos límites
  deben seguir visibles en la UX.
- La qualification no es aceptación humana de un empresario real; E42 debe
  ejecutar esa prueba, generar el catálogo funcional y producir el PDF español.
- La compatibilidad de rutas fue revisada por contrato, pero no se ejecutó en
  Windows nativo; esa comprobación pertenece a E41/E42 con el instalador.
- No existe adaptador Jira configurado; la reconciliación de hijos se dejó
  registrada como `No results`/sin adapter y el estado local de stories es la
  fuente verificable para este cierre.
- El reporte local es evidencia descargable, no autoridad compartida. Para
  equipos, la carpeta Drive/OneDrive sigue siendo intercambio ordinario de
  documentos, nunca la SQLite o el ledger canónico.

## Patrones descubiertos

| ID | Patrón | Aplicación |
|---|---|---|
| PAT-L-1311 | Perfilar y preguntar antes de derivar | Todo dominio que consume hojas heterogéneas |
| PAT-L-1312 | Provenance compuesta y bloqueo fail-closed | Toda cifra o diagnóstico derivado |
| PAT-L-1313 | Validar calidad y periodicidad antes del motor | Métricas de cash y recomendaciones |
| PAT-L-1314 | Reporte local determinista con receipt redacted | Artefactos visuales descargables |

## Aprendizajes de proceso RaiSE

- Los gates de requisito exacto evitan declarar una épica completa por la mera
  presencia de código.
- El ledger maestro necesitó reconciliar el baseline de E37 junto con E38;
  se corrigió la expectativa de gobernanza a 14 proved / 28 unproved sin
  ocultar que la misión aún no termina.
- La secuencia lineal S38.1 → S38.2 → S38.3 → S38.4 redujo el riesgo de que un
  cálculo financiero inventara mappings o autoridad.
- La qualification negativa debe ser parte del contrato, no una prueba manual
  posterior; por eso cada gate también comprueba ausencia de recomendaciones.

## Artefactos

- **Scope:** `work/epics/e38-cash-and-financial-intelligence/scope.md`
- **Design/plan:** `design.md`, `plan.md`
- **Stories:** `stories/`
- **Código:** `escala_server/financial/`
- **Tests:** `tests/test_e38_financial_intelligence.py`
- **Qualification:** `scripts/qualify_e38.py`
- **Evidence:** `evidence/`

## Siguiente paso

E38 queda cerrado localmente y desbloquea el consumo del contrato financiero
por E39 (ritmos/transcripts) y E40 (diagnóstico/cockpit). E41 debe validar el
instalador y ejecución nativa; E42 debe conducir la aceptación end-to-end con
empresarios, el catálogo de funcionalidades y el PDF de producto.

No se hizo push ni publicación remota.
