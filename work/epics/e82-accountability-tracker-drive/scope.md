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

## Historias

| Historia | Entrega | Tamaño | Estado |
|---|---|:---:|---|
| S82.1 | Spike: capacidades reales de edición de Sheets vía conectores Drive (Claude, ChatGPT) | S | complete — ver stories/s82.1-spike-drive-connectors.md |
| S82.2 | Modelo del tracker: lectura/validación de una hoja de participante y sus variaciones | M | complete — `coaching/tracker/` |
| S82.3 | Flujo guiado: identidad → conexión → selección de hoja propia con confirmación (`ESCALA-53`) | M | complete — `coaching/tracker/identity.py`, `escala-execution-tracker` |
| S82.6 | Spike: escritura en Sheets (MCP de Sheets, ChatGPT Work) (`ESCALA-56`) | S | planned — antes de S82.4 |
| S82.4 | Llenado: proponer filas desde prioridades/rocks de ESCALA y escribir tras confirmación (`ESCALA-54`) | M | planned — tras S82.6 |
| S82.5 | Mantenimiento previo a reunión: vencidos, `Done`, estado (`ESCALA-55`) | S | planned |

Orden de ejecución: S82.3 → S82.6 → S82.4 → S82.5. Diseño detallado en `design.md`.

Detalle por historia (dependencia → entrega concreta):

- S82.3 (depende de S82.2): `identity.py` (candidatas por nombre de pestaña, placeholder, `TrackerLink`, pestaña pegada) + procedimiento interno `escala-execution-tracker` (catálogo 62 → 63), alcanzado como sub-procedimiento de `procedure.set-quarterly-priority` + aviso de una línea al conectar Drive + `.escala/my-company/` en `.gitignore` + **test de privacidad**: con un workbook sintético multi-pestaña, ninguna celda de otra pestaña llega a un mensaje de ESCALA ni a un archivo local.
- S82.6 (depende de S82.1): tabla verificada GO/NO-GO por superficie (ChatGPT Work, MCP de Sheets en Claude y en Codex) sobre una copia sintética.
- S82.4 (depende de S82.3, S82.6): `proposal.py`: filas desde `quarterly_plan`, bloque para pegar; escritura directa sólo con GO.
- S82.5 (depende de S82.3): `maintenance.py`: vencidos, pasar a Done, faltantes; sólo propone.

## Criterios de terminado

- Un empresario, desde `escala` y sin nombrar comandos, llega a "esta es tu hoja, ¿es la tuya?" y confirma.
- Una pestaña con placeholder ("Name 6") nunca se elige sin confirmación.
- S82.4 entrega filas pegables y consistentes con la hoja; ninguna escritura sin GO de S82.6 y un sí explícito.
- S82.5 entrega la preparación de la reunión sin mover nada.
- Ningún dato de otros participantes se usa, se guarda ni se escribe; los tests usan sólo fixtures sintéticos.
- Un test con workbook sintético multi-pestaña prueba que ninguna celda de otra pestaña llega a un mensaje o archivo local (S82.3).

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

## Implementation Plan

Estrategia: dependency-driven con riesgo aislado temprano. S82.1 y S82.2 están completas; quedan 4 historias (M + S + M + S). Orden fijo: S82.3 → S82.6 → S82.4 → S82.5.

| # | Historia | Jira | Tam. | Depende de | Por qué en esta posición | Habilita |
|---|---|---|:---:|---|---|---|
| 1 | S82.3 | ESCALA-53 | M | S82.2 (hecha) | Camino crítico: da identidad, `TrackerLink`, `.gitignore` y el test de privacidad que S82.4/S82.5 heredan; es el esqueleto E2E (pegar pestaña o conector → "esta es tu hoja") | S82.4, S82.5 |
| 2 | S82.6 | ESCALA-56 | S | S82.1 (hecha) | Spike con límite de 1 día; decide si S82.4 construye la rama de escritura directa. Va antes de S82.4 para no diseñar a ciegas | S82.4 (rama de escritura) |
| 3 | S82.4 | ESCALA-54 | M | S82.3 (dura), S82.6 (dura) | Primer valor de llenado; MVP = filas para pegar, escritura sólo con GO | M3 |
| 4 | S82.5 | ESCALA-55 | S | S82.3 (dura) | Sólo propone; cierra el ciclo previo a la reunión | M3 |

Dependencias: S82.3 → {S82.4, S82.5}; S82.6 → S82.4. Sin ciclos. Externas: cuenta Drive sintética para S82.6 (copia que luego va a la papelera); E85 (ChatGPT) no bloquea y no se afirma soporte.

Camino crítico: S82.3 → S82.4 (S82.6 cabe en paralelo o antes, no alarga el camino si se hace en 1 día).

Oportunidades de paralelo (opcionales, no alteran el orden de ejecución acordado):
- S82.6 no toca código de producto ni depende de S82.3; puede hacerse en paralelo con S82.3 si hay manos.
- S82.5 depende sólo de S82.3; puede correr en paralelo con S82.4 (archivos distintos: `maintenance.py` vs `proposal.py`). Único punto de contacto compartido: fixtures sintéticos de `coaching/tracker/tests/` (acordar nombres antes).

## Milestones

| Hito | Historias | Criterio de éxito verificable | Demo |
|---|---|---|---|
| M1 Esqueleto | S82.3 | Desde `escala`, sin nombrar comandos, se llega a "esta es tu hoja, ¿es la tuya?" y se confirma; placeholder ("Name 6") nunca se elige sin confirmación; test de privacidad verde; `.escala/my-company/` ignorado; catálogo 62 → 63 y capabilities 63 → 64 con tests verdes | Conversación con workbook sintético multi-pestaña y con pestaña pegada |
| M2 Decisión de escritura | S82.6 | Tabla GO/NO-GO por superficie (ChatGPT Work, MCP Sheets en Claude y Codex) con comando de reproducción, sobre copia sintética | Tabla verificada |
| M3 MVP completo | S82.4, S82.5 | Filas pegables consistentes con la hoja (etiquetas de área, sin duplicados, Critical Number distinto señalado); escritura directa sólo con GO y sí explícito; preparación de reunión sin mover nada; fixtures sintéticos únicamente | Propuesta de filas + resumen "antes de tu reunión" |
| M4 Epic complete | todas | Criterios de terminado del scope cumplidos; gates (tests, pyright strict, lint) verdes; sin datos reales en el repo | Listo para `/rai-epic-close` |

Checkpoint de integración: epic de un solo componente (Python + procedimiento + adaptadores); en lugar de E2E con infraestructura, S82.5 (última) corre el flujo completo sintético S82.3 → S82.4 → S82.5 sobre un mismo fixture como verificación de costuras antes de M4.

## Progress Tracking

| Historia | Tam. | Estado | Real | Notas |
|---|:---:|---|---|---|
| S82.1 | S | complete | - | - |
| S82.2 | M | complete | - | - |
| S82.3 | M | complete | M | ESCALA-53 |
| S82.6 | S | planned | - | ESCALA-56; límite 1 día |
| S82.4 | M | planned | - | ESCALA-54; rama de escritura condicionada a S82.6 |
| S82.5 | S | planned | - | ESCALA-55 |

Velocidad: sin datos de calibración para este dominio; los tamaños son hipótesis y se recalibran tras S82.3.

### Sequencing Risks

1. **S82.6 da NO-GO en todas las superficies**: S82.4 se entrega sólo con bloque para pegar (ya es el MVP, D3); la rama de escritura directa no se construye. Impacto bajo por diseño.
2. **S82.3 concentra el riesgo de privacidad y de gobierno** (test de privacidad, cambio de baseline del catálogo, `.gitignore`): si se desliza, bloquea S82.4 y S82.5. Mitigar haciendo primero `.gitignore` y el test de privacidad (RED) antes del flujo.
3. **Validaciones/formatos al pegar TSV (U5) y fechas reales (U4)** sólo se conocen con la copia sintética: pueden forzar retrabajo en S82.4/S82.5. Mitigar verificando U5 al inicio de S82.4 y manteniendo `parse_due` conservador.
