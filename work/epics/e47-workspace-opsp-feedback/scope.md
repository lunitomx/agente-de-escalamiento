---
epic_id: "E47"
title: "Coherencia del viaje instalado: Workspace, OPSP y Feedback"
status: "designed"
created: "2026-08-09"
jira_key: "ESCALA-1"
---

# E47 — Coherencia del viaje instalado: Workspace, OPSP y Feedback

## Objetivo

Hacer que el recorrido instalado de ESCALA sea coherente y recuperable: Codex
opera RaiSE mediante MCP sin abrir secretos, OPSP tiene estructura real y
persistencia local, y los usuarios pueden reportar errores o mejoras de forma
redactada y confirmada.

## Criterios de terminación

- Codex no requiere permiso permanente sobre una carpeta que mezcla base de
  datos y secretos.
- El provisionador no crea artefactos Git-visibles y deja un worktree listo o
  explica el bloqueo.
- Las instalaciones nuevas y existentes resuelven una única versión de cada
  skill y recurso.
- OPSP mantiene pendientes explícitos y no inventa datos de empresa.
- Bug/mejora se confirma, se redacta y se guarda localmente; nunca se envía por
  defecto.

## Dependencias

S47.1 workspace y S47.2 instalación desbloquean S47.3 OPSP; S47.4 persiste el
OPSP; S47.5 crea feedback local; S47.6 califica el recorrido.

## Restricciones

- No copiar `.raise/rai/raise.db`, tokens ni secretos a un worktree.
- No usar permisos globales como sustituto de un contrato de instalación.
- Diferenciar prueba técnica, configuración externa y aceptación humana.
