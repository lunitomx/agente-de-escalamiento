"""S88.1: a sheet shows several prompts — at step 1 and after the main one."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from coaching.core import write_yaml
from coaching.worksheet import run
from coaching.worksheet.guide import parse_guide
from coaching.worksheet.view import build_view, render_html, render_markdown

DAY = date(2026, 11, 18)


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


# --- T2: the chat ------------------------------------------------------------


def _install(base: Path, sheet: dict[str, Any]) -> None:
    """Register ``sheet`` as the only sheet of a client knowledge root."""
    knowledge = base / ".escala" / "knowledge"
    write_yaml(
        knowledge / "registry" / "worksheets.yaml",
        {
            "worksheets": [
                {
                    "id": sheet["id"],
                    "name": sheet["name"],
                    "decision": "strategy",
                    "node_path": "strategy/worksheets/a.yaml",
                }
            ]
        },
    )
    write_yaml(knowledge / "strategy" / "worksheets" / "a.yaml", sheet)


def _call(base: Path, action: str, **fields: str) -> str:
    return str(
        run(
            {
                "action": action,
                "worksheet_name": "worksheet-a",
                "base_path": str(base),
                "fields": fields,
            }
        )["output"]
    )


def test_start_prompt_shows_in_step_1_before_the_checklist(tmp_path: Path) -> None:
    _install(tmp_path, _sheet(extra_prompts=[START, END]))
    out = _call(tmp_path, "start")
    start = "**Arranque con IA:** Pega esto una vez."
    assert start in out
    assert out.index("### Paso 1") < out.index(start)
    assert out.index(start) < out.index("Antes de empezar")
    assert "Hazla visual" not in out


def test_start_prompt_is_not_in_later_steps_nor_review(tmp_path: Path) -> None:
    _install(tmp_path, _sheet(extra_prompts=[START]))
    _call(tmp_path, "start")
    step_2 = _call(tmp_path, "step")
    _call(tmp_path, "step", uno="Fondas")
    review = _call(tmp_path, "step", dos="Masa")
    assert "### Revisión Final" in review
    for out in (step_2, review):
        assert "Arranque con IA" not in out


def test_end_prompt_follows_the_main_one_in_the_review(tmp_path: Path) -> None:
    _install(tmp_path, _sheet(extra_prompts=[START, END]))
    _call(tmp_path, "start")
    _call(tmp_path, "step")
    _call(tmp_path, "step", uno="Fondas")
    review = _call(tmp_path, "step", dos="Masa")
    main = "**Prompt para tu asistente de IA:** Prompt principal."
    end = "**Hazla visual:** Haz un cartel."
    assert review.index(main) < review.index(end)
    assert review.index(end) < review.index("Responde 'confirmar'")


def test_review_without_extra_prompts_is_unchanged(tmp_path: Path) -> None:
    _install(tmp_path, _sheet())
    _call(tmp_path, "start")
    _call(tmp_path, "step")
    _call(tmp_path, "step", uno="Fondas")
    review = _call(tmp_path, "step", dos="Masa")
    assert review.splitlines()[-3:] == [
        "**Prompt para tu asistente de IA:** Prompt principal.",
        "",
        "Responde 'confirmar' para guardar la hoja y abrir tu vista.",
    ]


# --- T3: the view ------------------------------------------------------------


def _ordered(text: str, parts: list[str]) -> bool:
    places = [text.index(part) for part in parts]
    return places == sorted(places)


def test_view_html_shows_start_first_and_end_after_the_main_prompt() -> None:
    view = build_view(_sheet(extra_prompts=[START, END]), {"uno": "Fondas"}, DAY)
    page = render_html(view)
    assert _ordered(
        page,
        [
            "Arranque con IA",
            "Pega esto una vez.",
            "¿Pregunta uno?",
            "Prompt para tu asistente de IA",
            "Hazla visual",
            "Haz un cartel.",
        ],
    )


def test_view_markdown_shows_the_same_order_with_titles() -> None:
    view = build_view(_sheet(extra_prompts=[START, END]), {"uno": "Fondas"}, DAY)
    md = render_markdown(view)
    assert _ordered(
        md,
        [
            "## Arranque con IA",
            "Pega esto una vez.",
            "## ¿Pregunta uno?",
            "## Prompt para tu asistente de IA",
            "## Hazla visual",
            "Haz un cartel.",
        ],
    )


def test_view_never_draws_markup_from_an_extra_prompt() -> None:
    bad = {"title": "<b>T</b>", "text": "<script>x</script>", "at": "end"}
    page = render_html(build_view(_sheet(extra_prompts=[bad]), {}, DAY))
    assert "<script>" not in page
    assert "<b>T</b>" not in page


def test_view_without_extra_prompts_is_unchanged() -> None:
    plain = build_view(_sheet(), {"uno": "Fondas"}, DAY)
    assert plain.extra_prompts == []
    assert render_markdown(plain).count("## ") == 3


# --- T4: save names the next sheet ------------------------------------------


def _save(base: Path) -> dict[str, Any]:
    _call(base, "start")
    _call(base, "step")
    _call(base, "step", uno="Fondas")
    _call(base, "step", dos="Masa")
    return run(
        {"action": "save", "worksheet_name": "worksheet-a", "base_path": str(base)}
    )


def test_save_names_the_next_sheet_of_the_last_step(tmp_path: Path) -> None:
    last = {**_step("dos"), "next_sheet": {"id": "worksheet-b", "title": "Hoja B"}}
    _install(tmp_path, _sheet(guide={"steps": [_step("uno"), last]}))
    result = _save(tmp_path)
    assert result["errors"] == []
    assert result["output"].splitlines()[-1] == (
        "Siguiente hoja: Hoja B. Escribe `/escala-worksheet worksheet-b` para seguir."
    )
    assert result["artifacts"]["next_sheet"] == {"id": "worksheet-b", "title": "Hoja B"}


def test_save_without_next_sheet_is_unchanged(tmp_path: Path) -> None:
    first = {**_step("uno"), "next_sheet": {"id": "worksheet-b", "title": "Hoja B"}}
    _install(tmp_path, _sheet(guide={"steps": [first, _step("dos")]}))
    result = _save(tmp_path)
    assert "Siguiente hoja" not in result["output"]
    assert len(result["output"].splitlines()) == 2
    assert "next_sheet" not in result["artifacts"]
