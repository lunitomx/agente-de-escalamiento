"""S87.2 T2: ToolGuide contract for guided worksheets."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from coaching.worksheet import list_worksheets, load_worksheet_content
from coaching.worksheet.guide import ToolGuide, parse_guide, source_label


def _step(step_id: str) -> dict[str, str]:
    return {
        "id": step_id,
        "question": f"¿Pregunta {step_id}?",
        "how": "Una frase.",
        "example": "Tortillería El Sol: tortilla caliente a las 13:00.",
    }


def _tip(n: int, step: str | None = None) -> dict[str, Any]:
    return {
        "text": f"Tip {n}",
        "source": f"work/research/e87-tips/core-customer.md#f{n}",
        "step": step,
    }


def _sheet(**overrides: Any) -> dict[str, Any]:
    sheet: dict[str, Any] = {
        "id": "worksheet-x",
        "metadata": {"fields": ["a"]},
        "guide": {"steps": [_step("quien-es"), _step("necesidad")]},
        "tips": [_tip(1), _tip(2, "quien-es"), _tip(3)],
    }
    sheet.update(overrides)
    return sheet


def test_valid_guide_parses_and_ignores_other_keys() -> None:
    guide = parse_guide(_sheet())
    assert isinstance(guide, ToolGuide)
    assert [s.id for s in guide.guide.steps] == ["quien-es", "necesidad"]
    assert guide.view.layout == "cards"
    assert guide.view.sections == []
    assert guide.ai_prompt is None
    assert guide.derived_from == []


def test_sheet_without_guide_returns_none() -> None:
    assert parse_guide({"id": "worksheet-face", "metadata": {"fields": ["a"]}}) is None


def test_step_without_example_is_rejected() -> None:
    step = _step("promesa-principal")
    del step["example"]
    with pytest.raises(ValidationError):
        parse_guide(_sheet(guide={"steps": [step]}, tips=[_tip(1), _tip(2), _tip(3)]))


def test_blank_example_is_rejected() -> None:
    step = _step("promesa")
    step["example"] = "  "
    with pytest.raises(ValidationError):
        parse_guide(_sheet(guide={"steps": [step]}, tips=[_tip(1), _tip(2), _tip(3)]))


def test_bad_step_id_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_guide(
            _sheet(
                guide={"steps": [_step("Quien Es")]}, tips=[_tip(1), _tip(2), _tip(3)]
            )
        )


def test_two_tips_are_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_guide(_sheet(tips=[_tip(1), _tip(2)]))


def test_tip_without_source_is_rejected() -> None:
    tip: dict[str, Any] = {"text": "Sin fuente"}
    with pytest.raises(ValidationError):
        parse_guide(_sheet(tips=[_tip(1), _tip(2), tip]))


def test_ai_prompt_page_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_guide(_sheet(ai_prompt={"text": "Ayúdame", "page": 20}))


def test_ai_prompt_text_is_accepted() -> None:
    guide = parse_guide(_sheet(ai_prompt={"text": "Ayúdame"}))
    assert guide is not None and guide.ai_prompt is not None


def test_tip_for_missing_step_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_guide(_sheet(tips=[_tip(1), _tip(2), _tip(3, "nadie")]))


def test_duplicate_step_ids_are_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_guide(_sheet(guide={"steps": [_step("a"), _step("a")]}))


def test_section_with_missing_step_is_rejected() -> None:
    view = {
        "sections": [{"title": "Todo", "steps": ["quien-es", "necesidad", "nadie"]}]
    }
    with pytest.raises(ValidationError):
        parse_guide(_sheet(view=view))


def test_step_outside_every_section_is_rejected() -> None:
    view = {"sections": [{"title": "Solo uno", "steps": ["quien-es"]}]}
    with pytest.raises(ValidationError):
        parse_guide(_sheet(view=view))


def test_canvas_with_full_sections_is_accepted() -> None:
    view = {
        "layout": "canvas",
        "sections": [
            {"title": "Quién", "steps": ["quien-es"]},
            {"title": "Qué", "steps": ["necesidad"]},
        ],
    }
    guide = parse_guide(_sheet(view=view))
    assert guide is not None and guide.view.layout == "canvas"


def test_unknown_layout_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_guide(_sheet(view={"layout": "grid"}))


def test_derived_from_shape_is_accepted() -> None:
    derived = [
        {"sheet": "worksheet-core-customer", "fields": ["quien-es"], "into": "x"}
    ]
    guide = parse_guide(_sheet(derived_from=derived))
    assert guide is not None and guide.derived_from[0].required is True


def _with_next(next_sheet: Any) -> dict[str, Any]:
    step = {**_step("quien-es"), "next_sheet": next_sheet}
    return _sheet(guide={"steps": [step, _step("necesidad")]})


def test_next_sheet_is_accepted() -> None:
    guide = parse_guide(
        _with_next({"id": "worksheet-sandbox", "title": "Caja de arena"})
    )
    assert guide is not None
    bridge = guide.guide.steps[0].next_sheet
    assert bridge is not None
    assert (bridge.id, bridge.title) == ("worksheet-sandbox", "Caja de arena")


def test_next_sheet_is_optional() -> None:
    guide = parse_guide(_sheet())
    assert guide is not None
    assert all(step.next_sheet is None for step in guide.guide.steps)


@pytest.mark.parametrize(
    "bad",
    [
        {"id": "Caja de arena", "title": "Caja de arena"},
        {"id": "sandbox", "title": "Caja de arena"},
        {"id": "worksheet-sandbox"},
        {"id": "worksheet-sandbox", "title": "  "},
        {"id": "worksheet-sandbox", "title": "Caja", "page": 28},
    ],
)
def test_bad_next_sheet_is_rejected(bad: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        parse_guide(_with_next(bad))


def test_every_registered_sheet_loads_and_passes_the_contract() -> None:
    sheets = list_worksheets()
    assert len(sheets) == 18
    for sheet in sheets:
        content = load_worksheet_content(sheet)
        assert content.get("metadata") or content.get("guide"), sheet["id"]
        parse_guide(content)


def test_source_label_hides_the_internal_path() -> None:
    assert (
        source_label("work/research/e87-tips/core-customer.md#f3")
        == "Investigación ESCALA (nota interna f3)"
    )
    assert source_label("Libro de trabajo, p. 13") == "Libro de trabajo, p. 13"
