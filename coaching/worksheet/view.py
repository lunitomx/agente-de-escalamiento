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
from coaching.worksheet.guide import GuideStep, ToolGuide, parse_guide

VIEWS_DIR = Path(".escala") / "my-company" / "vistas"

_SHEET_CSS = (
    "main.wide{max-width:1100px}"
    "h2{font-size:1.1rem;margin:0 0 8px}"
    ".answer{margin:2px 0 10px;white-space:pre-line}"
    ".next{margin:2px 0 10px;font-weight:600}"
    ".canvas{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));"
    "gap:12px}"
    ".canvas .card{margin:0}"
)


class ViewItem(BaseModel):
    """One step as shown: its question, the answer or what is missing,
    and the bridge to the next sheet when the step has one."""

    model_config = ConfigDict(extra="forbid")

    label: str
    answer: str | None
    how: str
    next_step: str | None = None
    missing: str | None = None


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
    ai_prompt: str | None = None


AI_PROMPT_TITLE = "Prompt para tu asistente de IA"


def answer_text(value: Any) -> str | None:
    """One line for an answer: a list joins with "; ", empty becomes None."""
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
    bridge = step.next_sheet
    return ViewItem(
        label=safe_text(step.question),
        answer=answer_text(answers.get(step.id)),
        how=safe_text(step.how),
        # Shown always: it maps the canvas, not the owner's answer (D4).
        next_step=(
            f"Siguiente paso: llena {safe_text(bridge.title)}"
            if bridge is not None
            else None
        ),
    )


def missing_source_text(question: str, sheet_name: str, sheet_id: str) -> str:
    """What the canvas says when a field of a source sheet is not saved (D4).

    The owner reads the step's question and the sheet's Spanish name; the id
    appears only inside the command.
    """
    ask = question if question.endswith(("?", ".", "!")) else f"{question}."
    return f"Falta: {ask} Llena la hoja {sheet_name} con /escala-worksheet {sheet_id}"


DerivedSources = dict[str, tuple[dict[str, Any], dict[str, Any] | None]]


def derived_blocks(guide: ToolGuide, sources: DerivedSources) -> list[ViewBlock]:
    """One block per ``derived_from`` entry, from the source sheets' answers (D5).

    ``sources`` maps a sheet id to (its content, its saved answers or None when
    it is not saved as completed). An optional sheet that is not saved is left
    out; a required one shows one "Falta" line per field.
    """
    blocks: list[ViewBlock] = []
    for source in guide.derived_from:
        content, answers = sources.get(source.sheet, ({}, None))
        if answers is None and not source.required:
            continue
        source_guide = parse_guide(content) if content else None
        questions = (
            {step.id: step.question for step in source_guide.guide.steps}
            if source_guide is not None
            else {}
        )
        items: list[ViewItem] = []
        for field in source.fields:
            answer = answer_text((answers or {}).get(field))
            label = safe_text(questions.get(field, field))
            items.append(
                ViewItem(
                    label=label,
                    answer=answer,
                    how="",
                    missing=(
                        missing_source_text(
                            label, safe_text(source.title), source.sheet
                        )
                        if answer is None
                        else None
                    ),
                )
            )
        blocks.append(ViewBlock(title=safe_text(source.title), items=items))
    return blocks


def build_view(
    content: dict[str, Any],
    answers: dict[str, Any],
    made_on: date,
    derived: list[ViewBlock] | None = None,
) -> SheetView:
    """Arrange a sheet and its answers into blocks; sections or one per step.

    ``derived`` blocks (a canvas reading other sheets) go before its own.
    """
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
    blocks = [*(derived or []), *blocks]
    title = str(content.get("name_es") or content.get("name") or content.get("id", ""))
    prompt = guide.ai_prompt if guide is not None else None
    return SheetView(
        sheet_id=str(content.get("id", "")),
        title=safe_text(title),
        layout=guide.view.layout if guide is not None else "cards",
        made_on=made_on,
        blocks=blocks,
        ai_prompt=safe_text(prompt.text) if prompt is not None else None,
    )


def label_heading(label: str) -> str:
    """A label in bold; adds ":" only when it does not end in ? . ! or : (D9)."""
    if label.rstrip().endswith(("?", ".", "!", ":")):
        return f"**{label}**"
    return f"**{label}:**"


def markdown_lines(text: str) -> str:
    """One answer line per Markdown line inside a list item.

    A hard break (two spaces) ends each line and the next one is indented, so
    "Uno por línea" answers do not collapse into one line.
    """
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return "  \n  ".join(lines)


def _missing_text(item: ViewItem) -> str:
    if item.missing is not None:
        return item.missing
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
        if item.next_step is not None:
            items.append(f"<p class='next'>{e(item.next_step)}</p>")
    return f"<section class='card'><h2>{e(block.title)}</h2>{''.join(items)}</section>"


def render_html(view: SheetView) -> str:
    """Self-contained HTML: inline CSS, no script, no external reference."""
    e = html.escape
    blocks = "".join(_html_block(block) for block in view.blocks)
    prompt = (
        f"<section class='card prompt'><h2>{e(AI_PROMPT_TITLE)}</h2>"
        f"<p class='answer'>{e(view.ai_prompt)}</p></section>"
        if view.ai_prompt is not None
        else ""
    )
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
        f"{body}{prompt}"
        "</main></body></html>\n"
    )


def markdown_blocks(blocks: list[ViewBlock]) -> list[str]:
    """Markdown lines for blocks; shared by the view and the canvas step 1 (D6)."""
    lines: list[str] = []
    for block in blocks:
        lines += [f"## {block.title}", ""]
        for item in block.items:
            if item.answer is None:
                lines.append(f"- {_missing_text(item)}")
            else:
                answer = markdown_lines(html.escape(item.answer, quote=False))
                lines.append(f"- {label_heading(item.label)} {answer}")
            if item.next_step is not None:
                lines.append(f"- {item.next_step}")
        lines.append("")
    return lines


def render_markdown(view: SheetView) -> str:
    """The same content as the HTML, for the chat and the ``.md`` twin."""
    lines = [f"> {LOCAL_ONLY}", "", f"# {view.title}", "", _subtitle(view), ""]
    lines += markdown_blocks(view.blocks)
    if view.ai_prompt is not None:
        lines += [
            f"## {AI_PROMPT_TITLE}",
            "",
            html.escape(view.ai_prompt, quote=False),
            "",
        ]
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
