# E88: Strategy 2026 — design

Jira: ESCALA-119 · Fecha: 2026-11-18 · Strategy Day: lunes 23-nov-2026 (todo implementable al domingo 22).
Insumos: `brief.md`, `scope.md`, `capability-map.md`, `evidence/predesign.json` (commit 27c9753c).

## 1. Hallazgos del gemba (código leído)

- Grafo: `rai graph query` sobre worksheet/ai_prompt → 0 resultados (el grafo no indexa `coaching/worksheet`). Diseño por lectura directa.
- `coaching/worksheet/guide.py`: `AiPrompt` tiene solo `text` (`extra="forbid"`, por eso `page` se rechaza). `ToolGuide.ai_prompt: AiPrompt | None`. `ToolGuide` usa `extra="ignore"`: una llave desconocida (p. ej. `ai_followups` del borrador de Vivid Vision) se pierde sin aviso.
- `coaching/worksheet/__init__.py`: `_ai_prompt_text()` devuelve un `str`; `_review_lines()` lo pinta en la revisión final (2 sitios: líneas ~451 y ~535). `_step_lines()` pinta cada paso; el paso 1 ya recibe los tips de hoja (`step: null`).
- `coaching/worksheet/view.py`: `SheetView.ai_prompt: str | None`; `render_html` y `render_markdown` pintan un bloque `AI_PROMPT_TITLE`.
- Pruebas que fijan la forma actual (no deben romperse): `tests/test_e87_tool_guides.py` (`set(content["ai_prompt"]) == {"text"}` en 3 hojas; vision-summary exige «10 tareas» y «semana» en `ai_prompt.text`), `coaching/worksheet/tests/test_guide.py` (`page` rechazado), `test_review_text.py` (`view.ai_prompt == text`).
- `swt.yaml`: sin `guide`; `name_es` sin acentos; `summary` en inglés con un término vetado. Nunca muestra prompt.
- `governance/public-boundary.yaml`: única llave raíz prohibida es `source`; los términos vetados no incluyen BHAG. Una llave nueva `extra_prompts` no choca (PAT-221 revisado).
- Registro `conocimiento/registry/worksheets.yaml`: `total_worksheets: 21` → 26. `tests/test_e6_migration.py`: 88/84 → 93/89 tras 5 yaml nuevos (PAT-222).
- Cobertura 2025: `tests/test_e87_workbook_coverage.py` + `tests/fixtures/e87-workbook-coverage.yaml`. `check_coverage()` es reusable (recibe `total_pages`).
- Encadenar hojas: `GuideStep.next_sheet` ya existe (solo forma). No reusar `coaching/journey` (es otro concepto).
- Borradores 2026 (scratchpad `drafts/`): 5 hojas pasan `parse_guide`. Hallazgos al leerlos:
  - `vivid-vision.yaml` usa `ai_followups` (ignorada por el motor) → se renombra a `extra_prompts`. Su 4.º elemento «Imprímela» no es un prompt → pasa al `how` del último paso.
  - Un tip de `vivid-vision.yaml` dice «10-25 años»; la decisión es 10–30 → alinear.
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

| Prompt | Chat: paso 1 | Chat: revisión final | Vista guardada (HTML y MD) |
|---|---|---|---|
| `extra_prompts` con `at: start` | sí, bajo el paso 1, con su título | no | sí, primero |
| `ai_prompt` (principal) | no | sí (como hoy) | sí (como hoy) |
| `extra_prompts` con `at: end` | no | sí, después del principal, con título | sí, después del principal |

`SheetView` gana `extra_prompts: list[tuple[str, str, str]]` o un modelo `ViewPrompt(title, text, at)`; `ai_prompt: str | None` se queda igual (la prueba `view.ai_prompt == text` sigue verde). Todo texto pasa por `safe_text`/`html.escape` como hoy.

Uso en E88:

| Hoja | `ai_prompt` (principal, fin) | `extra_prompts` |
|---|---|---|
| swt | SWT 2026 | `start`: «Arranque con IA» (AI Setup) |
| vision-summary | Make Change Stick 2026 (conserva «10 tareas» y «semana») | `start`: «Tu día en una sola hoja» (Vision Summary) |
| vivid-vision | Vivid Vision | `end` ×3: cartel de pared, hazla visual, ponla a prueba |
| las demás | su prompt | — |

## 3. Recorrido del Strategy Day (S88.6)

Cadena con el mecanismo que ya existe: el último paso de cada hoja lleva `next_sheet` a la siguiente.

```
swt (AI Setup al inicio) → differentiating-activities → core-purpose → bhag
  → vivid-vision → fanocracy → life-purpose → vision-summary (Make Change Stick al final)
```

9 hojas cubren 10 ejercicios (AI Setup vive dentro de swt). La fuente de verdad del orden es `tests/fixtures/workbook-2026-coverage.yaml` (no público, con páginas):

```yaml
total_pages: 24
exercises:            # orden del taller; la prueba sigue la cadena next_sheet
  - {n: 1, name: AI Setup, sheet: worksheet-swt, prompt: start}
  - {n: 2, name: SWT, sheet: worksheet-swt, prompt: main}
  ...
pages:
  - {page: 4, nodes: [worksheet-swt]}
  - {page: 1, no_exercise: portada}
pending: []           # solo puede encoger; meta: vacío
```

Prueba nueva `tests/test_e88_workbook_coverage.py`: reusa `check_coverage()` de E87 con `total_pages=24`; verifica que la cadena `next_sheet` desde `worksheet-swt` recorre `exercises` en orden y que cada hoja está en el registro. Prueba de punta a punta `tests/test_e88_strategy_day_path.py` (PAT-227): con un `base_path` temporal, el dueño llena las 9 hojas en orden por las acciones del motor (start → respuestas → save); se afirma que aparecen los 10 prompts en el lugar de la tabla de la sección 2 y que se escriben 9 vistas `.md`/`.html`.

## 4. Hojas nuevas (S88.3, S88.4)

- Rutas: `conocimiento/strategy/worksheets/{core-purpose,bhag,vivid-vision,fanocracy}.yaml`; `conocimiento/people/worksheets/life-purpose.yaml` (`decision: people`).
- Ids: `worksheet-core-purpose`, `worksheet-bhag` (nombre visible «Meta grande (BHAG)», plazo 10–30 años), `worksheet-vivid-vision`, `worksheet-fanocracy`, `worksheet-life-purpose`.
- Cada hoja: `guide` con ejemplo «Tortillería El Sol:», ≥3 tips con fuente, `ai_prompt` sin página, `view` con secciones que cubren todos los pasos, `metadata.fields` = ids de paso.
- Fanocracy: prompt fiel al workbook (7 de 9 principios); los 9 principios en el `how` de los pasos.
- Por cada yaml nuevo: entrada en el registro, `total_worksheets` +1, regenerar `ontology/v2/e6-migration-map.json` con `scripts/build_e6_migration_map.py` y subir los conteos de `tests/test_e6_migration.py`.

## 5. Investigación (S88.2)

`work/research/e88-tips/{vivid-vision,life-purpose,fanocracy}.md`, cada una con ≥3 hallazgos `### fN` triangulados (≥2 fuentes externas citadas). Los tips de S88.4 citan `work/research/e88-tips/<tema>.md#fN`; `source_label()` ya los muestra como «Investigación ESCALA (nota interna fN)».

## 6. Riesgos aceptados

- No hay texto 2026 del workbook en el repo: la prueba anticopia no cubre las paráfrasis 2026. Mitigación: paráfrasis en español escritas desde cero; no se agrega el texto original.
- Dos historias (S88.3 y S88.4) suben los mismos conteos (registro y E6): S88.4 se fusiona después de S88.3 y recalcula.

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
    choice: "at:start se ve bajo el paso 1 y primero en la vista; ai_prompt y at:end en la revisión final y en la vista, en ese orden"
    rationale: "AI Setup y Vision Summary se usan antes de llenar; los demás al cerrar"
    constraint: "No mostrar prompts start en la revisión final"
  - id: D3
    choice: "AI Setup = extra_prompts start de swt; Vision Summary = extra_prompts start de vision-summary; Make Change Stick = ai_prompt de vision-summary"
    rationale: "No hay hoja vacía para AI Setup (rompería la regla de 3 tips); la prueba de vision-summary (10 tareas, semana) sigue verde"
    constraint: "Sin hoja nueva para AI Setup ni para Make Change Stick"
  - id: D4
    choice: "Id worksheet-bhag, nombre visible «Meta grande (BHAG)», plazo 10–30 años"
    rationale: "BHAG no está en vocabulary_rules de public-boundary; opsp.yaml y 7-strata.yaml ya lo usan"
    constraint: "vision-summary.yaml sigue sin la palabra BHAG (su prueba la prohíbe)"
  - id: D5
    choice: "Recorrido = cadena next_sheet en el último paso de cada hoja; orden fijado en tests/fixtures/workbook-2026-coverage.yaml"
    rationale: "Reusa GuideStep.next_sheet; cero código nuevo de motor"
    constraint: "No reusar coaching/journey; ningún yaml nuevo bajo conocimiento/ para el recorrido"
  - id: D6
    choice: "Mapa de 24 páginas en tests/fixtures con prueba que reusa check_coverage de E87"
    rationale: "Las páginas no pueden ir en hojas públicas"
    constraint: "Ningún número de página en conocimiento/; ni imágenes ni PDF del workbook en el repo"
  - id: D7
    choice: "SWT pasa a guiada en S88.1 con su prompt 2026 y la lista de 10 tendencias; S88.1 aporta el 3.er tip con un hallazgo nuevo en work/research/e88-tips/swt.md"
    rationale: "Una hoja guiada sin prompt no sirve; solo hay 2 fuentes reales para SWT"
    constraint: "swt.yaml sin metadata.fields en inglés ni términos vetados; mínimo 3 tips"
  - id: D8
    choice: "Fanocracy: prompt fiel (7 de 9 principios); los 9 en la guía. Life Purpose en conocimiento/people/worksheets"
    rationale: "Decisión de Eduardo"
    constraint: "No completar el prompt con los 2 principios faltantes"
constraints:
  - "Cada yaml nuevo bajo conocimiento/ regenera ontology/v2/e6-migration-map.json (scripts/build_e6_migration_map.py) y sube el conteo de tests/test_e6_migration.py (PAT-222)"
  - "Revisar governance/public-boundary.yaml antes de agregar llaves (PAT-221); llave raíz 'source' prohibida"
  - "Una prueba de punta a punta del Strategy Day completo del dueño (PAT-227)"
  - "Ningún número de página ni 'pág' en prompts o textos públicos"
  - "Sin nodos nuevos en ontology/v2/"
  - "Ejemplos con 'Tortillería El Sol:'; ≥3 tips con fuente por hoja guiada"
  - "Worktrees de historia copian .raise/pipelines/story.yaml (override historia/tarea, raise-conocido A43)"
  - "TDD; pyright strict, ruff y pytest en verde antes de cada commit"
```
