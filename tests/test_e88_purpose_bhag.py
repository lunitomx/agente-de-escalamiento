"""S88.3: the Core Purpose and Big Goal (BHAG) sheets.

Both follow the ToolGuide contract of E87, cite only research anchors and
open their view after ``save``. The public-vocabulary terms are read from
``governance/public-boundary.yaml``; this file never writes them.
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
CORE_PURPOSE = KNOWLEDGE / "strategy" / "worksheets" / "core-purpose.yaml"
BHAG_SHEET = KNOWLEDGE / "strategy" / "worksheets" / "bhag.yaml"
E88_TIPS = ROOT / "work" / "research" / "e88-tips"

ANCHOR_RE = re.compile(r"^(work/research/e8[78]-tips/[a-z0-9-]+\.md)#(f\d+)$")
YAML_BLOCK_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
PAGE_RE = re.compile(r"\bp\.\s*\d|\bp[áa]g(ina)?s?\b|workbook_pages", re.IGNORECASE)
WORD_RE = re.compile(r"[a-záéíóúñü0-9]+")

PURPOSE_STEPS = [
    "que-hace",
    "cinco-porques",
    "fundador",
    "si-desaparecemos",
    "cuatro-tipos",
    "una-palabra",
    "proposito",
    "prueba",
]
BHAG_STEPS = [
    "pasion",
    "mejor-en",
    "cliente-x",
    "borradores",
    "impacto",
    "meta-grande",
    "prueba",
]
PURPOSE_SECTIONS = [
    "Qué haces y por qué importa",
    "De dónde viene",
    "Tus borradores",
    "Tu propósito central",
]
BHAG_SECTIONS = ["Tus tres círculos", "Tus borradores", "Tu meta grande"]
SHEETS = [
    (CORE_PURPOSE, PURPOSE_STEPS, PURPOSE_SECTIONS),
    (BHAG_SHEET, BHAG_STEPS, BHAG_SECTIONS),
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


@pytest.mark.parametrize(("path", "steps", "sections"), SHEETS)
def test_sheet_passes_the_contract(
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
    assert set(content["ai_prompt"]) == {"text"}
    assert guide.view.layout == "cards"
    assert [s.title for s in guide.view.sections] == sections
    covered = [step for sec in guide.view.sections for step in sec.steps]
    assert sorted(covered) == sorted(steps)
    assert derived_errors(content) == []
    assert "source" not in content


@pytest.mark.parametrize(("path", "steps", "sections"), SHEETS)
def test_sheet_has_no_pages_and_no_vetoed_terms(
    path: Path, steps: list[str], sections: list[str]
) -> None:
    text = path.read_text(encoding="utf-8")
    assert not PAGE_RE.search(text)
    for term in _forbidden_terms():
        assert term.lower() not in text.lower(), term


@pytest.mark.parametrize(("path", "steps", "sections"), SHEETS)
def test_tips_cite_research_anchors(
    path: Path, steps: list[str], sections: list[str]
) -> None:
    guide = parse_guide(_load(path))
    assert guide is not None
    for tip in guide.tips:
        match = ANCHOR_RE.match(tip.source)
        assert match, tip.source
        finding = _findings(ROOT / match.group(1)).get(match.group(2))
        assert finding is not None, tip.source
        assert finding["triangulated"] is True, tip.source
        assert tip.step in steps


@pytest.mark.parametrize(("path", "steps", "sections"), SHEETS)
def test_sheet_does_not_copy_the_workbook(
    path: Path, steps: list[str], sections: list[str]
) -> None:
    copied = _shingles(path.read_text(encoding="utf-8")) & _shingles(
        WORKBOOK.read_text(encoding="utf-8")
    )
    assert not copied, sorted(" ".join(s) for s in copied)[:3]


# --- research notes ----------------------------------------------------------


@pytest.mark.parametrize("tool", ["core-purpose", "bhag"])
def test_research_note_is_triangulated(tool: str) -> None:
    note = E88_TIPS / f"{tool}.md"
    text = note.read_text(encoding="utf-8")
    match = FRONT_MATTER_RE.match(text)
    assert match
    meta = yaml.safe_load(match.group(1))
    assert meta["tool"] == tool and meta["title_es"] and meta["question"]
    assert not PAGE_RE.search(text)
    findings = _findings(note)
    assert list(findings) == ["f1", "f2", "f3"]
    assert re.findall(r'<a id="(f\d+)"></a>', text) == list(findings)
    for finding in findings.values():
        assert finding["triangulated"] is True
        assert 20 <= len(str(finding["tip"])) <= 200
        urls = [s for s in finding["sources"] if str(s["url"]).startswith("http")]
        families = {str(s.get("family") or s["origin"]) for s in urls}
        assert len(urls) >= 3, finding["id"]
        assert len(families) >= 3, finding["id"]


@pytest.mark.parametrize("tool", ["core-purpose", "bhag"])
def test_research_note_does_not_copy_the_workbook(tool: str) -> None:
    text = (E88_TIPS / f"{tool}.md").read_text(encoding="utf-8")
    copied = _shingles(text) & _shingles(WORKBOOK.read_text(encoding="utf-8"))
    assert not copied, sorted(" ".join(s) for s in copied)[:3]


# --- prompts faithful to the workbook ---------------------------------------


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


def test_big_goal_name_shows_bhag_and_horizon() -> None:
    content = _load(BHAG_SHEET)
    assert content["name_es"] == "Meta grande (BHAG)"
    assert "10-30 años" in content["summary"]


def test_big_goal_reads_purpose_promise_and_customer() -> None:
    guide = parse_guide(_load(BHAG_SHEET))
    assert guide is not None
    assert [(s.sheet, s.fields, s.into, s.required) for s in guide.derived_from] == [
        ("worksheet-core-purpose", ["proposito"], "pasion", False),
        ("worksheet-brand-promise", ["promesa-principal"], "mejor-en", False),
        ("worksheet-core-customer", ["quien-es"], "cliente-x", False),
    ]


# --- registry ----------------------------------------------------------------


def test_purpose_and_big_goal_are_registered() -> None:
    registry = _load(REGISTRY)
    by_id = {w["id"]: w for w in registry["worksheets"]}
    purpose = by_id["worksheet-core-purpose"]
    bhag = by_id["worksheet-bhag"]
    assert purpose["node_path"] == "strategy/worksheets/core-purpose.yaml"
    assert purpose["name_es"] == "Propósito central"
    assert bhag["node_path"] == "strategy/worksheets/bhag.yaml"
    assert bhag["name_es"] == "Meta grande (BHAG)"
    assert bhag["prerequisites"] == ["worksheet-core-purpose"]
    assert registry["total_worksheets"] == len(registry["worksheets"]) == 26


# --- the owner walks both sheets ---------------------------------------------

PURPOSE_ANSWERS = {
    "que-hace": "Masa y tortilla para fondas",
    "cinco-porques": "Sin masa la fonda no abre",
    "fundador": "La fonda de su mamá cerró",
    "si-desaparecemos": "45 fondas abrirían tarde",
    "cuatro-tipos": "Que ninguna fonda abra sin masa",
    "una-palabra": "barrio",
    "proposito": "Que la fonda de barrio siga viva",
    "prueba": "Luis lo dice de memoria",
}


def _fill_and_save(base: Path, sheet: str, answers: dict[str, str]) -> dict[str, Any]:
    def call(action: str, **extra: Any) -> dict[str, Any]:
        return run(
            {"action": action, "worksheet_name": sheet, "base_path": str(base), **extra}
        )

    assert call("start")["errors"] == []
    call("step")
    for step_id, answer in answers.items():
        call("step", fields={step_id: answer})
    return call("save")


def test_list_shows_both_sheets(tmp_path: Path) -> None:
    out = run({"action": "list", "base_path": str(tmp_path)})["output"]
    assert "Propósito central" in out
    assert "Meta grande (BHAG)" in out


def test_purpose_saves_and_opens_its_view(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    result = _fill_and_save(tmp_path, "worksheet-core-purpose", PURPOSE_ANSWERS)
    assert result["errors"] == []
    view = result["artifacts"]["view"]
    assert Path(view["html"]).is_file()
    md = Path(view["md"]).read_text(encoding="utf-8")
    assert "Tu propósito central" in md
    assert "Que la fonda de barrio siga viva" in md
    assert view["open_cmd"] == ["open", view["html"]]
    saved = tmp_path / ".escala" / "my-company" / "worksheets"
    assert (saved / "worksheet-core-purpose.yaml").is_file()


def test_big_goal_shows_the_saved_purpose(tmp_path: Path) -> None:
    write_yaml(
        tmp_path / ".escala/my-company/worksheets/worksheet-core-purpose.yaml",
        {
            "worksheet_id": "worksheet-core-purpose",
            "fields": {"proposito": "Que la fonda de barrio siga viva"},
            "status": "completed",
        },
    )
    out = run(
        {
            "action": "start",
            "worksheet_name": "worksheet-bhag",
            "base_path": str(tmp_path),
        }
    )["output"]
    assert "Esto ya llenaste:" in out
    assert "#### Propósito central" in out
    assert "Que la fonda de barrio siga viva" in out
