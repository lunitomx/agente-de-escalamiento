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
POLICY = ROOT / "governance" / "public-boundary.yaml"
CORE_CUSTOMER = KNOWLEDGE / "strategy" / "worksheets" / "core-customer.yaml"
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
