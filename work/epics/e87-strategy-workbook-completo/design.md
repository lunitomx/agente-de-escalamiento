# E87 · Diseño — Strategy workbook completo

Jira: ESCALA-107 · Fecha: 2026-10-20 · Revisión 2 (después de la revisión adversaria, `adversarial-review.md`).
Entradas: brief.md, scope.md, capability-map.md, evidence/predesign.json, adversarial-review.md.

## Flujo en una pantalla

```
Dueño: "/escala-worksheet promesa de marca"
   │
   ▼
Motor de hojas (coaching/worksheet)
   │  knowledge_root(base):
   │    ¿existe <base>/.escala/knowledge/registry/worksheets.yaml (ARCHIVO)?
   │      sí → raíz = <base>/.escala/knowledge      (instalación vieja con registro propio)
   │      no → raíz = conocimiento/ del paquete     (repo y clientes con instalación editable)
   │  registro y node_path se leen desde la MISMA raíz
   │
   │   por cada paso: pregunta + cómo + ejemplo real + tips con fuente
   │   (Strategy Canvas: lee además las hojas guardadas de derived_from)
   ▼
Dueño responde paso a paso  (prompt de IA del workbook disponible en cada hoja)
   │
   ▼  action=save
<base>/.escala/my-company/worksheets/<hoja>.yaml          (respuestas, ya existía)
<base>/.escala/my-company/vistas/AAAA-MM-DD-<hoja>.html   (nuevo, autocontenido)
<base>/.escala/my-company/vistas/AAAA-MM-DD-<hoja>.md     (nuevo, gemelo)
   │  el motor devuelve artifacts.view = {html, md, open_cmd}
   ▼
Paso final del skill escala-worksheet:
   open_cmd = ["open", html] (macOS) | ["xdg-open", html] (Linux) | null
   ├─ corre open_cmd; si es null o falla → muestra el .md en el chat y da la ruta del .md
   └─ la sesión de Claude puede además publicar el HTML como artefacto (opcional)
```

## Hallazgos del gemba (leídos en código, 2026-10-20; corregidos en la revisión)

1. **El motor de hojas hoy devuelve 0 hojas.** `coaching/worksheet/__init__.py:11-17` fija `REGISTRY_PATH` en `.escala/knowledge/registry/worksheets.yaml`. Ese **archivo** no existe. El **directorio** `.escala/knowledge/` sí existe en el repo (23 archivos rastreados: `cash/`, `strategy/overview.md`…) pero sin `registry/`. El registro real vive en `conocimiento/registry/worksheets.yaml` (15 hojas). `load_worksheet_content()` (`__init__.py:86-95`) resuelve `node_path` contra `.escala/knowledge/` por su cuenta. Comprobado: `list_worksheets()` → 0. Se arregla en S87.2 con una sola función de raíz para los dos puntos.
2. **Copia canónica = `conocimiento/`.** `tests/test_public_export.py:224` exige `conocimiento` en la exportación; `:246` prohíbe `.scaleup`. `conocimiento/retrieval.py:17` lee `conocimiento/`, no `.scaleup/`. Nadie en producción lee `.scaleup/knowledge/strategy/`; solo una prueba lee `opsp.yaml` de ahí, y E87 no toca ese archivo.
   - **Corrección:** `pyproject.toml` declara `package-data "conocimiento" = ["**/*.yaml"]`, pero la rueda **no** lleva `conocimiento/`. `packages.find` solo incluye `coaching*`, `validators*`, `escala_server*`, y `conocimiento/` no tiene `__init__.py`; por eso `package-data` se ignora (`uv build --wheel` → 0 archivos de `conocimiento/`). Hoy funciona solo porque `install.sh:229` instala en modo editable (`uv pip install -e`), y el motor encuentra `conocimiento/` por `Path(__file__)`. E87 no arregla el empaquetado: va al estacionamiento (ver "Estacionado"). S87.2 agrega una prueba que fija esa dependencia.
3. **El renderizador de E84 tiene forma de tablero de métricas.** `render.py:237-245`: `save_board` rechaza un tablero sin números. Una hoja de estrategia es texto. Se reutiliza la parte común (`FORBIDDEN`, `LOCAL_ONLY`, `HIDDEN`, `_CSS`, `_atomic_write`), no el modelo `Board`.
4. **El esquema de hoja es una lista de textos.** `metadata.fields` es `list[str]`; el motor arma un paso por campo (`__init__.py:188-192`). No hay dónde poner ejemplo, tips ni prompt.
5. La tarjeta `tools/sandbox.yaml` contradice la p. 28 (define QUIÉN/DÓNDE). La p. 28 pide: DÓNDE (zonas), QUÉ (3-5 categorías), a QUIÉN le vendes (**canales**: socios, directo, en línea, menudeo, mayoreo) y PRONÓSTICO (cambios a 3-5 años).
6. **El Plan Personal ya existe.** `worksheet-oppp` (`conocimiento/registry/worksheets.yaml:40-50`, `conocimiento/people/worksheets/oppp.yaml`, `people/tools/oppp.yaml`), con 4 columnas y las 5Fs. La p. 32 tiene 8 columnas (Relación, Familia, Amigos, Salud, Trabajo, Dinero, Diversión, Espiritual) por 4 filas (10-25 años, Un año, Empezar, Dejar). S87.9 extiende esa hoja; no crea otra.
7. **El "Strategy Canvas" del workbook es el de Scaling Up.** PDF p. 7 y p. 12: Cliente central, Promesa de marca, Actividades diferenciadoras, Caja de arena. No es el Strategy Canvas de Océano Azul (Kim y Mauborgne).
8. **Vision Summary en la ontología v2 solo tiene identidad.** `ontology/v2/releases/s64.1.json` → `nodes[75]` = `tool.vision-summary`, sin campos. Los nombres de campo de E65 viven en `validators/oppp_vision_artifacts.py` (`_ARTIFACT_SPECS["procedure.build-vision-summary"]` = `purpose`, `customer`, `differentiator`, `future_direction`). La p. 36 pide: Valores, Propósito, Promesas, BHAG, prioridades a 3-5 años, 1 año y trimestre, KPIs y prioridades trimestrales personales.
9. **El skill `escala-worksheet` cita rutas que no existen**: `.escala/coaching/worksheet/` (línea 14) y `.escala/agent/validators/worksheet.py` (línea 63). S87.2 lo reescribe; no lo parcha.
10. Grafo de RaiSE: 0 resultados para este dominio. Válido; no cambia el diseño.

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
  - page: 27
    class: no_tool
    reason: "repite el ejemplo de la p. 23 (abogados); la Caja de arena vive en p. 28-29"
pending: [7, 8, 9, 10, 11, 12, 13, 14, ...]   # solo puede encoger
```

Prueba `tests/test_e87_workbook_coverage.py`:

- Hay 38 entradas, páginas 1 a 38, sin repetir.
- Toda página `no_tool` tiene `reason`.
- Toda página `tool` que no está en `pending` tiene al menos un nodo. Cada nodo existe en `conocimiento/` (cualquier decisión, también `people/`) y cita esa página en `source.pages`.
- Toda página de `pending` es `tool`.
- `pending` es subconjunto de la lista congelada en la prueba; la lista congelada solo puede encoger.
- Cero archivos de imagen o PDF bajo `conocimiento/`, `escala-skills/` y `templates/` que vengan del workbook. El PDF origen no se versiona.
- **E87 no agrega archivos bajo `.scaleup/`.** La prueba compara los archivos rastreados bajo `.scaleup/` contra una lista congelada tomada en S87.1 (`git ls-files .scaleup`); un archivo nuevo ahí falla. Se retira la prueba de sincronía de la revisión 1.

Ejemplo de falla esperada: si S87.4 agrega la hoja BMC pero olvida `source.pages: [10]`, la página 10 sale de `pending` y la prueba falla con "p. 10: worksheet-bmc no cita la página".

#### Mapa de las 38 páginas (verificado con `pdftotext`, 2026-10-20)

| Páginas | Clase | Qué es | Historia |
|---|---|---|---|
| 1-6 | no_tool | Portada e instrucciones, agenda, reglas, herramientas EOA, ejemplos "¿En qué eres diferente?", cita de Welch y horizontes | S87.1 |
| 7 | tool | Strategy Canvas (4 piezas) y vista previa del Vision Summary | S87.7 |
| 8-11 | tool | BMC: resumen y puente a Scaling Up (8), prompt (9), lienzo (10), lista de verificación (11) | S87.4 |
| 12 | tool | Strategy Canvas de Scaling Up | S87.7 |
| 13-14 | tool | Cliente central: gráfica "¿Está claro tu QUIÉN?" (13) y personas ejemplo (14) | S87.6 |
| 15-16 | tool | Cliente central: atributos, ejercicio y prompt | S87.6 |
| 17-19 | tool | Promesa de marca: ejemplos con medida, NPS, antipromesas y compensaciones | S87.5 |
| 20 | tool | Promesa de marca (3 preguntas y prompt); preguntas del Cliente central | S87.5 y S87.6 |
| 21 | tool | Hoja de Promesa de marca (Count On / Expect / Unique) | S87.5 |
| 22-26 | tool | Actividades diferenciadoras: modelo, ejemplo (23), Dell (24), hoja (25), prompt (26) | S87.6 |
| 27 | no_tool | Repite el ejemplo de la p. 23; la Caja de arena vive en p. 28-29 | S87.1 |
| 28-29 | tool | Caja de arena: DÓNDE, QUÉ, canales, pronóstico; prompt y ejercicio | S87.7 |
| 30-32 | tool | Plan Personal de Una Página (8 columnas × 4 filas) | S87.9 |
| 33 | tool | Tableros de visión y su prompt | S87.9 |
| 34-35 | tool | Prompt de 10 tareas semanales y compromiso "¿A qué te comprometes?" | S87.8 |
| 36 | tool | Vision Summary | S87.8 |
| 37-38 | no_tool | Notas y aviso de derechos | S87.1 |

Total: 29 páginas de herramienta (7-26 y 28-36) y 9 sin herramienta (1-6, 27, 37, 38).

### C2 · Contrato de herramienta y raíz del conocimiento (S87.2)

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
  sections: [...]
derived_from: []           # opcional; ver C6
```

Modelo Pydantic `ToolGuide` en `coaching/worksheet/guide.py`. Una hoja con `guide` exige: al menos un paso, `example` no vacío en cada paso, al menos 3 tips con `source`, y `source.pages`.

Cambios en el motor:

- **Raíz del conocimiento.** Una función `knowledge_root(base_path) -> Path`:
  - Si existe el **archivo** `<base>/.escala/knowledge/registry/worksheets.yaml`, la raíz es `<base>/.escala/knowledge`.
  - Si no, la raíz es `conocimiento/` del paquete (`Path(__file__).parents[2] / "conocimiento"`).
  - `list_worksheets()` y `load_worksheet_content()` usan esta misma función. Ninguno arma la ruta por su cuenta.
  - Ejemplo: en el repo, `.escala/knowledge/` existe pero no tiene `registry/`; la raíz es `conocimiento/` y `list_worksheets()` da 15.
- `start`/`step`: si la hoja trae `guide.steps`, cada paso muestra pregunta, cómo, ejemplo y los tips de ese paso. Si no, se usa `metadata.fields` como hoy.
- `save`: además del YAML, llama a `save_view` y devuelve `artifacts.view = {html, md, open_cmd}`.

### C3 · Vista de hoja y quién la abre (S87.2)

`coaching/worksheet/view.py`:

- `render_html(sheet, answers) -> str`, `render_markdown(sheet, answers) -> str`, `save_view(base, sheet, answers, made_on) -> list[Path]`.
- `open_command(html: Path, platform: str) -> list[str] | None`: `darwin` → `["open", str(html)]`; `linux` → `["xdg-open", str(html)]`; otro → `None`. Función pura; el motor la llama con `sys.platform` y la devuelve en `artifacts.view.open_cmd`. El código **no** ejecuta el comando.
- Reutiliza de `coaching/dashboard/boards/render.py`: `FORBIDDEN`, `LOCAL_ONLY`, `HIDDEN`, el CSS base y la escritura atómica. Se vuelven públicos (`safe_text`, `atomic_write`, `BASE_CSS`) sin cambiar el comportamiento del tablero; `test_render.py` sigue igual.
- `layout: cards`: una tarjeta por sección, en una columna.
- `layout: canvas`: rejilla CSS (BMC de 9 bloques, Strategy Canvas de 4, Plan Personal de 8×4) que en el teléfono baja a una columna. Sin JavaScript, sin CDN, sin imágenes.
- Un campo vacío dice "Falta: <paso>. Cómo llenarlo: <how>".
- Determinista: mismos datos, mismos bytes.

**Quién abre la vista.** El paso final de `escala-skills/escala-worksheet/SKILL.md` dice:

1. Corre `open_cmd` si no es `null` (macOS: `open <ruta.html>`; Linux: `xdg-open <ruta.html>`).
2. Si `open_cmd` es `null` o el comando falla, muestra el contenido del `.md` en el chat y da la ruta del `.md`.
3. La sesión de Claude puede además publicar el HTML como artefacto. Es opcional y no lo hace el código.

Ejemplo: Eduardo guarda la Promesa de marca en su Mac. El skill corre `open .escala/my-company/vistas/2026-10-21-worksheet-brand-promise.html` y el navegador muestra la hoja.

### C4 · Tips investigados (S87.3)

`/rai-research` una vez por herramienta. Salida en `work/research/e87-tips/<herramienta>.md`, con hallazgos numerados (`#f1`, `#f2`…) y al menos 3 fuentes independientes por hallazgo usado. **8 herramientas**:

1. Business Model Canvas (Strategyzer).
2. Strategy Canvas de Scaling Up (las 4 piezas juntas en una hoja; no Océano Azul).
3. Promesa de marca.
4. Cliente central.
5. Actividades diferenciadoras.
6. Caja de arena (Sandbox): zonas, categorías, canales y pronóstico.
7. Vision Summary.
8. Plan Personal de Una Página y tableros de visión.

Cada archivo tiene al menos 3 hallazgos triangulados. Así cada historia de herramienta tiene de dónde citar sus 3 tips. Las historias copian a `tips:` solo hallazgos con triangulación y citan el ancla.

### C5 · Hojas por historia

| Historia | Hojas | Páginas | Layout |
|---|---|---|---|
| S87.4 | `worksheet-bmc` (9 bloques, puente, checklist) | 8-11 | canvas |
| S87.5 | `worksheet-brand-promise`; concepto `brand-promise` corregido | 17-21 | cards |
| S87.6 | `worksheet-core-customer` extendida; `worksheet-differentiating-activities` | 13-16, 20, 22-26 | cards |
| S87.7 | `worksheet-sandbox`; `worksheet-strategy-canvas` (con `derived_from`, C6) | 7, 12, 28-29 | canvas |
| S87.8 | `worksheet-vision-summary` (p. 36) + prompt y compromiso de 10 semanas (p. 34-35) | 34-36 | cards |
| S87.9 | `worksheet-oppp` **extendida** (8 columnas × 4 filas) + tableros de visión | 30-33 | canvas |

El puente BMC → Scaling Up (p. 8) es dato de la hoja BMC. Cada bloque dice a qué hoja lleva: Segmentos → Cliente central, Propuesta de valor → Promesa de marca, Actividades clave → Actividades diferenciadoras, Canales → Caja de arena. La vista lo muestra como "Siguiente paso: llena <hoja>".

S87.9: `worksheet-oppp` se queda en `decision: people` y con su `id`. No se registra dos veces. La hoja gana `source.pages: [30, 31, 32, 33]`, `guide` con las 8 columnas de la p. 32 y `view.layout: canvas`. `metadata.fields` se conserva para que la prueba de las 15 hojas viejas siga pasando. La tarjeta `people/tools/oppp.yaml` se corrige a 8 columnas.

### C6 · Hojas derivadas: `derived_from` (S87.7)

El Strategy Canvas no pide los datos otra vez. Los lee de otras hojas guardadas.

```yaml
id: worksheet-strategy-canvas
derived_from:
  - sheet: worksheet-core-customer
    fields: [quien-es, necesidad]
    into: cliente-central
  - sheet: worksheet-brand-promise
    fields: [promesa-principal]
    into: promesa
  - sheet: worksheet-differentiating-activities
    fields: [actividades]
    into: actividades
  - sheet: worksheet-sandbox
    fields: [donde, que, canales]
    into: caja-de-arena
  - sheet: worksheet-bmc            # opcional: el BMC alimenta el lienzo, no lo sustituye
    fields: [segmentos, propuesta-de-valor]
    into: contexto
    required: false
```

Reglas:

- El motor lee `<base>/.escala/my-company/worksheets/<sheet>.yaml` por cada entrada. No escribe en ellas.
- Si la hoja origen no existe o le falta el campo, la sección `into` muestra "Falta: <campo> de <hoja>. Llénala con `/escala-worksheet <hoja>`". Con `required: false`, la sección se omite en vez de mostrar "Falta".
- `ToolGuide` valida que cada `sheet` exista en el registro y que cada `field` sea un `id` de paso de esa hoja. Una hoja derivada no puede derivar de sí misma.
- Ejemplo: Tortillería El Sol llenó Cliente central y Promesa, pero no Caja de arena. El lienzo muestra 3 bloques llenos y "Falta: donde de worksheet-sandbox…".

### C7 · Vision Summary alineado con la ontología (S87.8)

Decisión: se acepta la copia de campos en `conocimiento/` con pruebas de alineación. No se enseña al motor a leer `ontology/v2/` (más código, otra raíz).

Hallazgo: `s64.1.json` solo trae `tool.vision-summary` como identidad, sin campos. Los nombres de campo de la ontología ejecutable viven en E65 (`validators/oppp_vision_artifacts.py`, `procedure.build-vision-summary`).

```yaml
id: worksheet-vision-summary
ontology_ref: tool.vision-summary
guide:
  steps:
    - id: valores
      maps_to: []
    - id: proposito
      maps_to: [purpose]
    - id: promesas
      maps_to: [differentiator]
    - id: bhag
      maps_to: [future_direction]
    # cliente central (customer) llega por derived_from de worksheet-core-customer
```

Pruebas en S87.8:

- `ontology_ref` existe como `canonical_id` en `ontology/v2/releases/s64.1.json`.
- Cada campo de `_ARTIFACT_SPECS["procedure.build-vision-summary"]` (`purpose`, `customer`, `differentiator`, `future_direction`) aparece en al menos un `maps_to` o en un `derived_from`. Si E65 cambia un nombre, la prueba falla.
- Los pasos cubren los bloques de la p. 36: valores, propósito, promesas, BHAG, prioridades 3-5 años, 1 año, trimestre, KPIs y prioridades trimestrales.

## Pruebas por historia (TDD)

- **S87.1:** cobertura de 38 páginas con la lista `pending`; cero imágenes; "E87 no agrega archivos bajo `.scaleup/`"; tarjeta de Caja de arena con las 4 preguntas de p. 28.
- **S87.2:**
  - En el repo, `list_worksheets(base_path=Path("."))` → 15 aunque `.escala/knowledge/` exista.
  - Con `base_path = tmp_path` sin `.escala/`: 15 hojas listadas; `save` escribe YAML + HTML + MD bajo `tmp_path/.escala/my-company/`.
  - La prueba que siembra `tmp_path/.escala/knowledge/registry/` sigue usando ese registro.
  - `load_worksheet_content` lee desde la misma raíz que el registro.
  - La raíz del paquete contiene `conocimiento/registry/worksheets.yaml` (fija la dependencia de la instalación editable).
  - `ToolGuide` rechaza un paso sin ejemplo y una hoja con menos de 3 tips con fuente.
  - El HTML no trae ningún token de `FORBIDDEN`; mismos datos dan mismos bytes.
  - `open_command`: `darwin` → `open`, `linux` → `xdg-open`, `win32` → `None`.
  - `SKILL.md` contiene el paso de abrir con `open_cmd` y el plan B del `.md`; no cita `.escala/agent/validators/` ni `.escala/coaching/`.
  - Las 15 hojas viejas siguen cargando; `test_render.py` sin cambios de expectativa.
- **S87.3:** 8 archivos en `work/research/e87-tips/`, cada uno con al menos 3 hallazgos con 3 fuentes.
- **S87.4 a S87.9:** cada hoja nueva o extendida pasa `ToolGuide`; sus páginas salen de `pending`; un guardado de ejemplo produce la vista con todas sus secciones y `open_cmd`.
- **S87.7 además:** `derived_from` con hojas llenas, a medias y vacías; validación de `sheet` y `field`.
- **S87.8 además:** pruebas de C7.

## Riesgos

- PRECAUCIÓN: cambiar la raíz puede romper a clientes con `.escala/knowledge/registry/worksheets.yaml` propio. Mitigación: ese archivo sigue teniendo prioridad.
- PRECAUCIÓN: la raíz del paquete depende de la instalación editable. Si un día se instala desde la rueda, el motor vuelve a 0 hojas. Mitigación: la prueba de S87.2 lo hace visible; el arreglo está estacionado.
- Repetir S6.3. Mitigación: S87.1 va primero y la lista `pending` hace visible lo que falta.
- Tips sin fuente. Mitigación: `ToolGuide` exige `source` en cada tip; S87.3 cubre las 8 herramientas.

## Estacionado (fuera de E87)

- Empaquetar `conocimiento/` en la rueda (agregar `conocimiento*` a `packages.find` o mover a `package-data` de un paquete real). No es trivial: cambia cómo se importa `conocimiento.retrieval` y la prueba de exportación. Va a una historia propia.
- Retirar el espejo `.scaleup/knowledge/strategy/` y sus 18 diferencias.

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
  - path: conocimiento/people/worksheets/oppp.yaml
    change: modify
  - path: conocimiento/people/tools/oppp.yaml
    change: modify
  - path: conocimiento/registry/worksheets.yaml
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
    change: rewrite
  - path: work/research/e87-tips/
    change: create
  - path: tests/test_e87_workbook_coverage.py
    change: create
decisions:
  - id: D1
    choice: "conocimiento/ es la única copia que E87 toca; E87 no agrega archivos bajo .scaleup/"
    rationale: "La exportación incluye conocimiento/ y excluye .scaleup/; nadie en producción lee .scaleup/knowledge/strategy/"
    constraint: "Prueba: archivos rastreados bajo .scaleup/ = lista congelada en S87.1"
  - id: D2
    choice: "Mapa de cobertura con lista pending que solo encoge"
    rationale: "Prueba la brecha en S87.1 sin dejar la suite en rojo"
    constraint: "pending vacío antes de cerrar la épica"
  - id: D3
    choice: "knowledge_root(base): si existe el ARCHIVO <base>/.escala/knowledge/registry/worksheets.yaml usa <base>/.escala/knowledge; si no, conocimiento/ del paquete. Registro y node_path usan la misma raíz"
    rationale: ".escala/knowledge/ existe en el repo sin registry/; mirar el directorio dejaría 0 hojas"
    constraint: "No mover ni duplicar conocimiento/ hacia .escala/"
  - id: D4
    choice: "Extensión compatible del YAML de hoja (guide, tips, ai_prompt, view, source.pages, derived_from) validada con Pydantic ToolGuide"
    rationale: "Las 15 hojas viejas siguen con metadata.fields"
    constraint: "Sin framework nuevo ni motor paralelo"
  - id: D5
    choice: "Vista nueva coaching/worksheet/view.py que reutiliza helpers públicos de boards/render.py"
    rationale: "Board exige números; una hoja de estrategia es texto"
    constraint: "Sin JS, CDN, imágenes ni enlaces; determinista; escritura atómica; tablero E84 sin cambio de comportamiento"
  - id: D6
    choice: "El código escribe HTML+MD y devuelve open_cmd; el skill corre open/xdg-open y si falla muestra el .md; publicar como artefacto es opcional de la sesión"
    rationale: "Sin un paso explícito nadie abre la vista (CA 3 no verificable)"
    constraint: "Ningún módulo Python ejecuta procesos ni llama servicios externos"
  - id: D7
    choice: "Vision Summary: copia de campos en conocimiento/ con ontology_ref y maps_to, probada contra s64.1.json (id) y E65 _ARTIFACT_SPECS (campos)"
    rationale: "s64.1.json no trae campos; leer ontology/v2 desde el motor es más código"
    constraint: "No tocar ontology/v2/ ni validators/oppp_vision_artifacts.py"
  - id: D8
    choice: "Plan Personal: extender worksheet-oppp (decision people), no crear hoja nueva"
    rationale: "Ya existe; otra hoja repetiría el patrón que E87 corrige"
    constraint: "Conservar id y metadata.fields"
  - id: D9
    choice: "Strategy Canvas = lienzo de 4 piezas de Scaling Up con derived_from; sin Océano Azul"
    rationale: "PDF p. 7 y p. 12"
    constraint: "derived_from solo lee; falta visible como 'Falta: <campo> de <hoja>'"
parked:
  - "Empaquetar conocimiento/ en la rueda (hoy solo funciona con instalación editable, install.sh:229)"
  - "Retirar el espejo .scaleup/knowledge/strategy/"
constraints:
  - "Cero imágenes o PDF del workbook en el repo"
  - "Texto en español parafraseado; cada nodo cita source.pages"
  - "Cada paso de guía trae ejemplo real; cada hoja trae al menos 3 tips con fuente de S87.3"
  - "Tests de tablero E84 (coaching/dashboard/boards/tests) sin cambios de expectativa"
```
