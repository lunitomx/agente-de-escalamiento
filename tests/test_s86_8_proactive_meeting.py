"""S86.8 (A3): "Antes de tu reunión" without the owner asking.

When a conversation opens, if the owner has a confirmed tab and the group
meeting is in 3 days or less, the first line offers to review the sheet. It is
offered once per meeting: any answer (sí, después, no) closes that meeting;
the next meeting is offered again. A damaged memory file offers nothing.
Synthetic data only.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from coaching.tracker.identity import TrackerLink, save_link
from coaching.tracker.meeting import (
    MeetingAnswer,
    MeetingSchedule,
    day_phrase,
    meeting_path,
    next_meeting,
    opening_nudge,
    parse_weekday,
    read_memory,
    record_answer,
    save_schedule,
)

# Wednesday 2026-09-30; Thursday 2026-10-01 ... Sunday 2026-10-04.
WEDNESDAY = date(2026, 9, 30)
THURSDAY = 3


def _weekly_thursday() -> MeetingSchedule:
    return MeetingSchedule(weekday=THURSDAY)


# --- T1: when is the next meeting --------------------------------------------


def test_weekly_weekday_gives_the_next_one_including_today() -> None:
    schedule = _weekly_thursday()

    assert next_meeting(schedule, WEDNESDAY) == date(2026, 10, 1)
    assert next_meeting(schedule, date(2026, 10, 1)) == date(2026, 10, 1)
    assert next_meeting(schedule, date(2026, 10, 2)) == date(2026, 10, 8)


def test_a_single_date_is_gone_once_it_passes() -> None:
    schedule = MeetingSchedule(next_date=date(2026, 10, 2))

    assert next_meeting(schedule, WEDNESDAY) == date(2026, 10, 2)
    assert next_meeting(schedule, date(2026, 10, 3)) is None


def test_every_two_weeks_counts_from_the_date_the_owner_gave() -> None:
    schedule = MeetingSchedule(next_date=date(2026, 10, 1), every_weeks=2)

    assert next_meeting(schedule, WEDNESDAY) == date(2026, 10, 1)
    assert next_meeting(schedule, date(2026, 10, 2)) == date(2026, 10, 15)
    assert next_meeting(schedule, date(2026, 10, 16)) == date(2026, 10, 29)


def test_every_two_weeks_needs_a_date() -> None:
    with pytest.raises(ValidationError):
        MeetingSchedule(weekday=THURSDAY, every_weeks=2)


def test_a_schedule_needs_a_date_or_a_day() -> None:
    with pytest.raises(ValidationError):
        MeetingSchedule()


def test_weekday_and_date_must_agree() -> None:
    with pytest.raises(ValidationError):
        MeetingSchedule(next_date=date(2026, 10, 1), weekday=0)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("jueves", 3),
        ("Los jueves", 3),
        ("miércoles", 2),
        ("miercoles", 2),
        ("sábado", 5),
        ("lunes", 0),
        ("mañana", None),
        ("", None),
    ],
)
def test_weekday_names_in_spanish(text: str, expected: int | None) -> None:
    assert parse_weekday(text) == expected


# --- T1: the opening line -------------------------------------------------


@pytest.mark.parametrize(
    ("today", "phrase"),
    [
        (date(2026, 10, 1), "hoy"),
        (WEDNESDAY, "mañana"),
        (date(2026, 9, 29), "el jueves"),
        (date(2026, 9, 28), "el jueves"),
    ],
)
def test_day_in_plain_spanish(today: date, phrase: str) -> None:
    assert day_phrase(date(2026, 10, 1), today) == phrase


def test_meeting_within_three_days_with_confirmed_tab_offers_the_review() -> None:
    nudge = opening_nudge(date(2026, 9, 28), _weekly_thursday(), True, [])

    assert nudge is not None
    assert nudge.meeting == date(2026, 10, 1)
    assert nudge.message == "Tu reunión del grupo es el jueves. ¿Reviso tu hoja?"


def test_meeting_tomorrow_says_manana() -> None:
    nudge = opening_nudge(WEDNESDAY, _weekly_thursday(), True, [])

    assert nudge is not None
    assert nudge.message == "Tu reunión del grupo es mañana. ¿Reviso tu hoja?"


def test_meeting_in_four_days_says_nothing() -> None:
    # Sunday 2026-09-27 -> Thursday 2026-10-01 is 4 days away.
    assert opening_nudge(date(2026, 9, 27), _weekly_thursday(), True, []) is None


def test_without_confirmed_tab_says_nothing() -> None:
    assert opening_nudge(WEDNESDAY, _weekly_thursday(), False, []) is None


def test_without_schedule_says_nothing() -> None:
    assert opening_nudge(WEDNESDAY, None, True, []) is None


def test_after_an_answer_that_meeting_is_not_offered_again() -> None:
    answered = [date(2026, 10, 1)]

    assert opening_nudge(WEDNESDAY, _weekly_thursday(), True, answered) is None
    # The next meeting (Thursday 2026-10-08) is offered again.
    nudge = opening_nudge(date(2026, 10, 6), _weekly_thursday(), True, answered)
    assert nudge is not None
    assert nudge.meeting == date(2026, 10, 8)


# --- T1: memory on disk ----------------------------------------------------


def test_missing_file_is_an_empty_memory(tmp_path: Path) -> None:
    memory = read_memory(tmp_path)

    assert memory is not None
    assert memory.schedule is None
    assert memory.answered == []


def test_schedule_and_answers_survive_between_conversations(tmp_path: Path) -> None:
    save_schedule(tmp_path, _weekly_thursday())
    record_answer(tmp_path, MeetingAnswer(meeting=date(2026, 10, 1), outcome="despues"))

    memory = read_memory(tmp_path)
    assert memory is not None
    assert memory.schedule == _weekly_thursday()
    assert [item.meeting for item in memory.answered] == [date(2026, 10, 1)]
    assert meeting_path(tmp_path) == tmp_path / ".escala/my-company/meeting.yaml"


def test_memory_keeps_no_owner_words(tmp_path: Path) -> None:
    save_schedule(tmp_path, _weekly_thursday())
    record_answer(tmp_path, MeetingAnswer(meeting=date(2026, 10, 1), outcome="no"))

    text = meeting_path(tmp_path).read_text(encoding="utf-8")
    assert set(text.split()) <= {
        "schedule:",
        "next_date:",
        "null",
        "weekday:",
        "3",
        "every_weeks:",
        "answered:",
        "-",
        "meeting:",
        "'2026-10-01'",
        "outcome:",
        "'no'",
    }


@pytest.mark.parametrize("content", ["::: x [", "schedule: 12\n", "- a\n- b\n"])
def test_damaged_file_reads_as_none(tmp_path: Path, content: str) -> None:
    path = meeting_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")

    assert read_memory(tmp_path) is None


def test_writing_over_a_damaged_file_keeps_a_backup(tmp_path: Path) -> None:
    path = meeting_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("::: x [", encoding="utf-8")

    save_schedule(tmp_path, _weekly_thursday())

    assert path.with_name("meeting.yaml.bak").read_text(encoding="utf-8") == "::: x ["
    memory = read_memory(tmp_path)
    assert memory is not None and memory.schedule == _weekly_thursday()


def _confirm_tab(base: Path) -> None:
    save_link(
        TrackerLink(
            tab_name="Ana",
            confirmed_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        ),
        base,
    )
