"""S87.2 T5: the saved sheet as one local HTML plus its Markdown twin."""

from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from coaching.dashboard.boards.render import LOCAL_ONLY
from coaching.worksheet import find_worksheet, load_worksheet_content
from coaching.worksheet.view import (
    build_view,
    open_command,
    render_html,
    render_markdown,
    save_view,
    view_path,
)

DAY = date(2026, 10, 20)


def _core_customer() -> dict[str, Any]:
    sheet = find_worksheet("worksheet-core-customer")
    assert sheet is not None
    return load_worksheet_content(sheet)


def _answers() -> dict[str, Any]:
    return {
        "top-5-clientes": ["Doña Mari", "Don Beto"],
        "quien-es": "Dueños de fondas a 3 km que no pueden quedarse sin tortilla.",
        "necesidad": "   ",
        "atributos": "ver http://ejemplo.mx/lista",
    }


@pytest.mark.parametrize(
    ("platform", "expected"),
    [
        ("darwin", ["open", "/x/v.html"]),
        ("linux", ["xdg-open", "/x/v.html"]),
        ("linux2", ["xdg-open", "/x/v.html"]),
        ("win32", None),
    ],
)
def test_open_command_by_platform(platform: str, expected: list[str] | None) -> None:
    assert open_command(Path("/x/v.html"), platform) == expected


def test_empty_answer_says_what_is_missing_and_how() -> None:
    view = build_view(_core_customer(), _answers(), DAY)
    md = render_markdown(view)
    assert (
        "- Falta: ¿Qué necesidad de tu Cliente central llena tu producto o servicio? "
        "Cómo llenarlo: Una frase: el problema que tiene y qué cambia cuando te compra."
    ) in md
    assert "Falta: ¿Qué necesidad" in render_html(view)


def test_answer_with_a_link_or_markup_is_shown_as_plain_text() -> None:
    answers = {
        **_answers(),
        "quien-es": "<script>alert(1)</script> fondas",
    }
    view = build_view(_core_customer(), answers, DAY)
    page = render_html(view)
    md = render_markdown(view)
    assert "ver http://ejemplo.mx/lista" in page
    assert "ver http://ejemplo.mx/lista" in md
    assert "&lt;script&gt;alert(1)&lt;/script&gt; fondas" in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt; fondas" in md
    lowered = page.lower()
    for tag in ("<script", "<a ", "<link", "<img", "@import", "url("):
        assert tag not in lowered, tag


def test_same_data_gives_same_bytes() -> None:
    first = render_html(build_view(_core_customer(), _answers(), DAY))
    second = render_html(build_view(_core_customer(), _answers(), DAY))
    assert first == second
    assert first.endswith("\n")
    assert render_markdown(build_view(_core_customer(), _answers(), DAY)).endswith("\n")


def test_header_and_date() -> None:
    view = build_view(_core_customer(), _answers(), DAY)
    page = render_html(view)
    assert page.startswith("<!doctype html>")
    assert html.escape(LOCAL_ONLY) in page
    assert "Hecho el 20 de octubre de 2026." in page
    assert "<script" not in page
    assert view.title == "Hoja de Trabajo de Definicion del Cliente Central"


def test_list_answers_are_joined() -> None:
    md = render_markdown(build_view(_core_customer(), _answers(), DAY))
    assert "Doña Mari; Don Beto" in md


def test_cards_and_canvas_layouts() -> None:
    content = _core_customer()
    cards = render_html(build_view(content, {}, DAY))
    assert "class='canvas'" not in cards
    canvas_content = {**content, "view": {**content["view"], "layout": "canvas"}}
    canvas = render_html(build_view(canvas_content, {}, DAY))
    assert "class='canvas'" in canvas
    assert "<main class='wide'>" in canvas


def test_html_and_markdown_share_labels_in_order() -> None:
    view = build_view(_core_customer(), _answers(), DAY)
    labels = [view.title] + [
        text
        for block in view.blocks
        for text in [block.title] + [item.label for item in block.items]
    ]
    page = render_html(view)
    md = render_markdown(view)
    html_positions = [page.index(html.escape(label, quote=True)) for label in labels]
    md_positions = [md.index(label) for label in labels]
    assert html_positions == sorted(html_positions)
    assert md_positions == sorted(md_positions)
    assert [b.title for b in view.blocks] == [
        "Tus mejores clientes",
        "Tu Cliente central",
        "Revisión de la promesa",
        "Lo que ve tu Cliente central",
    ]


def test_legacy_sheet_builds_one_section_per_field() -> None:
    sheet = find_worksheet("worksheet-face")
    assert sheet is not None
    content = load_worksheet_content(sheet)
    fields: list[str] = content["metadata"]["fields"]
    view = build_view(content, {fields[0]: "Gerente de ventas"}, DAY)
    assert len(view.blocks) == len(fields)
    assert view.blocks[0].items[0].answer == "Gerente de ventas"
    md = render_markdown(view)
    assert f"- Falta: {fields[1]}" in md
    assert "Cómo llenarlo" not in md


def test_save_view_writes_html_and_md(tmp_path: Path) -> None:
    view = build_view(_core_customer(), {}, DAY)
    paths = save_view(tmp_path, view)
    expected_dir = tmp_path / ".escala" / "my-company" / "vistas"
    assert paths == [
        expected_dir / "2026-10-20-worksheet-core-customer.html",
        expected_dir / "2026-10-20-worksheet-core-customer.md",
    ]
    assert view_path(tmp_path, view, "md") == paths[1]
    assert all(p.is_file() for p in paths)
    assert re.search(r"Falta", paths[1].read_text(encoding="utf-8"))
    assert str(tmp_path) not in paths[0].read_text(encoding="utf-8")


def _bridged() -> dict[str, Any]:
    content = _core_customer()
    steps = [dict(s) for s in content["guide"]["steps"]]
    quien = next(s for s in steps if s["id"] == "quien-es")
    quien["next_sheet"] = {"id": "worksheet-sandbox", "title": "Caja de arena"}
    return {**content, "guide": {"steps": steps}}


def test_next_sheet_shows_after_the_answer() -> None:
    view = build_view(_bridged(), _answers(), DAY)
    item = view.blocks[1].items[0]
    assert item.next_step == "Siguiente paso: llena Caja de arena"
    page = render_html(view)
    answer = "<p class='answer'>Dueños de fondas a 3 km"
    bridge = "<p class='next'>Siguiente paso: llena Caja de arena</p>"
    assert page.index(answer) < page.index(bridge)
    md = render_markdown(view)
    assert (
        "- **¿Quién es tu Cliente central, en 10 a 20 palabras?**: "
        "Dueños de fondas a 3 km que no pueden quedarse sin tortilla.\n"
        "- Siguiente paso: llena Caja de arena\n"
    ) in md


def test_next_sheet_shows_even_when_the_answer_is_missing() -> None:
    view = build_view(_bridged(), {}, DAY)
    page = render_html(view)
    assert page.index("Falta: ¿Quién es") < page.index("Siguiente paso: llena")
    assert "- Siguiente paso: llena Caja de arena" in render_markdown(view)


def test_step_without_next_sheet_shows_no_bridge() -> None:
    view = build_view(_core_customer(), _answers(), DAY)
    assert all(i.next_step is None for b in view.blocks for i in b.items)
    assert "Siguiente paso" not in render_html(view)
    assert "Siguiente paso" not in render_markdown(view)


def test_bmc_canvas_has_ten_sections_and_four_bridges() -> None:
    sheet = find_worksheet("worksheet-bmc")
    assert sheet is not None
    view = build_view(load_worksheet_content(sheet), {}, DAY)
    assert view.layout == "canvas"
    assert len(view.blocks) == 10
    assert view.blocks[-1].title == "Lista de verificación"
    bridges = [
        (block.title, item.next_step)
        for block in view.blocks
        for item in block.items
        if item.next_step is not None
    ]
    assert bridges == [
        ("Actividades clave", "Siguiente paso: llena Actividades diferenciadoras"),
        ("Propuesta de valor", "Siguiente paso: llena Promesa de marca"),
        ("Canales", "Siguiente paso: llena Caja de arena"),
        ("Segmentos de clientes", "Siguiente paso: llena Cliente central"),
    ]
    page = render_html(view)
    md = render_markdown(view)
    assert "<div class='canvas'>" in page
    html_order = [page.index(step) for _, step in bridges if step]
    md_order = [md.index(step) for _, step in bridges if step]
    assert html_order == sorted(html_order)
    assert md_order == sorted(md_order)
