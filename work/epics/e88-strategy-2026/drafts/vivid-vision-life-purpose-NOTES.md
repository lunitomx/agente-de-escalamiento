# Notas: borradores de Visión vívida y Tu propósito de vida

Fuente: Workbook Strategy 2026 (24 páginas). Estos son borradores. No se cambió nada en el repo.

## 1. Qué contiene cada borrador

| Hoja | Archivo | Páginas | Decisión | Pasos | Consejos | Prompt de IA |
|---|---|---|---|---|---|---|
| Visión vívida (`worksheet-vivid-vision`) | `vivid-vision.yaml` | pp. 14, 15, 16 | strategy | 17 (fecha + meta grande + 15 preguntas) | 3 | 1 principal + 4 pasos extra en `ai_followups` |
| Tu propósito de vida (`worksheet-life-purpose`) | `life-purpose.yaml` | pp. 18, 19 | people | 4 (pasión, poder, juego, propósito) | 3 (encaje parcial) | 1 (entrevista ikigai) |

Validación (solo lectura, `PYTHONDONTWRITEBYTECODE=1`, script en `scratchpad/scripts/validate_drafts.py`):

- Las 2 hojas pasan `parse_guide` (contrato `ToolGuide`).
- Cada ejemplo empieza con «Tortillería El Sol:».
- `metadata.fields` es igual a la lista de pasos.
- Cada fuente de consejo existe en `work/research/e87-tips/`.
- No hay términos de `governance/public-boundary.yaml`, ni llave raíz `source`.
- No hay número de página dentro de los YAML.
- No hay nombres de terceros (Canfield, Sinek, Qumu, MN Custom Homes).

### Mapa pregunta por pregunta (p. 16)

| Workbook p. 16 | Paso |
|---|---|
| Vision Date | `fecha-vision` |
| BHAG | `meta-grande` |
| Top line revenue | `ingresos` |
| People on team | `tamano-equipo` |
| How people describe the culture | `cultura` |
| What the press says | `prensa` |
| Local news | `noticias-locales` |
| Favorite blog / magazine | `blog-revista` |
| What the team loves about vision & direction | `equipo-ama` |
| How customers describe working with you | `clientes-describen` |
| What they tell their best friends | `clientes-amigos` |
| Accomplishment you're most proud of | `logro-tuyo` |
| Accomplishment the team is most proud of | `logro-equipo` |
| What you do better than anyone | `mejor-que-nadie` |
| Describe office and culture in detail | `oficina-cultura` |
| Describe service area | `zona-servicio` |
| Who are your customers and how they feel | `clientes-sienten` |

El intro de p. 16 (cerrar los ojos, respirar, imaginar el lugar, el equipo, los socios y los clientes) va en el `how` de `fecha-vision`.

La hoja de p. 19 tiene: Pasión → `pasion`, Poderes → `poderes`, Juego → `juego`, «The Purpose of my life is:» → `proposito`. La idea del «mundo perfecto» del intro va en el `how` de `proposito`.

## 2. Hallazgos del motor

1. **Solo hay UN prompt de IA.**
   - `AiPrompt` (`coaching/worksheet/guide.py:90`) usa `extra="forbid"` y solo tiene `text`.
   - Una lista de prompts falla la validación.
   - `test_guide.py:90` rechaza cualquier llave extra, como `page`.
2. **`ToolGuide` usa `extra="ignore"`.**
   - Por eso la llave raíz `ai_followups` que usé pasa la validación hoy.
   - **No se muestra en ningún lado.** `_review_lines`, `build_view`, `render_html` y `render_markdown` solo leen `ai_prompt.text`.
3. **Los prerrequisitos frenan la recomendación.**
   - `progress/engine.py` solo recomienda la hoja siguiente si sus prerrequisitos están completos.
   - Por eso propongo `prerequisites: []` para las dos.
4. **La política pública prohíbe páginas en los nodos.**
   - El docstring de `AiPrompt` dice «no page numbers».
   - `test_brand_promise_ai_prompt_has_no_page` prohíbe `p.` y dígitos en ese prompt.
   - Por eso las páginas viven solo en estas notas y en la fixture de la sección 6.

### Opciones para guardar los pasos extra (follow-ups)

| Opción | Cambio | Se ve en la hoja | Recomiendo |
|---|---|---|---|
| A. Campo `followups` dentro de `AiPrompt` | `followups: list[AiFollowup]` (title, text), con `extra="forbid"`; mostrarlo en `_review_lines`, `build_view`, `render_html` y `render_markdown`; agregar pruebas | Sí, debajo del prompt principal | **Sí.** El modelo lo valida y queda junto a su prompt. |
| B. Llave raíz `ai_followups` (como en el borrador) | El mismo trabajo de mostrar, más un campo en `ToolGuide` | Sí, después del cambio | No. Queda separado del prompt. |
| C. Sin código: todo en `ai_prompt.text` | Ninguno. Se agrega «Después del borrador: 1)… 2)… 3)… 4)…» al texto | Sí, hoy mismo | Solo si no hay tiempo para A. El bloque crece a unas 280 palabras. |

Si se elige A, el borrador cambia así: `ai_followups` pasa a `ai_prompt.followups`.

## 3. Por qué Tu propósito de vida va en `people`

1. **Precedente D8.** El plan personal de una página del mismo workbook (`worksheet-oppp`) ya vive en `people`.
2. **Es personal, no de la empresa.** La hoja habla del dueño, no del negocio. «Pasión, poder, juego» son de la persona.
3. **El motor ya trata lo personal en `people`.** El validador `oppp_vision_artifacts` usa el contexto «personal».
4. **Solo hay 4 decisiones** (people, strategy, execution, cash). `strategy` es la estrategia de la empresa.
5. **La hoja alimenta al OPPP.** El propósito de vida da la base de la visión personal a 10-25 años. Por eso la relación es `feeds-into worksheet-oppp`.

Ruta propuesta: `conocimiento/people/worksheets/life-purpose.yaml`.

Visión vívida va en `strategy`: `conocimiento/strategy/worksheets/vivid-vision.yaml`. Es la empresa a 3-5 años y alimenta el Resumen de visión.

## 4. Entradas del registro (`conocimiento/registry/worksheets.yaml`)

`total_worksheets: 21` → `23`. Sección PEOPLE pasa de 4 a 5. STRATEGY pasa de 10 a 11.

```yaml
  # --- PEOPLE ---
  - id: worksheet-life-purpose
    decision: people
    name: Life Purpose Worksheet
    name_es: Tu propósito de vida
    node_path: people/worksheets/life-purpose.yaml
    prerequisites: []
    outputs:
      - personal life purpose statement
    difficulty: beginner
    time_estimate: "1 hour"
    time_es: "1 hora"
    summary_es: "Escribe lo que te apasiona, tus fortalezas y con quién te gusta jugar. Con eso declara el propósito de tu vida."
    frequency: annually
    tags: [people, life-purpose, personal, why]

  # --- STRATEGY ---
  - id: worksheet-vivid-vision
    decision: strategy
    name: Vivid Vision Worksheet
    name_es: Visión vívida
    node_path: strategy/worksheets/vivid-vision.yaml
    prerequisites: []          # opción: [worksheet-vision-summary]; ver incertidumbre 7
    outputs:
      - 3-5 year vivid vision of the company, written in present tense
    difficulty: intermediate
    time_estimate: "1-2 hours"
    time_es: "1-2 horas"
    summary_es: "Describe tu empresa en una fecha de 3 a 5 años, en presente: números, equipo, cultura, clientes y lo que dicen de ti."
    frequency: annually
    tags: [strategy, vivid-vision, vision, 3-5-years]
```

Conteos fijos que hay que cambiar de 21 a 23:

- `coaching/worksheet/tests/test_guide.py:217` → `assert len(sheets) == 23`
- `coaching/worksheet/tests/test_root.py:20` → `EXPECTED_WORKSHEETS = 23`
- registro → `total_worksheets: 23`

## 5. Borrador de prueba (estilo `tests/test_e87_tool_guides.py`)

```python
VIVID_VISION = KNOWLEDGE / "strategy" / "worksheets" / "vivid-vision.yaml"
LIFE_PURPOSE = KNOWLEDGE / "people" / "worksheets" / "life-purpose.yaml"
COVERAGE_2026 = ROOT / "tests" / "fixtures" / "strategy-2026-workbook-coverage.yaml"

VIVID_STEPS = (
    "fecha-vision", "meta-grande", "ingresos", "tamano-equipo", "cultura",
    "prensa", "noticias-locales", "blog-revista", "equipo-ama",
    "clientes-describen", "clientes-amigos", "logro-tuyo", "logro-equipo",
    "mejor-que-nadie", "oficina-cultura", "zona-servicio", "clientes-sienten",
)
LIFE_STEPS = ("pasion", "poderes", "juego", "proposito")


@pytest.mark.parametrize(
    ("path", "steps", "decision"),
    [(VIVID_VISION, VIVID_STEPS, "strategy"), (LIFE_PURPOSE, LIFE_STEPS, "people")],
)
def test_e87_2026_sheets_pass_the_contract(
    path: Path, steps: tuple[str, ...], decision: str
) -> None:
    content = _load(path)
    guide = parse_guide(content)
    assert guide is not None
    assert content["decision"] == decision
    assert tuple(s.id for s in guide.guide.steps) == steps
    assert tuple(content["metadata"]["fields"]) == steps
    assert all(s.example.startswith("Tortillería El Sol:") for s in guide.guide.steps)
    assert len(guide.tips) >= 3
    assert all(ANCHOR_SOURCE_RE.match(t.source) for t in guide.tips)
    assert set(content["ai_prompt"]) == {"text"}   # cambia si se elige la opción A
    assert not re.search(r"\bp\.\s*\d", content["ai_prompt"]["text"])


def test_vivid_vision_has_four_followups() -> None:
    content = _load(VIVID_VISION)
    followups = content["ai_followups"]          # opción A: content["ai_prompt"]["followups"]
    assert [f["title"] for f in followups] == [
        "Hazla un cartel de pared", "Hazla visual", "Ponla a prueba", "Imprímela",
    ]
    assert all(f["text"] for f in followups)


def test_vivid_vision_view_covers_every_step() -> None:
    content = _load(VIVID_VISION)
    shown = [s for sec in content["view"]["sections"] for s in sec["steps"]]
    assert sorted(shown) == sorted(VIVID_STEPS)


def test_life_purpose_lives_in_people_and_feeds_the_oppp() -> None:
    content = _load(LIFE_PURPOSE)
    rels = {(r["type"], r["target"]) for r in content["relationships"]}
    assert ("belongs-to", "decision-people") in rels
    assert ("feeds-into", "worksheet-oppp") in rels


@pytest.mark.parametrize(
    ("node", "pages"),
    [("worksheet-vivid-vision", (14, 15, 16)), ("worksheet-life-purpose", (18, 19))],
)
def test_2026_pages_are_covered(node: str, pages: tuple[int, ...]) -> None:
    coverage = _load(COVERAGE_2026)
    by_page = {int(e["page"]): e for e in coverage["pages"]}
    for number in pages:
        assert node in by_page[number].get("nodes", []), number
```

## 6. Fixture propuesta de cobertura 2026

`tests/fixtures/strategy-2026-workbook-coverage.yaml`. Va aparte de la de 2025, porque `test_e87_workbook_coverage.py` fija `total_pages == 38`. Solo pongo las páginas que revisé para esta tarea. Las demás quedan en `pending` hasta que alguien las clasifique.

```yaml
# Mapa de cobertura del Strategy Workbook 2026. Procedencia, no contenido público.
workbook: strategy-2026
total_pages: 24
pages:
  - page: 14
    class: tool
    nodes: [worksheet-vivid-vision]
    content: "Meta grande (diagrama de 3 círculos) y definición de Visión vívida a 3-5 años"
  - page: 15
    class: tool
    nodes: [worksheet-vivid-vision]
    content: "Visión vívida: prompt principal y 3 pasos extra; cierre 'imprímela'"
  - page: 16
    class: tool
    nodes: [worksheet-vivid-vision]
    content: "Visión vívida: hoja con fecha, meta grande y 15 preguntas"
  - page: 17
    class: no_tool
    reason: "ejemplo lleno de Visión vívida (ilegible) y tema de fans, fuera de alcance"
  - page: 18
    class: tool
    nodes: [worksheet-life-purpose]
    content: "Porqué personal y propósito de vida; prompt de entrevista ikigai"
  - page: 19
    class: tool
    nodes: [worksheet-life-purpose]
    content: "Hoja: pasión, poder, juego y 'el propósito de mi vida es'"
pending: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 20, 21, 22, 23, 24]
```

Nota: p. 14 también trae un prompt para la meta grande. No lo usé. Tampoco cabe en el único `ai_prompt` de Visión vívida.

## 7. Consejos: qué tan bien encajan

Regla: cada consejo cita una fuente que ya existe en el repo. Busqué con `git grep` en `conocimiento/` y `work/research/`. **No hay ninguna fuente sobre Visión vívida, ikigai, Canfield, Sinek o propósito de vida personal.** Solo aparecen en `metodologias_parsed/`, que es contenido derivado y no se puede citar.

| Hoja | Paso | Fuente | Encaje |
|---|---|---|---|
| Visión vívida | `meta-grande` | `vision-summary.md#f3` (meta grande = número con fecha) | Bueno |
| Visión vívida | `cultura` | `oppp-vision-boards.md#f1` (escribir algo que se ve o se cuenta) | Medio |
| Visión vívida | todos | `oppp-vision-boards.md#f4` (obstáculo + plan «si pasa X, haré Y») | Bueno: va con «las 5 cosas en riesgo» del prompt |
| Propósito | `proposito` | `vision-summary.md#f2` («¿por qué importa?» hasta 5 veces) | Parcial: la fuente habla del propósito de una empresa |
| Propósito | `juego` | `oppp-vision-boards.md#f5` (las relaciones pesan más) | Parcial |
| Propósito | `poderes` | `oppp-vision-boards.md#f1` (concreto y visible) | Parcial |

**FALTA (shortfall):**

- Visión vívida tiene 3 consejos citables. Ninguno es sobre la técnica misma.
- Propósito de vida llega a 3 solo con encaje parcial. Ninguno respalda Pasión/Poder/Juego ni el ikigai.
- Recomiendo un `/rai-research` antes de publicar. Saldrían 2 archivos nuevos: `e87-tips/vivid-vision.md` y `e87-tips/life-purpose.md`.
- PRECAUCIÓN: `tests/test_e87_research_tips.py` exige exactamente 8 archivos en `work/research/e87-tips/`. Hay que subir ese número o usar otra carpeta.
- Punto a verificar en esa investigación: el diagrama de 4 círculos del ikigai es una adaptación occidental, no el concepto japonés original.

## 8. Incertidumbres y decisiones abiertas

1. **Ikigai frente a las 3 P.**
   - El prompt (p. 18) usa 4 círculos: amo, soy bueno, el mundo necesita, me pueden pagar.
   - La hoja (p. 19) usa 3: Pasión, Poder, Juego.
   - «Juego» no tiene círculo en el ikigai. «Me pueden pagar» no tiene casilla en la hoja.
   - Lo dejé fiel a las dos páginas. Opción: agregar un paso «¿Por qué te pagarían?». Eso ya no sería fiel a p. 19.
2. **Páginas: el pedido contra la política.**
   - El pedido decía citar la página en el prompt («Workbook Strategy 2026, p. 15»).
   - El repo lo prohíbe en nodos públicos (docstring de `AiPrompt` y pruebas).
   - Seguí la política del repo. Las páginas están en estas notas y en la fixture de la sección 6.
3. **El ejemplo de p. 17 es ilegible.** No usé nada de él. Todos los ejemplos son de Tortillería El Sol y siguen las cifras del Resumen de visión (6 sucursales, 120 fondas, meta de 400 fondas para 2040).
4. **Nombre en español.** Usé «Visión vívida». Otras opciones: «Visión viva» o «Tu empresa en 3 años».
5. **La prueba de no copiar.** `test_vision_summary_does_not_copy_the_workbook` compara contra `metodologias_parsed/strategy_workbook.md` (2025). El workbook 2026 no está procesado, así que esa prueba no cubre estas hojas.
6. **Se cruza con el OPPP.** El prompt del OPPP ya pide una carta «desde dentro de tres años, en presente». Visión vívida pide lo mismo para la empresa. Propongo dejar las dos: una es personal y la otra es de la empresa. Vale revisar que el coach no las confunda.
7. **Prerrequisitos.** Dejé `[]` en las dos. Si Visión vívida pide `worksheet-vision-summary`, el motor no la recomienda hasta terminar el Resumen de visión. El paso `meta-grande` ya dice «si ya llenaste tu Resumen de visión, cópiala».
8. **La palabra «BHAG».** `test_vision_summary_uses_plain_spanish_names` prohíbe «BHAG» en el Resumen de visión. Mi borrador no lo dice en el texto. Solo aparece en la relación `requires concept-bhag`, que es el id real del concepto. El Resumen de visión no tiene esa relación. Si se quiere el mismo criterio, se quita la relación.
9. **Frecuencia y tiempo.** Son supuestos míos: las dos son anuales; 1 a 2 horas para Visión vívida y 1 hora para Propósito. El workbook no lo dice.
