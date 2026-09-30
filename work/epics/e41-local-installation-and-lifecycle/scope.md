---
epic_id: "E41"
title: "Local Installation and Lifecycle"
status: "active"
created: "2026-07-22"
updated: "2026-09-12"
closure_disposition: "active"
remediation_epic: E78
mission: "escala-local-v2-plan-maestro-2607202112"
---

# Epic Scope: E41 — Local Installation and Lifecycle

## Reapertura por regresión reproducida — 2026-09-12

H05 obtuvo `healthy` sin aplicación ni base existentes: `LifecycleRuntime`
sólo escribe/lee un marker. Esto contradice la entrega de ejecución real.
[E78](../e78-reliable-installation-runtime-recovery/scope.md) es el propietario
único de la implementación correctiva de runtime, artefacto, actualización y
recuperación; E41 recualifica los requisitos afectados con esos recibos.

Los estados Done y checks de entrega siguientes son el registro histórico de
calificación sintética, no aceptación vigente del runtime. Se conserva la
historia sin usarla para cerrar la regresión. E42 sigue siendo el gate externo.

### Condiciones actuales para volver a cerrar

- [ ] S78.2/S78.4 prueban artefacto íntegro y proceso real con lectura/escritura.
- [ ] S78.3/S78.5 prueban activación efectiva de código, snapshot consistente,
  rollback y preservación de datos; no basta cambiar metadata.
- [ ] S78.6 revalida comandos/schedules/diagnóstico y requisitos afectados de E41.
- [ ] Se revisan recibos actuales y aceptación maestra sin reutilizar como prueba
  suficiente el conteo histórico 36/42 anterior a esta regresión.

## Objective

Entregar un flujo reproducible para instalar, ejecutar, compartir documentos,
actualizar, migrar, revertir y programar ESCALA localmente en macOS y Windows.

## Architectural invariants

1. Runtime, SQLite, configuración canónica y backups viven en la máquina instaladora.
2. Google Drive, OneDrive y carpetas sincronizadas son únicamente exchange de documentos.
3. No se requiere servicio hospedado, OAuth, API cloud, worker remoto o red para el runtime.
4. Artefactos y migraciones se verifican antes de escribir y siempre dejan safe-stop o rollback.

## Stories (7 requirements)

| ID | Story | Requirements | Status |
|---|---|---|---|
| S41.1 | macOS and Windows Installation | REQ-E41-001, REQ-E41-002 | Done |
| S41.2 | Local Runtime and Folder Setup | REQ-E41-003, REQ-E41-006 | Done |
| S41.3 | Safe Migration Update and Rollback | REQ-E41-004, REQ-E41-005 | Done |
| S41.4 | Release Qualification Gates | REQ-E41-007 | Done |

## In scope (MUST)

- [x] Paquete local determinista y flujo documentado para macOS y Windows.
- [x] Runtime local con health/version/data role y stop limpio.
- [x] Exchange opcional validado fuera de SQLite y estado canónico.
- [x] Backup, migración, verificación de artefacto, update y rollback.
- [x] Schedules nativos offline para launchd y Task Scheduler.
- [x] Qualification sintética con siete receipts y negative cases.

## Out of scope

- Publicación, firma comercial y aceptación de empresarios reales: E42.
- OAuth, APIs de Google Drive/OneDrive, servidor hospedado o telemetría.
- DISC y correlación personal: parking lot con consentimiento explícito.

## Done criteria

- [x] S41.1–S41.4 completas.
- [x] `REQ-E41-001` … `REQ-E41-007` tienen artefacto y receipt exactos.
- [x] Qualification pasa en la matriz simulada macOS/Windows.
- [x] Tests focalizados, lint, formato, tipos y gates de requisitos pasan.
- [x] Retrospectiva y tag local existen; no se publica sin autorización.
