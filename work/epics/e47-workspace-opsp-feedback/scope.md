---
epic_id: "E47"
title: "Coherencia del viaje instalado: Workspace, OPSP y Feedback"
status: "done"
created: "2026-08-09"
jira_key: "ESCALA-1"
---

# E47 — Coherencia del viaje instalado: Workspace, OPSP y Feedback

## Objetivo

Hacer que el recorrido instalado de ESCALA sea coherente y recuperable: Codex opera RaiSE mediante MCP sin abrir secretos, OPSP tiene estructura real y persistencia local, y los usuarios pueden reportar errores o mejoras de forma redactada y confirmada.

**Valor:** una persona recibe una herramienta que conserva su avance, reconoce sus límites y permite mejorar el producto sin transferir información de su empresa.

## Historias

| ID | Historia | Tamaño | Estado | Termina cuando |
|---|---|:---:|:---:|---|
| S47.1 | Contrato Workspace Codex/MCP (`ESCALA-2`) | 5 | Done | CLI en sandbox falla de forma comprensible; Codex usa MCP; el provisionado no ensucia el worktree. |
| S47.2 | Instalador, recursos y migración (`ESCALA-3`) | 8 | Done | Nueva y existente instalación reciben recursos/skills compatibles sin duplicados. |
| S47.3 | OPSP completo y coherente (`ESCALA-4`) | 5 | Done | La guía representa columnas, filas, responsables y capacidades sin contradicciones. |
| S47.4 | Persistir, reanudar y exportar OPSP (`ESCALA-8`) | 8 | Done | Estado estructurado y Markdown local permiten continuar y exportar el plan. |
| S47.5 | Feedback contextual local (`ESCALA-9`) | 5 | Done | El usuario confirma bug/mejora y recibe un reporte redactado, sin envío automático — ya satisfecho por `escala-bugreport/SKILL.md` existente, verificado con `tests/test_bugreport_skill.py`. |
| S47.6 | Calificación y release (`ESCALA-10`) | 5 | Done | Casos de instalación, regresión y límites de privacidad pasan con evidencia: instalación aislada verificada, regresión 1097 passed (1 fallo preexistente ajeno), canary de privacidad en verde. |
| S47.7 | Sincronizar clones del repo (`ESCALA-5`) | 3 | Done | Un fix en `escala-skills/` llega al clon que sirve los symlinks activos (`agente-de-escalamiento`) sin pasos manuales olvidables. |
| S47.8 | ~~Evitar contaminación cross-repo en `rai graph query`~~ (`ESCALA-6`) | 3 | Fuera de alcance | RaiSE es herramienta interna de desarrollo, no una dependencia del producto — verificado que `install.sh`/`escala-skills/` no invocan `rai`. Fix de referencia dejado en raise-commons, no bloquea E47. |
| S47.9 | Company State Document como Project de ChatGPT (`ESCALA-7`) | 5 | Done | El mismo documento de estado de empresa que usa S47.4/S47.3 en Claude es subible a un Project de ChatGPT (web y desktop) con instrucciones equivalentes. |

**Nota de alcance (2026-08-10):** S47.7-S47.9 se agregaron durante una auditoría de producto (comparación contra PRD, parking lot, y arquitectura de LifeOS/danielmiessler) que encontró: (a) los dos clones locales del repo divergieron y solo uno sirve los symlinks activos de los coaches, (b) `rai graph query` sin `--strategy` cae a un fallback cross-repo que contamina el contexto de las skills `rai-*`, (c) el alcance de plataforma es Claude + ChatGPT (ambos, no genérico). No forman parte del diseño original de E47 pero comparten su objetivo de coherencia del viaje instalado.

## Criterios de terminación

- [x] Codex no requiere permiso permanente sobre una carpeta que mezcla base de datos y secretos (S47.1).
- [x] El fallback CLI identifica una base de solo lectura y orienta a MCP en vez de devolver traceback (S47.1).
- [x] El provisionador no crea artefactos Git-visibles y deja un worktree listo o explica el bloqueo (S47.1/S47.2).
- [x] Las instalaciones nuevas y existentes resuelven una única versión de cada skill y recurso (S47.2; instalación aislada verificada en S47.6 — 62 skills, sin duplicados).
- [x] OPSP mantiene pendientes explícitos y no inventa datos de empresa (S47.3 corrige el bug de traducción recursiva; S47.4 exporta `[PENDIENTE]` explícito, nunca inventado).
- [x] La persistencia local es versionada y recuperable (S47.4: `.escala/my-company/opsp.yaml` + `opsp.md`, git-trackable).
- [x] Bug/mejora se confirma, se redacta y se guarda localmente; nunca se envía por defecto (S47.5, `escala-bugreport`).
- [x] Las pruebas distinguen validación técnica de aceptación humana (gates automáticos vs. checklist de calidad conversacional en cada SKILL.md).
- [x] Jira: Epic `ESCALA-1` y S47.1 `ESCALA-2` creados con la cuenta Eduardo Luna.
- [x] Regresión, instalación y límites de privacidad verificados con evidencia (S47.6): 1097 passed / 1 fallo preexistente ajeno; canary de boundary público en verde.

## Dependencias

```text
S47.1 workspace ─┐
S47.2 instalación ├→ S47.3 OPSP → S47.4 persistencia
                  └────────────────→ S47.5 feedback → S47.6 calificación
```

### Machine
```yaml
modules_affected:
  - path: .codex/config.toml
    change: modify
  - path: .mcp.json
    change: modify
  - path: install.sh
    change: modify
  - path: escala-skills/
    change: modify
  - path: escala-agent/skills/
    change: modify
  - path: escala_server/
    change: modify
  - path: tests/
    change: modify
decisions:
  - id: D1
    choice: "Codex usa MCP para estado RaiSE; el CLI se trata como fallback fuera del sandbox."
    rationale: "La base RaiSE y secretos comparten directorio global; ampliar la escritura es inseguro."
    constraint: "No agregar ~/.rai como writable root ni leer secretos."
  - id: D2
    choice: "OPSP se conserva como estado estructurado y se renderiza a Markdown."
    rationale: "Permite reanudar, validar y exportar sin perder la lectura humana."
    constraint: "Los campos faltantes permanecen explícitos; no se infieren."
  - id: D3
    choice: "Feedback es un artefacto Markdown local confirmado por la persona."
    rationale: "El reporte puede usar el contexto conversacional visible sin extraer memoria privada."
    constraint: "No hay envío automático ni datos identificables."
constraints:
  - "No mezclar cambios pendientes de otros worktrees."
  - "No usar permisos globales como sustituto de un contrato de instalación."
  - "Diferenciar prueba técnica, configuración externa y aceptación humana."
```

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Base operativa y secretos comparten directorio | MCP-first; no ampliar writable roots; separar responsabilidades en producto. |
| Worktree con runtime incompleto | Reproducción y test de provisionado limpio antes de corregir. |
| Configuración Jira o MCP vencida | Verificar identidad y permisos; reiniciar el servidor MCP antes de crear trabajo. |
| Deriva de skills | Inventario por origen, instalador y destino antes de migrar. |
| Datos empresariales en feedback | Sanitización fail-closed, revisión del usuario y outbox local. |
