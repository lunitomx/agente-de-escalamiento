# S87.8 (ESCALA-115) · Journal

## Phase: start (2026-10-20)

- Rama `story/s87.8/resumen-vision` y worktree ya existían (base main 0b72e7ee); no se creó otra. `raise_story_open` no se usó.
- Escritos a mano `stories/s87.8-story.md` (9 escenarios) y `stories/s87.8-scope.md`. Tamaño 3.
- Hallazgo: `vision-summary.md` tiene 1 de 5 hallazgos triangulados; `SHORTFALL = {"vision-summary": 1}` es la última entrada (S87.9 ya quitó la suya). Diseño debe correr `/rai-research` fuera de Scaling Up y EOS.
- Hallazgo: `ontology_ref` y campos de E65 verificados: `tool.vision-summary` en `s64.1.json`; `purpose, customer, differentiator, future_direction` en `validators/oppp_vision_artifacts.py`.
- Hallazgo: `customer` depende de `derived_from` (S87.7). La historia no puede cerrar su prueba C7 sin S87.7 fusionada.
- Registro hoy en 18 hojas; con S87.7 (20) más esta, probable 21. Choques con S87.7 listados en el scope.
- Jira ESCALA-115 movida a "En curso".

## Phase: design (2026-10-20)

- Diseño en `stories/s87.8-design.md`. Complejidad simple, 6 tareas (T0 fusiona S87.7 primero).
- Investigación hecha: `vision-summary.md` pasa de 1 a 5 hallazgos triangulados, con fuentes fuera de Scaling Up y EOS (`added_by: S87.8`). `SHORTFALL` quedó vacío; `test_e87_research_tips.py` 44 de 44.
- Hallazgo: `GuideStep` tiene `extra="forbid"` y no tiene `maps_to`. D1 agrega `maps_to` opcional en `guide.py` (desviación aceptada del alcance "motor sin cambios").
- D2: `customer` por `derived_from` con `into: customer`, campos `quien-es` y `necesidad` de `worksheet-core-customer`.
- D3: solo el Cliente central se deriva; valores, meta grande y prioridades viven en hojas sin `guide`.
- Choques con S87.7 listados en el diseño. Registro esperado: 21. Mapa E6 esperado: 88 y 84.

## Phase: implement (2026-10-21)

- T0: `origin/main` (S87.7, 6bca96fc) fusionada sin conflictos. Suite completa: 3776 pasan, 5 omitidas.
- T1: `GuideStep.maps_to` agregado. **Desviación:** el diseño decía `list[Slug]`, pero el campo de E65 es `future_direction` (guion bajo) y `Slug` lo rechaza. Se usa `FieldName` en snake_case (`^[a-z0-9]+(_[a-z0-9]+)*$`). `future-direction`, `Purpose` y vacío se rechazan.
- T1 se commiteó a mano (8ecf3cc7) antes de cargar `raise_task_complete`; T2 en adelante con la herramienta.
- T2: hoja `vision-summary.yaml` (10 pasos, 6 tips triangulados, `derived_from` Cliente central → `customer`, layout cards, 5 secciones) + 7 pruebas: contrato, C7 (ontología y campos de E65), compromiso y prompt de 10 tareas, vocabulario público, sin secuencias de 10 palabras del workbook. El prompt parafrasea "menos de una hora por semana y casi sin dinero" del workbook (p. 34) en palabras propias.
- T3: entrada del registro con `name_es`, `time_es` y **`summary_es`** (el diseño no lo nombraba; S87.7 lo exige en cada entrada para el paso 1). `total_worksheets` recontado: 21 (Estrategia 10). Conteos 21 en `test_root.py` y `test_guide.py`; búsqueda "resumen de vision" agregada a `test_owner_spanish.py`.
- T4: recorrido de punta a punta en `test_engine_guide.py` (con y sin Cliente central: bloque derivado, "Falta: ¿Quién es…? Llena la hoja Cliente central con …", Revisión Final con prompt, guardar → yaml + html + md, `open_cmd`, orden de bloques, respuesta de varias líneas) y prueba de vista en `test_view.py`. Verde sin tocar código de motor (S87.7 ya lo trae). Recorrí a mano la salida del dueño de la hoja nueva (paso 1, pasos 2 y 11, Revisión Final) y el paso 1 de las 21 hojas: cada una con su resumen y su tiempo (PAT-241).
- Sorpresa: `raise_task_complete` no puede preparar `work/` (lo ignora `.gitignore`); el journal se prepara antes con `git add -f`. Con `gate_scope` en un directorio `tests/`, la puerta de tipos busca un `src/` que no existe; usar el directorio del paquete (`coaching/worksheet`).
- T5: p. 34, 35 y 36 nombran `worksheet-vision-summary`; `pending: []` (la épica ya no tiene páginas pendientes). Mapa E6 regenerado con `scripts/build_e6_migration_map.py` en el scratchpad y copiado: 88 entradas, 84 en espera de evidencia (+1 hoja, sha del registro). **Desviación:** `test_real_pending_is_one_page_per_line` buscaba la línea literal `pending:`; con la lista vacía se escribe `pending: []`, y la guarda ahora acepta esa forma.
- Puertas: suite completa 3797 pasan + 1 corregida (ver arriba), 5 omitidas; ruff check, ruff format y pyright en verde.
