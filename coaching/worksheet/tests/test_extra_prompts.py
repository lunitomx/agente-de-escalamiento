"""S88.1: a sheet shows several prompts — at step 1 and after the main one."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from coaching.worksheet.guide import parse_guide


def _step(step_id: str) -> dict[str, Any]:
    return {
        "id": step_id,
        "question": f"¿Pregunta {step_id}?",
        "how": "Una frase.",
        "example": "Tortillería El Sol: tortilla caliente a las 13:00.",
    }


def _tip(n: int) -> dict[str, Any]:
    return {"text": f"Tip {n}", "source": f"work/research/e87-tips/swt.md#f{n}"}


def _sheet(**overrides: Any) -> dict[str, Any]:
    sheet: dict[str, Any] = {
        "id": "worksheet-a",
        "name": "Hoja A",
        "guide": {"steps": [_step("uno"), _step("dos")]},
        "tips": [_tip(1), _tip(2), _tip(3)],
        "ai_prompt": {"text": "Prompt principal."},
    }
    sheet.update(overrides)
    return sheet


START = {"title": "Arranque con IA", "text": "Pega esto una vez.", "at": "start"}
END = {"title": "Hazla visual", "text": "Haz un cartel.", "at": "end"}


# --- T1: the contract --------------------------------------------------------


def test_sheet_without_extra_prompts_has_an_empty_list() -> None:
    guide = parse_guide(_sheet())
    assert guide is not None
    assert guide.extra_prompts == []
    assert guide.ai_prompt is not None
    assert guide.ai_prompt.text == "Prompt principal."


def test_extra_prompts_parse_in_order() -> None:
    guide = parse_guide(_sheet(extra_prompts=[START, END]))
    assert guide is not None
    assert [(p.title, p.at) for p in guide.extra_prompts] == [
        ("Arranque con IA", "start"),
        ("Hazla visual", "end"),
    ]


def test_extra_prompt_defaults_to_end() -> None:
    guide = parse_guide(_sheet(extra_prompts=[{"title": "X", "text": "Y"}]))
    assert guide is not None
    assert guide.extra_prompts[0].at == "end"


@pytest.mark.parametrize(
    "prompt",
    [
        {"title": "X", "text": "Y", "page": 4},
        {"text": "Y"},
        {"title": "X", "text": "Y", "at": "middle"},
        {"title": " ", "text": "Y"},
    ],
    ids=["page", "no-title", "bad-at", "blank-title"],
)
def test_bad_extra_prompt_is_rejected(prompt: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        parse_guide(_sheet(extra_prompts=[prompt]))
