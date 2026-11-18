# E88: Strategy 2026 — scope

jira_key: ESCALA-119

## Objetivo

ESCALA guía los 10 ejercicios del Workbook Strategy 2026 EOA en el orden del Strategy Day, cada uno con su prompt 2026 en español.

## Los 10 ejercicios (orden del taller, agenda p. 2)

1. AI Setup (p. 4)
2. SWT con tendencias 2026/27 (p. 5-6)
3. Actividades diferenciadoras (p. 7-8)
4. Propósito de la empresa (p. 9-11)
5. Meta grande / BHAG (p. 11-14)
6. Vivid Vision (p. 14-16)
7. Fanocracy (p. 17-18)
8. Personal Why (p. 18-19)
9. Resumen de visión (p. 20, 22)
10. Make Change Stick (p. 20)

## Dentro del alcance

- El motor de hojas muestra varios prompts por hoja; la hoja SWT pasa a guiada.
- Hojas nuevas: Propósito, Meta grande, Vivid Vision, Fanocracy, Personal Why (área people).
- Prompts 2026 en SWT, Actividades, Resumen de visión, Make Change Stick y AI Setup.
- Lista de 10 tendencias 2026/2027 (p. 5) en la hoja SWT.
- Investigación con fuentes para Vivid Vision, propósito personal y Fanocracy.
- Recorrido «Strategy Day 2026» en orden y mapa de cobertura de las 24 páginas con prueba.

## Fuera del alcance

- Copiar imágenes o el PDF del workbook al repo.
- Cambiar las hojas del workbook 2025 que no están en el 2026.
- Nodos nuevos en `ontology/v2/`.

## Historias

Diseño: `design.md` (secciones 2–9 y Machine). Borradores: `drafts/` de esta épica (commit 96ec3669). Tamaños en Fibonacci; total 24.

| ID | Jira | Historia | Tamaño | Depende de |
|----|------|----------|--------|------------|
| S88.1 | ESCALA-120 | Una hoja muestra varios prompts, y el SWT pasa a hoja guiada | 5 | — |
| S88.2 | ESCALA-121 | Investigación con fuentes: Vivid Vision, propósito personal y Fanocracy | 3 | — |
| S88.3 | ESCALA-122 | Hojas de Propósito de la empresa y Meta grande (BHAG) | 3 | — |
| S88.4 | ESCALA-123 | Hojas de Vivid Vision, Personal Why y Fanocracy | 5 | S88.1, S88.2, S88.3 (conteos) |
| S88.5 | ESCALA-124 | Prompts 2026: AI Setup, Actividades, Resumen de visión y Make Change Stick; reabrir una hoja ya completada | 3 | S88.1 |
| S88.6 | ESCALA-125 | Recorrido del Strategy Day 2026 en orden y mapa de cobertura de las 24 páginas | 5 | S88.3, S88.4, S88.5 |

Orden: S88.1 ∥ S88.2 ∥ S88.3 → S88.5, S88.4 → S88.6.

Fusiones en serie, una a la vez. Cada historia trae la rama destino a su rama, regenera el mapa E6 (design.md sección 7) y corre la suite completa antes de fusionarse.

### Criterios de aceptación por historia

**S88.1 (ESCALA-120)**
- `ToolGuide` acepta `extra_prompts: [{title, text, at: start|end}]`; `ai_prompt` no cambia.
- Las 21 hojas actuales y las pruebas actuales siguen verdes sin tocarlas.
- `page` se rechaza dentro de cada prompt extra; `title` es obligatorio.
- Prompt `start`: sale bajo el paso 1 y primero en la vista; no en la revisión final.
- Prompt `end`: sale después del principal en la revisión final y en la vista (HTML y MD), con su título.
- `swt.yaml` guiada: pasos `tendencias-2026` (lista de 10 tendencias), `tendencias`, `fortalezas`, `debilidades`, `ideas`; ejemplos «Tortillería El Sol:»; nombre en español con acentos; `summary` en español sin términos vetados.
- Prompt `start`: se pinta en la rama `current_step == 0` de `run()` («Paso 1: Información General»), antes de «Antes de empezar», con `_start_prompt_lines()`. No en `_step_lines` («Paso 2»).
- `swt.yaml` trae su prompt SWT 2026 como `ai_prompt` y ≥3 tips; el 3.º sale de `work/research/e88-tips/swt.md#fN` (ancla `<a id="fN"></a>` + bloque yaml con `triangulated: true`).
- `save`: si el último paso tiene `next_sheet`, la salida agrega «Siguiente hoja: <title>. Escribe `/escala-worksheet <id>` para seguir.» y `artifacts.next_sheet`. Sin `next_sheet`, la salida no cambia. Prueba con una hoja de ejemplo.
- `escala-skills/escala-worksheet/SKILL.md`: Step 2 menciona los prompts del paso 1; Step 4 dice que muestre «Siguiente hoja» y ofrezca empezarla.
- Mapa E6 regenerado (swt.yaml cambió; conteos 88/84 sin cambio).

**S88.2 (ESCALA-121)**
- `work/research/e88-tips/{vivid-vision,life-purpose,fanocracy}.md`.
- Cada archivo: ≥3 hallazgos `### fN`, cada uno con ≥2 fuentes externas citadas.
- Formato de cada hallazgo igual a `work/research/e87-tips/`: `<a id="fN"></a>` + bloque yaml con `id`, `triangulated: true`.
- `ANCHOR_SOURCE_RE` en `tests/test_e87_tool_guides.py` pasa a `work/research/e8[78]-tips/`. Prueba: una fuente e88 coincide; un hallazgo e88 sin `triangulated: true` falla.
- Si S88.1 ya se fusionó, `swt.md` pasa la revisión ampliada.
- Ningún texto copiado del workbook; sin números de página.

**S88.3 (ESCALA-122)**
- `worksheet-core-purpose` y `worksheet-bhag` desde los borradores; nombre visible «Meta grande (BHAG)», plazo 10–30 años.
- Cada hoja pasa `parse_guide`, ≥3 tips con fuente, vista con todos los pasos.
- Registro: 2 entradas, `total_worksheets` 21 → 23. Mapa E6 regenerado (design.md sección 7); conteos 88/84 → 90/86.

**S88.4 (ESCALA-123)**
- `worksheet-vivid-vision`, `worksheet-fanocracy` (strategy) y `worksheet-life-purpose` (people).
- Vivid Vision: `ai_followups` pasa a `extra_prompts` (3, `at: end`); «Imprímela» va al `how` del último paso; meta a 10–30 años.
- Fanocracy: prompt fiel (7 de 9 principios); los 9 en la guía.
- ≥3 tips por hoja con fuente de S88.2.
- Registro 23 → 26. Mapa E6 regenerado (design.md sección 7); conteos 90/86 → 93/89.

**S88.5 (ESCALA-124)**
- `swt.yaml`: `extra_prompts` `start` «Arranque con IA» (AI Setup).
- `differentiating-activities.yaml`: prompt 2026.
- `vision-summary.yaml`: `ai_prompt` = Make Change Stick 2026 (con «10 tareas» y «semana»); `extra_prompts` `start` «Tu día en una sola hoja» (Vision Summary); sin BHAG ni «pág».
- `vision-summary.yaml`: `derived_from` de `worksheet-core-customer` con `required: false`; paso `meta-grande` y su tip dicen 10-30 años. Prueba: sin Cliente central guardada, la vista no trae «Falta» ni «Cliente central»; la hoja no contiene «10-25».
- Reabrir hoja completada (design.md sección 3): `start` respalda `<id>.yaml` como `<id>-AAAAMMDD-HHMMSS.yaml`, empieza en el paso 1 y dice dónde quedó el respaldo. `resume` sobre completada indica usar `start`. `get_completed_ids()` lee solo `<id>.yaml`. Pruebas: respaldo con los datos de antes; `list` muestra ⬜ al reabrir y ✅ al guardar.
- Mapa E6 regenerado (3 yaml cambiaron; conteos sin cambio).

**S88.6 (ESCALA-125)**
- `next_sheet` en el último paso: swt → differentiating-activities → core-purpose → bhag → vivid-vision → fanocracy → life-purpose → vision-summary.
- `tests/fixtures/workbook-2026-coverage.yaml`: 10 ejercicios en orden y 24 de 24 páginas (hoja o `no_exercise`), `pending: []`.
- Páginas con la forma de E87: `{page, class: tool|no_tool, nodes, reason}` (`reason` obligatorio en `no_tool`); lista aparte `exercises`.
- `tests/test_e88_workbook_coverage.py`: `check_coverage(..., frozen_pending=frozenset())` devuelve `[]`; la cadena `next_sheet` sigue `exercises` en orden.
- `tests/test_e88_strategy_day_path.py`: el dueño llena las 9 hojas en orden; aparecen los 10 prompts; cada `save` menos el último dice «Siguiente hoja» correcta; 9 vistas. Un caso con SWT ya completada: se reabre y el recorrido sigue (PAT-227).
- `escala-skills/escala-worksheet/SKILL.md`: sección «Strategy Day 2026» (empieza en `worksheet-swt`, sigue «Siguiente hoja»).
- Mapa E6 regenerado (8 yaml con `next_sheet`; conteos 93/89 sin cambio).
- Instalación verificada (design.md sección 9): con la épica en `main` en GitHub, en la Mac de Eduardo `/escala-update`; desde su carpeta ESCALA, `list` muestra 26 hojas y `start worksheet-swt` muestra «Arranque con IA». Se anotan fecha y hash instalado en el cierre.

## Decisiones tomadas (Eduardo puede cambiarlas)

- Id `worksheet-bhag`; nombre visible «Meta grande (BHAG)». BHAG no está vetada en `governance/public-boundary.yaml`; `opsp.yaml` y `7-strata.yaml` ya la usan. El Resumen de visión sigue sin la palabra.
- Plazo de la meta grande: 10 a 30 años (workbook 2026).
- Prompt de Fanocracy fiel al workbook (7 de 9 principios); los 9 en la guía. Personal Why vive en el área people.
- Páginas solo en el mapa de cobertura (`tests/fixtures/`), nunca en hojas públicas. Sin imágenes ni PDF del workbook.
- Varios prompts: lista `extra_prompts` junto a `ai_prompt` (design.md D1–D3).
- AI Setup y Make Change Stick viven dentro de swt y vision-summary; no tienen hoja propia.
- Una hoja ya completada (p. ej. SWT 2025) se reabre con respaldo al hacer `start`; nada se borra.
- Resumen de visión: Cliente central pasa a opcional (no está en el recorrido 2026).

## Criterios de terminado

- 10 de 10 ejercicios con hoja en español y prompt 2026.
- Prueba de cobertura: 24 de 24 páginas mapeadas.
- Prueba de punta a punta del Strategy Day en verde.
- Cada hoja nueva: guía con ejemplo real, ≥3 consejos con fuente, vista que se abre sola, guardado md/yaml.
- Gates en verde: pruebas, tipos y lint.
- La ESCALA instalada de Eduardo trae las hojas nuevas (verificado, S88.6).
- Listo el domingo 22-nov-2026 (Strategy Day: lunes 23). Si el sábado S88.6 no ha empezado, se recorta primero el mapa de 24 páginas, no el recorrido ni la instalación.

### Machine
```yaml
modules_affected:
  - path: coaching/worksheet/
    change: modify
  - path: conocimiento/strategy/worksheets/
    change: modify
  - path: conocimiento/people/worksheets/life-purpose.yaml
    change: create
  - path: conocimiento/registry/worksheets.yaml
    change: modify
  - path: ontology/v2/e6-migration-map.json
    change: modify
  - path: tests/
    change: modify
  - path: escala-skills/escala-worksheet/SKILL.md
    change: modify
  - path: work/research/e88-tips/
    change: create
decisions:
  - id: D1
    choice: "extra_prompts [{title, text, at}] junto a ai_prompt sin cambio"
    rationale: "Compatible: ninguna hoja ni prueba actual cambia"
    constraint: "ai_prompt no se vuelve lista; page rechazado"
  - id: D2
    choice: "Recorrido por next_sheet; orden y 24 páginas en tests/fixtures/workbook-2026-coverage.yaml"
    rationale: "Reusa el motor; páginas fuera de lo público"
    constraint: "Sin yaml de recorrido en conocimiento/; sin páginas en hojas"
  - id: D3
    choice: "worksheet-bhag con nombre «Meta grande (BHAG)», 10–30 años"
    rationale: "BHAG no vetada en public-boundary"
    constraint: "vision-summary.yaml sin BHAG"
  - id: D4
    choice: "start reabre una hoja completada con respaldo; save nombra la siguiente hoja"
    rationale: "Sin esto el Strategy Day se detiene en hojas 2025 guardadas y el chat no dice qué sigue"
    constraint: "Nunca borrar ni sobrescribir una hoja completada sin respaldo"
constraints:
  - "Cada yaml tocado en conocimiento/ regenera e6-migration-map (design.md sección 7); yaml nuevo también sube conteos (PAT-222)"
  - "Fusiones en serie; regenerar el mapa E6 tras traer la rama destino"
  - "Revisar public-boundary antes de llaves nuevas (PAT-221)"
  - "Prueba de punta a punta del Strategy Day (PAT-227)"
  - "Sin nodos nuevos en ontology/v2/"
  - "Todo implementable al 22-nov-2026"
```
