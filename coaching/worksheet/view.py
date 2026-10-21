# pyright: strict
"""Worksheet view (E87 S87.2): one self-contained HTML plus its Markdown twin.

Pattern of the E84 board (``coaching/dashboard/boards/render.py``):
``build_view`` decides what is shown, ``render_html`` and ``render_markdown``
only draw it, so both outputs carry the same labels in the same order.
Deterministic: same content, answers and date give the same bytes.
The owner's answers are always shown, escaped as plain text in both outputs;
a link is text, never a tag.

``open_command`` is pure: it returns the command; the skill runs it.
"""

from __future__ import annotations

import html
from datetime import date
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict

from coaching.dashboard.boards.render import (
    BASE_CSS,
    LOCAL_ONLY,
    atomic_write,
    safe_text,
)
from coaching.journey.view import spanish_date
from coaching.worksheet.guide import GuideStep, parse_guide

VIEWS_DIR = Path(".escala") / "my-company" / "vistas"

_SHEET_CSS = (
    "main.wide{max-width:1100px}"
    "h2{font-size:1.1rem;margin:0 0 8px}"
    ".answer{margin:2px 0 10px;white-space:pre-line}"
    ".canvas{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));"
    "gap:12px}"
    ".canvas .card{margin:0}"
)


class ViewItem(BaseModel):
    """One step as shown: its question and the answer, or what is missing."""

    model_config = ConfigDict(extra="forbid")

    label: str
    answer: str | None
    how: str


class ViewBlock(BaseModel):
    """One section of the view."""

    model_config = ConfigDict(extra="forbid")

    title: str
    items: list[ViewItem]


class SheetView(BaseModel):
    """What the HTML and the Markdown both show, in the same order."""

    model_config = ConfigDict(extra="forbid")

    sheet_id: str
    title: str
    layout: Literal["cards", "canvas"]
    made_on: date
    blocks: list[ViewBlock]


def _answer_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        items = cast(list[Any], value)
        text = "; ".join(p for p in (str(i).strip() for i in items) if p)
    else:
        text = str(value).strip()
    # The owner's answer is never dropped: a link or markup stays as plain
    # text, escaped by each renderer (R1 of the S87.2 quality review).
    return text or None


def _legacy_steps(content: dict[str, Any]) -> list[GuideStep]:
    metadata: Any = content.get("metadata")
    fields: Any = (
        cast(dict[str, Any], metadata).get("fields")
        if isinstance(metadata, dict)
        else None
    )
    texts = (
        [str(f) for f in cast(list[Any], fields)] if isinstance(fields, list) else []
    )
    return [
        GuideStep.model_construct(id=text, question=text, how="", example="")
        for text in texts
    ]


def _item(step: GuideStep, answers: dict[str, Any]) -> ViewItem:
    return ViewItem(
        label=safe_text(step.question),
        answer=_answer_text(answers.get(step.id)),
        how=safe_text(step.how),
    )


def build_view(
    content: dict[str, Any], answers: dict[str, Any], made_on: date
) -> SheetView:
    """Arrange a sheet and its answers into blocks; sections or one per step."""
    guide = parse_guide(content)
    steps = guide.guide.steps if guide is not None else _legacy_steps(content)
    by_id = {step.id: step for step in steps}
    if guide is not None and guide.view.sections:
        blocks = [
            ViewBlock(
                title=safe_text(section.title),
                items=[_item(by_id[step_id], answers) for step_id in section.steps],
            )
            for section in guide.view.sections
        ]
    else:
        blocks = [
            ViewBlock(title=safe_text(step.question), items=[_item(step, answers)])
            for step in steps
        ]
    title = str(content.get("name_es") or content.get("name") or content.get("id", ""))
    return SheetView(
        sheet_id=str(content.get("id", "")),
        title=safe_text(title),
        layout=guide.view.layout if guide is not None else "cards",
        made_on=made_on,
        blocks=blocks,
    )


def markdown_lines(text: str) -> str:
    """One answer line per Markdown line inside a list item.

    A hard break (two spaces) ends each line and the next one is indented, so
    "Uno por línea" answers do not collapse into one line.
    """
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return "  \n  ".join(lines)


def _missing_text(item: ViewItem) -> str:
    label = item.label if item.label.endswith(("?", ".", "!")) else f"{item.label}."
    if item.how:
        return f"Falta: {label} Cómo llenarlo: {item.how}"
    return f"Falta: {label}"


def _subtitle(view: SheetView) -> str:
    return f"Hecho el {spanish_date(view.made_on)}."


def _html_block(block: ViewBlock) -> str:
    e = html.escape
    items: list[str] = []
    for item in block.items:
        if item.answer is None:
            items.append(f"<p class='missing'>{e(_missing_text(item))}</p>")
        else:
            items.append(
                f"<div class='name'>{e(item.label)}</div>"
                f"<p class='answer'>{e(item.answer)}</p>"
            )
    return f"<section class='card'><h2>{e(block.title)}</h2>{''.join(items)}</section>"


def render_html(view: SheetView) -> str:
    """Self-contained HTML: inline CSS, no script, no external reference."""
    e = html.escape
    blocks = "".join(_html_block(block) for block in view.blocks)
    if view.layout == "canvas":
        main_open, body = "<main class='wide'>", f"<div class='canvas'>{blocks}</div>"
    else:
        main_open, body = "<main>", blocks
    return (
        "<!doctype html>\n<html lang='es'><head><meta charset='utf-8'>"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{e(view.title)}</title><style>{BASE_CSS}{_SHEET_CSS}</style>"
        f"</head><body>{main_open}"
        f"<p class='local'>{e(LOCAL_ONLY)}</p>"
        f"<h1>{e(view.title)}</h1><p class='muted'>{e(_subtitle(view))}</p>"
        f"{body}"
        "</main></body></html>\n"
    )


def render_markdown(view: SheetView) -> str:
    """The same content as the HTML, for the chat and the ``.md`` twin."""
    lines = [f"> {LOCAL_ONLY}", "", f"# {view.title}", "", _subtitle(view), ""]
    for block in view.blocks:
        lines += [f"## {block.title}", ""]
        for item in block.items:
            if item.answer is None:
                lines.append(f"- {_missing_text(item)}")
            else:
                answer = markdown_lines(html.escape(item.answer, quote=False))
                lines.append(f"- **{item.label}**: {answer}")
        lines.append("")
    return "\n".join(lines)


def view_path(base: Path, view: SheetView, suffix: str) -> Path:
    """``.escala/my-company/vistas/AAAA-MM-DD-<sheet_id>.<suffix>``."""
    return base / VIEWS_DIR / f"{view.made_on.isoformat()}-{view.sheet_id}.{suffix}"


def save_view(base: Path, view: SheetView) -> list[Path]:
    """Write the HTML and its Markdown twin; an all-missing view is still written."""
    paths = [view_path(base, view, "html"), view_path(base, view, "md")]
    atomic_write(paths[0], render_html(view))
    atomic_write(paths[1], render_markdown(view))
    return paths


def open_command(html_path: Path, platform: str) -> list[str] | None:
    """Command that opens the HTML: ``open`` (macOS), ``xdg-open`` (Linux), else None."""
    if platform == "darwin":
        return ["open", str(html_path)]
    if platform.startswith("linux"):
        return ["xdg-open", str(html_path)]
    return None
