---
epic_id: E82
title: Tracker de accountability guiado en Google Drive
status: planned
jira_key: "ESCALA-48"
closure_disposition: active
created: 2026-09-30
updated: 2026-09-30
depends_on: []
related: [E45, E68, E79, E85]
---

# Scope E82

## Objetivo

ESCALA ayuda a cada participante de un grupo de accountability a mantener al día **su propia hoja** del "Accountability Group Goal Tracker": pregunta quién es, le sugiere conectar su Google Drive por MCP desde su cliente (Claude o ChatGPT), identifica su hoja y la llena con él.

## Estructura del tracker (observada en la plantilla 2025-26)

- `START HERE`: instrucciones y datos del grupo (nombre, teléfono, email, negocio).
- Una hoja por participante: nombre, negocio, **Critical Number**, **Monthly Commitments** (Focus Area Cash/Strategy/Execution/People · Priority · KPI · Due Date · estado), **Quarterly Goals (Rocks)** y **Done**. Algunas hojas agregan columnas propias (p.ej. revenue real/proyectado por mes).

Las áreas coinciden con Cash/People/Strategy/Execution de ESCALA; Critical Number y Rocks ya los produce la capacidad de prioridad trimestral / OPSP.

## Dentro

- Flujo conversacional: "¿quién eres?" → guía para conectar Drive → localizar el archivo → confirmar cuál hoja es suya → proponer filas → escribir sólo tras confirmación.
- Conocimiento del formato del tracker (incluidas variaciones por hoja) sin romper fórmulas ni la hoja `START HERE`.
- Mover compromisos terminados a `Done` y revisar vencidos antes de la reunión del grupo.

## Fuera

- Leer o editar hojas de otros participantes (el archivo es compartido y contiene datos de todo el grupo).
- Guardar el contenido del tracker en el repositorio o fuera de la carpeta local de la empresa.
- Construir un conector propio a Google: se usa el MCP/conector que el cliente del usuario ya ofrece.

## Incógnitas (spike primero)

1. ¿Los conectores de Drive de Claude y ChatGPT permiten editar celdas de una Google Sheet, o sólo leer/reemplazar el archivo? ¿Y si el tracker es un `.xlsx` subido a Drive sin convertir?
2. ¿ESCALA corre hoy en ChatGPT? Hoy los adaptadores son Claude y Codex; ChatGPT depende de E85.
3. Cómo identificar la hoja de forma inequívoca (nombre en `Participant Name`, a veces fórmula a `START HERE`).

## Historias (borrador)

| Historia | Entrega | Tamaño | Estado |
|---|---|:---:|---|
| S82.1 | Spike: capacidades reales de edición de Sheets vía conectores Drive (Claude, ChatGPT) | S | complete — ver stories/s82.1-spike-drive-connectors.md |
| S82.2 | Modelo del tracker: lectura/validación de una hoja de participante y sus variaciones | M | complete — `coaching/tracker/` |
| S82.3 | Flujo guiado: identidad → conexión → selección de hoja propia con confirmación | M | planned (ESCALA-53) |
| S82.4 | Llenado: proponer filas desde prioridades/rocks de ESCALA y escribir tras confirmación | M | planned (ESCALA-54) — tras S82.6 |
| S82.5 | Mantenimiento previo a reunión: vencidos, `Done`, estado | S | planned (ESCALA-55) |
| S82.6 | Spike: escritura en Sheets (MCP de Sheets, ChatGPT Work) | S | planned (ESCALA-56) — antes de S82.4 |

Orden de ejecución: S82.3 → S82.6 → S82.4 → S82.5. Diseño detallado en `design.md`.

| Historia | Depende de | Entrega concreta |
|---|---|---|
| S82.3 | S82.2 | `identity.py` (candidatas, placeholder, `TrackerLink`, pestaña pegada) + procedimiento interno `escala-execution-tracker` al que se llega desde `escala` |
| S82.6 | S82.1 | Tabla verificada GO/NO-GO por superficie (ChatGPT Work, MCP de Sheets en Claude y en Codex) sobre una copia sintética |
| S82.4 | S82.3, S82.6 | `proposal.py`: filas desde `quarterly_plan`, bloque para pegar; escritura directa sólo con GO |
| S82.5 | S82.3 | `maintenance.py`: vencidos, pasar a Done, faltantes; sólo propone |

## Criterios de terminado

- Un empresario, desde `escala` y sin nombrar comandos, llega a "esta es tu hoja, ¿es la tuya?" y confirma.
- Una pestaña con placeholder ("Name 6") nunca se elige sin confirmación.
- S82.4 entrega filas pegables y consistentes con la hoja; ninguna escritura sin GO de S82.6 y un sí explícito.
- S82.5 entrega la preparación de la reunión sin mover nada.
- Ningún dato de otros participantes se usa, se guarda ni se escribe; los tests usan sólo fixtures sintéticos.

### Machine
```yaml
modules_affected:
  - path: coaching/tracker/
    change: modify
  - path: escala-skills/escala-execution-tracker/SKILL.md
    change: create
  - path: escala-skills/catalog.yaml
    change: modify
decisions:
  - id: D1
    choice: "Sin comandos públicos nuevos; un procedimiento interno reachable sólo desde escala"
    rationale: "Experiencia ultra simple para un empresario no técnico"
    constraint: "Ningún alias o comando público nuevo"
  - id: D3
    choice: "MVP para pegar; escritura directa condicionada a S82.6"
    rationale: "El conector verificado no edita celdas"
    constraint: "S82.6 antes de S82.4"
constraints:
  - "Nunca escribir ni usar hojas de otros participantes"
  - "Datos de la empresa sólo en .escala/my-company/; tests sintéticos"
  - "No afirmar soporte de ChatGPT Work (E85)"
```
