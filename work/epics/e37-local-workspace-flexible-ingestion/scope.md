---
epic_id: "E37"
title: "Local Workspace & Flexible Ingestion"
status: "in_progress"
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

E37 se planifica como un walking skeleton con riesgo primero. No existe un
registro formal de aprendizaje de `rai-epic-design` ni un archivo de
calibración de velocidad disponible; los tamaños se mantienen como hipótesis y
los tiempos reales se anotarán por story, sin convertirlos en fechas objetivo.
Los patrones de grafo consultados favorecen boundary-first, gates fail-closed y
un checkpoint E2E real antes del cierre.

### Story Sequence

| Order | Story | Size | Dependencies | Milestone | Rationale and what it enables |
|:-----:|---|:---:|---|---|---|
| 1 | S37.1 Local Workspace & Data Authority | M | E36 (hard) | M1 Walking Skeleton | Prueba primero el riesgo de autoridad y evita abrir SQLite en una carpeta de intercambio; habilita cualquier procesamiento seguro. |
| 2 | S37.2 Flexible File Ingestion | L | S37.1 (hard) | M2 Profile MVP | Construye el contrato de fuente, adapters y preguntas sobre una frontera ya segura; habilita la integración del inbox. |
| 3 | S37.3 Synced-Folder Inbox & Failure Handling | M | S37.1 + S37.2 (hard) | M3 E2E / Epic Complete | Integra enum, fingerprint, reintento, duplicado y cuarentena contra una carpeta temporal real; es la demostración que une todos los contratos. |

Critical path: `E36 → S37.1 → S37.2 → S37.3 → E37 close`.

No se programa trabajo de stories en paralelo: las tres tocan el mismo límite
de autoridad y el processor no puede ser confiable antes del modelo de fuente.
Dentro de S37.2 sí pueden prepararse fixtures de formatos en paralelo con la
implementación del registry, siempre que cada commit mantenga el ciclo TDD.

### Milestones

| Milestone | Stories | Success criteria | Demonstrable capability |
|---|---|---|---|
| **M1: Local Authority Walking Skeleton** | S37.1 | Guards de path y symlink, macOS/Windows-style fixtures, tests/lint/format/types pass; SQLite dentro del exchange falla antes de abrir. | Configurar un workspace y ver un receipt seguro de autoridad. |
| **M2: Flexible Profile MVP** | S37.1–S37.2 | Registry tipado, perfiles de texto/tablas y adapters declarados; unknown/ambiguous/provider-missing inputs generan estados explícitos y preguntas. | Entregar CSV/TSV/XLSX/documento/PDF/transcript y saber qué se entendió o qué falta. |
| **M3: Real Inbox Integration** | S37.1–S37.3 | Una carpeta temporal ordinaria procesa entradas válidas, duplica cero fuentes al repetir, aísla inválidos y deja DB/receipts sin filtraciones ni mutación indebida. | Repetir la corrida diaria sobre una carpeta sincronizada simulada con una empresa sintética. |
| **M4: Epic Complete** | S37.1–S37.3 + exit audit | REQ-E37-001…007 tienen artifacts/receipts y gates PASS; scope, retrospective y ledger reflejan la evidencia, no planes. | E37 listo para que E38 consuma perfiles confirmados. |

### Progress Tracking

| Story | Size | Status | Actual | Velocity | Notes |
|---|:---:|:---:|:---:|:---:|---|
| S37.1 | M | complete | 17m02s | 1 M / 17m02s | Merged locally at `0d66f11` review + close gates; 12 focused tests, 858 full-suite passed / 2 skipped; requirements remain unproved until master receipts. |
| S37.2 | L | pending | — | — | Registry, profiling, clarification and source identity. |
| S37.3 | M | pending | — | — | Real inbox, idempotency, quarantine and safe receipts. |

### Sequencing Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Un parser local no cubre los workbooks/documentos reales | High | S37.2 mantiene adapters pequeños, capability reporting y `unsupported`; E42 prueba con empresa sintética antes de ampliar promesas. |
| La guarda de autoridad falla en symlinks o diferencias de paths | High | S37.1 usa resolución real, containment estricto y fixtures de ambos separadores/plataformas. |
| El E2E modifica la carpeta de intercambio o duplica estado | High | S37.3 usa inbox read-only, fingerprint antes de persistir, no-mutation assertions y receipts redacted. |

## Design Artifacts

- `design.md` — gemba, contratos, control flow, riesgos y story dependencies.
- `adr-local-authority-and-inbox.md` — decisión vinculante sobre autoridad
  local e inbox no destructivo.

## Progress Tracking

| Story | Size | Status | Actual | Notes |
|---|:---:|:---:|:---:|---|
| S37.1 | M | complete | 17m02s | Autoridad local y rechazo de SQLite sincronizado; close gates PASS, requisitos E37 todavía `unproved` en el ledger maestro. |
| S37.2 | L | pending | — | Perfilado e ingestión flexible con aclaraciones. |
| S37.3 | M | pending | — | Inbox idempotente, cuarentena y receipts seguros. |

## Dependencies

- E36 Product Truth, IP Boundary & Governance — **complete** (`039f54c`).
- E38-E42 consumen los contratos y receipts de E37; no deben duplicarlos.
