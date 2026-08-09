---
epic_id: "E47"
title: "Coherencia del viaje instalado: Workspace, OPSP y Feedback"
status: "started"
created: "2026-08-09"
jira_key: null
---

# E47 — Coherencia del viaje instalado: Workspace, OPSP y Feedback

## Objetivo

Hacer que el recorrido instalado de ESCALA sea coherente y recuperable: Codex opera RaiSE mediante MCP sin abrir secretos, OPSP tiene estructura real y persistencia local, y los usuarios pueden reportar errores o mejoras de forma redactada y confirmada.

**Valor:** una persona recibe una herramienta que conserva su avance, reconoce sus límites y permite mejorar el producto sin transferir información de su empresa.

## Historias

| ID | Historia | Tamaño | Estado | Termina cuando |
|---|---|:---:|:---:|---|
| S47.1 | Contrato Workspace Codex/MCP | 5 | In progress | CLI en sandbox falla de forma comprensible; Codex usa MCP; el provisionado no ensucia el worktree. |
| S47.2 | Instalador, recursos y migración | 8 | Pending | Nueva y existente instalación reciben recursos/skills compatibles sin duplicados. |
| S47.3 | OPSP completo y coherente | 5 | Pending | La guía representa columnas, filas, responsables y capacidades sin contradicciones. |
| S47.4 | Persistir, reanudar y exportar OPSP | 8 | Pending | Estado estructurado y Markdown local permiten continuar y exportar el plan. |
| S47.5 | Feedback contextual local | 5 | Pending | El usuario confirma bug/mejora y recibe un Markdown redactado, sin envío automático. |
| S47.6 | Calificación y release | 5 | Pending | Casos de instalación, regresión y límites de privacidad pasan con evidencia. |

## Criterios de terminación

- [ ] Codex no requiere permiso permanente sobre una carpeta que mezcla base de datos y secretos.
- [ ] El fallback CLI identifica una base de solo lectura y orienta a MCP en vez de devolver traceback.
- [ ] El provisionador no crea artefactos Git-visibles y deja un worktree listo o explica el bloqueo.
- [ ] Las instalaciones nuevas y existentes resuelven una única versión de cada skill y recurso.
- [ ] OPSP mantiene pendientes explícitos y no inventa datos de empresa.
- [ ] La persistencia local es versionada y recuperable.
- [ ] Bug/mejora se confirma, se redacta y se guarda localmente; nunca se envía por defecto.
- [ ] Las pruebas distinguen validación técnica de aceptación humana.
- [ ] Jira: el vínculo se añadirá tras resolver el permiso de creación en el proyecto ESCALA.

## Dependencias

```text
S47.1 workspace ─┐
S47.2 instalación ├→ S47.3 OPSP → S47.4 persistencia
                  └────────────────→ S47.5 feedback → S47.6 calificación
```

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Base operativa y secretos comparten directorio | MCP-first; no ampliar writable roots; separar responsabilidades en producto. |
| Worktree con runtime incompleto | Reproducción y test de provisionado limpio antes de corregir. |
| Jira no disponible | Artefactos versionados locales; no fingir ticket remoto ni transición. |
| Deriva de skills | Inventario por origen, instalador y destino antes de migrar. |
| Datos empresariales en feedback | Sanitización fail-closed, revisión del usuario y outbox local. |