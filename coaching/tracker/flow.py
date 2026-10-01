# pyright: strict
"""Guided flow the tracker procedure drives: ``python -m coaching.tracker``.

Actions (JSON on stdin, like ``coaching.strategy_opsp``):

- ``ask_name`` / ``connect``: the fixed messages (connect carries the Drive notice).
- ``drive_not_found`` / ``drive_no_access`` (S86.3): fixed messages for when the
  connector finds no file or has no permission; only the agent can tell.
- ``tabs``: tab names of the connector text; no cell is read.
- ``candidates``: reuse the remembered tab if the file and tab still match,
  otherwise propose tabs by name only.
- ``confirm``: requires ``user_confirmed: true``; keeps only the confirmed tab
  (connector text or pasted tab), parses it and saves the reference.
- ``load``: the remembered reference, if any.
- ``propose`` (S82.4): rows for the month from the quarter's priorities, for
  the remembered tab only, plus the block to paste and where to paste it.
  Nothing is written: the owner pastes the rows himself after reviewing them.
  With ``"table": "rocks"`` (S82.7) the rows go to Quarterly Goals (Rocks)
  for the quarter the sheet declares; if it declares none, ESCALA asks (the
  answer comes back in ``quarter``), and a plan for another quarter is asked
  about before any block is given.
- ``prepare`` (S82.5): before the group meeting, for the remembered tab only:
  overdue commitments, finished ones to move to Done (with the block and the
  cell to paste it), missing KPI or date, and dates "por confirmar". ``today``
  (``YYYY-MM-DD``) sets the reference date. Suggestions only; nothing is written.
- ``opening`` (S86.8): the door's one call when a conversation opens. With a
  confirmed tab and the group meeting in 3 days or less, ``message`` is the
  first line ("Tu reunión del grupo es el jueves. ¿Reviso tu hoja?") and
  ``meeting`` its date; otherwise ``message`` is empty. It never returns an
  error: any failure means saying nothing (the nudge is optional).
- ``meeting_ask`` / ``meeting_set`` (S86.8): ask the meeting day once, when it
  first matters, and keep it (``weekday`` as the owner said it, and/or
  ``next_date`` ISO; ``every_weeks`` 1 or 2, two weeks needs ``next_date``).
- ``meeting_answer`` (S86.8): the owner's ``si`` / ``despues`` / ``no`` to the
  offer for ``meeting`` (ISO); that meeting is not offered again.

The procedure persists the choice through this module; the private specialist
never writes state.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, timezone
from pathlib import Path
from typing import cast

import yaml
from pydantic import BaseModel, Field, ValidationError

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
from coaching.tracker.maintenance import (
    MeetingPrep,
    review_before_meeting,
    to_done_block,
)
from coaching.tracker.meeting import (
    MeetingAnswer,
    MeetingSchedule,
    opening_nudge,
    parse_weekday,
    read_memory,
    record_answer,
    save_schedule,
)
from coaching.tracker.models import TrackerSheet
from coaching.tracker.parser import (
    Grid,
    commitments_layout,
    done_layout,
    parse_sheet,
    rocks_layout,
)
from coaching.tracker.proposal import (
    QuarterCheck,
    QuarterlyPlanInput,
    RockProposal,
    RowProposal,
    check_quarter,
    propose_rocks,
    propose_rows,
    to_paste_block,
)


class FlowResult(BaseModel):
    """Everything the flow hands back to the conversation."""

    action: str
    message: str = ""
    tab_names: list[str] = Field(default_factory=list)
    candidates: list[SheetCandidate] = Field(default_factory=list[SheetCandidate])
    link: TrackerLink | None = None
    sheet: TrackerSheet | None = None
    proposal: RowProposal | None = None
    prep: MeetingPrep | None = None
    rock_proposal: RockProposal | None = None
    quarter_check: QuarterCheck | None = None
    paste_block: str = ""
    meeting: date | None = None
    meeting_schedule: MeetingSchedule | None = None
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
    connector, pasted = _text(context, "connector_text"), _text(context, "pasted_text")
    tab_name = _text(context, "tab_name")
    if tab_name is None and connector is None and pasted is not None:
        # Owner default (S82.4): a pasted tab takes the name the user already gave.
        tab_name = _text(context, "name")
    if tab_name is None:
        return _refusal(messages.ASK_TAB_NAME, "needs_tab_name")
    if " ".join(tab_name.lower().split()) == START_HERE:
        return _refusal(messages.START_HERE_IS_NOT_YOURS, "start_here")
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
    # Owner default (S82.4): the Drive notice is said once, on the first link
    # through the connector, even if Drive was already connected.
    first_link = load_link(base) is None
    notice = (
        connector is not None
        and first_link
        and context.get("drive_notice_shown") is not True
    )
    link = TrackerLink(
        file_title=_text(context, "file_title") if connector is not None else None,
        file_id=_text(context, "file_id") if connector is not None else None,
        tab_name=tab_name,
        confirmed_at=datetime.now(timezone.utc),
    )
    save_link(link, base)
    message = messages.confirmed_message(tab_name, sheet.participant)
    return FlowResult(
        action="confirm",
        message=f"{message} {messages.DRIVE_NOTICE}" if notice else message,
        link=link,
        sheet=sheet,
    )


def _opsp_plan(base: Path) -> QuarterlyPlanInput | None:
    path = base / ".escala" / "my-company" / "opsp.yaml"
    try:
        raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(raw, dict):
        return None
    return QuarterlyPlanInput.from_opsp_state(cast(dict[str, object], raw))


def _plan(context: Mapping[str, object], base: Path) -> QuarterlyPlanInput | None:
    raw = context.get("plan")
    try:
        plan = (
            QuarterlyPlanInput.from_opsp_state({"quarterly_plan": cast(object, raw)})
            if isinstance(raw, dict)
            else _opsp_plan(base)
        )
    except ValidationError:
        return None
    return plan if plan is not None and plan.priorities else None


def _propose_refusal(message: str, error: str) -> FlowResult:
    return FlowResult(action="propose", message=message, errors=[error])


def _own_grid(context: Mapping[str, object], link: TrackerLink) -> Grid | str:
    """Only the remembered tab's grid, or the error code why it cannot be read."""
    connector, pasted = _text(context, "connector_text"), _text(context, "pasted_text")
    grid: Grid | None
    if connector is not None:
        same = link_matches(
            link,
            _text(context, "file_title"),
            _text(context, "file_id"),
            list_tab_names(connector),
        )
        if link.file_title is not None or link.file_id is not None:
            if not same:
                return "link_mismatch"
        grid = confirmed_tab_grid(connector, link.tab_name)
    elif pasted is not None:
        grid = parse_pasted_tab(pasted)
    else:
        grid = None
    return "tab_not_found" if grid is None else grid


def _propose(context: Mapping[str, object], base: Path) -> FlowResult:
    link = load_link(base)
    if link is None:
        return _propose_refusal(messages.NEEDS_CONFIRMED_TAB, "needs_confirmed_tab")
    grid = _own_grid(context, link)
    if grid == "link_mismatch":
        return _propose_refusal(messages.LINK_MISMATCH, "link_mismatch")
    if isinstance(grid, str):
        return _propose_refusal(messages.tab_not_found_message(link.tab_name), grid)
    table = _text(context, "table") or "commitments"
    if table not in ("commitments", "rocks"):
        return _propose_refusal(messages.ASK_TABLE, "bad_table")
    plan = _plan(context, base)
    if plan is None:
        return _propose_refusal(messages.NO_PLAN, "needs_plan")
    if table == "rocks":
        return _propose_rocks(context, grid, plan, link)
    month = _text(context, "month") or date.today().strftime("%Y-%m")
    try:
        proposal = propose_rows(parse_sheet(grid), plan, month)
    except ValueError:
        return _propose_refusal(messages.ASK_MONTH, "bad_month")
    layout = commitments_layout(grid)
    block = to_paste_block(proposal.rows, layout.fields if layout else None)
    return FlowResult(
        action="propose",
        message=messages.proposal_message(proposal, layout, link.tab_name, block),
        link=link,
        proposal=proposal,
        paste_block=block,
    )


def _propose_rocks(
    context: Mapping[str, object],
    grid: Grid,
    plan: QuarterlyPlanInput,
    link: TrackerLink,
) -> FlowResult:
    """Rocks rows for the quarter the sheet declares (S82.7); asks if unclear."""
    layout = rocks_layout(grid)
    if layout is None:
        return _propose_refusal(messages.NO_ROCKS_TABLE, "no_rocks_table")
    sheet = parse_sheet(grid)
    check = check_quarter(sheet, plan, _text(context, "quarter"))
    if check.status != "ok" or check.quarter is None:
        ask = check.status == "mismatch"
        return FlowResult(
            action="propose",
            message=(
                messages.quarter_mismatch_message(check)
                if ask
                else messages.ask_quarter_message(check)
            ),
            link=link,
            quarter_check=check,
            errors=["quarter_mismatch" if ask else "needs_quarter"],
        )
    proposal = propose_rocks(sheet, plan, check.quarter)
    block = to_paste_block(proposal.rows, layout.fields)
    return FlowResult(
        action="propose",
        message=messages.rocks_proposal_message(proposal, layout, link.tab_name, block),
        link=link,
        rock_proposal=proposal,
        quarter_check=check,
        paste_block=block,
    )


def _prepare_refusal(message: str, error: str) -> FlowResult:
    return FlowResult(action="prepare", message=message, errors=[error])


def _today(context: Mapping[str, object]) -> date | None:
    raw = _text(context, "today")
    if raw is None:
        return date.today()
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _prepare(context: Mapping[str, object], base: Path) -> FlowResult:
    link = load_link(base)
    if link is None:
        return _prepare_refusal(
            messages.PREP_NEEDS_CONFIRMED_TAB, "needs_confirmed_tab"
        )
    grid = _own_grid(context, link)
    if grid == "link_mismatch":
        return _prepare_refusal(messages.PREP_LINK_MISMATCH, "link_mismatch")
    if isinstance(grid, str):
        return _prepare_refusal(messages.tab_not_found_message(link.tab_name), grid)
    today = _today(context)
    if today is None:
        return _prepare_refusal(messages.ASK_TODAY, "bad_today")
    rocks = rocks_layout(grid)
    prep = review_before_meeting(
        parse_sheet(grid), today, rocks.fields if rocks else None
    )
    layout = done_layout(grid)
    block = to_done_block(prep.finished, layout.fields if layout else None)
    return FlowResult(
        action="prepare",
        message=messages.prep_message(prep, layout, link.tab_name, block),
        link=link,
        prep=prep,
        paste_block=block,
    )


def _opening_nudge(context: Mapping[str, object], base: Path) -> FlowResult:
    today = _today(context)
    memory = read_memory(base)
    if today is None or memory is None:
        return FlowResult(action="opening")
    answered = [item.meeting for item in memory.answered]
    has_tab = load_link(base) is not None
    nudge = opening_nudge(today, memory.schedule, has_tab, answered)
    if nudge is None:
        return FlowResult(action="opening")
    return FlowResult(action="opening", message=nudge.message, meeting=nudge.meeting)


def _opening(context: Mapping[str, object], base: Path) -> FlowResult:
    """Never an error at the door: an optional nudge that fails says nothing."""
    try:
        return _opening_nudge(context, base)
    except Exception:
        return FlowResult(action="opening")


def _iso(context: Mapping[str, object], key: str) -> date | None:
    raw = _text(context, key)
    try:
        return date.fromisoformat(raw) if raw is not None else None
    except ValueError:
        return None


def _meeting_refusal(message: str, error: str) -> FlowResult:
    return FlowResult(action="meeting_set", message=message, errors=[error])


def _meeting_set(context: Mapping[str, object], base: Path) -> FlowResult:
    raw_weekday = _text(context, "weekday")
    weekday = parse_weekday(raw_weekday) if raw_weekday is not None else None
    next_date = _iso(context, "next_date")
    every_weeks = context.get("every_weeks")
    today = _today(context) or date.today()
    if every_weeks == 2 and next_date is None and weekday is not None:
        return _meeting_refusal(messages.ASK_NEXT_MEETING_DATE, "needs_next_date")
    try:
        schedule = MeetingSchedule.model_validate(
            {"next_date": next_date, "weekday": weekday, "every_weeks": every_weeks}
        )
    except ValidationError:
        return _meeting_refusal(messages.ASK_MEETING_DAY, "needs_meeting_day")
    if schedule.next_date is not None and schedule.next_date < today:
        return _meeting_refusal(messages.ASK_MEETING_DAY, "needs_meeting_day")
    save_schedule(base, schedule)
    return FlowResult(
        action="meeting_set",
        message=messages.meeting_saved_message(
            schedule.next_date, schedule.weekday, schedule.every_weeks
        ),
        meeting_schedule=schedule,
    )


def _meeting_answer(context: Mapping[str, object], base: Path) -> FlowResult:
    try:
        answer = MeetingAnswer.model_validate(
            {"meeting": _iso(context, "meeting"), "outcome": _text(context, "outcome")}
        )
    except ValidationError:
        return FlowResult(action="meeting_answer", errors=["bad_answer"])
    record_answer(base, answer)
    return FlowResult(action="meeting_answer", meeting=answer.meeting)


def _meeting_schedule(base: Path) -> MeetingSchedule | None:
    memory = read_memory(base)
    return memory.schedule if memory is not None else None


def run(context: Mapping[str, object]) -> FlowResult:
    """Run one step of the guided flow."""
    action = _text(context, "action") or ""
    base = Path(_text(context, "base_path") or ".")
    if action == "ask_name":
        return FlowResult(action=action, message=messages.ASK_NAME)
    if action == "connect":
        return FlowResult(action=action, message=messages.connect_message())
    if action == "drive_not_found":
        return FlowResult(action=action, message=messages.DRIVE_FILE_NOT_FOUND)
    if action == "drive_no_access":
        return FlowResult(action=action, message=messages.DRIVE_NO_ACCESS)
    if action == "tabs":
        return FlowResult(action=action, tab_names=_tab_names(context))
    if action == "candidates":
        return _candidates(context, base)
    if action == "confirm":
        return _confirm(context, base)
    if action == "propose":
        return _propose(context, base)
    if action == "prepare":
        return _prepare(context, base)
    if action == "load":
        return FlowResult(
            action=action,
            link=load_link(base),
            meeting_schedule=_meeting_schedule(base),
        )
    if action == "opening":
        return _opening(context, base)
    if action == "meeting_ask":
        return FlowResult(action=action, message=messages.ASK_MEETING_DAY)
    if action == "meeting_set":
        return _meeting_set(context, base)
    if action == "meeting_answer":
        return _meeting_answer(context, base)
    return FlowResult(action=action, errors=["unknown_action"])
