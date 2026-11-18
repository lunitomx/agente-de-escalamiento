# E88: Strategy 2026 — design

Jira: ESCALA-119 · Fecha: 2026-11-18 · Strategy Day: lunes 23-nov-2026 (todo implementable al domingo 22).
Insumos: `brief.md`, `scope.md`, `capability-map.md`, `evidence/predesign.json` (commit 27c9753c), borradores en `drafts/` (commit 96ec3669).
Revisión adversarial aplicada (8 hallazgos, verificados contra el código el 2026-11-18).

## 1. Hallazgos del gemba (código leído)

- Grafo: `rai graph query` sobre worksheet/ai_prompt → 0 resultados (el grafo no indexa `coaching/worksheet`). Diseño por lectura directa.
- `coaching/worksheet/guide.py`: `AiPrompt` tiene solo `text` (`extra="forbid"`, por eso `page` se rechaza). `ToolGuide.ai_prompt: AiPrompt | None`. `ToolGuide` usa `extra="ignore"`: una llave desconocida (p. ej. `ai_followups` del borrador de Vivid Vision) se pierde sin aviso. `DerivedFrom.required: bool = True`.
- `coaching/worksheet/__init__.py`, acción `start`/`resume` de `run()`:
  - **«Paso 1: Información General»** es la rama `if current_step == 0:` (≈ línea 409): pinta los bloques derivados, «Antes de empezar, confirma que tienes:» y «Responde con 'listo'».
  - `_step_lines(steps, tips, index, …)` pinta los pasos guiados como «Paso index+2». Los tips de hoja (`step: null`) salen en `index == 0`, es decir en **«Paso 2»**, no en el paso 1.
  - `_review_lines()` pinta la revisión final (2 llamadas: ≈ líneas 451 y 535) con `_ai_prompt_text()`.
  - **`start` sobre una hoja completada no deja seguir** (≈ línea 371): devuelve «ya está completada. Usa list» y nada más. `resume` pasa por el mismo chequeo.
  - `get_completed_ids()` lee todo `*.yaml` de la carpeta, también los respaldos `<id>-AAAAMMDD-HHMMSS.yaml` que escribe `save`: una hoja con respaldo cuenta como completada aunque su archivo propio esté en progreso.
  - `save` (≈ líneas 555-620) escribe la vista y responde «guardada como completada. Vista lista: …». **No nombra la siguiente hoja.**
- `coaching/worksheet/view.py`: `SheetView.ai_prompt: str | None`; `render_html`/`render_markdown` pintan `AI_PROMPT_TITLE`. `next_sheet` solo se ve en la vista guardada (≈ línea 114). `missing_source_text()` escribe «Falta: … Llena la hoja X con /escala-worksheet id».
- `vision-summary.yaml`: `derived_from: worksheet-core-customer` (obligatorio por omisión). Cliente central no está en el recorrido 2026, así que su vista mostraría «Falta: … Llena la hoja Cliente central». Su paso `meta-grande` y un tip dicen «10-25 años»; la decisión es 10–30.
- `escala-skills/escala-worksheet/SKILL.md`: Step 4 (guardar) y Step 5 (abrir vista) no dicen qué hoja sigue.
- Pruebas que fijan la forma actual (no deben romperse): `tests/test_e87_tool_guides.py` (`set(content["ai_prompt"]) == {"text"}` en 3 hojas; vision-summary exige «10 tareas» y «semana» en `ai_prompt.text`), `coaching/worksheet/tests/test_guide.py` (`page` rechazado), `test_review_text.py` (`view.ai_prompt == text`).
- `tests/test_e87_tool_guides.py:41`: `ANCHOR_SOURCE_RE = ^(work/research/e87-tips/…)#(fN)$`. Un tip con fuente `work/research/e88-tips/x.md#f1` cae en la rama «limpio» y **no se revisa la triangulación**. El archivo de investigación necesita `<a id="fN"></a>` y un bloque ```yaml con `id: fN` y `triangulated: true` (`_findings`).
- `tests/test_e87_workbook_coverage.py::check_coverage(coverage, node_ids, registry_ids, frozen_pending)`: cada página usa `class: tool | no_tool`, `nodes` y `reason` (obligatorio en `no_tool`). No conoce `no_exercise`. Llaves extra en el mapa (p. ej. `exercises`) se ignoran. Se importa con `from tests.test_e87_workbook_coverage import …` (hay precedente en `tests/test_s86_10_parity_consent.py`).
- Mapa E6 (`validators/e6_migration.py`): una entrada con `sha256` por **cada** `conocimiento/**/*.yaml`. Cualquier cambio a un yaml bajo `conocimiento/` (también el registro) cambia el mapa. `scripts/build_e6_migration_map.py --repo . --output X` se niega si `X` ya existe («output exists»).
- `swt.yaml`: sin `guide`; `name_es` sin acentos; `summary` en inglés con un término vetado. Nunca muestra prompt.
- `governance/public-boundary.yaml`: única llave raíz prohibida es `source`; los términos vetados no incluyen BHAG. `extra_prompts` no choca (PAT-221 revisado).
- Registro `conocimiento/registry/worksheets.yaml`: `total_worksheets: 21` → 26. `tests/test_e6_migration.py`: 88/84 → 93/89 tras 5 yaml nuevos (PAT-222).
- Encadenar hojas: `GuideStep.next_sheet: NextSheet(id, title)` ya existe (solo forma, no se valida contra el registro). No reusar `coaching/journey`.
- Instalación del dueño: `install.sh` instala el paquete `escala-coaching` y guarda la ruta del repo en `~/.config/agente-de-escalamiento/repo-path`; `/escala-update` (`update.sh`) hace `git pull` de esa ruta y reinstala. Las hojas nuevas solo llegan a Eduardo cuando la épica está en `main` en GitHub y él corre la actualización.
- Borradores 2026 (`drafts/`, commit 96ec3669): 5 hojas pasan `parse_guide`. Al leerlos:
  - `vivid-vision.yaml` usa `ai_followups` (ignorada) → se renombra a `extra_prompts`. Su 4.º elemento «Imprímela» no es un prompt → pasa al `how` del último paso.
  - Un tip de `vivid-vision.yaml` dice «10-25 años» → 10–30.
  - Los tips citan investigación E87 genérica o archivos `conocimiento/`; S88.2 aporta fuentes propias del tema.
  - Ningún borrador trae `next_sheet`; el recorrido lo agrega S88.6.

## 2. Contrato clave: varios prompts por hoja (S88.1)

Forma elegida — la más simple compatible: **`ai_prompt` no cambia; se agrega una lista opcional `extra_prompts`**.

```python
# coaching/worksheet/guide.py
class ExtraPrompt(BaseModel):
    """A titled extra prompt; ``at`` says where the owner sees it."""
    model_config = ConfigDict(extra="forbid")   # page sigue rechazado
    title: Text
    text: Text
    at: Literal["start", "end"] = "end"

class ToolGuide(BaseModel):
    ...
    ai_prompt: AiPrompt | None = None                      # sin cambio
    extra_prompts: list[ExtraPrompt] = Field(default_factory=lambda: list[ExtraPrompt]())
```

Por qué no `AiPrompt | list[AiPrompt]`: obliga a ramificar en 3 consumidores y rompe 6 pruebas que leen `guide.ai_prompt.text`. Con la lista aparte: 0 pruebas actuales cambian y las 21 hojas cargan igual.

Dónde se ve cada prompt:

| Prompt | Chat: «Paso 1: Información General» | Chat: revisión final | Vista guardada (HTML y MD) |
|---|---|---|---|
| `extra_prompts` con `at: start` | sí, con su título | no | sí, primero |
| `ai_prompt` (principal) | no | sí (como hoy) | sí (como hoy) |
| `extra_prompts` con `at: end` | no | sí, después del principal, con título | sí, después del principal |

**Sitio exacto de `at: start` en el chat:** la rama `if current_step == 0:` de `run()` (acción `start`/`resume`), después de los bloques derivados y **antes** de «Antes de empezar, confirma que tienes:». Una función nueva `_start_prompt_lines(content) -> list[str]` devuelve `**<title>:** <text>` por cada prompt `start`. **No** va en `_step_lines` (eso es «Paso 2» y se repetiría al reanudar). Ejemplo: el dueño escribe `start worksheet-swt` y, antes de «Responde con 'listo'», lee «**Arranque con IA:** …».

`SheetView` gana `extra_prompts: list[ViewPrompt]` (`ViewPrompt(title, text, at)`); `ai_prompt: str | None` se queda igual (la prueba `view.ai_prompt == text` sigue verde). Todo texto pasa por `safe_text`/`html.escape` como hoy.

**`save` nombra la siguiente hoja (S88.1, motor; datos en S88.6).** Si el último paso de la hoja tiene `next_sheet`, la salida de `save` agrega:

```
Siguiente hoja: <title>. Escribe `/escala-worksheet <id>` para seguir.
```

y `artifacts.next_sheet = {id, title}`. Sin `next_sheet`, la salida no cambia. `escala-skills/escala-worksheet/SKILL.md` (Step 4) dice: «si `output` trae “Siguiente hoja”, muéstrala y ofrece empezarla».

Uso en E88:

| Hoja | `ai_prompt` (principal, fin) | `extra_prompts` |
|---|---|---|
| swt | SWT 2026 | `start`: «Arranque con IA» (AI Setup) |
| vision-summary | Make Change Stick 2026 (conserva «10 tareas» y «semana») | `start`: «Tu día en una sola hoja» (Vision Summary) |
| vivid-vision | Vivid Vision | `end` ×3: cartel de pared, hazla visual, ponla a prueba |
| las demás | su prompt | — |

## 3. Hoja ya completada: reabrir con respaldo (S88.5)

Problema real: Eduardo pudo guardar SWT, Actividades o Resumen de visión en 2025. Hoy `start worksheet-swt` le respondería «ya está completada» y el Strategy Day se detiene en la primera hoja.

Decisión: **`start` sobre una hoja completada la reabre.**

1. Copia el archivo completado a `<id>-AAAAMMDD-HHMMSS.yaml` (mismo nombre que ya usa `save`). Nada se borra.
2. Empieza una versión nueva en el paso 1.
3. La salida dice: «Ya llenaste esta hoja el <fecha>. Guardé esa versión en <ruta>. Empiezas una versión nueva.»

`resume` sobre una hoja completada responde: «Esta hoja ya está completada. Escribe `start <id>` para hacer una versión nueva.» Ya no dice solo «usa list».

`get_completed_ids()` lee solo el archivo propio de cada hoja (`<id>.yaml`), no los respaldos. Así una hoja reabierta sale ⬜ en `list` hasta que se guarda de nuevo. Pruebas: `start` sobre completada → respaldo existe con los datos de antes; `list` muestra ⬜; `save` → ✅ y 2 archivos (el respaldo y el nuevo).

## 4. Recorrido del Strategy Day (S88.6)

Cadena con el mecanismo que ya existe: el último paso de cada hoja lleva `next_sheet` a la siguiente. El dueño la ve en la salida de `save` (sección 2) y en la vista guardada.

```
swt (AI Setup al inicio) → differentiating-activities → core-purpose → bhag
  → vivid-vision → fanocracy → life-purpose → vision-summary (Make Change Stick al final)
```

9 hojas cubren 10 ejercicios (AI Setup vive dentro de swt). La fuente de verdad del orden es `tests/fixtures/workbook-2026-coverage.yaml` (no público, con páginas). Forma compatible con `check_coverage()` de E87:

```yaml
workbook: strategy-2026
total_pages: 24
exercises:            # orden del taller; check_coverage lo ignora, la prueba E88 lo lee
  - {n: 1, name: AI Setup, sheet: worksheet-swt, prompt: start}
  - {n: 2, name: SWT, sheet: worksheet-swt, prompt: main}
  ...
pages:
  - {page: 1, class: no_tool, reason: "portada"}
  - {page: 4, class: tool, nodes: [worksheet-swt]}
  ...
pending: []           # meta: vacío
```

Prueba nueva `tests/test_e88_workbook_coverage.py`:

- `check_coverage(coverage, build_node_index(KNOWLEDGE), build_registry_index(REGISTRY), frozen_pending=frozenset())` devuelve `[]`.
- La cadena `next_sheet` desde `worksheet-swt` recorre las hojas de `exercises` en orden, sin hojas de más.

Prueba de punta a punta `tests/test_e88_strategy_day_path.py` (PAT-227): con un `base_path` temporal, el dueño llena las 9 hojas en orden por las acciones del motor (start → listo → respuestas → save). Se afirma:

- los 10 prompts salen en el lugar de la tabla de la sección 2;
- cada `save` (menos el último) dice «Siguiente hoja: …» con la hoja que sigue;
- se escriben 9 vistas `.md`/`.html`;
- un caso con `worksheet-swt` ya completada de antes: `start` la reabre (sección 3) y el recorrido sigue.

`escala-skills/escala-worksheet/SKILL.md` gana una sección corta «Strategy Day 2026»: empieza en `worksheet-swt` y sigue la «Siguiente hoja» de cada `save`.

## 5. Hojas nuevas (S88.3, S88.4)

- Rutas: `conocimiento/strategy/worksheets/{core-purpose,bhag,vivid-vision,fanocracy}.yaml`; `conocimiento/people/worksheets/life-purpose.yaml` (`decision: people`).
- Ids: `worksheet-core-purpose`, `worksheet-bhag` (nombre visible «Meta grande (BHAG)», plazo 10–30 años), `worksheet-vivid-vision`, `worksheet-fanocracy`, `worksheet-life-purpose`.
- Cada hoja: `guide` con ejemplo «Tortillería El Sol:», ≥3 tips con fuente, `ai_prompt` sin página, `view` con secciones que cubren todos los pasos, `metadata.fields` = ids de paso.
- Fanocracy: prompt fiel al workbook (7 de 9 principios); los 9 principios en el `how` de los pasos.
- Por cada yaml nuevo: entrada en el registro, `total_worksheets` +1, conteos de `tests/test_e6_migration.py` +1, y el mapa E6 regenerado (sección 7).

## 6. Investigación (S88.2)

- `work/research/e88-tips/{vivid-vision,life-purpose,fanocracy}.md`, cada una con ≥3 hallazgos. Cada hallazgo lleva `<a id="fN"></a>` y un bloque ```yaml con `id: fN`, `triangulated: true` y ≥2 fuentes externas citadas (mismo formato que `work/research/e87-tips/`).
- **S88.2 amplía `ANCHOR_SOURCE_RE`** en `tests/test_e87_tool_guides.py` a `^(work/research/e8[78]-tips/[a-z0-9-]+\.md)#(f\d+)$`. Prueba nueva: una fuente `work/research/e88-tips/x.md#f1` coincide con el patrón; un hallazgo sin `triangulated: true` hace fallar la revisión (con un archivo temporal).
- S88.1 escribe `work/research/e88-tips/swt.md` con el mismo formato. Como S88.1 y S88.2 van en paralelo, el ancla de swt se revisa en cuanto S88.2 se fusiona; si S88.2 se fusiona después, su suite debe pasar ya con swt.md adentro.
- Los tips de S88.4 citan `work/research/e88-tips/<tema>.md#fN`; `source_label()` ya los muestra como «Investigación ESCALA (nota interna fN)».

## 7. Mapa E6: cuándo y cómo regenerarlo

Toda historia que toque un yaml bajo `conocimiento/` regenera `ontology/v2/e6-migration-map.json`: **S88.1** (swt.yaml), **S88.3** y **S88.4** (yaml nuevos + registro), **S88.5** (swt, differentiating-activities, vision-summary) y **S88.6** (`next_sheet` en 8 hojas). S88.2 no toca `conocimiento/`.

Procedimiento (el script no sobrescribe; no se borra nada):

```bash
OUT="$(mktemp -d)/e6-migration-map.json"
uv run python scripts/build_e6_migration_map.py --repo . --output "$OUT"
cp "$OUT" ontology/v2/e6-migration-map.json
uv run pytest tests/test_e6_migration.py -q
```

Conteos esperados de `tests/test_e6_migration.py` (entradas / `await-domain-evidence`): 88/84 hasta S88.3; 90/86 tras S88.3; 93/89 tras S88.4. S88.1, S88.5 y S88.6 no cambian conteos, solo hashes.

**Fusiones en serie.** Dos historias que regeneran el mapa en paralelo chocan en el mismo json. Regla: se fusiona una historia a la vez; la siguiente trae la rama destino a su rama, **regenera el mapa otra vez** con el procedimiento de arriba, corre la suite completa y solo entonces se fusiona. Nunca se resuelve el choque del json a mano.

## 8. Resumen de visión: sin «Falta» de Cliente central y con 10–30 años (S88.5)

- `derived_from: worksheet-core-customer` pasa a `required: false`. Si Cliente central no está guardada, el bloque no sale (comportamiento que ya existe en `derived_blocks`). Si está guardada, sale como hoy.
- Paso `meta-grande`: pregunta «¿Cuál es tu meta grande a 10-30 años?» y el tip dice 10-30. El id del paso no cambia.
- Pruebas: con un `base_path` sin Cliente central, la vista de vision-summary no contiene «Falta» ni «Cliente central»; el texto de la hoja no contiene «10-25».

## 9. Instalación en la ESCALA de Eduardo (S88.6)

Las hojas viven en el paquete instalado, no en este repo. Criterio de terminado de S88.6, después de que la épica esté en `main` en GitHub:

1. En la Mac de Eduardo, `/escala-update` (o `update.sh` desde la ruta de `~/.config/agente-de-escalamiento/repo-path`).
2. Desde su carpeta de trabajo ESCALA, `list` muestra las 5 hojas nuevas (26 en total).
3. `start worksheet-swt` muestra «Arranque con IA» en el paso 1; si su SWT 2025 está guardada, la reabre con respaldo.
4. Se anota la salida (fecha, hash instalado) en el cierre de S88.6.

Si la ruta guardada apunta a otra copia del repo o falla el `git pull`, se detiene y se avisa a Eduardo con el comando exacto; no se toca su carpeta de datos `.escala/`.

## 10. Riesgos aceptados

- No hay texto 2026 del workbook en el repo: la prueba anticopia no cubre las paráfrasis 2026. Mitigación: paráfrasis en español escritas desde cero; no se agrega el texto original.
- Cinco historias tocan el mapa E6 y dos tocan el registro: fusiones en serie (sección 7): S88.1, S88.2 y S88.3 de a una; luego S88.5 y S88.4 de a una, en el orden en que terminen; al final S88.6.
- Calendario: 24 puntos entre jueves 19 y domingo 22. La instalación del paso 9 depende de que la épica esté en `main` el domingo. Si el sábado S88.6 no ha empezado, se recorta el mapa de 24 páginas (la prueba de cobertura) antes que el recorrido y la instalación.

### Machine
```yaml
modules_affected:
  - path: coaching/worksheet/guide.py
    change: modify
  - path: coaching/worksheet/__init__.py
    change: modify
  - path: coaching/worksheet/view.py
    change: modify
  - path: coaching/worksheet/tests/
    change: modify
  - path: escala-skills/escala-worksheet/SKILL.md
    change: modify
  - path: conocimiento/strategy/worksheets/swt.yaml
    change: modify
  - path: conocimiento/strategy/worksheets/differentiating-activities.yaml
    change: modify
  - path: conocimiento/strategy/worksheets/vision-summary.yaml
    change: modify
  - path: conocimiento/strategy/worksheets/core-purpose.yaml
    change: create
  - path: conocimiento/strategy/worksheets/bhag.yaml
    change: create
  - path: conocimiento/strategy/worksheets/vivid-vision.yaml
    change: create
  - path: conocimiento/strategy/worksheets/fanocracy.yaml
    change: create
  - path: conocimiento/people/worksheets/life-purpose.yaml
    change: create
  - path: conocimiento/registry/worksheets.yaml
    change: modify
  - path: ontology/v2/e6-migration-map.json
    change: modify
  - path: tests/test_e6_migration.py
    change: modify
  - path: tests/test_e87_tool_guides.py
    change: modify
  - path: tests/fixtures/workbook-2026-coverage.yaml
    change: create
  - path: tests/test_e88_workbook_coverage.py
    change: create
  - path: tests/test_e88_strategy_day_path.py
    change: create
  - path: work/research/e88-tips/
    change: create
decisions:
  - id: D1
    choice: "Varios prompts = lista opcional extra_prompts [{title, text, at: start|end}] junto a ai_prompt, que no cambia"
    rationale: "Compatible al 100%: 21 hojas y 6 pruebas que leen ai_prompt.text siguen igual; consumidores no ramifican por tipo"
    constraint: "No convertir ai_prompt en lista ni unión; ExtraPrompt con extra=forbid (page rechazado); title obligatorio"
  - id: D2
    choice: "at:start se pinta en la rama current_step == 0 de run() (Paso 1: Información General), antes de 'Antes de empezar', vía _start_prompt_lines(); y primero en la vista. ai_prompt y at:end en la revisión final y en la vista, en ese orden"
    rationale: "AI Setup y Vision Summary se usan antes de llenar; _step_lines index 0 es 'Paso 2' y no es el sitio"
    constraint: "No pintar prompts start en _step_lines ni en la revisión final"
  - id: D3
    choice: "AI Setup = extra_prompts start de swt; Vision Summary = extra_prompts start de vision-summary; Make Change Stick = ai_prompt de vision-summary"
    rationale: "No hay hoja vacía para AI Setup (rompería la regla de 3 tips); la prueba de vision-summary (10 tareas, semana) sigue verde"
    constraint: "Sin hoja nueva para AI Setup ni para Make Change Stick"
  - id: D4
    choice: "Id worksheet-bhag, nombre visible «Meta grande (BHAG)», plazo 10–30 años"
    rationale: "BHAG no está en vocabulary_rules de public-boundary; opsp.yaml y 7-strata.yaml ya lo usan"
    constraint: "vision-summary.yaml sigue sin la palabra BHAG (su prueba la prohíbe)"
  - id: D5
    choice: "Recorrido = next_sheet en el último paso de cada hoja (datos S88.6); save imprime 'Siguiente hoja: <title>. Escribe /escala-worksheet <id>' y artifacts.next_sheet (motor S88.1); SKILL.md lo explica (S88.1 y S88.6)"
    rationale: "next_sheet hoy solo se ve en la vista guardada; el chat nunca nombraba la siguiente hoja"
    constraint: "No reusar coaching/journey; ningún yaml nuevo bajo conocimiento/ para el recorrido; sin next_sheet la salida de save no cambia"
  - id: D6
    choice: "Mapa de 24 páginas en tests/fixtures/workbook-2026-coverage.yaml con páginas {page, class: tool|no_tool, nodes, reason} y lista exercises; la prueba reusa check_coverage de E87 con frozen_pending=frozenset()"
    rationale: "check_coverage exige class/reason; no_exercise no existe. Las páginas no pueden ir en hojas públicas"
    constraint: "Ningún número de página en conocimiento/; ni imágenes ni PDF del workbook en el repo"
  - id: D7
    choice: "SWT pasa a guiada en S88.1 con su prompt 2026 y la lista de 10 tendencias; S88.1 aporta el 3.er tip con un hallazgo en work/research/e88-tips/swt.md (formato e87: ancla + yaml triangulated)"
    rationale: "Una hoja guiada sin prompt no sirve; solo hay 2 fuentes reales para SWT"
    constraint: "swt.yaml sin metadata.fields en inglés ni términos vetados; mínimo 3 tips"
  - id: D8
    choice: "Fanocracy: prompt fiel (7 de 9 principios); los 9 en la guía. Life Purpose en conocimiento/people/worksheets"
    rationale: "Decisión de Eduardo"
    constraint: "No completar el prompt con los 2 principios faltantes"
  - id: D9
    choice: "start sobre hoja completada la reabre: respalda <id>.yaml como <id>-AAAAMMDD-HHMMSS.yaml y empieza en paso 1; resume sobre completada indica 'start' para versión nueva; get_completed_ids lee solo <id>.yaml (S88.5)"
    rationale: "Las hojas 2025 guardadas de Eduardo (swt, actividades, resumen) bloquearían el Strategy Day"
    constraint: "Nunca borrar ni sobrescribir una hoja completada sin respaldo"
  - id: D10
    choice: "Toda historia que toque yaml bajo conocimiento/ (S88.1, S88.3, S88.4, S88.5, S88.6) regenera e6-migration-map.json a un archivo temporal y lo copia encima; fusiones en serie y regenerar tras traer la rama destino"
    rationale: "Hay sha256 por archivo y el script se niega a escribir sobre un archivo existente"
    constraint: "No editar el json a mano ni resolver conflictos del json a mano; no borrar el mapa para regenerarlo"
  - id: D11
    choice: "vision-summary: derived_from core-customer con required: false; meta grande 10-30 años en pregunta y tip (S88.5)"
    rationale: "Cliente central no está en el recorrido 2026; el 'Falta' confundiría al dueño"
    constraint: "No agregar core-customer al recorrido; el id del paso meta-grande no cambia"
  - id: D12
    choice: "ANCHOR_SOURCE_RE pasa a work/research/e8[78]-tips/ con prueba (S88.2)"
    rationale: "Sin el cambio, los tips E88 se saltan la revisión de triangulación"
    constraint: "No relajar la revisión para e87"
constraints:
  - "Cada yaml tocado bajo conocimiento/ regenera ontology/v2/e6-migration-map.json con el procedimiento de design.md sección 7; yaml nuevo también sube los conteos de tests/test_e6_migration.py (PAT-222)"
  - "Fusiones en serie, una a la vez (S88.1 ∥ S88.2 ∥ S88.3 → S88.5, S88.4 → S88.6); tras traer la rama destino, regenerar el mapa E6 y correr la suite completa"
  - "Revisar governance/public-boundary.yaml antes de agregar llaves (PAT-221); llave raíz 'source' prohibida"
  - "Una prueba de punta a punta del Strategy Day completo del dueño (PAT-227), con un caso de hoja ya completada"
  - "Ningún número de página ni 'pág' en prompts o textos públicos"
  - "Sin nodos nuevos en ontology/v2/"
  - "Ejemplos con 'Tortillería El Sol:'; ≥3 tips con fuente por hoja guiada"
  - "Las historias toman los borradores de work/epics/e88-strategy-2026/drafts/ (no del scratchpad)"
  - "Nada se borra: respaldos de hojas y del mapa E6 por copia"
  - "Worktrees de historia copian .raise/pipelines/story.yaml (override historia/tarea, raise-conocido A43)"
  - "TDD; pyright strict, ruff y pytest en verde antes de cada commit"
```
