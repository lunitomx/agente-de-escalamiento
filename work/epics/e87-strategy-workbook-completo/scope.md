---
epic_id: E87
title: Strategy workbook completo — todas las herramientas del workbook, con guía, tips y vista visual
status: designed
jira_key: "ESCALA-107"
created: 2026-10-20
designed: 2026-10-20
revised: 2026-10-20 (después de la revisión adversaria; consistencia final en write-design)
source: metodologias que debes tener llenadas/EOA Strategy 2025 Participant Workbook (1).pdf
components_touched: conocimiento, coaching/worksheet, coaching/dashboard/boards, escala-skills
change_mode: additive
---

# Scope E87

## Jira

Epic: ESCALA-107

## Objetivo

Que ESCALA cubra todas las herramientas del workbook de Strategy (38 páginas). Cada herramienta lleva una guía de llenado paso a paso con un ejemplo real, tips profesionales investigados y, al terminar, una vista HTML que se abre sola más su gemelo Markdown. Cierra la brecha que dejó E6 (prometió 34 hojas, cerró con 15).

## Decisiones del dueño y del orquestador (2026-10-20)

- Alcance: solo el workbook de Strategy. People, Execution y Cash quedan fuera.
- El Plan Personal de Una Página y los tableros de visión (p. 30-33) entran. Se **extiende** la hoja `worksheet-oppp` que ya existe; no se crea otra.
- Vision Summary: E61 (ESCALA-29) es dueña de la ontología. E87 solo agrega guía de llenado y vista, con prueba de alineación de campos.
- La tarjeta de Caja de arena se corrige según p. 28: DÓNDE, QUÉ, canales y pronóstico a 3-5 años.
- El Strategy Canvas del workbook es el lienzo de 4 piezas de Scaling Up (p. 7 y 12). No es el de Océano Azul.
- Fuente canónica del conocimiento: `conocimiento/`. E87 no agrega archivos bajo `.scaleup/`.
- No se copian imágenes del workbook. El contenido se parafrasea en español y cita página.
- Simple primero: se reutilizan el registro de hojas, el motor `coaching/worksheet/` y el renderizador de E84.

## Criterios de aceptación de cada historia de herramienta (S87.4 a S87.9)

1. **Guía de llenado** paso a paso, con un ejemplo real (empresa mexicana ficticia pero concreta) en cada paso.
2. **Tips profesionales investigados** que vienen de S87.3, al menos 3, cada uno con su fuente citada.
3. **Vista visual abierta al terminar.** Al guardar, el motor escribe la vista HTML y devuelve `open_cmd`. El skill `escala-worksheet` corre `open` (macOS) o `xdg-open` (Linux). Si no puede, muestra el `.md` en el chat y da su ruta. Prueba: el guardado de ejemplo devuelve `open_cmd` con la ruta del HTML escrito.
4. **Persistencia en md/yaml.** Las respuestas quedan en `.escala/my-company/worksheets/<hoja>.yaml` y la vista tiene su gemelo `.md`. Prueba: los tres archivos existen después del guardado.
5. Su prompt de IA del workbook, parafraseado, con número de página, cuando el workbook trae uno para esa herramienta (`ai_prompt.page` dentro de `source.pages`).
6. Sus páginas salen de la lista de pendientes de la prueba de cobertura (S87.1).

## Historias

| Historia | Jira | Entrega | Tamaño | Depende de | Estado |
|---|---|---|---|---|---|
| S87.1 | ESCALA-108 | Mapa versionado de las 38 páginas y prueba de cobertura. Lista de pendientes que solo puede encoger. Corrige la tarjeta de Caja de arena (p. 28). Prueba "E87 no agrega archivos bajo `.scaleup/`". Prueba de cero imágenes. | 3 | — | cerrada |
| S87.2 | ESCALA-109 | Raíz única del conocimiento (mira el archivo del registro, no el directorio). Contrato de herramienta (`ToolGuide`). Vista HTML + MD con `open_cmd`. Reescritura del skill `escala-worksheet` con el paso de abrir. Se valida con la hoja existente de Cliente central. | 8 | S87.1 | cerrada |
| S87.3 | ESCALA-110 | `/rai-research` para 8 herramientas: BMC, Strategy Canvas de Scaling Up (4 piezas), Promesa de marca, Cliente central, Actividades diferenciadoras, Caja de arena, Vision Summary, Plan Personal y tableros de visión. Al menos 3 hallazgos triangulados por herramienta. | 5 | — | cerrada |
| S87.4 | ESCALA-111 | BMC de 9 bloques, puente a Scaling Up (p. 8), prompt (p. 9), lienzo (p. 10), lista de verificación (p. 11). | 5 | S87.2, S87.3 | pendiente |
| S87.5 | ESCALA-112 | Promesa de marca: 1 principal + 2 de apoyo con medida, Count On / Expect / Unique, 3 pruebas, antipromesas y compensaciones, prompt (p. 20). | 3 | S87.2, S87.3 | pendiente |
| S87.6 | ESCALA-113 | Cliente central: gráfica "¿Está claro tu QUIÉN?" y personas ejemplo (p. 13-14), las 3 preguntas (p. 20) y el prompt (p. 16). Hoja nueva de Actividades diferenciadoras con competidores y 4 ejes (p. 25) y prompt (p. 26). | 5 | S87.2, S87.3 | pendiente |
| S87.7 | ESCALA-114 | Hoja de Caja de arena con pronóstico a 3-5 años y prompt (p. 28-29). Strategy Canvas de una hoja (p. 7, 12) que lee las 4 piezas con el contrato `derived_from` y muestra "Falta: …" si una hoja origen no está llena. | 5 | S87.4, S87.5, S87.6 | pendiente |
| S87.8 | ESCALA-115 | Hoja de Vision Summary (p. 36) con `ontology_ref: tool.vision-summary`, probada contra `s64.1.json` y los campos de E65. Prompt de 10 tareas y compromiso (p. 34-35). | 3 | S87.7 | pendiente |
| S87.9 | ESCALA-116 | Extiende `worksheet-oppp`: 8 columnas × 4 filas de la p. 32 (p. 30-32) y tableros de visión con su prompt (p. 33). Corrige la tarjeta `people/tools/oppp.yaml`. | 3 | S87.2, S87.3 | cerrada |

Tips S87.3: 24 de 42 trianguladas por familia. Faltan fuentes para Vision Summary (1) y Plan personal/OPPP (2): S87.8 y S87.9 investigan fuentes fuera de las familias Scaling Up y EOS hasta llegar a 3 y quitan su SHORTFALL.

Total: 9 historias, 40 puntos (antes 34: S87.2 sube de 5 a 8, S87.3 de 3 a 5, S87.8 de 2 a 3).

S87.2 es la más pesada. Si en el plan no cabe en una sesión, se parte en "raíz + contrato" (3) y "vista + skill" (5).

## Olas (qué puede correr en paralelo)

1. **Ola 1:** S87.1 ∥ S87.3.
2. **Ola 2:** S87.2 (necesita S87.1).
3. **Ola 3:** S87.4 ∥ S87.5 ∥ S87.6 ∥ S87.9 (necesitan S87.2 y S87.3).
4. **Ola 4:** S87.7 (necesita S87.4, S87.5 y S87.6: `derived_from` valida que cada hoja origen, también `worksheet-bmc`, exista en el registro).
5. **Ola 5:** S87.8 (necesita S87.7).

## Criterios de terminado de la épica

- Prueba de cobertura: 38 de 38 páginas mapeadas a un nodo existente o marcadas como no herramienta. La lista de pendientes queda vacía.
- Cada hoja nueva o extendida cumple los 6 criterios de aceptación de arriba, con prueba.
- `conocimiento/registry/worksheets.yaml` lista las hojas nuevas y `total_worksheets` coincide con la lista.
- Desde el repo, `/escala-worksheet` lista todas las hojas (hoy 0).
- Ninguna imagen ni PDF del workbook en el repo (prueba). Ningún archivo nuevo bajo `.scaleup/` (prueba).
- `uv run rai gate check --all` pasa.

## Fuera de alcance

- People, Execution y Cash del mismo workbook (el Plan Personal entra porque está en el workbook de Strategy).
- Nodos nuevos en `ontology/v2/` para Vision Summary (es de E61).
- Reescribir los 5 tableros web de `escala_server/static/dashboards/strategy/`.
- Código que publique un artefacto de Claude. La sesión puede publicar el HTML; el código solo lo escribe en disco y devuelve `open_cmd`.
- Empaquetar `conocimiento/` en la rueda. Hoy la rueda no lo lleva; funciona solo con la instalación editable de `install.sh`. Estacionado.
- Unificar o retirar `.scaleup/knowledge/strategy/` (18 diferencias previas).

### Machine
```yaml
stories:
  - {id: S87.1, jira: ESCALA-108, size: 3, depends_on: []}
  - {id: S87.2, jira: ESCALA-109, size: 8, depends_on: [S87.1]}
  - {id: S87.3, jira: ESCALA-110, size: 5, depends_on: []}
  - {id: S87.4, jira: ESCALA-111, size: 5, depends_on: [S87.2, S87.3]}
  - {id: S87.5, jira: ESCALA-112, size: 3, depends_on: [S87.2, S87.3]}
  - {id: S87.6, jira: ESCALA-113, size: 5, depends_on: [S87.2, S87.3]}
  - {id: S87.7, jira: ESCALA-114, size: 5, depends_on: [S87.4, S87.5, S87.6]}
  - {id: S87.8, jira: ESCALA-115, size: 3, depends_on: [S87.7]}
  - {id: S87.9, jira: ESCALA-116, size: 3, depends_on: [S87.2, S87.3]}
total_points: 40
waves:
  - [S87.1, S87.3]
  - [S87.2]
  - [S87.4, S87.5, S87.6, S87.9]
  - [S87.7]
  - [S87.8]
modules_affected:
  - path: conocimiento/strategy/workbook-coverage.yaml
    change: create
  - path: conocimiento/strategy/worksheets/
    change: modify
  - path: conocimiento/strategy/tools/sandbox.yaml
    change: modify
  - path: conocimiento/strategy/concepts/brand-promise.yaml
    change: modify
  - path: conocimiento/people/worksheets/oppp.yaml
    change: modify
  - path: conocimiento/people/tools/oppp.yaml
    change: modify
  - path: conocimiento/registry/worksheets.yaml
    change: modify
  - path: coaching/worksheet/
    change: modify
  - path: coaching/dashboard/boards/render.py
    change: modify
  - path: escala-skills/escala-worksheet/SKILL.md
    change: modify   # reescritura completa; los pasos actuales citan rutas que no existen
  - path: work/research/e87-tips/
    change: create
  - path: tests/test_e87_workbook_coverage.py
    change: create
decisions:   # mismos ids que design.md (D1-D9)
  - id: D1
    choice: "conocimiento/ es la copia canónica; E87 no agrega archivos bajo .scaleup/"
    rationale: "La exportación pública incluye conocimiento/ y excluye .scaleup/ (tests/test_public_export.py:224,246); nadie en producción lee .scaleup/knowledge/strategy/"
    constraint: "Prueba con lista congelada de archivos rastreados bajo .scaleup/"
  - id: D2
    choice: "Pendientes de cobertura en lista que solo puede encoger"
    rationale: "S87.1 prueba la brecha sin dejar la suite en rojo; patrón de S86.27"
    constraint: "Ninguna historia agrega páginas a pendientes"
  - id: D3
    choice: "Raíz del conocimiento por el archivo registry/worksheets.yaml; registro y node_path con la misma raíz"
    rationale: ".escala/knowledge/ existe sin registry/"
    constraint: "No duplicar conocimiento/ en .escala/"
  - id: D4
    choice: "Extensión compatible del YAML de hoja validada con Pydantic ToolGuide"
    rationale: "Las 15 hojas viejas siguen con metadata.fields"
    constraint: "Sin framework nuevo ni motor paralelo"
  - id: D5
    choice: "Vista nueva coaching/worksheet/view.py que reutiliza helpers públicos de boards/render.py"
    rationale: "Board exige números; una hoja de estrategia es texto"
    constraint: "Tablero E84 sin cambio de comportamiento"
  - id: D6
    choice: "Vista abierta por el skill con open/xdg-open; plan B: mostrar el .md"
    rationale: "Sin paso explícito nadie abre la vista"
    constraint: "El código Python no ejecuta procesos"
  - id: D7
    choice: "Vision Summary: hoja en conocimiento/ con ontology_ref y maps_to, probada contra s64.1.json y E65"
    rationale: "E61 es dueña de la ontología; s64.1.json no trae campos"
    constraint: "No tocar ontology/v2/"
  - id: D8
    choice: "Plan Personal: extender worksheet-oppp"
    rationale: "Ya existe"
    constraint: "Conservar id, decision people y metadata.fields"
  - id: D9
    choice: "Strategy Canvas = lienzo de 4 piezas de Scaling Up con derived_from; sin Océano Azul"
    rationale: "PDF p. 7 y p. 12"
    constraint: "derived_from solo lee; falta visible como 'Falta: <campo> de <hoja>'"
constraints:
  - "Cero imágenes o PDF del workbook en el repo"
  - "Todo texto de herramienta en español parafraseado con número de página"
  - "Cada tip cita una fuente de S87.3"
  - "Cada historia de herramienta: guía con ejemplo real, 3+ tips citados, vista abierta al terminar, persistencia yaml+md"
```
