## Phase: start (S87.7 · ESCALA-114) — 2026-10-20

- Worktree `story/s87.7/caja-de-arena` desde main 0b72e7ee; sync-dev-branch: skipped (in-worktree).
- Jira ESCALA-114: Tareas por hacer → En curso.
- `raise_story_open` no se usó: la rama ya existía (crearía `branch-exists`). Story y scope escritos a mano
  como en S87.4-S87.6: `work/epics/e87-strategy-workbook-completo/stories/s87.7-{story,scope}.md`.
- Seguimientos del orquestador agregados al scope (4): encabezado paso 1 en inglés, `find_worksheet` sin
  `name_es`, "?.:" en Revisión Final, prompt de IA oculto. Causas ubicadas en `coaching/worksheet/__init__.py`.
- Hallazgos: C6 dice `actividades` pero el id real es `actividades-elegidas`. Tips triangulados:
  sandbox f2/f3/f4, strategy-canvas f2/f3/f4. Tarjeta `tools/sandbox.yaml` ya corregida (S87.1).
  `total_worksheets` hoy 18 → 20.

## Phase: design (S87.7 · ESCALA-114) — 2026-10-20

- Diseño: `work/epics/e87-strategy-workbook-completo/stories/s87.7-design.md` (moderate, 5 pts).
- D1: el lienzo es vista derivada + 1 paso propio `decision` ("¿a qué le dices que no?"). Motivo: `Guide.steps` exige ≥1
  y el flujo start→step→Revisión→save ya está probado; solo-lectura pediría una rama nueva del motor.
- D2-D5: `DerivedSource.title`; autoderivación en `ToolGuide` (campo `id`), registro/campos en `__init__.derived_errors`;
  solo hojas `status: completed`; "Falta" por campo; `required: false` sin guardar → se omite; `derived_blocks` puro en view.py.
- Id real usado: `actividades-elegidas`.
- D7/D8: registro gana `name_es` corto + `time_es` (20 entradas); mapas de dificultad/decisión; un solo buscador
  (`engine.find_worksheet`, sin acentos) al que delega `__init__`. D9 `label_heading` (Revisión + .md). D10 prompt de IA visible.
- Tips: los 6 usados ya tenían ≥3 familias. Complemento fuera de Scaling Up para sandbox f3 (Danish Lead Co.),
  strategy-canvas f2 (HBR Coherence Premium) y f3 (Umbrex); `added_by: S87.7`. test_e87_research_tips: 44 de 44.
- Hotspots listados: registro 18→20, test_root, test_guide:187, test_view, cobertura pending 7/12/28/29, E6 85/81 regenerar.
- Grafo sin patrones útiles; sin drift-hotspots.json; portafolio additive.

## Phase: implement (S87.7 · ESCALA-114) — 2026-10-20

- T1 721fd2d7: búsqueda por nombre en español (`engine.find_worksheet`, sin acentos) y paso 1 en español; `name_es`/`time_es` en 20 entradas.
- T2 906f25e3: `label_heading` (sin "?:" ni "?.:") y prompt de IA en Revisión Final, HTML y .md.
- T3 da731833: `DerivedSource.title`, autoderivación rechazada, `derived_errors` contra registro y pasos.
- T4 7408ba1b: hoja Caja de arena (4 pasos, 3 tips, prompt, lienzo).
- T5 e06744fa: lienzo de estrategia (5 fuentes, BMC opcional, paso `decision`); lee solo hojas `completed`.
- T6 e80088d9: cobertura del workbook (7/12/28/29; pending solo 34), mapa E6 regenerado con su generador 87/83, SKILL.md.
- Pruebas: 3750 passed, 5 skipped (base 3709). ruff, format y pyright de coaching/worksheet: limpios.
- `rai gate check --all`: 4 de 51 fallan, las mismas de la línea base (domain-model, last-diff, graph, skill-cli-refint).
- Prueba del dueño en carpeta temporal: "promesa de marca" encuentra la hoja; encabezado en español;
  Caja de arena llena y guardada; Revisión con prompt; HTML y .md sin "?:"; el lienzo muestra Caja de arena y líneas "Falta".
- Observaciones: el resumen de Promesa de marca sigue en inglés (previo, fuera de alcance). Las líneas "Falta" muestran
  slug e id, como pide el diseño. El paso 1 dice "1-2 horas sin interrupciones" para toda hoja, incluso el lienzo (30-60 min).

## Phase: verify · quality-review (S87.7 · ESCALA-114) — 2026-10-21

- Veredicto: FAIL, 2 Critical. Artefacto: `work/epics/e87-strategy-workbook-completo/stories/s87.7-qr.md`.
- C1: el resumen del paso 1 sigue en inglés en 17 de 20 hojas (incluye Promesa de marca, el caso del seguimiento 1);
  la lista dice "Worksheets Disponibles"/"Worksheet". Arreglo: `summary_es` en el registro (patrón D7) + prueba de 20.
- C2: el paso 1 fija "1-2 horas sin interrupciones"; el lienzo dice 30-60 minutos arriba (15 de 20 hojas se contradicen).
  Arreglo: usar `_time_es(worksheet)`.
- Pasa: búsqueda en español (engine e __init__), sin "?:"/"?.:"/".:" en 20 de 20, prompt de IA en Revisión/md/html
  en 7 de 7, derived_from (solo completed, Falta por campo, no escribe origen, validaciones), mapa E6 regenerado
  idéntico 87/83, registro 20, tips ≥3 familias. 198 pruebas, ruff y pyright limpios; 7 de 7 mutaciones muertas.
- Recommended: "Falta" con claves (R1, diseño D4), "Esto ya llenaste:" con 0 llenas (R2), `##` bajo `###` (R3).

## Phase: implement · retry 1 tras VERIFY FAIL (S87.7 · ESCALA-114) — 2026-10-21

- C1 + C2 (e5c3fc11): `summary_es` propio, en español llano, en las 20 hojas del registro; el paso 1 lo usa
  (respaldo: `summary`). Lista: "Hojas disponibles", columna "Hoja". El paso 1 usa `_time_es` en lugar de "1-2 horas".
  Pruebas: 20 de 20 con resumen y tiempo propios; el lienzo no dice "1-2 horas". Un solo commit para los dos: ambos
  son el encabezado del paso 1 y la prueba parametrizada cubre los dos.
- Mapa E6: el sha del registro cambió; regenerado con `scripts/build_e6_migration_map.py` (solo esa línea).
- R1 (d76e3051): "Falta" muestra la pregunta del paso y "Llena la hoja <nombre> con /escala-worksheet <id>".
  `missing_source_text(question, sheet_name, sheet_id)`. Pruebas que fijaban el texto viejo actualizadas.
- R2 + R3 (86e43d55): con 0 piezas, "Todavía no llenas ninguna de estas piezas:". Bloques del paso 1 en `####`
  (`markdown_blocks(..., heading=)`); la vista y el `.md` siguen en `##`.
- Sorpresa: el generador del mapa E6 falla con "unable to produce a safe map" si el archivo de salida ya existe.
- Gates: 3776 pasan, 5 omitidas; ruff, format y pyright de `coaching/worksheet` limpios; mapa E6 idéntico al generado.
- Revisión del dueño (carpeta temporal): Promesa de marca y lienzo con encabezado en español, tiempo correcto
  (1-2 horas / 30-60 minutos) y líneas "Falta" legibles.
