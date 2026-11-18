"""S88.1: the SWT sheet is guided and carries the 2026 trends and prompt.

The public-vocabulary terms are read from ``governance/public-boundary.yaml``;
this file never writes them (decision D5 of S87.2).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from coaching.worksheet.guide import ToolGuide, parse_guide

ROOT = Path(__file__).resolve().parents[1]
SWT = ROOT / "conocimiento" / "strategy" / "worksheets" / "swt.yaml"
POLICY = ROOT / "governance" / "public-boundary.yaml"
E88_ANCHOR_RE = re.compile(r"^(work/research/e88-tips/[a-z0-9-]+\.md)#(f\d+)$")
YAML_BLOCK_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
PAGE_RE = re.compile(r"\bp(á|a)g(ina)?s?\.?\s*\d|\bp\.\s*\d", re.IGNORECASE)
TRENDS_2026 = (
    "Agents doing the work, not just drafting it",
    "Who owns your face/voice",
    "GLP-1s rewriting food, alcohol, and retail",
    "Healthspan as the new status symbol",
    "The friendship recession and the return of third places",
    "Phones out of schools, and the analog revival",
    "Birth rates become a boardroom and policy question",
    "The sandwich generation gets squeezed on both ends",
    "Live and in person carries the price premium",
    "Trust shifts from institutions to individuals",
)


def _load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _guide() -> ToolGuide:
    guide = parse_guide(_load(SWT))
    assert guide is not None, "swt.yaml no es hoja guiada"
    return guide


def _forbidden_terms() -> list[str]:
    terms: list[str] = []
    for rule in _load(POLICY)["vocabulary_rules"]:
        terms.extend(str(t).lower() for t in rule["terms"])
    return terms


def test_swt_has_the_five_steps_in_order() -> None:
    assert [s.id for s in _guide().guide.steps] == [
        "tendencias-2026",
        "tendencias",
        "fortalezas",
        "debilidades",
        "ideas",
    ]


def test_every_example_is_the_tortilleria() -> None:
    for step in _guide().guide.steps:
        assert step.example.startswith("Tortillería El Sol:"), step.id


def test_trends_step_lists_the_ten_2026_trends() -> None:
    step = _guide().guide.steps[0]
    for trend in TRENDS_2026:
        assert trend in step.how, trend


def test_name_and_summary_are_spanish_and_clean() -> None:
    data = _load(SWT)
    assert data["name_es"] == "Fortalezas, debilidades y tendencias (SWT)"
    summary = str(data["summary"])
    assert "tendencias" in summary
    lowered = summary.lower()
    assert "opsp" not in lowered
    hits = [t for t in _forbidden_terms() if t in lowered]
    assert not hits


def test_sheet_text_has_no_forbidden_term_nor_page_number() -> None:
    text = SWT.read_text(encoding="utf-8")
    lowered = text.lower()
    hits = [t for t in _forbidden_terms() if t in lowered]
    assert not hits
    assert not PAGE_RE.search(text)
    assert "metadata" not in _load(SWT) or "fields" not in _load(SWT)["metadata"]


def test_main_prompt_is_the_swt_2026_prompt() -> None:
    prompt = _guide().ai_prompt
    assert prompt is not None
    for part in ("dame 5 de cada una", "dame 12", "próximos 3 años", "3 preguntas"):
        assert part in prompt.text, part


def test_view_groups_outside_inside_and_ideas() -> None:
    sections = _guide().view.sections
    assert [(s.title, s.steps) for s in sections] == [
        ("Lo que pasa afuera", ["tendencias-2026", "tendencias"]),
        ("Lo que tienes adentro", ["fortalezas", "debilidades"]),
        ("Tus ideas", ["ideas"]),
    ]


def test_trends_tip_comes_from_a_triangulated_e88_finding() -> None:
    tips = [t for t in _guide().tips if E88_ANCHOR_RE.match(t.source)]
    assert tips, "falta el tip con ancla e88"
    for tip in tips:
        match = E88_ANCHOR_RE.match(tip.source)
        assert match is not None
        research = (ROOT / match.group(1)).read_text(encoding="utf-8")
        assert f'<a id="{match.group(2)}"></a>' in research
        findings = {
            str(f["id"]): f
            for f in (yaml.safe_load(b) for b in YAML_BLOCK_RE.findall(research))
            if isinstance(f, dict)
        }
        assert findings[match.group(2)]["triangulated"] is True
        assert "workbook_pages" not in findings[match.group(2)]
