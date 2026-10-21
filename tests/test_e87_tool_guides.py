"""S87.2: guided sheets follow the ToolGuide contract and cite safe sources.

The public-vocabulary terms are read from ``governance/public-boundary.yaml``;
this file never writes them (decision D5 of S87.2).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from coaching.worksheet.guide import parse_guide

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "conocimiento"
COVERAGE = ROOT / "tests" / "fixtures" / "e87-workbook-coverage.yaml"
POLICY = ROOT / "governance" / "public-boundary.yaml"
CORE_CUSTOMER = KNOWLEDGE / "strategy" / "worksheets" / "core-customer.yaml"
BRAND_PROMISE_CONCEPT = KNOWLEDGE / "strategy" / "concepts" / "brand-promise.yaml"
BRAND_PROMISE = KNOWLEDGE / "strategy" / "worksheets" / "brand-promise.yaml"
DIFF_ACTIVITIES = (
    KNOWLEDGE / "strategy" / "worksheets" / "differentiating-activities.yaml"
)
OPPP_SHEET = KNOWLEDGE / "people" / "worksheets" / "oppp.yaml"
OPPP_CARD = KNOWLEDGE / "people" / "tools" / "oppp.yaml"
OPPP_ROW_STEPS = ("vision-10-25-anos", "metas-un-ano", "empezar", "dejar")
EIGHT_AREAS = (
    "relación",
    "familia",
    "amigos",
    "salud",
    "trabajo",
    "dinero",
    "diversión",
    "espiritual",
)
ANCHOR_SOURCE_RE = re.compile(r"^(work/research/e87-tips/[a-z0-9-]+\.md)#(f\d+)$")
YAML_BLOCK_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)


def _load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _guided_sheets() -> list[Path]:
    return sorted(p for p in KNOWLEDGE.rglob("*.yaml") if "guide" in _load(p))


def _forbidden_terms() -> list[str]:
    policy = _load(POLICY)
    terms: list[str] = []
    for rule in policy["vocabulary_rules"]:
        terms.extend(str(t) for t in rule["terms"])
    return terms


def _findings(research: Path) -> dict[str, dict[str, Any]]:
    text = research.read_text(encoding="utf-8")
    found: dict[str, dict[str, Any]] = {}
    for block in YAML_BLOCK_RE.findall(text):
        data = yaml.safe_load(block)
        if isinstance(data, dict) and "id" in data:
            found[str(data["id"])] = data
    return found


def test_core_customer_passes_the_contract() -> None:
    guide = parse_guide(_load(CORE_CUSTOMER))
    assert guide is not None
    assert [s.id for s in guide.guide.steps] == [
        "top-5-clientes",
        "atributos",
        "top-atributos",
        "persona-ejemplo",
        "quien-es",
        "prueba-quien",
        "necesidad",
        "chequeo-promesa",
        "mejor-en",
        "diferente-en",
        "raro-o-malo",
    ]
    assert len(guide.tips) == 5
    assert guide.view.layout == "cards"
    assert len(guide.view.sections) == 4
    assert guide.ai_prompt is not None and guide.ai_prompt.text


def test_differentiating_activities_passes_the_contract() -> None:
    content = _load(DIFF_ACTIVITIES)
    guide = parse_guide(content)
    assert guide is not None
    assert content["id"] == "worksheet-differentiating-activities"
    assert [s.id for s in guide.guide.steps] == [
        "competidores",
        "eje-personas",
        "eje-producto",
        "eje-operaciones",
        "eje-terminos",
        "actividades-elegidas",
        "como-se-refuerzan",
        "que-dejas-de-hacer",
    ]
    assert sorted(t.source.rsplit("#", 1)[1] for t in guide.tips) == [
        "f1",
        "f2",
        "f4",
    ]
    assert guide.view.layout == "cards"
    assert [sec.title for sec in guide.view.sections] == [
        "Tu competencia",
        "En qué eres distinto",
        "Tus actividades diferenciadoras",
    ]
    assert guide.ai_prompt is not None and guide.ai_prompt.text


def test_brand_promise_passes_the_contract() -> None:
    guide = parse_guide(_load(BRAND_PROMISE))
    assert guide is not None
    assert [s.id for s in guide.guide.steps] == [
        "cuentan-esperan-solo-tu",
        "promesa-principal",
        "promesas-de-apoyo",
        "medidas",
        "prueba-de-promesa",
        "lealtad",
        "garantia",
        "antipromesas",
    ]
    assert all(s.example.startswith("Tortillería El Sol:") for s in guide.guide.steps)
    assert len(guide.tips) >= 3
    assert guide.view.layout == "cards"
    assert len(guide.view.sections) == 4


def test_brand_promise_tips_are_only_f1_f2_f5() -> None:
    guide = parse_guide(_load(BRAND_PROMISE))
    assert guide is not None
    assert sorted(t.source for t in guide.tips) == [
        "work/research/e87-tips/brand-promise.md#f1",
        "work/research/e87-tips/brand-promise.md#f2",
        "work/research/e87-tips/brand-promise.md#f5",
    ]


def test_brand_promise_ai_prompt_has_no_page() -> None:
    prompt = _load(BRAND_PROMISE)["ai_prompt"]
    assert set(prompt) == {"text"}


def test_brand_promise_concept_names_main_supporting_guarantee_anti() -> None:
    summary = " ".join(_load(BRAND_PROMISE_CONCEPT)["summary"].split()).lower()
    assert "10-20 word" not in summary
    for piece in ("1 main", "2 supporting", "weekly measure", "guarantee"):
        assert piece in summary, piece
    assert "anti-promise" in summary


def test_brand_promise_pages_are_covered_and_not_pending() -> None:
    coverage = _load(COVERAGE)
    pages = {int(e["page"]): e for e in coverage["pages"]}
    pending = {int(p) for p in coverage["pending"]}
    for number in range(17, 22):
        assert "worksheet-brand-promise" in pages[number].get("nodes", []), number
        assert number not in pending, number


def test_core_customer_keeps_legacy_fields() -> None:
    assert len(_load(CORE_CUSTOMER)["metadata"]["fields"]) == 6


def test_oppp_passes_the_contract() -> None:
    guide = parse_guide(_load(OPPP_SHEET))
    assert guide is not None
    assert [s.id for s in guide.guide.steps] == [*OPPP_ROW_STEPS, "tablero-de-vision"]
    assert len(guide.tips) >= 3
    assert guide.view.layout == "canvas"
    assert len(guide.view.sections) == 5
    assert guide.ai_prompt is not None
    assert guide.ai_prompt.text.strip()
    assert not re.search(r"\bp\.|\d", guide.ai_prompt.text)


def test_oppp_row_steps_name_the_eight_areas() -> None:
    guide = parse_guide(_load(OPPP_SHEET))
    assert guide is not None
    steps = {s.id: s for s in guide.guide.steps}
    for step_id in OPPP_ROW_STEPS:
        how = steps[step_id].how.lower()
        missing = [area for area in EIGHT_AREAS if area not in how]
        assert not missing, f"{step_id}: faltan {missing}"


@pytest.mark.parametrize("part", ["imagen", "obstáculo", "si pasa"])
def test_oppp_vision_board_step_asks_image_obstacle_and_if_then_plan(
    part: str,
) -> None:
    guide = parse_guide(_load(OPPP_SHEET))
    assert guide is not None
    step = {s.id: s for s in guide.guide.steps}["tablero-de-vision"]
    assert part in step.how.lower(), f"el tablero ya no pide '{part}'"


ONE_PAGE_PLANS = (
    OPPP_SHEET,
    OPPP_CARD,
    KNOWLEDGE / "strategy" / "worksheets" / "opsp.yaml",
    KNOWLEDGE / "strategy" / "tools" / "opsp.yaml",
)


@pytest.mark.parametrize(
    "path", ONE_PAGE_PLANS, ids=["oppp-sheet", "oppp-card", "opsp-sheet", "opsp-card"]
)
def test_one_page_plan_names_carry_their_accents(path: Path) -> None:
    name = str(_load(path)["name_es"])
    assert "Una Página" in name
    assert "Pagina" not in name
    assert "Estrategico" not in name


@pytest.mark.parametrize("path", [OPPP_SHEET, OPPP_CARD], ids=["sheet", "card"])
def test_oppp_card_matches_the_sheet(path: Path) -> None:
    data = _load(path)
    summary = str(data["summary"]).lower()
    assert "eight" in summary
    assert "vision board" in summary
    assert "four columns" not in summary
    assert "5f" not in summary
    assert "5Fs" not in data["tags"]
    assert "vision-board" in data["tags"]


def test_at_least_one_guided_sheet_exists() -> None:
    assert CORE_CUSTOMER in _guided_sheets()


@pytest.mark.parametrize("sheet", _guided_sheets(), ids=lambda p: p.stem)
def test_tip_sources_are_triangulated_anchors_or_clean(sheet: Path) -> None:
    guide = parse_guide(_load(sheet))
    assert guide is not None
    terms = [t.lower() for t in _forbidden_terms()]
    for tip in guide.tips:
        match = ANCHOR_SOURCE_RE.match(tip.source)
        if match:
            research = ROOT / match.group(1)
            assert research.is_file(), f"{sheet.name}: {tip.source}"
            assert f'<a id="{match.group(2)}"></a>' in research.read_text(
                encoding="utf-8"
            ), f"{sheet.name}: ancla inexistente {tip.source}"
            finding = _findings(research)[match.group(2)]
            assert finding["triangulated"] is True, (
                f"{sheet.name}: {tip.source} no está triangulado"
            )
        else:
            lowered = tip.source.lower()
            hits = [t for t in terms if t in lowered]
            assert not hits, f"{sheet.name}: fuente con término prohibido"


def test_guided_sheet_has_no_root_source_key() -> None:
    for sheet in _guided_sheets():
        assert "source" not in _load(sheet), sheet.name


BMC = KNOWLEDGE / "strategy" / "worksheets" / "bmc.yaml"
BMC_BRIDGES = {
    "segmentos": ("worksheet-core-customer", "Cliente central"),
    "propuesta-de-valor": ("worksheet-brand-promise", "Promesa de marca"),
    "canales": ("worksheet-sandbox", "Caja de arena"),
    "actividades-clave": (
        "worksheet-differentiating-activities",
        "Actividades diferenciadoras",
    ),
}


def test_bmc_passes_the_contract() -> None:
    content = _load(BMC)
    assert content["id"] == "worksheet-bmc"
    assert content["decision"] == "strategy"
    guide = parse_guide(content)
    assert guide is not None
    steps = guide.guide.steps
    assert [s.id for s in steps] == [
        "segmentos",
        "propuesta-de-valor",
        "canales",
        "relaciones",
        "ingresos",
        "recursos-clave",
        "actividades-clave",
        "socios-clave",
        "costos",
        "lista-de-verificacion",
    ]
    assert all(s.example.startswith("Tortillería El Sol:") for s in steps)
    bridges = {
        s.id: (s.next_sheet.id, s.next_sheet.title)
        for s in steps
        if s.next_sheet is not None
    }
    assert bridges == BMC_BRIDGES
    assert len(guide.tips) >= 3
    sources = {t.source.rsplit("#", 1)[1] for t in guide.tips}
    assert sources <= {"f1", "f2", "f3", "f4"}
    assert guide.ai_prompt is not None
    assert guide.view.layout == "canvas"
    assert [s.title for s in guide.view.sections] == [
        "Socios clave",
        "Actividades clave",
        "Recursos clave",
        "Propuesta de valor",
        "Relaciones con clientes",
        "Canales",
        "Segmentos de clientes",
        "Estructura de costos",
        "Fuentes de ingreso",
        "Lista de verificación",
    ]
    assert len(content["metadata"]["fields"]) == 10


def test_bmc_keeps_the_fields_the_strategy_canvas_reads() -> None:
    """S87.7 reads these two ids through ``derived_from``; they must not change."""
    guide = parse_guide(_load(BMC))
    assert guide is not None
    ids = {s.id for s in guide.guide.steps}
    assert {"segmentos", "propuesta-de-valor"} <= ids


SANDBOX = KNOWLEDGE / "strategy" / "worksheets" / "sandbox.yaml"


def test_sandbox_passes_the_contract() -> None:
    content = _load(SANDBOX)
    assert content["id"] == "worksheet-sandbox"
    assert content["decision"] == "strategy"
    guide = parse_guide(content)
    assert guide is not None
    steps = guide.guide.steps
    assert [s.id for s in steps] == ["donde", "que", "canales", "pronostico"]
    assert all(s.example.startswith("Tortillería El Sol:") for s in steps)
    assert sorted(t.source for t in guide.tips) == [
        "work/research/e87-tips/sandbox.md#f2",
        "work/research/e87-tips/sandbox.md#f3",
        "work/research/e87-tips/sandbox.md#f4",
    ]
    assert set(content["ai_prompt"]) == {"text"}
    assert guide.view.layout == "canvas"
    assert content["metadata"]["fields"] == ["donde", "que", "canales", "pronostico"]


STRATEGY_CANVAS = KNOWLEDGE / "strategy" / "worksheets" / "strategy-canvas.yaml"


def test_strategy_canvas_passes_the_contract() -> None:
    content = _load(STRATEGY_CANVAS)
    assert content["id"] == "worksheet-strategy-canvas"
    guide = parse_guide(content)
    assert guide is not None
    assert [s.id for s in guide.guide.steps] == ["decision"]
    assert [(d.sheet, d.fields, d.title, d.required) for d in guide.derived_from] == [
        ("worksheet-core-customer", ["quien-es", "necesidad"], "Cliente central", True),
        ("worksheet-brand-promise", ["promesa-principal"], "Promesa de marca", True),
        (
            "worksheet-differentiating-activities",
            ["actividades-elegidas"],
            "Actividades diferenciadoras",
            True,
        ),
        ("worksheet-sandbox", ["donde", "que", "canales"], "Caja de arena", True),
        (
            "worksheet-bmc",
            ["segmentos", "propuesta-de-valor"],
            "Contexto del modelo de negocio",
            False,
        ),
    ]
    assert sorted(t.source for t in guide.tips) == [
        "work/research/e87-tips/strategy-canvas.md#f2",
        "work/research/e87-tips/strategy-canvas.md#f3",
        "work/research/e87-tips/strategy-canvas.md#f4",
    ]
    assert set(content["ai_prompt"]) == {"text"}
    assert guide.view.layout == "canvas"


VISION_SUMMARY = KNOWLEDGE / "strategy" / "worksheets" / "vision-summary.yaml"
VISION_SUMMARY_STEPS = [
    "valores",
    "proposito",
    "promesas",
    "meta-grande",
    "prioridades-3-5-anos",
    "prioridades-ano",
    "prioridades-trimestre",
    "kpis",
    "prioridades-personales",
    "compromiso",
]
ONTOLOGY_RELEASE = ROOT / "ontology" / "v2" / "releases" / "s64.1.json"
WORKBOOK = ROOT / "metodologias_parsed" / "strategy_workbook.md"
WORD_RE = re.compile(r"[a-záéíóúñü0-9]+")


def _e65_vision_fields() -> set[str]:
    from validators.oppp_vision_artifacts import (
        _ARTIFACT_SPECS,  # pyright: ignore[reportPrivateUsage]
    )

    return set(_ARTIFACT_SPECS["procedure.build-vision-summary"][1])


def test_vision_summary_passes_the_contract() -> None:
    content = _load(VISION_SUMMARY)
    assert content["id"] == "worksheet-vision-summary"
    assert content["decision"] == "strategy"
    guide = parse_guide(content)
    assert guide is not None
    steps = guide.guide.steps
    assert all(s.example.startswith("Tortillería El Sol:") for s in steps)
    assert sorted(t.source for t in guide.tips) == [
        "work/research/e87-tips/oppp-vision-boards.md#f4",
        "work/research/e87-tips/vision-summary.md#f1",
        "work/research/e87-tips/vision-summary.md#f2",
        "work/research/e87-tips/vision-summary.md#f3",
        "work/research/e87-tips/vision-summary.md#f4",
        "work/research/e87-tips/vision-summary.md#f5",
    ]
    assert guide.view.layout == "cards"
    assert [s.title for s in guide.view.sections] == [
        "Quiénes somos",
        "Hacia dónde vamos",
        "Este año y este trimestre",
        "Tus prioridades personales",
        "Tu compromiso de 10 semanas",
    ]
    assert set(content["ai_prompt"]) == {"text"}
    assert content["metadata"]["fields"] == VISION_SUMMARY_STEPS
    assert [
        (d.sheet, d.fields, d.into, d.title, d.required) for d in guide.derived_from
    ] == [
        (
            "worksheet-core-customer",
            ["quien-es", "necesidad"],
            "customer",
            "Cliente central",
            True,
        )
    ]


def test_vision_summary_steps_cover_page_blocks() -> None:
    guide = parse_guide(_load(VISION_SUMMARY))
    assert guide is not None
    assert [s.id for s in guide.guide.steps] == VISION_SUMMARY_STEPS


def test_vision_summary_ontology_ref_exists() -> None:
    import json

    release = json.loads(ONTOLOGY_RELEASE.read_text(encoding="utf-8"))
    ids = {str(n["canonical_id"]) for n in release["nodes"]}
    assert _load(VISION_SUMMARY)["ontology_ref"] == "tool.vision-summary"
    assert "tool.vision-summary" in ids


def test_vision_summary_covers_e65_fields() -> None:
    guide = parse_guide(_load(VISION_SUMMARY))
    assert guide is not None
    e65 = _e65_vision_fields()
    assert e65 == {"purpose", "customer", "differentiator", "future_direction"}
    mapped = {f for s in guide.guide.steps for f in s.maps_to}
    derived = {d.into for d in guide.derived_from}
    assert mapped <= e65, mapped - e65
    assert e65 <= mapped | derived, e65 - (mapped | derived)
    by_step = {s.id: s.maps_to for s in guide.guide.steps}
    assert by_step["proposito"] == ["purpose"]
    assert by_step["promesas"] == ["differentiator"]
    assert by_step["meta-grande"] == ["future_direction"]


def test_vision_summary_ends_in_commitment_and_ten_week_prompt() -> None:
    content = _load(VISION_SUMMARY)
    guide = parse_guide(content)
    assert guide is not None
    last = guide.guide.steps[-1]
    assert last.id == "compromiso"
    assert "comprometes" in last.question.lower()
    prompt = guide.ai_prompt
    assert prompt is not None
    assert "10 tareas" in prompt.text
    assert "semana" in prompt.text
    assert not re.search(r"p[aá]g", prompt.text.lower())


def test_vision_summary_uses_plain_spanish_names() -> None:
    text = VISION_SUMMARY.read_text(encoding="utf-8")
    for term in ("BHAG", "Rocks", "OPSP", *_forbidden_terms()):
        assert term.lower() not in text.lower(), term


def test_vision_summary_does_not_copy_the_workbook() -> None:
    def shingles(text: str) -> set[tuple[str, ...]]:
        words = WORD_RE.findall(text.lower())
        return {tuple(words[i : i + 10]) for i in range(len(words) - 9)}

    copied = shingles(VISION_SUMMARY.read_text(encoding="utf-8")) & shingles(
        WORKBOOK.read_text(encoding="utf-8")
    )
    assert not copied, sorted(" ".join(s) for s in copied)[:3]


def test_vision_summary_pages_are_covered_and_nothing_is_pending() -> None:
    coverage = _load(COVERAGE)
    pages = {int(e["page"]): e for e in coverage["pages"]}
    for number in (34, 35, 36):
        assert "worksheet-vision-summary" in pages[number].get("nodes", []), number
    assert not coverage.get("pending")
