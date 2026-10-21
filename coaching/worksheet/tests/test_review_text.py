"""S87.7: Final Review and saved view read cleanly and show the AI prompt."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from coaching.worksheet import find_worksheet, load_worksheet_content, run
from coaching.worksheet.view import (
    build_view,
    label_heading,
    render_html,
    render_markdown,
)

DAY = date(2026, 10, 20)
DOUBLE = ("?:", "?.:", ".:", "?**:", ".**:")


@pytest.mark.parametrize(
    ("label", "shown"),
    [
        ("¿Qué prometes?", "**¿Qué prometes?**"),
        ("Escribe tus segmentos.", "**Escribe tus segmentos.**"),
        ("¡Listo!", "**¡Listo!**"),
        ("Nota:", "**Nota:**"),
        ("Functions list", "**Functions list:**"),
    ],
)
def test_label_heading_adds_a_colon_only_when_needed(label: str, shown: str) -> None:
    assert label_heading(label) == shown


def _content(sheet_id: str) -> dict[str, Any]:
    sheet = find_worksheet(sheet_id)
    assert sheet is not None
    return load_worksheet_content(sheet)


def _walk(base: Path, sheet: str, answers: dict[str, str]) -> str:
    run({"action": "start", "worksheet_name": sheet, "base_path": str(base)})
    run({"action": "step", "worksheet_name": sheet, "base_path": str(base)})
    out = ""
    for step_id, answer in answers.items():
        out = run(
            {
                "action": "step",
                "worksheet_name": sheet,
                "base_path": str(base),
                "fields": {step_id: answer},
            }
        )["output"]
    return out


def test_bmc_review_has_no_double_punctuation_and_shows_the_prompt(
    tmp_path: Path,
) -> None:
    content = _content("worksheet-bmc")
    steps = content["guide"]["steps"]
    answers = {str(s["id"]): "Fondas" for s in steps}
    out = _walk(tmp_path, "worksheet-bmc", answers)
    assert "### Revisión Final" in out
    for bad in DOUBLE:
        assert bad not in out, bad
    question = str(steps[0]["question"])
    assert f"- **{question}** Fondas" in out
    prompt = f"**Prompt para tu asistente de IA:** {content['ai_prompt']['text']}"
    assert prompt in out
    assert out.index(prompt) < out.index("Responde 'confirmar'")


def test_view_markdown_has_no_double_punctuation() -> None:
    content = _content("worksheet-bmc")
    answers = {str(s["id"]): "Fondas" for s in content["guide"]["steps"]}
    md = render_markdown(build_view(content, answers, DAY))
    for bad in DOUBLE:
        assert bad not in md, bad


def test_ai_prompt_block_in_html_and_md() -> None:
    content = _content("worksheet-brand-promise")
    view = build_view(content, {}, DAY)
    text = str(content["ai_prompt"]["text"])
    assert view.ai_prompt == text
    page = render_html(view)
    md = render_markdown(view)
    assert "<h2>Prompt para tu asistente de IA</h2>" in page
    assert "## Prompt para tu asistente de IA" in md
    assert text in md
    assert md.rstrip().endswith(text)


def test_sheet_without_ai_prompt_shows_no_prompt_block(tmp_path: Path) -> None:
    content = _content("worksheet-face")
    view = build_view(content, {}, DAY)
    assert view.ai_prompt is None
    assert "Prompt para tu asistente de IA" not in render_html(view)
    assert "Prompt para tu asistente de IA" not in render_markdown(view)
    out = _walk(tmp_path, "worksheet-face", {})
    assert "Prompt para tu asistente de IA" not in out
