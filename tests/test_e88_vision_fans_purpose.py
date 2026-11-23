"""S88.4: the Vivid Vision, Fans and Life Purpose sheets.

The three follow the ToolGuide contract of E87, cite only the S88.2 research
anchors and open their view after ``save``. The public-vocabulary terms are
read from ``governance/public-boundary.yaml``; this file never writes them.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from coaching.core import write_yaml
from coaching.worksheet import derived_errors, run
from coaching.worksheet.guide import parse_guide

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "conocimiento"
POLICY = ROOT / "governance" / "public-boundary.yaml"
WORKBOOK = ROOT / "metodologias_parsed" / "strategy_workbook.md"
REGISTRY = KNOWLEDGE / "registry" / "worksheets.yaml"
VIVID = KNOWLEDGE / "strategy" / "worksheets" / "vivid-vision.yaml"
FANS = KNOWLEDGE / "strategy" / "worksheets" / "fanocracy.yaml"
PURPOSE = KNOWLEDGE / "people" / "worksheets" / "life-purpose.yaml"

E88_ANCHOR_RE = re.compile(r"^(work/research/e88-tips/([a-z0-9-]+)\.md)#(f\d+)$")
YAML_BLOCK_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
PAGE_RE = re.compile(r"\bp\.\s*\d|\bp[áa]g(ina)?s?\b|workbook_pages", re.IGNORECASE)
WORD_RE = re.compile(r"[a-záéíóúñü0-9]+")

VIVID_STEPS = [
    "fecha-vision",
    "meta-grande",
    "ingresos",
    "tamano-equipo",
    "cultura",
    "prensa",
    "noticias-locales",
    "blog-revista",
    "equipo-ama",
    "clientes-describen",
    "clientes-amigos",
    "logro-tuyo",
    "logro-equipo",
    "mejor-que-nadie",
    "oficina-cultura",
    "zona-servicio",
    "clientes-sienten",
]
FANS_STEPS = [
    "quien-te-ama",
    "que-reciben",
    "principios",
    "clientes-a-fans",
    "fans-a-clientes",
    "regalo",
    "acciones-30-dias",
]
PURPOSE_STEPS = ["pasion", "poderes", "juego", "proposito"]

VIVID_SECTIONS = [
    "Tu fecha y tu meta grande",
    "Tus números",
    "Lo que dicen de ti",
    "Tu equipo y tu cultura",
    "Tus clientes",
    "De qué estás orgulloso",
]
FANS_SECTIONS = [
    "Tus fans hoy",
    "Cómo vas en los 9 principios",
    "De cliente a fan y de fan a cliente",
    "Tus próximos 30 días",
]
PURPOSE_SECTIONS = ["Pasión", "Poder", "Juego", "Tu propósito de vida"]

# (path, id, name_es, decision, layout, steps, sections, research topic)
SHEETS = [
    (
        VIVID,
        "worksheet-vivid-vision",
        "Visión vívida",
        "strategy",
        "canvas",
        VIVID_STEPS,
        VIVID_SECTIONS,
        "vivid-vision",
    ),
    (
        FANS,
        "worksheet-fanocracy",
        "De clientes a fans",
        "strategy",
        "cards",
        FANS_STEPS,
        FANS_SECTIONS,
        "fanocracy",
    ),
    (
        PURPOSE,
        "worksheet-life-purpose",
        "Tu propósito de vida",
        "people",
        "canvas",
        PURPOSE_STEPS,
        PURPOSE_SECTIONS,
        "life-purpose",
    ),
]
PATHS = [s[0] for s in SHEETS]

# The «principios» step lists the nine principles; it is a list, not one
# instruction, so the 20-word rule does not apply to it (design D6).
LONG_HOW_ALLOWED = {"principios"}

SEVEN_PRINCIPLES = [
    "acercarse más de lo normal",
    "soltar lo que creamos",
    "dar más de lo que toca",
    "identidad más allá del producto",
    "quitar barreras",
    "escuchar para volver a lo humano",
    "decir la verdad aunque duela",
]
NINE_PRINCIPLES = [
    "acércate más de lo normal",
    "suelta lo que creas",
    "da más de lo que te toca",
    "más que un producto",
    "influencers",
    "quita barreras",
    "escucha para volver a lo humano",
    "di la verdad aunque duela",
    "equipo que también sea fan",
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


def _findings(research: Path) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for block in YAML_BLOCK_RE.findall(research.read_text(encoding="utf-8")):
        data = yaml.safe_load(block)
        if isinstance(data, dict) and "id" in data:
            found[str(data["id"])] = data
    return found


def _shingles(text: str) -> set[tuple[str, ...]]:
    words = WORD_RE.findall(text.lower())
    return {tuple(words[i : i + 10]) for i in range(len(words) - 9)}


# --- the ToolGuide contract --------------------------------------------------


@pytest.mark.parametrize(
    ("path", "sheet_id", "name_es", "decision", "layout", "steps", "sections", "topic"),
    SHEETS,
)
def test_sheet_passes_the_contract(
    path: Path,
    sheet_id: str,
    name_es: str,
    decision: str,
    layout: str,
    steps: list[str],
    sections: list[str],
    topic: str,
) -> None:
    content = _load(path)
    assert content["id"] == sheet_id
    assert content["name_es"] == name_es
    assert content["decision"] == decision
    guide = parse_guide(content)
    assert guide is not None
    assert [s.id for s in guide.guide.steps] == steps
    assert content["metadata"]["fields"] == steps
    assert all(s.example.startswith("Tortillería El Sol:") for s in guide.guide.steps)
    for step in guide.guide.steps:
        if step.id not in LONG_HOW_ALLOWED:
            assert len(step.how.split()) <= 20, step.id
    assert len(guide.tips) >= 3
    assert set(content["ai_prompt"]) == {"text"}
    assert guide.view.layout == layout
    assert [s.title for s in guide.view.sections] == sections
    covered = [step for sec in guide.view.sections for step in sec.steps]
    assert sorted(covered) == sorted(steps)
    assert derived_errors(content) == []
    assert "source" not in content
    assert "ai_followups" not in content


@pytest.mark.parametrize("path", PATHS)
def test_sheet_has_no_pages_and_no_vetoed_terms(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert not PAGE_RE.search(text)
    for term in _forbidden_terms():
        assert term.lower() not in text.lower(), term


@pytest.mark.parametrize(
    ("path", "sheet_id", "name_es", "decision", "layout", "steps", "sections", "topic"),
    SHEETS,
)
def test_tips_cite_the_s88_2_research(
    path: Path,
    sheet_id: str,
    name_es: str,
    decision: str,
    layout: str,
    steps: list[str],
    sections: list[str],
    topic: str,
) -> None:
    guide = parse_guide(_load(path))
    assert guide is not None
    for tip in guide.tips:
        match = E88_ANCHOR_RE.match(tip.source)
        assert match, tip.source
        assert match.group(2) == topic, tip.source
        finding = _findings(ROOT / match.group(1)).get(match.group(3))
        assert finding is not None, tip.source
        assert finding["triangulated"] is True, tip.source
        assert tip.step is None or tip.step in steps


@pytest.mark.parametrize("path", PATHS)
def test_sheet_does_not_copy_the_workbook(path: Path) -> None:
    copied = _shingles(path.read_text(encoding="utf-8")) & _shingles(
        WORKBOOK.read_text(encoding="utf-8")
    )
    assert not copied, sorted(" ".join(s) for s in copied)[:3]


# --- Vivid Vision ------------------------------------------------------------


def test_vivid_vision_has_three_end_prompts_and_print_in_last_step() -> None:
    guide = parse_guide(_load(VIVID))
    assert guide is not None
    assert [(p.title, p.at) for p in guide.extra_prompts] == [
        ("Hazla un cartel de pared", "end"),
        ("Hazla visual", "end"),
        ("Ponla a prueba", "end"),
    ]
    assert all("imprím" not in p.title.lower() for p in guide.extra_prompts)
    assert "imprime" in guide.guide.steps[-1].how.lower()


def test_vivid_vision_big_goal_is_10_to_30_years() -> None:
    content = _load(VIVID)
    guide = parse_guide(content)
    assert guide is not None
    step = next(s for s in guide.guide.steps if s.id == "meta-grande")
    assert "10-30 años" in step.question
    assert "10-25" not in VIVID.read_text(encoding="utf-8")
    assert [(s.sheet, s.fields, s.into, s.required) for s in guide.derived_from] == [
        ("worksheet-bhag", ["meta-grande"], "meta-grande", False),
    ]


def test_vivid_vision_prompt_keeps_the_workbook_rules() -> None:
    text = _load(VIVID)["ai_prompt"]["text"]
    assert "3 años" in text
    assert "en presente" in text
    assert "1,000 palabras" in text
    assert "5 cosas" in text


# --- Fans --------------------------------------------------------------------


def test_fans_prompt_names_seven_principles() -> None:
    text = _load(FANS)["ai_prompt"]["text"]
    for principle in SEVEN_PRINCIPLES:
        assert principle in text, principle
    assert "influencer" not in text.lower()
    assert "5 acciones" in text and "30 días" in text


def test_fans_guide_names_all_nine_principles() -> None:
    guide = parse_guide(_load(FANS))
    assert guide is not None
    how = next(s.how for s in guide.guide.steps if s.id == "principios")
    assert "9" in how
    assert how.count(";") == 8
    for principle in NINE_PRINCIPLES:
        assert principle in how, principle


def test_fans_asks_both_discussion_questions() -> None:
    guide = parse_guide(_load(FANS))
    assert guide is not None
    questions = {s.id: s.question.lower() for s in guide.guide.steps}
    assert "clientes en fans" in questions["clientes-a-fans"]
    assert "fans en clientes" in questions["fans-a-clientes"]


# --- Life Purpose ------------------------------------------------------------


def test_life_purpose_lives_in_people_and_feeds_the_one_page_plan() -> None:
    content = _load(PURPOSE)
    rels = {(r["type"], r["target"]) for r in content["relationships"]}
    assert ("belongs-to", "decision-people") in rels
    assert ("feeds-into", "worksheet-oppp") in rels
    assert "ikigai" in content["ai_prompt"]["text"]


# --- registry ----------------------------------------------------------------


def test_three_sheets_are_registered() -> None:
    registry = _load(REGISTRY)
    by_id = {w["id"]: w for w in registry["worksheets"]}
    expected = {
        "worksheet-vivid-vision": (
            "strategy/worksheets/vivid-vision.yaml",
            "Visión vívida",
        ),
        "worksheet-fanocracy": (
            "strategy/worksheets/fanocracy.yaml",
            "De clientes a fans",
        ),
        "worksheet-life-purpose": (
            "people/worksheets/life-purpose.yaml",
            "Tu propósito de vida",
        ),
    }
    for sheet_id, (node_path, name_es) in expected.items():
        entry = by_id[sheet_id]
        assert entry["node_path"] == node_path
        assert entry["name_es"] == name_es
        assert entry["prerequisites"] == []
    assert registry["total_worksheets"] == len(registry["worksheets"]) == 27


# --- the owner walks the three sheets ----------------------------------------


def _fill_and_save(base: Path, sheet: str, steps: list[str]) -> dict[str, Any]:
    def call(action: str, **extra: Any) -> dict[str, Any]:
        return run(
            {"action": action, "worksheet_name": sheet, "base_path": str(base), **extra}
        )

    assert call("start")["errors"] == []
    call("step")
    for step_id in steps:
        call("step", fields={step_id: f"Respuesta de {step_id}"})
    return call("save")


def test_list_shows_the_three_sheets(tmp_path: Path) -> None:
    out = run({"action": "list", "base_path": str(tmp_path)})["output"]
    for name in ("Visión vívida", "De clientes a fans", "Tu propósito de vida"):
        assert name in out


@pytest.mark.parametrize(
    ("path", "sheet_id", "name_es", "decision", "layout", "steps", "sections", "topic"),
    SHEETS,
)
def test_sheet_saves_and_opens_its_view(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path: Path,
    sheet_id: str,
    name_es: str,
    decision: str,
    layout: str,
    steps: list[str],
    sections: list[str],
    topic: str,
) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    result = _fill_and_save(tmp_path, sheet_id, steps)
    assert result["errors"] == []
    view = result["artifacts"]["view"]
    assert Path(view["html"]).is_file()
    md = Path(view["md"]).read_text(encoding="utf-8")
    for title in sections:
        assert title in md, title
    for step_id in steps:
        assert f"Respuesta de {step_id}" in md, step_id
    assert view["open_cmd"] == ["open", view["html"]]
    saved = tmp_path / ".escala" / "my-company" / "worksheets"
    assert (saved / f"{sheet_id}.yaml").is_file()


def test_vivid_vision_view_shows_the_three_end_prompts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    result = _fill_and_save(tmp_path, "worksheet-vivid-vision", VIVID_STEPS)
    md = Path(result["artifacts"]["view"]["md"]).read_text(encoding="utf-8")
    html = Path(result["artifacts"]["view"]["html"]).read_text(encoding="utf-8")
    for title in ("Hazla un cartel de pared", "Hazla visual", "Ponla a prueba"):
        assert title in md, title
        assert title in html, title


def test_vivid_vision_shows_the_saved_big_goal(tmp_path: Path) -> None:
    write_yaml(
        tmp_path / ".escala/my-company/worksheets/worksheet-bhag.yaml",
        {
            "worksheet_id": "worksheet-bhag",
            "fields": {
                "meta-grande": "400 fondas surtidas cada día en Jalisco para 2040"
            },
            "status": "completed",
        },
    )
    out = run(
        {
            "action": "start",
            "worksheet_name": "worksheet-vivid-vision",
            "base_path": str(tmp_path),
        }
    )["output"]
    assert "Esto ya llenaste:" in out
    assert "400 fondas surtidas cada día en Jalisco para 2040" in out
