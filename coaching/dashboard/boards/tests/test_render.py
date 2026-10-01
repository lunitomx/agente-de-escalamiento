# pyright: strict
"""S84.4: the local board, HTML plus its Markdown twin (synthetic data only)."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pytest

from coaching.dashboard.boards.patterns import PATTERNS
from coaching.dashboard.boards.recommend import build_proposal
from coaching.dashboard.boards.render import (
    FORBIDDEN,
    Board,
    build_board,
    render_html,
    render_markdown,
    save_board,
)
from coaching.evidence.facts import Fact

TODAY = date(2026, 10, 1)


def _fact(name: str, value: object, source: str = "tu cuaderno") -> Fact:
    return Fact(
        metric_definition=name,
        period="septiembre de 2026",
        source=source,
        confidence="high",
        value=value,
    )


def _board(facts: list[Fact], board_id: str = "ventas-etapas") -> Board:
    proposal = build_proposal(PATTERNS[board_id], facts)
    return build_board(proposal, facts, TODAY)


def _partial() -> Board:
    return _board([_fact("Personas que preguntan", 120)])


def test_known_numbers_show_value_source_and_period() -> None:
    board = _partial()
    asked = board.rows[0]
    assert asked.value == "120"
    assert asked.source == "tu cuaderno" and asked.period == "septiembre de 2026"
    for text in (render_html(board), render_markdown(board)):
        assert "120" in text and "tu cuaderno" in text and "septiembre de 2026" in text


def test_missing_data_is_shown_as_falta_with_how_to_get_it() -> None:
    board = _partial()
    for text in (render_html(board), render_markdown(board)):
        assert "Falta: Clientes que compran" in text
        assert "Cuenta las ventas del mes." in text


def test_header_says_local_and_footer_the_decision() -> None:
    board = _partial()
    for text in (render_html(board), render_markdown(board)):
        assert "Sólo en tu computadora; no se publica." in text
        assert PATTERNS["ventas-etapas"].decision in text


def test_no_external_reference_and_no_script() -> None:
    board = _board(
        [_fact("Personas que preguntan", 120, "mi hoja (ver https://x.example)")]
    )
    for text in (render_html(board), render_markdown(board)):
        lowered = text.lower()
        assert not any(token in lowered for token in FORBIDDEN)
    assert FORBIDDEN == ("http", "<script", "@import", "url(", "<link", "src=")


def test_text_is_escaped() -> None:
    board = _board([_fact("Personas que preguntan", "<b>120</b> & más")])
    html_text = render_html(board)
    assert "&lt;b&gt;120&lt;/b&gt; &amp; más" in html_text
    assert "<b>120" not in html_text


def test_output_is_deterministic() -> None:
    assert render_html(_partial()) == render_html(_partial())
    assert render_markdown(_partial()) == render_markdown(_partial())


def test_html_reads_on_a_phone() -> None:
    text = render_html(_partial())
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in (
        text
    )
    assert "<table" not in text
    assert "<svg" in text


def test_html_and_markdown_say_the_same() -> None:
    board = _partial()

    def words(text: str) -> set[str]:
        plain = re.sub(r"<[^>]+>", " ", text).replace("&amp;", "&")
        return set(re.findall(r"[a-záéíóúñü0-9]+", plain.lower()))

    html_words = words(render_html(board)) - {"style", "svg", "rect"}
    md_words = words(render_markdown(board))
    for row in board.rows:
        pieces = (
            (row.name, row.source, row.period, row.value or "")
            if row.value is not None
            else (row.name, "falta", row.how_to_get)
        )
        for piece in pieces:
            assert words(piece) <= html_words & md_words


def test_save_writes_html_and_md_only_under_tableros(tmp_path: Path) -> None:
    paths = save_board(tmp_path, _partial())
    assert [p.relative_to(tmp_path).as_posix() for p in paths] == [
        ".escala/my-company/tableros/2026-10-01-ventas-etapas.html",
        ".escala/my-company/tableros/2026-10-01-ventas-etapas.md",
    ]
    assert paths[0].read_text(encoding="utf-8") == render_html(_partial())
    assert sorted(p.name for p in paths[0].parent.iterdir()) == [
        "2026-10-01-ventas-etapas.html",
        "2026-10-01-ventas-etapas.md",
    ]


def test_without_numbers_nothing_is_generated(tmp_path: Path) -> None:
    board = _board([])
    assert not board.has_numbers
    with pytest.raises(ValueError, match="no_numbers"):
        save_board(tmp_path, board)
    assert not (tmp_path / ".escala").exists()


def test_guesses_are_never_shown_as_numbers() -> None:
    guess = _fact("Personas que preguntan", 100).model_copy(
        update={"comparable": False}
    )
    board = _board([guess])
    assert board.rows[0].value is None
    assert not board.has_numbers
