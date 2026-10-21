# E87 · Mapa de capacidades (evidencia previa al diseño)

Jira: ESCALA-107 · Commit base: 5172c03e · Fecha: 2026-10-20
Fuente leída: PDF de 38 páginas (texto por página con `pdftotext`) y `metodologias_parsed/strategy_workbook.md`. No se copió ninguna imagen.

## Resumen en cinco líneas

1. De las 9 herramientas que pide el dueño, ESCALA tiene hoy tarjetas para 4 conceptos (Cliente central, Promesa de marca, Actividades diferenciadoras, Caja de arena) y ninguna para BMC, Strategy Canvas, puente BMC, ni preguntas del Cliente central.
2. Vision Summary ya existe como herramienta en la ontología v2 (`tool.vision-summary`, release s64.1) y la cubre E61 (ESCALA-29, en curso). E87 no debe duplicarla: debe enlazarla y agregar guía y vista.
3. Lo que ya existe para mostrar resultados: el patrón de E84 (`coaching/dashboard/boards/render.py`): un HTML autocontenido más su gemelo Markdown. Se reutiliza.
4. Los 5 tableros de `dashboards/strategy/` son clones de una plantilla de 189 líneas; solo cambian título y 3 claves. No son vistas reales de una hoja (ver gaps G3).
5. El workbook tiene una herramienta que el brief no lista: el Plan Personal de Una Página y los tableros de visión (p. 30-33). Hay que decidir si entra o se declara fuera de alcance.

## Parte 1 · Hallazgos del gemba

### Conocimiento existente (Strategy)

| Pieza | Dónde | Estado | Disposición |
|---|---|---|---|
| Conceptos: Cliente central, Promesa de marca, Actividades diferenciadoras, BHAG, Propósito | `conocimiento/strategy/concepts/` | Existen. Sin números de página del workbook. | extend |
| Herramientas: OPSP, 7 Estratos, SWT, Caja de arena, Profit per X, X-Factor | `conocimiento/strategy/tools/` | Existen. | extend (Caja de arena) |
| Hojas: opsp, swt, 7-strata, core-customer | `conocimiento/strategy/worksheets/` | Solo 4. No hay hoja de Promesa, Actividades ni Caja de arena. | new |
| Registro de hojas | `conocimiento/registry/worksheets.yaml` | 15 hojas (Strategy: 4). `total_worksheets: 15` fijo. | extend |
| Copia espejo | `.scaleup/knowledge/strategy/` | Difiere de `conocimiento/strategy/` en 18 archivos; la copia `.scaleup` trae bloque `source:` con línea del workbook. | decidir autoridad en diseño |
| Vision Summary | ontología v2 `tool.vision-summary` (release s64.1); E61 | Cubierto por E61 (en curso). | reuse, coordinar |
| Tarjetas con cita de página | ninguna | Las tarjetas citan `file_line` del .txt, no página del PDF. | new (regla de E87) |

### Contenido de tarjetas que contradice el workbook

- `tools/sandbox.yaml` define la Caja de arena como "WHO y WHERE" (geografía y demografía). El workbook p. 28 la define con 4 preguntas: DÓNDE (zonas), QUÉ (3-5 categorías), A QUIÉN (canales de distribución) y PRONÓSTICO a 3-5 años. El cliente va en otra pieza (Cliente central). Corregir en S87.1.
- La Promesa de marca existente tiene una frase de garantía que el workbook p. 17-21 no usa como núcleo; el núcleo es 3 promesas con medida, Count On / Expect / Unique y tres pruebas.

### Motor de hojas y skills

| Pieza | Dónde | Hallazgo |
|---|---|---|
| Motor | `coaching/worksheet/` (`engine.py` 49 líneas, `formatter.py`, `__init__.py` 437) | Carga hojas del registro; guía en texto; guarda YAML por empresa. Sin render visual ni tips. |
| Skill | `escala-skills/escala-worksheet/SKILL.md` | Pasos list/start/step/save. Sirve de entrada para las hojas nuevas. |
| Skills Strategy | `escala-strategy`, `-opsp`, `-7strata`, `-swt`, `-swot`, `-journey`, `-research` | Ninguno guía Promesa, Actividades, Caja de arena, BMC o Strategy Canvas. |
| Investigación | `escala-strategy-research`, `rai-research` | Disponible para los tips de S87.8. |

### Dónde se dibuja un resultado hoy (pregunta del dueño)

| Pieza | Dónde | Qué hace | Disposición |
|---|---|---|---|
| Tablero local E84 | `coaching/dashboard/boards/render.py` (`render_html`, `render_markdown`, `board_path`) | HTML autocontenido, sin JS/CDN/imágenes, escapado, determinista, legible en teléfono, gemelo Markdown, escritura atómica. Falta de dato dice "Falta: X". | **reuse** como base de la vista |
| Reporte E38 | `escala_server/financial/report.py` (`write_cash_report`) | HTML + MD + JSON por hash. Solo Cash. | reuse del patrón |
| Exportador | `coaching/export/__init__.py` | Plan de acción en Markdown, 5 secciones. | extend opcional |
| Tableros web | `escala_server/static/dashboards/strategy/{bmc-board,brand-promises,core-customer,diff-activities,sandbox}.html` | 5 archivos de 189 líneas, idénticos salvo título y 3 claves; leen `/api/worksheets/strategy/<tool>` (server.py:305) y requieren el servidor. `bmc-board` muestra 3 campos (cliente, promesa, territorio), no 9 bloques. | extend solo si el puente lo exige |
| Artefacto de Claude | herramienta `Artifact` de Claude Code | No hay código en el repo que lo use. | decisión de diseño (ver G4) |

## Parte 2 · Barrido del backlog (Jira ESCALA, adaptador jira)

| Clave | Estado | Relevancia | Disposición |
|---|---|---|---|
| ESCALA-107 | En curso | Esta épica (E87). | n/a |
| ESCALA-29 (E61) | En curso | Corpus Strategy verificado: Vision Summary, OPSP, cliente, promesas, diferenciadores. Mismo dominio, otra fuente (libro y workbook). | approved_overlap: no duplicar extracción; consumir sus recibos |
| ESCALA-37 (E73) | Finalizada | Asesor adaptativo de tableros. | reuse |
| ESCALA-22 (S55.2) | Finalizada | Tablero de evidencia previo al diagnóstico. | reuse del patrón |
| ESCALA-17 (S48.3) | Finalizada | Auditoría Bitter Pill de Cash y Strategy. | contexto |

Revisadas por archivo (sin clave Jira propia): E6 (cerró con 15 hojas de 34), E15 strategy-dashboards, E84 (S84.4 es el render), E59/E64 (ontología v2).

## Parte 3 · Validación del alcance (scope.md)

| Historia | Veredicto | Nota |
|---|---|---|
| S87.1 inventario y cobertura | Confirmada, va primero | Ya hay un borrador de 38 páginas en `evidence/predesign.json` (campo `page_map`); S87.1 lo verifica. |
| S87.2 BMC + puente | Confirmada | Nada existe. p. 7-11. |
| S87.3 Strategy Canvas | Confirmada | Nada existe. p. 7 y 12 (p. 12 es una hoja de una página con los cuatro bloques). |
| S87.4 Promesa completa | Corregir páginas | Brief dice p. 16-21; el contenido está en p. 17-21 (ejemplos 17-19, pruebas y preguntas 20, hoja 21). p. 16 es ejercicio de Cliente central + prompt de IA. |
| S87.5 Cliente central y Actividades | Corregir páginas | Preguntas del Cliente central están en p. 20 (3 preguntas). La hoja de Cliente central es p. 15-16; Actividades p. 22-27 (hoja p. 25). |
| S87.6 Vision Summary | Reducir | Ya en ontología v2 y E61. Solo guía y vista. Páginas reales: 7, 35, 36. |
| S87.7 Vista visual | Confirmada | Reutilizar `render.py`. |
| S87.8 Tips | Confirmada | `rai-research`. |
| Sin historia | Pronóstico de Caja de arena (p. 28) y Caja de arena completa (p. 28-29) | Asignar a S87.3 o S87.5. |
| Sin historia | Plan Personal de Una Página y tableros de visión (p. 30-33) | Fuera de alcance del brief; decisión del dueño. |

## Brechas (gaps)

| Id | Brecha | Efecto |
|---|---|---|
| G1 | No hay mapa página a tarjeta; las tarjetas citan línea del .txt | Sin él, se repite S6.3. |
| G2 | Tarjeta de Caja de arena contradice p. 28 | Una guía basada en ella enseñaría mal la herramienta. |
| G3 | Los 5 tableros web son una plantilla clonada y leen una API que exige servidor | No sirven como vista "al terminar el llenado" en una instalación local. |
| G4 | El repo no tiene código que abra un artefacto de Claude | La vista se hace con HTML local de `render.py`; el artefacto de Claude es opción de la sesión, no del código. Decidir en diseño. |
| G5 | `conocimiento/strategy/` y `.scaleup/knowledge/strategy/` difieren en 18 archivos | Riesgo de editar la copia equivocada. |
| G6 | Herramienta de p. 30-33 sin dueño | Decisión del dueño: incluir o declarar no alcance. |
| G7 | Los prompts de IA no tienen tarjeta; están en p. 9, 16, 20, 26, 29, 33, 34 | Se agrega un tipo de contenido "prompt" por herramienta. |

## Nota de método

El flujo estándar de la habilidad asume Python en `packages/` y ejecuta `vulture` y consultas al grafo. Este repo no tiene `packages/` con el dominio; el recorrido fue por lectura directa de archivos y por la lista de Jira. No se llamó al grafo ni al portafolio.
