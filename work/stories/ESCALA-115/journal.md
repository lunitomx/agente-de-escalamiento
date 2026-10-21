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
