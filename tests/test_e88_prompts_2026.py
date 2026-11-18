"""S88.5: 2026 prompts in SWT, Activities and Vision summary; and their view (epic design section 8).

The public-vocabulary terms are read from ``governance/public-boundary.yaml``;
this file never writes them (decision D5 of S87.2).
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from coaching.worksheet import run
from coaching.worksheet.guide import ToolGuide, parse_guide
from coaching.worksheet.view import build_view, render_html, render_markdown

ROOT = Path(__file__).resolve().parents[1]
SHEETS = ROOT / "conocimiento" / "strategy" / "worksheets"
SWT = SHEETS / "swt.yaml"
ACTIVITIES = SHEETS / "differentiating-activities.yaml"
VISION = SHEETS / "vision-summary.yaml"
POLICY = ROOT / "governance" / "public-boundary.yaml"
PAGE_RE = re.compile(r"p[aá]g", re.IGNORECASE)
SHEET_PAGE_RE = re.compile(r"\bp[aá]gina|\bp[aá]g\.|\bp\.\s*\d", re.IGNORECASE)
SWT_ID = "worksheet-swt"


def _load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _guide(path: Path) -> ToolGuide:
    guide = parse_guide(_load(path))
    assert guide is not None
    return guide


def _forbidden_terms() -> list[str]:
    terms: list[str] = []
    for rule in _load(POLICY)["vocabulary_rules"]:
        terms.extend(str(t).lower() for t in rule["terms"])
    return terms


def _run(base: Path, action: str, **extra: Any) -> dict[str, Any]:
    return run(
        {"action": action, "worksheet_name": SWT_ID, "base_path": str(base), **extra}
    )


# --- 2026 prompts ---


def test_swt_start_prompt_is_the_ai_setup() -> None:
    starts = [p for p in _guide(SWT).extra_prompts if p.at == "start"]
    assert [p.title for p in starts] == ["Arranque con IA"]
    text = starts[0].text
    for phrase in ("un solo chat", "competidores", "una pregunta a la vez"):
        assert phrase in text, phrase


def test_swt_step_one_shows_the_ai_setup_before_the_checklist(tmp_path: Path) -> None:
    output = _run(tmp_path, "start")["output"]
    assert output.index("**Arranque con IA:**") < output.index("Antes de empezar")


def test_activities_prompt_is_the_2026_prompt() -> None:
    prompt = _guide(ACTIVITIES).ai_prompt
    assert prompt is not None
    for phrase in ("difícil de copiar", "dejar de hacer", "una a la vez"):
        assert phrase in prompt.text, phrase


def test_vision_summary_prompts_are_2026() -> None:
    guide = _guide(VISION)
    assert guide.ai_prompt is not None
    assert "10 tareas" in guide.ai_prompt.text
    assert "semana" in guide.ai_prompt.text
    assert [(p.title, p.at) for p in guide.extra_prompts] == [
        ("Tu día en una sola hoja", "start")
    ]


def test_vision_summary_core_customer_is_optional_and_goal_is_10_to_30() -> None:
    guide = _guide(VISION)
    assert [(d.sheet, d.required) for d in guide.derived_from] == [
        ("worksheet-swt", False),
        ("worksheet-differentiating-activities", False),
        ("worksheet-core-purpose", False),
        ("worksheet-bhag", False),
        ("worksheet-core-customer", False),
    ]
    goal = next(s for s in guide.guide.steps if s.id == "meta-grande")
    assert "10-30 años" in goal.question
    tip = next(t for t in guide.tips if t.step == "meta-grande")
    assert "10-30 años" in tip.text
    assert "10-25" not in VISION.read_text(encoding="utf-8")


def test_owner_text_of_the_three_sheets_is_clean() -> None:
    for path in (SWT, ACTIVITIES, VISION):
        guide = _guide(path)
        texts = [p.text for p in guide.extra_prompts]
        texts += [guide.ai_prompt.text] if guide.ai_prompt else []
        for text in texts:
            assert not PAGE_RE.search(text), (path.name, text[:40])
            for term in _forbidden_terms():
                assert term not in text.lower(), (path.name, term)
    # Los ids de hoja (worksheet-bhag) no los ve el dueño; solo el texto.
    vision = re.sub(r"worksheet-[a-z0-9-]+", "", VISION.read_text(encoding="utf-8"))
    assert "bhag" not in vision.lower()
    assert not SHEET_PAGE_RE.search(vision)


def test_vision_view_without_core_customer_has_no_missing_lines(
    tmp_path: Path,
) -> None:
    guide = _guide(VISION)
    answers = {s.id: f"Tortillería El Sol: {s.id}" for s in guide.guide.steps}
    result = run(
        {
            "action": "start",
            "worksheet_name": "worksheet-vision-summary",
            "base_path": str(tmp_path),
        }
    )
    assert result["errors"] == []
    assert "Falta" not in result["output"]
    run(
        {
            "action": "step",
            "worksheet_name": "worksheet-vision-summary",
            "fields": answers,
            "base_path": str(tmp_path),
        }
    )
    saved = run(
        {
            "action": "save",
            "worksheet_name": "worksheet-vision-summary",
            "base_path": str(tmp_path),
        }
    )
    assert saved["errors"] == []
    for kind in ("html", "md"):
        text = Path(saved["artifacts"]["view"][kind]).read_text(encoding="utf-8")
        assert "Falta" not in text, kind
        assert "Cliente central" not in text, kind
        assert "Tu día en una sola hoja" in text, kind
    view = build_view(_load(VISION), answers, made_on=date(2026, 11, 23))
    for text in (render_html(view), render_markdown(view)):
        assert "Cliente central" not in text
