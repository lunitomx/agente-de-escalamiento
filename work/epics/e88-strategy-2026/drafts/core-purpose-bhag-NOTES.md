# Notas: hojas «Propósito central» y «Meta grande» (borradores)

Fuente: Workbook Strategy 2026 (EOA), páginas 9-14. Son borradores para revisión.
No se cambió nada del repo. Los dos YAML siguen la forma de `vision-summary.yaml`.

## 1. Archivos

| Archivo | Va en el repo a |
|---|---|
| `core-purpose.yaml` | `conocimiento/strategy/worksheets/core-purpose.yaml` |
| `bhag.yaml` | `conocimiento/strategy/worksheets/bhag.yaml` |
| `registry-entries.yaml` | se pega en `conocimiento/registry/worksheets.yaml` |

## 2. Qué se comprobó (en una copia fuera del repo)

Copia de `conocimiento/` en `scratchpad/sandbox1/.escala/knowledge/`, con las 2 hojas y el registro nuevo.

- `parse_guide` acepta las 2 hojas. `derived_errors` sale vacío.
- Recorrido completo con el motor: start → 8 y 7 pasos → revisión final → save.
  Save escribe yaml, html y md y devuelve `open_cmd`. Sin errores.
- «Meta grande» muestra «Esto ya llenaste:» con el propósito guardado.
- Cada instrucción (`how`) tiene 20 palabras o menos.
- Cada ejemplo empieza con «Tortillería El Sol:».
- `metadata.fields` es igual a la lista de pasos.
- `ai_prompt` solo tiene `text`, sin número de página.
- Cero términos prohibidos de `governance/public-boundary.yaml`.
- Cero frases de 10 palabras copiadas de `metodologias_parsed/strategy_workbook.md`.

## 3. Cambios al registro

1. Pegar las 2 entradas de `registry-entries.yaml` después de `worksheet-vision-summary`.
2. `total_worksheets: 21` → `23`.
3. Encabezado `# ── STRATEGY (10)` → `(12)`.
4. Opcional: `conocimiento/decisions/strategy.yaml` lista con `contains` solo 4 de las 10 hojas de estrategia (no lista «Resumen de visión»). Agregar las 2 nuevas no es obligatorio.

## 4. Prueba a agregar (`tests/test_e87_tool_guides.py`)

Usa los ayudantes que ya existen en ese archivo: `_load`, `_forbidden_terms`, `ANCHOR_SOURCE_RE`, `WORD_RE`, `WORKBOOK`, `KNOWLEDGE`.

```python
from coaching.worksheet import derived_errors

CORE_PURPOSE = KNOWLEDGE / "strategy" / "worksheets" / "core-purpose.yaml"
BHAG_SHEET = KNOWLEDGE / "strategy" / "worksheets" / "bhag.yaml"
REGISTRY = KNOWLEDGE / "registry" / "worksheets.yaml"

PURPOSE_STEPS = [
    "que-hace", "cinco-porques", "fundador", "si-desaparecemos",
    "cuatro-tipos", "una-palabra", "proposito", "prueba",
]
BHAG_STEPS = [
    "pasion", "mejor-en", "cliente-x", "borradores",
    "impacto", "meta-grande", "prueba",
]
PURPOSE_SECTIONS = [
    "Qué haces y por qué importa", "De dónde viene",
    "Tus borradores", "Tu propósito central",
]
BHAG_SECTIONS = ["Tus tres círculos", "Tus borradores", "Tu meta grande"]
PAGE_RE = re.compile(r"\bp\.\s*\d|\bpágina\b", re.IGNORECASE)


@pytest.mark.parametrize(
    ("path", "steps", "sections"),
    [
        (CORE_PURPOSE, PURPOSE_STEPS, PURPOSE_SECTIONS),
        (BHAG_SHEET, BHAG_STEPS, BHAG_SECTIONS),
    ],
)
def test_purpose_and_big_goal_pass_the_contract(
    path: Path, steps: list[str], sections: list[str]
) -> None:
    content = _load(path)
    guide = parse_guide(content)
    assert guide is not None
    assert [s.id for s in guide.guide.steps] == steps
    assert content["metadata"]["fields"] == steps
    assert all(s.example.startswith("Tortillería El Sol:") for s in guide.guide.steps)
    assert all(len(s.how.split()) <= 20 for s in guide.guide.steps)
    assert len(guide.tips) >= 3
    assert any(ANCHOR_SOURCE_RE.match(t.source) for t in guide.tips)
    assert set(content["ai_prompt"]) == {"text"}
    assert not PAGE_RE.search(content["ai_prompt"]["text"])
    assert guide.view.layout == "cards"
    assert [s.title for s in guide.view.sections] == sections
    assert derived_errors(content, ROOT / "conocimiento") == []
    text = path.read_text(encoding="utf-8").lower()
    for term in _forbidden_terms():
        assert term.lower() not in text, term


def test_purpose_prompt_keeps_the_workbook_rules() -> None:
    text = _load(CORE_PURPOSE)["ai_prompt"]["text"]
    assert "3 a 7 palabras" in text
    assert "8 opciones" in text
    assert "3 opciones de una sola palabra" in text


def test_big_goal_prompt_keeps_the_workbook_rules() -> None:
    text = _load(BHAG_SHEET)["ai_prompt"]["text"]
    assert "10-30 años" in text
    assert "5 opciones" in text
    assert "BHAG" not in text


def test_big_goal_reads_purpose_promise_and_customer() -> None:
    sources = parse_guide(_load(BHAG_SHEET)).derived_from
    assert [(s.sheet, s.fields, s.into, s.required) for s in sources] == [
        ("worksheet-core-purpose", ["proposito"], "pasion", False),
        ("worksheet-brand-promise", ["promesa-principal"], "mejor-en", False),
        ("worksheet-core-customer", ["quien-es"], "cliente-x", False),
    ]


def test_purpose_and_big_goal_are_registered() -> None:
    registry = _load(REGISTRY)
    by_id = {w["id"]: w for w in registry["worksheets"]}
    assert by_id["worksheet-core-purpose"]["node_path"] == (
        "strategy/worksheets/core-purpose.yaml"
    )
    assert by_id["worksheet-bhag"]["node_path"] == "strategy/worksheets/bhag.yaml"
    assert by_id["worksheet-bhag"]["prerequisites"] == ["worksheet-core-purpose"]
    assert registry["total_worksheets"] == len(registry["worksheets"])


@pytest.mark.parametrize("path", [CORE_PURPOSE, BHAG_SHEET])
def test_purpose_and_big_goal_do_not_copy_the_workbook(path: Path) -> None:
    def shingles(text: str) -> set[tuple[str, ...]]:
        words = WORD_RE.findall(text.lower())
        return {tuple(words[i : i + 10]) for i in range(len(words) - 9)}

    copied = shingles(path.read_text(encoding="utf-8")) & shingles(
        WORKBOOK.read_text(encoding="utf-8")
    )
    assert not copied, sorted(" ".join(s) for s in copied)[:3]
```

## 5. De qué página sale cada cosa (no va en el YAML)

El modelo `AiPrompt` solo acepta `text`. Su docstring y la política del repo dicen: sin números de página en `conocimiento/`.
Por eso la cita de página vive aquí y, si Eduardo aprueba, en un fixture nuevo.

| Página (Workbook Strategy 2026) | Qué tiene | Nodo |
|---|---|---|
| 9 | Introducción al propósito (ejemplos) | worksheet-core-purpose |
| 10 | Hoja de trabajo del propósito (5 porqués, 4 tipos, fundador) | worksheet-core-purpose |
| 11 | Descubrimiento, ejemplo con IA y prompt del propósito (p. 11) | worksheet-core-purpose |
| 11 (abajo) - 12 | Qué es la meta grande y ejemplos | worksheet-bhag |
| 13 | Hoja de los tres círculos | worksheet-bhag |
| 14 (arriba) | Ejemplo lleno y prompt de la meta grande (p. 14) | worksheet-bhag |
| 14 (abajo) | Visión vívida | fuera de alcance |

Propuesta de fixture: `tests/fixtures/e88-workbook-2026-coverage.yaml`, con la misma forma que `e87-workbook-coverage.yaml` (ese es del workbook 2025, 38 páginas).

## 6. Tips: cuántos tienen fuente investigada

La regla pide 3 tips o más con fuente real del repo. Cada hoja tiene 4. Pero solo 1 por hoja es un hallazgo triangulado:

| Hoja | Tip | Fuente | Tipo |
|---|---|---|---|
| Propósito | 5 porqués | `work/research/e87-tips/vision-summary.md#f2` | triangulado |
| Propósito | ¿Qué perdería el mundo? | `conocimiento/strategy/concepts/core-purpose.yaml` | nodo de conocimiento |
| Propósito | Decirlo en menos de un minuto | `conocimiento/strategy/concepts/core-purpose.yaml` | nodo de conocimiento |
| Propósito | 3 acciones, desde el primer día | `conocimiento/people/concepts/culture.yaml` | nodo de conocimiento |
| Meta grande | Número con fecha en tu unidad | `work/research/e87-tips/vision-summary.md#f3` | triangulado |
| Meta grande | Busca tu X | `conocimiento/strategy/tools/profit-per-x.yaml` | nodo de conocimiento |
| Meta grande | Revísala cada año | `conocimiento/strategy/concepts/bhag.yaml` | nodo de conocimiento |
| Meta grande | 3 acciones, desde el primer día | `conocimiento/people/concepts/culture.yaml` | nodo de conocimiento |

- Las 6 fuentes de nodo existen y pasan la prueba de fuentes de tips. Esa prueba solo exige ancla real a las fuentes `work/research/...`.
- No existe `work/research/e87-tips/core-purpose.md` ni `bhag.md`.
- Recomiendo una historia de investigación que cree esos 2 archivos con 3 hallazgos triangulados cada uno.
- Riesgo de vista: si la página del dueño muestra la fuente, verá una ruta `conocimiento/...`. Revisar `source_label`.

## 7. Dudas abiertas y decisiones tomadas

1. **Cita de página en el prompt.** Se pidió citar la página en `ai_prompt`. El contrato lo prohíbe (llave extra). La cita quedó en la sección 5. Recomiendo el fixture e88.
2. **Nombre «Meta grande» o «BHAG».** La hoja «Resumen de visión» prohíbe «BHAG» en su texto. Usé `name_es: Meta grande` y el prompt no dice BHAG. El `id` y `name` en inglés sí dicen BHAG, igual que el concepto `concept-bhag`. Recomiendo dejarlo así.
3. **Plazo: 10-30 o 10-25 años.** El workbook 2026 dice 10-30. El concepto `bhag.yaml`, el tip f3 y la hoja OPPP dicen 10-25. Usé 10-30 en la hoja nueva y no cité el plazo en el tip f3. Hay que decidir uno para todo el repo.
4. **Tercer círculo.** La p. 13 dice «cliente (tu X)». La p. 14 dice «motor económico (utilidad por X)». Los junté en un paso: `cliente-x`.
5. **Ejemplo de propósito distinto.** «Resumen de visión» usa un propósito de 15 palabras («que ninguna fonda de la colonia se quede sin comida caliente…»). La regla 2026 pide 3 a 7. La hoja nueva usa «que la fonda de barrio siga viva». Conviene alinear el ejemplo de «Resumen de visión».
6. **La meta grande sí coincide.** «400 fondas surtidas cada día en Jalisco para 2040» es la misma frase en las 2 hojas.
7. **Campo `into` de `derived_from`.** El motor no lo usa hoy. Puse el id del paso que recibe el dato (`pasion`, `mejor-en`, `cliente-x`). «Resumen de visión» usa `customer`, que no es un paso.
8. **Fuentes opcionales.** Las 3 fuentes de «Meta grande» van con `required: false`. Si faltan, la hoja no muestra «Falta:» y deja escribir el paso.
9. **5 porqués en un solo paso.** Más simple. La alternativa son 5 pasos, uno por porqué.
10. **Ejemplo lleno de la p. 14.** Está escrito a mano y casi no se lee. No lo usé.
11. **Siguiente paso posible.** «Resumen de visión» podría leer `proposito` y `meta-grande` de estas hojas con `derived_from`. Queda fuera de este borrador.
