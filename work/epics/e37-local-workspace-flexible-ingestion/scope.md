---
epic_id: "E37"
title: "Local Workspace & Flexible Ingestion"
status: "active"
created: "2026-07-22"
mission: "escala-local-v2-plan-maestro-2607202112"
---

# Epic Scope: E37 — Local Workspace & Flexible Ingestion

## Objective

Entregar el límite operativo local de ESCALA: el runtime y el estado
autoritativo viven en la máquina del instalador, mientras que el empresario
puede seleccionar una carpeta ordinaria —incluida una carpeta ya sincronizada
por Google Drive u OneDrive— como bandeja de intercambio de archivos. El
producto debe recibir los archivos en el formato en que ya existen, describir
qué entendió, preguntar por ambigüedades materiales y fallar de forma segura.

## Value

- **Para el empresario:** puede comenzar con sus propios excels,
  transcripciones y documentos sin una migración previa ni una plantilla nueva.
- **Para el equipo:** puede intercambiar documentos y reportes mediante una
  carpeta que ya controla, sin convertir el sistema en un servicio hospedado.
- **Para E38-E42:** cada fuente queda identificada, trazable y reutilizable,
  con límites claros para no confundir una inferencia con un dato confirmado.

## Architectural Invariants

1. El runtime de ESCALA se ejecuta únicamente en la máquina de quien lo
   instaló.
2. La raíz de datos autoritativa, el estado de la empresa y SQLite viven en esa
   máquina y no se sincronizan.
3. Una carpeta de Drive, OneDrive o filesystem elegida por el usuario solo
   contiene documentos de intercambio, nunca la base autoritativa.
4. La ingestión no depende de APIs cloud, OAuth, telemetría ni un servicio
   remoto.
5. Cada fuente conserva fingerprint, procedencia relativa, estado y una
   identidad idempotente; las rutas absolutas no salen en recibos.
6. Una entrada ambigua, corrupta, cifrada, sobredimensionada o no soportada no
   cambia el estado canónico sin una disposición explícita.

## In Scope

- Configuración y validación de workspace, raíz de datos e inbox local.
- Guardas multiplataforma para macOS y Windows, incluyendo rutas relativas y
  detección de una carpeta sincronizada.
- Perfiles de formatos para hojas de cálculo, CSV/TSV, documentos, PDF y
  transcripciones declaradas.
- Perfilado inicial de hojas, tablas, encabezados, unidades, fechas y entidades
  candidatas.
- Preguntas y estados de aclaración para ambigüedades materiales.
- Fingerprints, procedencia relativa, estados de extracción y reintentos
  seguros.
- Inbox idempotente y cuarentena/reportes de entradas problemáticas.
- Contratos, pruebas, recibos y gates de no-host/no-SQLite-sync.

## Out of Scope

- Reconstrucción de estados financieros y coaching de cash (E38).
- Lectura y tendencias de dailies/weeklies o coordinación del equipo (E39).
- Diagnóstico 0-100, cockpit, estrategia y coaching ejecutivo (E40).
- Instalador empaquetado, actualización y rollback completos (E41).
- Calificación end-to-end, catálogo funcional y PDF final (E42).
- APIs de Google Drive/OneDrive, OAuth, SaaS, base de datos cloud o
  colaboración multi-escritor.

## Planned Stories

| ID | Story | Size | Depends on | Outcome |
|---|---|:---:|---|---|
| S37.1 | Local Workspace & Data Authority | M | E36 | El workspace local y la autoridad de datos quedan definidos; SQLite dentro del inbox sincronizado es rechazado de forma verificable. |
| S37.2 | Flexible File Ingestion | L | S37.1 | Archivos reales del usuario se perfilan sin plantilla obligatoria; las ambigüedades generan preguntas y cada fuente tiene identidad y procedencia repetibles. |
| S37.3 | Synced-Folder Inbox & Failure Handling | M | S37.1, S37.2 | Una carpeta ordinaria funciona como inbox idempotente; fallos, duplicados y entradas peligrosas quedan aislados sin filtración ni corrupción. |

## Master Requirements Owned

| Requirement | Acceptance proof |
|---|---|
| REQ-E37-001 | Runtime y estado autoritativo solo en la máquina del instalador. |
| REQ-E37-002 | Rechazo ejecutable de SQLite/raíz canónica dentro del inbox sincronizado. |
| REQ-E37-003 | Formatos declarados sin adaptación a plantilla; variantes no soportadas fallan explícitamente. |
| REQ-E37-004 | Inferencia de estructura y preguntas ante ambigüedad material. |
| REQ-E37-005 | Fingerprint, procedencia relativa, estado e identidad rerun-safe sin rutas de máquina. |
| REQ-E37-006 | Inbox idempotente de carpeta local/Drive/OneDrive mediante filesystem únicamente. |
| REQ-E37-007 | Cuarentena o reporte seguro para corruptos, cifrados, grandes, duplicados y no soportados. |

## Done Criteria

- [ ] Las tres historias completan el ciclo RaiSE completo y sus ramas se
      integran en `main` con gates de tests, lint, formato y tipos.
- [ ] Los siete requisitos E37 tienen artefacto y receipt verificables en el
      ledger maestro; ningún estado `unproved` se presenta como terminado.
- [ ] Un caso sintético end-to-end demuestra ingestión desde una carpeta
      ordinaria, reejecución sin duplicados, pregunta de ambigüedad y
      cuarentena de una entrada inválida.
- [ ] Un caso negativo demuestra que SQLite autoritativo dentro del inbox
      sincronizado es rechazado y que el estado canónico permanece intacto.
- [ ] Los recibos no contienen rutas absolutas, secretos, contenido sensible ni
      llamadas a APIs cloud.
- [ ] La implementación queda consumible por E38-E40 sin duplicar el contrato
      de autoridad o la identificación de fuentes.

## Acceptance Evidence

- Contrato tipado de workspace y guardas positivas/negativas.
- Fixtures sintéticos de CSV/XLSX/TSV/documento/PDF/transcript y variantes
  rechazadas.
- Receipts JSON y Markdown deterministas por fuente y por corrida.
- Prueba de no mutación de SQLite/estado ante fallos y duplicados.
- Ejecución local en macOS y revisión de compatibilidad de rutas Windows.
- Ledger maestro actualizado únicamente con evidencia producida por gates.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Los excels reales tienen formatos no previstos | High | Perfilado estructural, estado `needs_clarification` y extensión incremental con fixtures. |
| Una carpeta sincronizada contiene por error SQLite | High | Guardas de ruta antes de abrir/escribir y pruebas negativas en cada plataforma. |
| Reintentos duplican fuentes o dañan la bandeja | High | Fingerprint estable, operaciones idempotentes, cuarentena y no mutación canónica. |
| La detección de "sincronizada" es imperfecta | Medium | Tratarla como configuración declarada/guardada por el usuario; nunca asumir seguridad por nombre de carpeta. |
| Se expone una ruta o contenido sensible en un receipt | High | Proveniencia relativa, redacción por defecto y tests de no filtración. |

## Implementation Plan

> Se añadirá mediante `/rai-epic-design` y `/rai-epic-plan` después de revisar
> los módulos actuales y convertir cada requisito en pruebas RED-GREEN-REFACTOR.

## Progress Tracking

| Story | Size | Status | Actual | Notes |
|---|:---:|:---:|:---:|---|
| S37.1 | M | pending | — | Autoridad local y rechazo de SQLite sincronizado. |
| S37.2 | L | pending | — | Perfilado e ingestión flexible con aclaraciones. |
| S37.3 | M | pending | — | Inbox idempotente, cuarentena y receipts seguros. |

## Dependencies

- E36 Product Truth, IP Boundary & Governance — **complete** (`039f54c`).
- E38-E42 consumen los contratos y receipts de E37; no deben duplicarlos.
