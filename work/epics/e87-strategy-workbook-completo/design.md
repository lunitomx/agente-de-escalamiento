# E87 · Diseño — Strategy workbook completo

Jira: ESCALA-107 · Fecha: 2026-10-20 · Entradas: brief.md, scope.md, capability-map.md, evidence/predesign.json.

## Flujo en una pantalla

```
Dueño: "/escala-worksheet promesa de marca"
   │
   ▼
Motor de hojas (coaching/worksheet) ── lee ──► conocimiento/registry/worksheets.yaml
   │                                           conocimiento/strategy/worksheets/<hoja>.yaml
   │   por cada paso: pregunta + cómo + ejemplo real + tips con fuente
   ▼
Dueño responde paso a paso  (prompt de IA del workbook disponible en cada hoja)
   │
   ▼  action=save
.escala/my-company/worksheets/<hoja>.yaml          (respuestas, ya existía)
.escala/my-company/vistas/AAAA-MM-DD-<hoja>.html   (nuevo, autocontenido)
.escala/my-company/vistas/AAAA-MM-DD-<hoja>.md     (nuevo, gemelo)
   │
   ▼
El skill le dice al agente: abre el HTML. La sesión de Claude puede además publicarlo como artefacto.
```

## Hallazgos del gemba (leídos en código, 2026-10-20)

1. **El motor de hojas hoy devuelve 0 hojas.** `coaching/worksheet/__init__.py` lee `.escala/knowledge/registry/worksheets.yaml`. Ese archivo no existe en el repo; el registro vive en `conocimiento/registry/worksheets.yaml`. Comprobado: `list_worksheets()` → 0 y `run({"action":"list","base_path":"."})` → tabla vacía. Ningún instalador ni `escala_server` copia `conocimiento/` a `.escala/knowledge/`. Sin arreglar esto, ninguna hoja nueva llega al dueño. Se arregla en S87.2.
2. **Copia canónica = `conocimiento/`.** `pyproject.toml` empaqueta `conocimiento/**/*.yaml`. `tests/test_public_export.py` exige `conocimiento` en la exportación y prohíbe `.scaleup`. La copia `.scaleup/knowledge/strategy/` es la de E6 (solo uso interno, `retrieval.py`). Los 18 archivos comunes ya difieren.
3. **El renderizador de E84 tiene forma de tablero de métricas.** `BoardRow` = nombre, valor, fuente, periodo, estado; el valor se pinta a 2rem y `save_board` rechaza un tablero sin números. Una hoja de estrategia es texto. Se reutiliza la parte común (escapado, filtro `FORBIDDEN`, CSS, aviso "Sólo en tu computadora", escritura atómica), no el modelo `Board`.
4. **El esquema de hoja es una lista de textos.** `metadata.fields` es `list[str]`; el motor arma un paso por campo. No hay dónde poner ejemplo, tips ni prompt.
5. La tarjeta `tools/sandbox.yaml` contradice p. 28 (define QUIÉN/DÓNDE). El cliente vive en Cliente central.
6. Grafo de RaiSE: 0 resultados para este dominio. Válido; no cambia el diseño.

## Componentes y contratos

### C1 · Mapa de cobertura (S87.1)

Archivo `conocimiento/strategy/workbook-coverage.yaml`:

```yaml
source: "EOA Strategy 2025 Participant Workbook"
total_pages: 38
pages:
  - page: 28
    class: tool            # tool | no_tool
    nodes: [worksheet-sandbox, tool-sandbox]
  - page: 37
    class: no_tool
    reason: "hoja de notas"
pending: [7, 8, 9, 10, 11, 12, 17, ...]   # solo puede encoger
```

Prueba `tests/test_e87_workbook_coverage.py`:

- Hay 38 entradas, páginas 1 a 38, sin repetir.
- Toda página `no_tool` tiene `reason`.
- Toda página `tool` que no está en `pending` tiene al menos un nodo, y cada nodo existe en `conocimiento/` y cita esa página en `source.pages`.
- Toda página de `pending` es `tool` (no se esconde una página `no_tool` ahí).
- `pending` es subconjunto de la lista congelada en la prueba; la lista congelada solo puede encoger.
- Cero archivos de imagen o PDF bajo `conocimiento/`, `escala-skills/` y `templates/` cuyo nombre o ruta venga del workbook. El PDF origen no se versiona.
- Sincronía: cada archivo de `conocimiento/strategy/` que E87 crea o modifica es idéntico en `.scaleup/knowledge/strategy/`. Las 18 diferencias previas van en una lista que solo puede encoger.

Ejemplo de falla esperada: si S87.4 agrega la hoja BMC pero olvida `source.pages: [10]`, la página 10 sale de `pending` y la prueba falla con "p. 10: worksheet-bmc no cita la página".

### C2 · Contrato de herramienta (S87.2)

Extensión compatible de la hoja YAML. Las 15 hojas viejas siguen funcionando con `metadata.fields`.

```yaml
id: worksheet-brand-promise
source:
  workbook: strategy-2025
  pages: [17, 18, 19, 20, 21]
guide:
  steps:
    - id: promesa-principal
      question: "¿Qué le prometes a tu Cliente central que nadie más le promete?"
      how: "Escribe una frase con un verbo y algo que se pueda medir."
      example: "Tortillería El Sol: 'Tu pedido llega antes de las 7:00 o no lo pagas'. Medida: % de pedidos a tiempo."
tips:
  - text: "Una promesa sin medida no se puede cumplir ni romper."
    source: "work/research/e87-tips/brand-promise.md#f3"
ai_prompt:
  page: 20
  text: "<paráfrasis en español del prompt de la p. 20>"
view:
  layout: cards            # cards | canvas
  sections: [...]          # agrupa pasos en bloques de la vista
```

Modelo Pydantic `ToolGuide` en `coaching/worksheet/guide.py` valida esto. Una hoja con `guide` exige: al menos un paso, `example` no vacío en cada paso, al menos 3 tips con `source`, y `source.pages`.

Cambios en el motor:

- Resolución del registro: primero `<base>/.escala/knowledge/` si existe (instalaciones viejas); si no, `conocimiento/` del paquete. Ejemplo: en el repo, `list_worksheets()` pasa de 0 a 15.
- `start`/`step`: si la hoja trae `guide.steps`, cada paso muestra pregunta, cómo, ejemplo y los tips de ese paso. Si no, se usa `metadata.fields` como hoy.
- `save`: además del YAML, llama a `render_worksheet_view` y devuelve las rutas en `artifacts.view`.

### C3 · Vista de hoja (S87.2)

`coaching/worksheet/view.py` con `render_html(sheet, answers) -> str`, `render_markdown(...) -> str` y `save_view(base, ...) -> list[Path]`.

- Reutiliza de `coaching/dashboard/boards/render.py`: `FORBIDDEN`, `LOCAL_ONLY`, `HIDDEN`, el CSS base y `_atomic_write`. Se vuelven públicos (`safe_text`, `atomic_write`, `BASE_CSS`) sin cambiar el comportamiento del tablero; `test_render.py` sigue igual.
- `layout: cards`: una tarjeta por sección, en una columna.
- `layout: canvas`: rejilla CSS (BMC de 9 bloques, Strategy Canvas de 4) que en el teléfono baja a una columna. Sin JavaScript, sin CDN, sin imágenes.
- Un campo vacío dice "Falta: <paso>. Cómo llenarlo: <how>".
- Determinista: mismos datos, mismos bytes.

### C4 · Tips investigados (S87.3)

`/rai-research` una vez por herramienta. Salida en `work/research/e87-tips/<herramienta>.md`, con hallazgos numerados (`#f1`, `#f2`…) y al menos 3 fuentes independientes por hallazgo usado. Herramientas: BMC (Strategyzer), Strategy Canvas / Océano Azul, Promesa de marca, Cliente central, Actividades diferenciadoras, Vision Summary, Plan Personal de Una Página. Las historias de herramienta copian a `tips:` solo hallazgos con triangulación y citan el ancla.

### C5 · Hojas por historia

| Historia | Hojas | Páginas | Layout |
|---|---|---|---|
| S87.4 | `worksheet-bmc` (9 bloques, puente, checklist) | 7-11 | canvas |
| S87.5 | `worksheet-brand-promise`; concepto `brand-promise` corregido | 17-21 | cards |
| S87.6 | `worksheet-core-customer` extendida; `worksheet-differentiating-activities` | 15-16, 20, 22-26 | cards |
| S87.7 | `worksheet-sandbox`; `worksheet-strategy-canvas` (lee las 4 hojas guardadas) | 7, 12, 28-29 | canvas |
| S87.8 | `worksheet-vision-summary` (enlaza `tool.vision-summary`) + prompts de 10 semanas | 34-36 | cards |
| S87.9 | `worksheet-one-page-personal-plan` + tableros de visión | 30-33 | canvas |

El puente BMC → Scaling Up (p. 8) es dato de la hoja BMC: cada bloque dice a qué hoja de Scaling Up lleva (Segmentos → Cliente central, Propuesta de valor → Promesa de marca, Actividades clave → Actividades diferenciadoras, Canales → Caja de arena). La vista lo muestra como "Siguiente paso: llena <hoja>".

El Strategy Canvas no pide los datos otra vez. Lee las respuestas guardadas de Cliente central, Promesa, Actividades y Caja de arena; lo que falte aparece como "Falta: …".

## Pruebas por historia (TDD)

- S87.1: la prueba de cobertura, la de sincronía, la de cero imágenes; la tarjeta de Caja de arena con las 4 preguntas de p. 28.
- S87.2: `list_worksheets()` > 0 desde el repo; `ToolGuide` rechaza un paso sin ejemplo; `save` escribe YAML + HTML + MD; el HTML no trae ningún token de `FORBIDDEN`; mismos datos dan mismos bytes; las 15 hojas viejas siguen cargando.
- S87.4 a S87.9: cada hoja nueva pasa `ToolGuide`; sus páginas salen de `pending`; un guardado de ejemplo produce la vista con todas sus secciones.

## Riesgos

- PRECAUCIÓN: cambiar la ruta del registro puede romper a clientes con `.escala/knowledge/` propio. Mitigación: esa ruta sigue primero.
- Repetir S6.3. Mitigación: S87.1 va primero y la lista `pending` hace visible lo que falta.
- Tips sin fuente. Mitigación: `ToolGuide` exige `source` en cada tip.

### Machine
```yaml
modules_affected:
  - path: conocimiento/strategy/workbook-coverage.yaml
    change: create
  - path: conocimiento/strategy/tools/sandbox.yaml
    change: modify
  - path: conocimiento/strategy/concepts/brand-promise.yaml
    change: modify
  - path: conocimiento/strategy/worksheets/
    change: modify
  - path: conocimiento/registry/worksheets.yaml
    change: modify
  - path: .scaleup/knowledge/strategy/
    change: modify
  - path: coaching/worksheet/__init__.py
    change: modify
  - path: coaching/worksheet/guide.py
    change: create
  - path: coaching/worksheet/view.py
    change: create
  - path: coaching/dashboard/boards/render.py
    change: modify
  - path: escala-skills/escala-worksheet/SKILL.md
    change: modify
  - path: work/research/e87-tips/
    change: create
  - path: tests/test_e87_workbook_coverage.py
    change: create
decisions:
  - id: D1
    choice: "conocimiento/ canónico; .scaleup/knowledge/strategy/ copiado solo en archivos que E87 toca, con prueba de sincronía"
    rationale: "La exportación pública incluye conocimiento/ y excluye .scaleup/"
    constraint: "No editar .scaleup/ a mano; las 18 diferencias previas solo pueden encoger"
  - id: D2
    choice: "Mapa de cobertura con lista pending que solo encoge"
    rationale: "Prueba la brecha en S87.1 sin dejar la suite en rojo"
    constraint: "pending vacío antes de cerrar la épica"
  - id: D3
    choice: "El motor busca el registro en <base>/.escala/knowledge/ y si no existe en conocimiento/ del paquete"
    rationale: "Hoy devuelve 0 hojas; el fallback no rompe instalaciones viejas"
    constraint: "No mover ni duplicar conocimiento/ hacia .escala/"
  - id: D4
    choice: "Extensión compatible del YAML de hoja (guide, tips, ai_prompt, view, source.pages) validada con Pydantic ToolGuide"
    rationale: "Las 15 hojas viejas siguen con metadata.fields"
    constraint: "Sin framework nuevo ni motor paralelo"
  - id: D5
    choice: "Vista nueva coaching/worksheet/view.py que reutiliza helpers públicos de boards/render.py"
    rationale: "Board exige números; una hoja de estrategia es texto"
    constraint: "Sin JS, CDN, imágenes ni enlaces; determinista; escritura atómica; tablero E84 sin cambio de comportamiento"
  - id: D6
    choice: "El código solo escribe HTML+MD; publicar como artefacto de Claude es decisión de la sesión"
    rationale: "El repo no tiene integración con Artifact (gap G4)"
    constraint: "Ningún módulo llama servicios externos"
  - id: D7
    choice: "Vision Summary: hoja de guía en conocimiento/ que enlaza tool.vision-summary"
    rationale: "E61 (ESCALA-29) es dueña de la ontología"
    constraint: "No tocar ontology/v2/"
constraints:
  - "Cero imágenes o PDF del workbook en el repo"
  - "Texto en español parafraseado; cada nodo cita source.pages"
  - "Cada paso de guía trae ejemplo real; cada hoja trae al menos 3 tips con fuente de S87.3"
  - "Tests de tablero E84 (coaching/dashboard/boards/tests) sin cambios de expectativa"
```
