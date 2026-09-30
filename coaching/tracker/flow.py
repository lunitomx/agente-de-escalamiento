# pyright: strict
"""Guided flow the tracker procedure drives: ``python -m coaching.tracker``.

Actions (JSON on stdin, like ``coaching.strategy_opsp``):

- ``ask_name`` / ``connect``: the fixed messages (connect carries the Drive notice).
- ``tabs``: tab names of the connector text; no cell is read.
- ``candidates``: reuse the remembered tab if the file and tab still match,
  otherwise propose tabs by name only.
- ``confirm``: requires ``user_confirmed: true``; keeps only the confirmed tab
  (connector text or pasted tab), parses it and saves the reference.
- ``load``: the remembered reference, if any.

The procedure persists the choice through this module; the private specialist
never writes state.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from pydantic import BaseModel, Field

from coaching.tracker import messages
from coaching.tracker.identity import (
    START_HERE,
    SheetCandidate,
    TrackerLink,
    confirmed_tab_grid,
    link_matches,
    list_tab_names,
    load_link,
    parse_pasted_tab,
    rank_candidates,
    save_link,
)
from coaching.tracker.models import TrackerSheet
from coaching.tracker.parser import Grid, parse_sheet


class FlowResult(BaseModel):
    """Everything the flow hands back to the conversation."""

    action: str
    message: str = ""
    tab_names: list[str] = Field(default_factory=list)
    candidates: list[SheetCandidate] = Field(default_factory=list[SheetCandidate])
    link: TrackerLink | None = None
    sheet: TrackerSheet | None = None
    errors: list[str] = Field(default_factory=list)


def _text(context: Mapping[str, object], key: str) -> str | None:
    value = context.get(key)
    return value.strip() or None if isinstance(value, str) else None


def _tab_names(context: Mapping[str, object]) -> list[str]:
    connector = _text(context, "connector_text")
    if connector is not None:
        return list_tab_names(connector)
    raw = context.get("tab_names")
    if isinstance(raw, list):
        return [str(item) for item in cast(list[object], raw)]
    return []


def _candidates(context: Mapping[str, object], base: Path) -> FlowResult:
    tab_names = _tab_names(context)
    file_title, file_id = _text(context, "file_title"), _text(context, "file_id")
    link = load_link(base)
    if link is not None and link_matches(link, file_title, file_id, tab_names):
        return FlowResult(
            action="candidates",
            message=messages.remembered_message(link.tab_name),
            tab_names=tab_names,
            link=link,
        )
    name = _text(context, "name")
    if name is None:
        return FlowResult(
            action="candidates", message=messages.ASK_NAME, errors=["needs_name"]
        )
    business = _text(context, "business")
    ranked = rank_candidates(tab_names, name, business)
    return FlowResult(
        action="candidates",
        message=messages.candidates_message(ranked, business),
        tab_names=tab_names,
        candidates=ranked,
    )


def _refusal(message: str, error: str) -> FlowResult:
    return FlowResult(action="confirm", message=message, errors=[error])


def _confirm(context: Mapping[str, object], base: Path) -> FlowResult:
    if context.get("user_confirmed") is not True:
        return _refusal(messages.NEEDS_YES, "needs_confirmation")
    tab_name = _text(context, "tab_name")
    if tab_name is None:
        return _refusal(messages.ASK_TAB_NAME, "needs_tab_name")
    if " ".join(tab_name.lower().split()) == START_HERE:
        return _refusal(messages.START_HERE_IS_NOT_YOURS, "start_here")
    connector, pasted = _text(context, "connector_text"), _text(context, "pasted_text")
    grid: Grid | None
    if connector is not None:
        grid = confirmed_tab_grid(connector, tab_name)
    elif pasted is not None:
        grid = parse_pasted_tab(pasted)
    else:
        grid = None
    if grid is None:
        return _refusal(messages.tab_not_found_message(tab_name), "tab_not_found")
    sheet = parse_sheet(grid)
    link = TrackerLink(
        file_title=_text(context, "file_title") if connector is not None else None,
        file_id=_text(context, "file_id") if connector is not None else None,
        tab_name=tab_name,
        confirmed_at=datetime.now(timezone.utc),
    )
    save_link(link, base)
    return FlowResult(
        action="confirm",
        message=messages.confirmed_message(tab_name, sheet.participant),
        link=link,
        sheet=sheet,
    )


def run(context: Mapping[str, object]) -> FlowResult:
    """Run one step of the guided flow."""
    action = _text(context, "action") or ""
    base = Path(_text(context, "base_path") or ".")
    if action == "ask_name":
        return FlowResult(action=action, message=messages.ASK_NAME)
    if action == "connect":
        return FlowResult(action=action, message=messages.connect_message())
    if action == "tabs":
        return FlowResult(action=action, tab_names=_tab_names(context))
    if action == "candidates":
        return _candidates(context, base)
    if action == "confirm":
        return _confirm(context, base)
    if action == "load":
        return FlowResult(action=action, link=load_link(base))
    return FlowResult(action=action, errors=["unknown_action"])
