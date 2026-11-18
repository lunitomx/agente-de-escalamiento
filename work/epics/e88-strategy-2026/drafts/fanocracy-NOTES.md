# Hoja «De clientes a fans» (fanocracy) — notas del borrador

Estado: borrador. No se cambió ningún archivo del repo.

Archivo de la hoja: `drafts/fanocracy.yaml`. Destino propuesto: `conocimiento/strategy/worksheets/fanocracy.yaml`.

Fuente: Workbook Strategy 2026, p. 17 (los 9 principios y el prompt) y p. 18 (las 2 preguntas de discusión).

## 1. Revisión hecha

- Pasa el contrato del repo (`parse_guide`): 7 pasos, 3 tips, 4 secciones de vista. Lo corrí desde el scratchpad, sin escribir en el repo.
- Cada ejemplo empieza con «Tortillería El Sol:».
- El texto (sin comentarios) no trae palabras prohibidas: Scaling Up, BHAG, OPSP, Verne, Gazelles.
- El prompt no trae página ni «pág». Sí trae números (3, 5, 30), como el original.
- Los 3 tips apuntan a hallazgos con `triangulated: true`.

## 2. Por qué va en la decisión `strategy`

1. El registro solo tiene 4 decisiones: personas, estrategia, ejecución y dinero. No existe «marketing».
2. Estrategia ya tiene las hojas de cliente central y promesa de marca. Fans es el paso siguiente de esas dos.
3. El workbook pone Fanocracy dentro del día de estrategia (agenda, p. 2).
4. Solo 1 de los 9 principios toca personas («forma un equipo que también sea fan»). No alcanza para mandarla a `people`.

## 3. Entrada propuesta para el registro

Archivo: `conocimiento/registry/worksheets.yaml`.

```yaml
  - id: worksheet-fanocracy
    decision: strategy
    name: Fanocracy Marketing Worksheet
    name_es: "De clientes a fans"
    node_path: strategy/worksheets/fanocracy.yaml
    prerequisites: [worksheet-core-customer]
    outputs:
      - who your fans are today
      - score on 9 fan principles
      - 5 moves for the next 30 days
    difficulty: beginner
    time_estimate: "1 hour"
    time_es: "1 hora"
    summary_es: "Encuentra quién ya es fan de tu negocio, califica tu marketing en 9 principios y elige 5 acciones para los próximos 30 días."
    frequency: annual
    tags: [strategy, marketing, fans, fanocracy]
```

Cambios que trae en el mismo archivo y en pruebas:
- `total_worksheets: 21` pasa a `22`.
- El encabezado de la sección de estrategia pasa de (10) a (11).
- `coaching/worksheet/tests/test_root.py`: `EXPECTED_WORKSHEETS = 21` pasa a `22`.
- Opcional: agregar `worksheet-fanocracy` en `contains` de `conocimiento/decisions/strategy.yaml`.
  Hoy esa lista no tiene las hojas nuevas (por ejemplo bmc), así que no es obligatorio.

## 4. Borrador de pruebas (TDD, se escriben antes de la hoja)

Para `tests/test_e87_tool_guides.py`, siguiendo el estilo de las pruebas de bmc y sandbox.

```python
FANOCRACY = KNOWLEDGE / "strategy" / "worksheets" / "fanocracy.yaml"
FANOCRACY_STEPS = [
    "quien-te-ama",
    "que-reciben",
    "principios",
    "clientes-a-fans",
    "fans-a-clientes",
    "regalo",
    "acciones-30-dias",
]


def test_fanocracy_passes_the_contract() -> None:
    content = _load(FANOCRACY)
    assert content["id"] == "worksheet-fanocracy"
    assert content["decision"] == "strategy"
    guide = parse_guide(content)
    assert guide is not None
    assert [s.id for s in guide.guide.steps] == FANOCRACY_STEPS
    assert len(guide.tips) >= 3
    assert set(content["ai_prompt"]) == {"text"}


def test_fanocracy_examples_use_the_shared_business() -> None:
    guide = parse_guide(_load(FANOCRACY))
    assert guide is not None
    for step in guide.guide.steps:
        assert step.example.startswith("Tortillería El Sol:"), step.id


def test_fanocracy_asks_both_discussion_questions() -> None:
    """Workbook Strategy 2026, p. 18: customers to fans, and fans to customers."""
    guide = parse_guide(_load(FANOCRACY))
    assert guide is not None
    questions = {s.id: s.question.lower() for s in guide.guide.steps}
    assert "clientes en fans" in questions["clientes-a-fans"]
    assert "fans en clientes" in questions["fans-a-clientes"]


def test_fanocracy_lists_the_nine_principles() -> None:
    guide = parse_guide(_load(FANOCRACY))
    assert guide is not None
    how = next(s.how for s in guide.guide.steps if s.id == "principios")
    assert "9" in how
    assert how.count(";") == 8  # 9 principios separados por punto y coma


def test_fanocracy_prompt_has_no_page_and_plain_names() -> None:
    content = _load(FANOCRACY)
    prompt = content["ai_prompt"]["text"]
    assert not re.search(r"\bp\.|p[aá]g", prompt.lower())
    text = FANOCRACY.read_text(encoding="utf-8")
    for term in ("BHAG", "OPSP", *_forbidden_terms()):
        assert term.lower() not in text.lower(), term
```

Las pruebas generales de tips (`test_tip_sources_are_triangulated_anchors_or_clean`) y de vista
ya cubren la hoja si recorren todas las hojas guiadas. Hay que confirmarlo al escribir la historia.

## 5. Dudas abiertas

1. **Los tips no son de fans.** No hay investigación de Fanocracy en el repo.
   - Usé 3 hallazgos triangulados de otras hojas: cliente central f4, actividades diferenciadoras f4 y promesa de marca f5.
   - Adapté el texto del primero («tu descripción» pasa a «tus fans»).
   - El hallazgo que mejor encaja (promesa de marca f7, sobre recomendaciones) no está triangulado. Citarlo rompe la prueba.
   - Las únicas menciones de David Meerman Scott están en `scaling_up_llamaparse.md`, que es fuente prohibida.
   - Recomiendo una historia de investigación (`/rai-research`) para tener 3 tips propios antes de publicar la hoja.
2. **7 o 9 principios.** La p. 17 lista 9 principios. El prompt de la misma página nombra solo 7: quita «influencers» y «equipo fan».
   - El paso `principios` pide los 9. El prompt respeta los 7 del original.
   - Decide Eduardo: ¿dejamos el prompt fiel (7) o lo completamos a 9?
3. **Página dentro del prompt.** El alcance de la épica (criterio 5) pide `ai_prompt.page`. El código y las pruebas la rechazan.
   - En este borrador la página va como comentario YAML y en el mapa de cobertura.
   - Hay que corregir el criterio 5 del alcance para que no se contradiga con el código.
4. **Nombre en español.** Propongo «De clientes a fans». Otras opciones: «Fans de tu marca», «Fanocracia».
   - «Fans» es palabra en inglés, pero se usa así en México.
5. **Aclaraciones mías.** En la lista de tendencias (archivo de prompts) agregué aclaraciones que no están en el workbook:
   «como Ozempic», «terceros lugares», «generación sándwich». En esta hoja, «suelta lo que creas»
   es mi forma corta de «let go of your creations» (dejar que tus fans usen y transformen lo que haces).
6. **Mapa de cobertura 2026.** No existe. Propuesta en la sección D del archivo de prompts.
   Sin el texto 2026 en el repo, ninguna prueba revisa que no copiemos frases del original.
7. **Páginas del encargo.** El encargo decía SWT en p. 5 y 6, y actividades diferenciadoras en p. 7 y 8.
   El prompt de SWT está solo en la p. 5; la p. 6 es la hoja impresa. El de actividades está solo en la p. 7; la p. 8 es la hoja impresa.
8. **Fechas del ejemplo.** El paso `acciones-30-dias` usa mayo como ejemplo. Si se prefiere sin fechas, se cambia a «semana 1, semana 2…».
