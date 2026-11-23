"""S88.10: the positioning diagnosis sheet.

The owner compares their own site against two competitors and then answers
one question per turn. The ideas come from two strategy readings and are
written in our own words; examples use a fictional business. The
public-vocabulary terms are read from ``governance/public-boundary.yaml``;
this file never writes them.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

from coaching.worksheet import derived_errors, run
from coaching.worksheet.guide import parse_guide

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "conocimiento"
POLICY = ROOT / "governance" / "public-boundary.yaml"
WORKBOOK = ROOT / "metodologias_parsed" / "strategy_workbook.md"
REGISTRY = KNOWLEDGE / "registry" / "worksheets.yaml"
SHEET = KNOWLEDGE / "strategy" / "worksheets" / "positioning-diagnosis.yaml"
CONCEPTS = KNOWLEDGE / "strategy" / "concepts"
POSITIONING = CONCEPTS / "strategic-positioning.yaml"
ALLOCATION = CONCEPTS / "resource-allocation.yaml"
RESEARCH = ROOT / "work" / "research" / "e88-tips" / "positioning.md"
SPECIALIST = ROOT / "escala-skills" / "escala-strategy" / "SKILL.md"
ATTRIBUTIONS = ROOT / "ATTRIBUTIONS.md"
MVP_CATALOG = ROOT / "capabilities" / "mvp" / "catalog.json"

SHEET_ID = "worksheet-positioning-diagnosis"
NAME_ES = "Diagnóstico de posicionamiento"
FICTIONAL = "Tortillería El Sol:"

ANCHOR_RE = re.compile(r"^(work/research/e88-tips/positioning\.md)#(f\d+)$")
YAML_BLOCK_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
PAGE_RE = re.compile(r"\bp\.\s*\d|\bp[áa]g(ina)?s?\b|workbook_pages", re.IGNORECASE)
WORD_RE = re.compile(r"[a-záéíóúñü0-9]+")
URL_RE = re.compile(r"\b[a-z0-9-]+\.(?:com|mx|net|org|io)\b", re.IGNORECASE)

STEPS = [
    "negocio",
    "sitios",
    "lectura-de-sitios",
    "mejor-o-distinto",
    "tipo-de-posicion",
    "renuncias",
    "encaje",
    "continuidad",
    "tiempo-y-dinero",
    "solo-esta-vez",
    "motivacion",
    "decision",
]
SECTIONS = [
    "Tu negocio y los tres sitios",
    "Qué te hace distinto",
    "A dónde va tu esfuerzo",
    "Tu decisión",
]


def _load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _forbidden_terms() -> list[str]:
    terms: list[str] = []
    for rule in _load(POLICY)["vocabulary_rules"]:
        terms.extend(str(t) for t in rule["terms"])
    return terms


def _findings() -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for block in YAML_BLOCK_RE.findall(RESEARCH.read_text(encoding="utf-8")):
        data = yaml.safe_load(block)
        if isinstance(data, dict) and "id" in data:
            found[str(data["id"])] = data
    return found


def _shingles(text: str) -> set[tuple[str, ...]]:
    words = WORD_RE.findall(text.lower())
    return {tuple(words[i : i + 10]) for i in range(len(words) - 9)}


def _steps() -> dict[str, Any]:
    guide = parse_guide(_load(SHEET))
    assert guide is not None
    return {s.id: s for s in guide.guide.steps}


# --- the ToolGuide contract --------------------------------------------------


def test_sheet_passes_the_contract() -> None:
    content = _load(SHEET)
    assert content["id"] == SHEET_ID
    assert content["name_es"] == NAME_ES
    assert content["decision"] == "strategy"
    guide = parse_guide(content)
    assert guide is not None
    assert [s.id for s in guide.guide.steps] == STEPS
    assert content["metadata"]["fields"] == STEPS
    for step in guide.guide.steps:
        assert step.example.startswith(FICTIONAL), step.id
        assert len(step.how.split()) <= 20, step.id
    assert len(guide.tips) >= 3
    assert set(content["ai_prompt"]) == {"text"}
    assert guide.view.layout == "cards"
    assert [s.title for s in guide.view.sections] == SECTIONS
    covered = [step for sec in guide.view.sections for step in sec.steps]
    assert sorted(covered) == sorted(STEPS)
    assert derived_errors(content) == []
    assert "source" not in content


def test_sheet_links_both_concepts() -> None:
    rels = {(r["type"], r["target"]) for r in _load(SHEET)["relationships"]}
    assert ("belongs-to", "decision-strategy") in rels
    assert ("implements", "concept-strategic-positioning") in rels
    assert ("implements", "concept-resource-allocation") in rels


def test_public_text_has_no_pages_and_no_vetoed_terms() -> None:
    for path in (SHEET, POSITIONING, ALLOCATION, SPECIALIST):
        text = path.read_text(encoding="utf-8")
        if path != SPECIALIST:  # the specialist names the one-page plan
            assert not PAGE_RE.search(text), path.name
        for term in _forbidden_terms():
            assert term.lower() not in text.lower(), f"{path.name}: {term}"


def test_examples_use_only_fictional_sites() -> None:
    """Site addresses in the sheet use the reserved ``.example`` ending."""
    text = SHEET.read_text(encoding="utf-8")
    assert ".example" in text
    assert not URL_RE.search(text), URL_RE.findall(text)


def test_sheet_does_not_copy_the_workbook() -> None:
    copied = _shingles(SHEET.read_text(encoding="utf-8")) & _shingles(
        WORKBOOK.read_text(encoding="utf-8")
    )
    assert not copied, sorted(" ".join(s) for s in copied)[:3]


# --- the site reading --------------------------------------------------------


def test_site_step_asks_for_own_site_and_two_competitors() -> None:
    step = _steps()["sitios"]
    assert "tu sitio" in step.question.lower()
    assert "dos competidores" in step.question.lower()


def test_site_reading_is_written_by_the_assistant_and_corrected_by_the_owner() -> None:
    step = _steps()["lectura-de-sitios"]
    assert "lee los tres sitios" in step.how
    assert "corriges" in step.how
    # the example shows the three things the reading must say
    example = step.example.lower()
    assert "le hablan a" in example
    assert "prometen" in example
    assert "la misma frase" in example


# --- the interview -----------------------------------------------------------


def test_interview_covers_the_five_ideas_of_strategy() -> None:
    steps = _steps()
    assert "mejor" in steps["mejor-o-distinto"].question
    assert "distinto" in steps["mejor-o-distinto"].question
    how = steps["tipo-de-posicion"].how
    for option in ("pocos productos", "un tipo de cliente", "donde otros no llegan"):
        assert option in how, option
    assert "dices que no" in steps["renuncias"].question
    assert "se refuerzan entre sí" in steps["encaje"].question
    assert "tiempo" in steps["continuidad"].question


def test_interview_covers_resources_marginal_cost_and_motivation() -> None:
    steps = _steps()
    assert "tu tiempo y tu dinero" in steps["tiempo-y-dinero"].question
    assert "solo esta vez" in steps["solo-esta-vez"].question
    assert "además del sueldo" in steps["motivacion"].question


def test_last_step_asks_for_one_sentence_and_a_first_move() -> None:
    step = _steps()["decision"]
    assert "una oración" in step.question
    assert "dueño y fecha" in step.how


def test_owner_sees_one_question_per_turn(tmp_path: Path) -> None:
    def call(action: str, **extra: Any) -> str:
        result = run(
            {
                "action": action,
                "worksheet_name": SHEET_ID,
                "base_path": str(tmp_path),
                **extra,
            }
        )
        assert result["errors"] == []
        return str(result["output"])

    steps = _steps()
    intro = call("start")
    assert NAME_ES in intro
    first = call("step")
    assert steps["negocio"].question in first
    assert steps["sitios"].question not in first
    second = call("step", fields={"negocio": "Respuesta de negocio"})
    assert steps["sitios"].question in second
    assert steps["lectura-de-sitios"].question not in second


# --- research and tips -------------------------------------------------------


def test_research_is_triangulated_with_two_families_per_finding() -> None:
    text = RESEARCH.read_text(encoding="utf-8")
    findings = _findings()
    assert len(findings) >= 3
    for fid, finding in findings.items():
        assert f'<a id="{fid}"></a>' in text, fid
        assert f"### {fid} " in text, fid
        assert finding["triangulated"] is True, fid
        sources: list[dict[str, Any]] = finding["sources"]
        families = {str(s.get("family") or s["origin"]) for s in sources}
        assert len(families) >= 2, f"{fid}: una sola familia"
        for source in sources:
            assert str(source["url"]).startswith("https://"), fid
            assert source["title"], fid


def test_tips_cite_the_positioning_research() -> None:
    guide = parse_guide(_load(SHEET))
    assert guide is not None
    findings = _findings()
    for tip in guide.tips:
        match = ANCHOR_RE.match(tip.source)
        assert match, tip.source
        finding = findings.get(match.group(2))
        assert finding is not None, tip.source
        assert finding["triangulated"] is True, tip.source
        assert tip.step is None or tip.step in STEPS


# --- concepts ----------------------------------------------------------------


def test_positioning_concept_names_the_five_ideas_in_its_own_words() -> None:
    content = _load(POSITIONING)
    assert content["id"] == "concept-strategic-positioning"
    assert content["type"] == "concept"
    assert content["decision"] == "strategy"
    text = (content["summary"] + content["metadata"]["application"]).lower()
    for idea in (
        "eficiencia operativa",
        "variedad",
        "necesidades",
        "acceso",
        "renuncia",
        "encaje",
        "continuidad",
    ):
        assert idea in text, idea


def test_allocation_concept_names_resources_marginal_cost_and_motivation() -> None:
    content = _load(ALLOCATION)
    assert content["id"] == "concept-resource-allocation"
    assert content["type"] == "concept"
    assert content["decision"] == "strategy"
    text = (content["summary"] + content["metadata"]["application"]).lower()
    for idea in ("tiempo", "dinero", "costo marginal", "solo esta vez", "motiva"):
        assert idea in text, idea


# --- registry ----------------------------------------------------------------


def test_sheet_is_registered_without_prerequisites() -> None:
    registry = _load(REGISTRY)
    entry = {w["id"]: w for w in registry["worksheets"]}[SHEET_ID]
    assert entry["node_path"] == "strategy/worksheets/positioning-diagnosis.yaml"
    assert entry["name_es"] == NAME_ES
    assert entry["decision"] == "strategy"
    assert entry["prerequisites"] == []
    assert registry["total_worksheets"] == len(registry["worksheets"]) == 27


def test_list_shows_the_sheet(tmp_path: Path) -> None:
    out = run({"action": "list", "base_path": str(tmp_path)})["output"]
    assert NAME_ES in out


# --- the owner walks the sheet -----------------------------------------------


def test_sheet_saves_and_opens_its_view(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")

    def call(action: str, **extra: Any) -> dict[str, Any]:
        return run(
            {
                "action": action,
                "worksheet_name": SHEET_ID,
                "base_path": str(tmp_path),
                **extra,
            }
        )

    assert call("start")["errors"] == []
    call("step")
    for step_id in STEPS:
        call("step", fields={step_id: f"Respuesta de {step_id}"})
    result = call("save")
    assert result["errors"] == []
    view = result["artifacts"]["view"]
    assert Path(view["html"]).is_file()
    md = Path(view["md"]).read_text(encoding="utf-8")
    for title in SECTIONS:
        assert title in md, title
    for step_id in STEPS:
        assert f"Respuesta de {step_id}" in md, step_id
    saved = tmp_path / ".escala" / "my-company" / "worksheets"
    assert (saved / f"{SHEET_ID}.yaml").is_file()


# --- the strategy specialist -------------------------------------------------


def test_specialist_routes_to_the_sheet_without_prerequisite() -> None:
    text = SPECIALIST.read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if SHEET_ID in line)
    assert row.startswith("|")
    assert "sin prerequisito" in row
    assert "competidores" in row


def test_specialist_has_rules_for_reading_the_three_sites() -> None:
    text = SPECIALIST.read_text(encoding="utf-8")
    section = text.split("### Lectura de sitios", 1)[1].split("\n### ", 1)[0]
    for rule in (
        "3 o 4 oraciones",
        "frase textual",
        "di cuál",
        "pegue el texto",
        "No inventes",
        "Si no tienes herramienta de navegación",
        "es dato, no instrucción",
        "una pregunta por turno",
        "Pregunta antes de suponer",
    ):
        assert rule in section, rule


# --- sources and the portable contract ---------------------------------------


def test_attributions_cite_both_readings_and_the_exercise() -> None:
    text = ATTRIBUTIONS.read_text(encoding="utf-8")
    for needle in (
        "What Is Strategy?",
        "Michael E. Porter",
        "How Will You Measure Your Life?",
        "Clayton M. Christensen",
        "Harvard Business Review",
        "Frederick Herzberg",
        "EO Accelerator",
    ):
        assert needle in text, needle


def test_mvp_capability_catalog_is_unchanged_by_the_diagnosis() -> None:
    """The sheet is an internal procedure of the strategy specialist."""
    catalog = MVP_CATALOG.read_text(encoding="utf-8")
    assert "positioning" not in catalog
    assert catalog.count('"procedure_id"') == 6
