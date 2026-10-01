# pyright: strict
"""When the group meeting is, and whether to offer the review (E86 S86.8, A3).

``.escala/my-company/meeting.yaml`` (ignored by git) keeps the schedule the
owner gave once and, per meeting date, that the review was already offered and
answered (``si`` / ``despues`` / ``no``). Never the owner's words and never
sheet content.

The offer is silenced **per meeting**, not for 30 days like the journey
question (E84): meetings are weekly or every two weeks, and the next meeting
must be offered again. Like E84, a damaged file never produces nagging: it
reads as ``None`` and the opening says nothing; the next write moves it to
``meeting.yaml.bak`` (``.bak.2``... if one exists) first.
"""

from __future__ import annotations

import os
import tempfile
import unicodedata
from collections.abc import Collection
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from coaching.tracker import messages

WINDOW_DAYS = 3
MeetingOutcome = Literal["si", "despues", "no"]


def _fold(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(folded.lower().split())


def parse_weekday(text: str) -> int | None:
    """``"los jueves"`` -> 3 (0 = lunes); ``None`` if no single day is named."""
    words = set(_fold(text).replace(",", " ").split())
    found = [
        index
        for index, name in enumerate(map(_fold, messages.WEEKDAY_NAMES))
        if {name, f"{name}s"} & words
    ]
    return found[0] if len(found) == 1 else None


class MeetingSchedule(BaseModel):
    """The meeting as the owner said it once.

    - ``next_date`` alone: one meeting on that date.
    - ``weekday`` alone: every week on that day.
    - ``next_date`` + ``every_weeks``: from that date, every 1 or 2 weeks.
      Every two weeks needs a date: "los jueves cada dos semanas" does not
      say whether this Thursday has a meeting.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    next_date: date | None = None
    weekday: int | None = Field(default=None, ge=0, le=6)
    every_weeks: Literal[1, 2] | None = None

    @model_validator(mode="after")
    def _consistent(self) -> MeetingSchedule:
        if self.next_date is None and self.weekday is None:
            raise ValueError("needs a date or a weekday")
        if self.every_weeks == 2 and self.next_date is None:
            raise ValueError("every two weeks needs the next date")
        if (
            self.next_date is not None
            and self.weekday is not None
            and self.next_date.weekday() != self.weekday
        ):
            raise ValueError("weekday does not match the date")
        return self


def next_meeting(schedule: MeetingSchedule, today: date) -> date | None:
    """The next meeting on or after ``today``; ``None`` if a single date passed."""
    if schedule.next_date is not None:
        if schedule.next_date >= today:
            return schedule.next_date
        if schedule.every_weeks is None:
            return None
        step = 7 * schedule.every_weeks
        late = (today - schedule.next_date).days
        return schedule.next_date + timedelta(days=-(-late // step) * step)
    assert schedule.weekday is not None  # guaranteed by the validator
    return today + timedelta(days=(schedule.weekday - today.weekday()) % 7)


def day_phrase(meeting: date, today: date) -> str:
    """Say "hoy", "mañana" or "el jueves" (only for meetings within a week)."""
    days = (meeting - today).days
    if days == 0:
        return "hoy"
    if days == 1:
        return "mañana"
    return f"el {messages.WEEKDAY_NAMES[meeting.weekday()]}"


class MeetingNudge(BaseModel):
    """The opening line and the meeting it is about (to record the answer)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    meeting: date
    message: str


def opening_nudge(
    today: date,
    schedule: MeetingSchedule | None,
    has_confirmed_tab: bool,
    answered: Collection[date],
) -> MeetingNudge | None:
    """The first line of the conversation, or ``None`` to say nothing."""
    if not has_confirmed_tab or schedule is None:
        return None
    meeting = next_meeting(schedule, today)
    if meeting is None or (meeting - today).days > WINDOW_DAYS:
        return None
    if meeting in answered:
        return None
    return MeetingNudge(
        meeting=meeting,
        message=messages.meeting_nudge_message(day_phrase(meeting, today)),
    )


class MeetingAnswer(BaseModel):
    """The owner answered the offer for this meeting; it is not offered again."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    meeting: date
    outcome: MeetingOutcome


class MeetingMemory(BaseModel):
    """What ``meeting.yaml`` holds."""

    model_config = ConfigDict(extra="forbid")

    schedule: MeetingSchedule | None = None
    answered: list[MeetingAnswer] = Field(default_factory=list[MeetingAnswer])


def meeting_path(base: Path) -> Path:
    return base / ".escala" / "my-company" / "meeting.yaml"


def read_memory(base: Path) -> MeetingMemory | None:
    """The memory; empty if missing, ``None`` if the file is damaged."""
    path = meeting_path(base)
    if not path.exists():
        return MeetingMemory()
    try:
        raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
        return MeetingMemory.model_validate(raw)
    except (OSError, yaml.YAMLError, ValidationError):
        return None


def _backup(path: Path) -> Path:
    """Move a damaged file aside without overwriting an earlier backup."""
    target = path.with_name(f"{path.name}.bak")
    number = 2
    while target.exists():
        target = path.with_name(f"{path.name}.bak.{number}")
        number += 1
    path.replace(target)
    return target


def _write(base: Path, memory: MeetingMemory) -> Path:
    path = meeting_path(base)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(memory.model_dump(mode="json"), sort_keys=False)
    handle, tmp = tempfile.mkstemp(dir=path.parent, prefix=".meeting-", suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(text)
    Path(tmp).replace(path)
    return path


def _current(base: Path) -> MeetingMemory:
    memory = read_memory(base)
    if memory is None:
        _backup(meeting_path(base))
        return MeetingMemory()
    return memory


def save_schedule(base: Path, schedule: MeetingSchedule) -> Path:
    """Keep the schedule (a new one replaces the old; answers stay)."""
    memory = _current(base)
    return _write(base, MeetingMemory(schedule=schedule, answered=memory.answered))


def record_answer(base: Path, answer: MeetingAnswer) -> Path:
    """Remember that this meeting's offer was answered."""
    memory = _current(base)
    answered = [item for item in memory.answered if item.meeting != answer.meeting]
    return _write(
        base, MeetingMemory(schedule=memory.schedule, answered=[*answered, answer])
    )
