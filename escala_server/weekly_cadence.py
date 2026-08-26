"""Local, opt-in weekly GTD cadence. It never sends notifications itself."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Literal
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .human_context import HumanContextStore
from .project_memory import ProjectMemoryRuntime

ReviewOutcome = Literal["done", "blocked", "deferred", "renegotiated"]
AutomationState = Literal["accepted", "rejected", "paused", "removed"]

_ACTION_STARTS = (
    "llamar", "enviar", "preparar", "revisar", "definir", "agendar", "escribir",
    "hablar", "validar", "pedir", "crear", "comparar", "actualizar", "reunir",
)


@dataclass(frozen=True)
class WeeklyCommitment:
    id: str
    priority: str
    project: str
    desired_outcome: str
    next_action: str
    owner: str
    status: str


@dataclass(frozen=True)
class CadenceResult:
    ready: bool
    cadence_id: str | None = None
    commitment: WeeklyCommitment | None = None
    commitments: tuple[WeeklyCommitment, ...] = ()
    due: bool = False
    next_review_on: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class AutomationProposal:
    kind: str
    purpose: str
    frequency_months: int
    data_minimum: str
    host_capability: str
    manual_alternative: str


class WeeklyCadenceStore:
    """Persist reviewed commitments locally, only after explicit user consent."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.runtime = ProjectMemoryRuntime(self.project_root)

    def configure(
        self,
        *,
        weekday: int,
        timezone: str,
        duration_minutes: int,
        owner: str,
        priority: str,
        project: str,
        desired_outcome: str,
        next_action: str,
        explicit_confirmation: bool,
        now: datetime | None = None,
    ) -> CadenceResult:
        if not explicit_confirmation:
            return CadenceResult(False, reason="explicit confirmation is required")
        try:
            zone = _zone(timezone)
            _validate_weekday(weekday)
            _validate_duration(duration_minutes)
            _text(owner, "owner")
            commitment = _commitment(priority, project, desired_outcome, next_action, owner)
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return CadenceResult(False, reason=memory.reason)
            review_on = _next_weekday(_local_date(now, zone), weekday, include_today=False)
            cadence_id, commitment_id = str(uuid4()), str(uuid4())
            with sqlite3.connect(memory.db_path) as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("UPDATE weekly_cadences SET status='paused', updated_at=CURRENT_TIMESTAMP WHERE status='active'")
                db.execute(
                    """INSERT INTO weekly_cadences
                       (id, status, weekday, timezone, duration_minutes, owner, next_review_on)
                       VALUES (?, 'active', ?, ?, ?, ?, ?)""",
                    (cadence_id, weekday, timezone, duration_minutes, owner.strip(), review_on.isoformat()),
                )
                db.execute(
                    """INSERT INTO weekly_commitments
                       (id, cadence_id, priority, project, desired_outcome, next_action, owner, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 'active')""",
                    (commitment_id, cadence_id, *commitment),
                )
                db.commit()
            return CadenceResult(True, cadence_id, WeeklyCommitment(commitment_id, *commitment, "active"), next_review_on=review_on.isoformat())
        except (OSError, sqlite3.Error, ValueError) as error:
            return CadenceResult(False, reason=str(error))

    def status(self, *, now: datetime | None = None) -> CadenceResult:
        try:
            # Status is safe to call on every public turn: never create a DB
            # merely to discover that the person has not opted in.
            memory = self.runtime.health()
            if not memory.ready:
                return CadenceResult(True)
            with sqlite3.connect(memory.db_path) as db:
                row = db.execute(
                    """SELECT id, status, weekday, timezone, next_review_on
                       FROM weekly_cadences ORDER BY created_at DESC, id DESC LIMIT 1"""
                ).fetchone()
                if row is None:
                    return CadenceResult(True)
                cadence_id, state, weekday, timezone, next_review_on = row
                rows = db.execute(
                    """SELECT id, priority, project, desired_outcome, next_action, owner, status
                       FROM weekly_commitments WHERE cadence_id=? AND status='active'
                       ORDER BY created_at, id""",
                    (cadence_id,),
                ).fetchall()
            due = state == "active" and _local_date(now, _zone(timezone)) >= date.fromisoformat(next_review_on)
            return CadenceResult(True, cadence_id, tuple_to_commitment(rows[0]) if rows else None, tuple(tuple_to_commitment(row) for row in rows), due, next_review_on)
        except (OSError, sqlite3.Error, ValueError) as error:
            return CadenceResult(False, reason=str(error))

    def pause(self) -> CadenceResult:
        return self._set_cadence_state("paused")

    def resume(self, *, now: datetime | None = None) -> CadenceResult:
        try:
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return CadenceResult(False, reason=memory.reason)
            with sqlite3.connect(memory.db_path) as db:
                row = db.execute("SELECT id, weekday, timezone FROM weekly_cadences ORDER BY created_at DESC, id DESC LIMIT 1").fetchone()
                if row is None:
                    return CadenceResult(False, reason="no weekly cadence exists")
                cadence_id, weekday, timezone = row
                due = _next_weekday(_local_date(now, _zone(timezone)), weekday, include_today=False).isoformat()
                db.execute("UPDATE weekly_cadences SET status='active', next_review_on=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (due, cadence_id))
                db.commit()
            return CadenceResult(True, cadence_id, next_review_on=due)
        except (OSError, sqlite3.Error, ValueError) as error:
            return CadenceResult(False, reason=str(error))

    def review(
        self,
        *,
        outcome: ReviewOutcome,
        result: str,
        blocker: str | None,
        priority: str,
        project: str,
        desired_outcome: str,
        next_action: str,
        owner: str,
        explicit_confirmation: bool,
        now: datetime | None = None,
    ) -> CadenceResult:
        if not explicit_confirmation:
            return CadenceResult(False, reason="explicit confirmation is required")
        try:
            if outcome not in {"done", "blocked", "deferred", "renegotiated"}:
                raise ValueError("invalid weekly review outcome")
            result_text = _text(result, "result")
            blocker_text = _text(blocker, "blocker") if blocker else None
            if outcome == "blocked" and not blocker_text:
                raise ValueError("a blocked commitment needs a stated blocker")
            new = _commitment(priority, project, desired_outcome, next_action, owner)
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return CadenceResult(False, reason=memory.reason)
            with sqlite3.connect(memory.db_path) as db:
                db.execute("BEGIN IMMEDIATE")
                cadence = db.execute("SELECT id, weekday, timezone FROM weekly_cadences WHERE status='active' ORDER BY created_at DESC, id DESC LIMIT 1").fetchone()
                if cadence is None:
                    return CadenceResult(False, reason="no active weekly cadence exists")
                cadence_id, weekday, timezone = cadence
                old = db.execute("SELECT id FROM weekly_commitments WHERE cadence_id=? AND status='active' ORDER BY created_at, id LIMIT 1", (cadence_id,)).fetchone()
                if old is None:
                    return CadenceResult(False, reason="no active weekly commitment exists")
                old_id = old[0]
                db.execute("INSERT INTO weekly_reviews (id, commitment_id, outcome, result, blocker) VALUES (?, ?, ?, ?, ?)", (str(uuid4()), old_id, outcome, result_text, blocker_text))
                db.execute("UPDATE weekly_commitments SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (outcome, old_id))
                new_id = str(uuid4())
                db.execute("""INSERT INTO weekly_commitments (id, cadence_id, priority, project, desired_outcome, next_action, owner, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'active')""", (new_id, cadence_id, *new))
                next_due = _next_weekday(_local_date(now, _zone(timezone)), weekday, include_today=False).isoformat()
                db.execute("UPDATE weekly_cadences SET next_review_on=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (next_due, cadence_id))
                db.commit()
            return CadenceResult(True, cadence_id, WeeklyCommitment(new_id, *new, "active"), next_review_on=next_due)
        except (OSError, sqlite3.Error, ValueError) as error:
            return CadenceResult(False, reason=str(error))

    def propose_automation(
        self, *, kind: str, purpose: str, frequency_months: int,
        data_minimum: str, host_capability: str, manual_alternative: str,
    ) -> AutomationProposal:
        """Return a proposal only. This method never writes or executes anything."""
        return AutomationProposal(
            _text(kind, "kind"), _text(purpose, "purpose"), _frequency(frequency_months),
            _text(data_minimum, "data minimum"), _text(host_capability, "host capability"),
            _text(manual_alternative, "manual alternative"),
        )

    def respond_automation(
        self, proposal: AutomationProposal, *, state: AutomationState,
        explicit_confirmation: bool, host_configured_by_user: bool = False,
    ) -> CadenceResult:
        if not explicit_confirmation:
            return CadenceResult(False, reason="explicit confirmation is required")
        if state not in {"accepted", "rejected", "paused", "removed"}:
            return CadenceResult(False, reason="invalid automation response")
        try:
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return CadenceResult(False, reason=memory.reason)
            with sqlite3.connect(memory.db_path) as db:
                db.execute("""INSERT INTO cadence_automation_preferences
                    (id, kind, purpose, frequency_months, data_minimum, host_capability, manual_alternative, state, host_state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    str(uuid4()), proposal.kind, proposal.purpose, proposal.frequency_months,
                    proposal.data_minimum, proposal.host_capability, proposal.manual_alternative,
                    state, "configured_by_user" if host_configured_by_user else "not_configured",
                ))
                db.commit()
            return CadenceResult(True)
        except (OSError, sqlite3.Error, ValueError) as error:
            return CadenceResult(False, reason=str(error))

    def relevant_human_context(self):
        """Cadence consumes only its explicitly relevant human context fields."""
        return HumanContextStore(self.project_root).project("cadence")

    def _set_cadence_state(self, state: str) -> CadenceResult:
        try:
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return CadenceResult(False, reason=memory.reason)
            with sqlite3.connect(memory.db_path) as db:
                row = db.execute("SELECT id FROM weekly_cadences ORDER BY created_at DESC, id DESC LIMIT 1").fetchone()
                if row is None:
                    return CadenceResult(False, reason="no weekly cadence exists")
                db.execute("UPDATE weekly_cadences SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (state, row[0]))
                db.commit()
            return CadenceResult(True, row[0])
        except (OSError, sqlite3.Error, ValueError) as error:
            return CadenceResult(False, reason=str(error))


def tuple_to_commitment(row: tuple) -> WeeklyCommitment:
    return WeeklyCommitment(*row)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")
    clean = " ".join(value.strip().split())
    if not 1 <= len(clean) <= 240 or "\x00" in clean:
        raise ValueError(f"{label} is invalid")
    return clean


def _commitment(priority: str, project: str, desired_outcome: str, next_action: str, owner: str) -> tuple[str, str, str, str, str]:
    action = _text(next_action, "next action")
    if len(action.split()) < 3 or not action.casefold().startswith(_ACTION_STARTS):
        raise ValueError("next action must be concrete and start with an action verb")
    return (_text(priority, "priority"), _text(project, "project"), _text(desired_outcome, "desired outcome"), action, _text(owner, "owner"))


def _validate_weekday(weekday: int) -> None:
    if not isinstance(weekday, int) or isinstance(weekday, bool) or not 0 <= weekday <= 6:
        raise ValueError("weekday must be between 0 and 6")


def _validate_duration(value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or not 10 <= value <= 180:
        raise ValueError("duration must be between 10 and 180 minutes")


def _frequency(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 12:
        raise ValueError("frequency must be between 1 and 12 months")
    return value


def _zone(value: str) -> ZoneInfo:
    try:
        return ZoneInfo(_text(value, "timezone"))
    except ZoneInfoNotFoundError as error:
        raise ValueError("timezone must be an IANA timezone") from error


def _local_date(now: datetime | None, zone: ZoneInfo) -> date:
    current = now or datetime.now(zone)
    return current.astimezone(zone).date() if current.tzinfo else current.replace(tzinfo=zone).date()


def _next_weekday(today: date, weekday: int, *, include_today: bool) -> date:
    offset = (weekday - today.weekday()) % 7
    if offset == 0 and not include_today:
        offset = 7
    return today + timedelta(days=offset)
