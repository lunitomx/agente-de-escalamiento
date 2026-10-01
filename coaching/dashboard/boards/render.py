# pyright: strict
"""Local board (E84 S84.4): one self-contained HTML plus its Markdown twin.

Pattern of ``escala_server/financial/report.py`` (E38): every text goes
through ``html.escape``, the output is deterministic (same data, same bytes)
and files are written atomically. On top of that:

- inline CSS and inline SVG bars; no JavaScript, no CDN, no fonts, no images,
  no ``url(`` or ``@import``. A text that carries any ``FORBIDDEN`` token
  (e.g. a link inside a source) is replaced, never rendered;
- readable on a phone: viewport meta, one column of cards, no tables;
- a missing number says "Falta: <dato>" and how to get it; a guess or a range
  is never shown as a number;
- header "Sólo en tu computadora; no se publica.", footer the decision;
- without a single number nothing is saved (``no_numbers``).
"""

from __future__ import annotations

import html
import os
import tempfile
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from coaching.dashboard.boards.memory import BOARDS_DIR
from coaching.dashboard.boards.models import BoardProposal, MetricStatus
from coaching.evidence.facts import Fact
from coaching.journey.view import spanish_date

FORBIDDEN: tuple[str, ...] = ("http", "<script", "@import", "url(", "<link", "src=")
LOCAL_ONLY = "Sólo en tu computadora; no se publica."
HIDDEN = "(texto con un enlace; no se muestra)"
_RATIO_PREFIX = "De cada 10"


class BoardRow(BaseModel):
    """One metric as shown: a number with source and period, or "Falta"."""

    model_config = ConfigDict(extra="forbid")

    name: str
    value: str | None
    source: str
    period: str
    status: MetricStatus
    how_to_get: str
    bar: float | None = None


class Board(BaseModel):
    """What the HTML and the Markdown both show, in the same order."""

    model_config = ConfigDict(extra="forbid")

    board_id: str
    title: str
    decision: str
    audience: str
    cadence: str
    made_on: date
    rows: list[BoardRow]

    @property
    def has_numbers(self) -> bool:
        return any(row.value is not None for row in self.rows)


def _clean(text: str) -> str:
    lowered = text.lower()
    return HIDDEN if any(token in lowered for token in FORBIDDEN) else text


def _number(value: object) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _bar(name: str, value: object, largest: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    if name.startswith(_RATIO_PREFIX):
        return max(0.0, min(1.0, float(value) / 10))
    return max(0.0, min(1.0, float(value) / largest)) if largest > 0 else None


def build_board(proposal: BoardProposal, facts: Sequence[Fact], made_on: date) -> Board:
    """The board of an accepted proposal, with the values of its known facts."""
    known: dict[str, Fact] = {
        fact.metric_definition.casefold(): fact for fact in facts if fact.comparable
    }
    values = {
        m.metric_definition: known[m.metric_definition.casefold()].value
        for m in proposal.metrics
        if m.status == "conocido" and m.metric_definition.casefold() in known
    }
    counts = [
        float(v)
        for name, v in values.items()
        if not name.startswith(_RATIO_PREFIX)
        and isinstance(v, int | float)
        and not isinstance(v, bool)
    ]
    largest = max(counts, default=0.0)
    rows = [
        BoardRow(
            name=_clean(metric.metric_definition),
            value=None
            if metric.metric_definition not in values
            else _clean(_number(values[metric.metric_definition])),
            source=_clean(metric.source),
            period=_clean(metric.period),
            status=metric.status,
            how_to_get=_clean(metric.how_to_get),
            bar=None
            if metric.metric_definition not in values
            else _bar(
                metric.metric_definition, values[metric.metric_definition], largest
            ),
        )
        for metric in proposal.metrics
    ]
    return Board(
        board_id=proposal.board_id,
        title=_clean(proposal.title),
        decision=_clean(proposal.decision),
        audience=_clean(proposal.audience),
        cadence=_clean(proposal.cadence),
        made_on=made_on,
        rows=rows,
    )


def _missing_text(row: BoardRow) -> str:
    why = (
        " (lo que tienes es aproximado o de otro mes)"
        if row.status == "no_comparable"
        else ""
    )
    return f"Falta: {row.name}{why}. Cómo conseguirlo: {row.how_to_get}"


def _subtitle(board: Board) -> str:
    return f"Lo mira: {board.audience}. {board.cadence}. Hecho el {spanish_date(board.made_on)}."


_CSS = (
    "*{box-sizing:border-box}"
    "body{margin:0;padding:16px;background:#f7f7f5;color:#1d2228;"
    "font:17px/1.5 system-ui,-apple-system,'Segoe UI',sans-serif}"
    "main{max-width:640px;margin:0 auto}"
    "h1{font-size:1.4rem;margin:.5rem 0}"
    ".local{background:#fff4d6;border-radius:8px;padding:8px 12px;font-weight:600}"
    ".muted{color:#5b6570;font-size:.95rem}"
    ".card{background:#fff;border:1px solid #e3e3df;border-radius:12px;"
    "padding:12px 14px;margin:12px 0}"
    ".name{font-weight:600}"
    ".value{font-size:2rem;font-weight:700;margin:2px 0}"
    ".missing{color:#9a3412;font-weight:600}"
    "svg{display:block;width:100%;height:12px;margin:6px 0}"
    "footer{border-top:2px solid #1d2228;margin-top:20px;padding-top:12px}"
)


def _html_row(row: BoardRow) -> str:
    e = html.escape
    if row.value is None:
        return (
            f"<section class='card'><div class='name'>{e(row.name)}</div>"
            f"<div class='missing'>{e(_missing_text(row))}</div></section>"
        )
    bar = ""
    if row.bar is not None:
        width = f"{row.bar * 100:.1f}"
        bar = (
            "<svg viewBox='0 0 100 12' preserveAspectRatio='none' aria-hidden='true'>"
            "<rect width='100' height='12' rx='6' fill='#e8e8e3'/>"
            f"<rect width='{width}' height='12' rx='6' fill='#2f6f4f'/></svg>"
        )
    return (
        f"<section class='card'><div class='name'>{e(row.name)}</div>"
        f"<div class='value'>{e(row.value)}</div>{bar}"
        f"<div class='muted'>Fuente: {e(row.source)}. Periodo: {e(row.period)}.</div>"
        "</section>"
    )


def render_html(board: Board) -> str:
    """Self-contained HTML: inline CSS and SVG, no script, no external reference."""
    e = html.escape
    rows = "".join(_html_row(row) for row in board.rows)
    return (
        "<!doctype html>\n<html lang='es'><head><meta charset='utf-8'>"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{e(board.title)}</title><style>{_CSS}</style></head><body><main>"
        f"<p class='local'>{e(LOCAL_ONLY)}</p>"
        f"<h1>{e(board.title)}</h1><p class='muted'>{e(_subtitle(board))}</p>"
        f"{rows}"
        f"<footer><div class='name'>Este tablero sirve para decidir:</div>"
        f"<p>{e(board.decision)}</p></footer>"
        "</main></body></html>\n"
    )


def render_markdown(board: Board) -> str:
    """The same content as the HTML, for the chat and the ``.md`` twin."""
    lines = [f"> {LOCAL_ONLY}", "", f"# {board.title}", "", _subtitle(board), ""]
    for row in board.rows:
        if row.value is None:
            lines += [f"- **{row.name}**: {_missing_text(row)}"]
        else:
            lines += [
                f"- **{row.name}**: {row.value}. "
                f"Fuente: {row.source}. Periodo: {row.period}."
            ]
    lines += ["", "**Este tablero sirve para decidir:**", "", board.decision, ""]
    return "\n".join(lines)


def board_path(base: Path, board: Board, suffix: str) -> Path:
    """``.escala/my-company/tableros/AAAA-MM-DD-<board_id>.<suffix>``."""
    return base / BOARDS_DIR / f"{board.made_on.isoformat()}-{board.board_id}.{suffix}"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp = tempfile.mkstemp(dir=path.parent, prefix=".board-", suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(content)
    Path(tmp).replace(path)


def save_board(base: Path, board: Board) -> list[Path]:
    """Write the HTML and its Markdown twin; refused without a single number."""
    if not board.has_numbers:
        raise ValueError("no_numbers")
    paths = [board_path(base, board, "html"), board_path(base, board, "md")]
    _atomic_write(paths[0], render_html(board))
    _atomic_write(paths[1], render_markdown(board))
    return paths
