"""S86.8 (A3): "Antes de tu reunión" without the owner asking.

When a conversation opens, if the owner has a confirmed tab and the group
meeting is in 3 days or less, the first line offers to review the sheet. It is
offered once per meeting: any answer (sí, después, no) closes that meeting;
the next meeting is offered again. A damaged memory file offers nothing.
Synthetic data only.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from coaching.tracker.flow import FlowResult, run
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
from coaching.tracker.messages import ASK_MEETING_DAY, ASK_NEXT_MEETING_DATE

ROOT = Path(__file__).resolve().parents[1]

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


# --- T2: the tracker actions ------------------------------------------------


def _run(base: Path, **context: object) -> FlowResult:
    return run({"base_path": str(base), **context})


def _ready(base: Path) -> None:
    _confirm_tab(base)
    save_schedule(base, _weekly_thursday())


def test_opening_offers_the_review_when_everything_is_in_place(tmp_path: Path) -> None:
    _ready(tmp_path)

    result = _run(tmp_path, action="opening", today="2026-09-30")

    assert result.message == "Tu reunión del grupo es mañana. ¿Reviso tu hoja?"
    assert result.meeting == date(2026, 10, 1)
    assert result.errors == []


# 2026-09-27 is 4 days before Thursday 2026-10-01; 2026-10-02 is 6 before 10-08.
@pytest.mark.parametrize("today", ["2026-09-27", "2026-10-02"])
def test_opening_far_from_the_meeting_says_nothing(tmp_path: Path, today: str) -> None:
    _ready(tmp_path)

    result = _run(tmp_path, action="opening", today=today)

    assert result.message == ""
    assert result.errors == []


def test_opening_without_confirmed_tab_says_nothing(tmp_path: Path) -> None:
    save_schedule(tmp_path, _weekly_thursday())

    result = _run(tmp_path, action="opening", today="2026-09-30")

    assert (result.message, result.errors, result.meeting) == ("", [], None)


def test_opening_without_a_meeting_day_says_nothing(tmp_path: Path) -> None:
    _confirm_tab(tmp_path)

    assert _run(tmp_path, action="opening", today="2026-09-30").message == ""


def test_opening_with_a_damaged_file_says_nothing(tmp_path: Path) -> None:
    _confirm_tab(tmp_path)
    path = meeting_path(tmp_path)
    path.write_text("schedule: [roto", encoding="utf-8")

    result = _run(tmp_path, action="opening", today="2026-09-30")

    assert (result.message, result.errors) == ("", [])
    assert path.read_text(encoding="utf-8") == "schedule: [roto"


def test_opening_with_a_bad_date_says_nothing(tmp_path: Path) -> None:
    _ready(tmp_path)

    result = _run(tmp_path, action="opening", today="ayer")

    assert (result.message, result.errors) == ("", [])


def test_opening_swallows_any_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import coaching.tracker.flow as flow

    def boom(_base: Path) -> None:
        raise RuntimeError("disco desconectado")

    _ready(tmp_path)
    monkeypatch.setattr(flow, "read_memory", boom)

    result = _run(tmp_path, action="opening", today="2026-09-30")

    assert (result.message, result.errors) == ("", [])


def test_after_despues_the_same_meeting_is_not_offered_again(tmp_path: Path) -> None:
    _ready(tmp_path)
    answer = _run(
        tmp_path, action="meeting_answer", meeting="2026-10-01", outcome="despues"
    )
    assert answer.errors == []

    # Another conversation the same day, and the day of the meeting: nothing.
    assert _run(tmp_path, action="opening", today="2026-09-30").message == ""
    assert _run(tmp_path, action="opening", today="2026-10-01").message == ""
    # Before the next meeting (Thursday 2026-10-08) it is offered again.
    again = _run(tmp_path, action="opening", today="2026-10-06")
    assert again.message == "Tu reunión del grupo es el jueves. ¿Reviso tu hoja?"


@pytest.mark.parametrize(
    "context",
    [
        {"meeting": "2026-10-01", "outcome": "quizas"},
        {"meeting": "jueves", "outcome": "no"},
        {"outcome": "no"},
    ],
)
def test_a_bad_answer_is_not_saved(tmp_path: Path, context: dict[str, object]) -> None:
    result = _run(tmp_path, action="meeting_answer", **context)

    assert result.errors == ["bad_answer"]
    assert not meeting_path(tmp_path).exists()


def test_meeting_ask_is_one_plain_question() -> None:
    result = run({"action": "meeting_ask"})

    assert result.message == ASK_MEETING_DAY
    assert result.message.startswith("¿Qué día es tu reunión del grupo?")
    assert result.message.count("?") == 1


def test_meeting_set_with_a_weekday(tmp_path: Path) -> None:
    result = _run(tmp_path, action="meeting_set", weekday="los jueves")

    assert result.errors == []
    assert result.meeting_schedule == _weekly_thursday()
    assert "los jueves" in result.message
    memory = read_memory(tmp_path)
    assert memory is not None and memory.schedule == _weekly_thursday()


def test_meeting_set_with_a_date_every_two_weeks(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        action="meeting_set",
        next_date="2026-10-08",
        every_weeks=2,
        today="2026-09-30",
    )

    assert result.errors == []
    assert result.meeting_schedule == MeetingSchedule(
        next_date=date(2026, 10, 8), every_weeks=2
    )
    assert "cada dos semanas" in result.message
    assert "jueves 8 de octubre" in result.message


def test_every_two_weeks_without_a_date_asks_for_the_next_one(tmp_path: Path) -> None:
    result = _run(tmp_path, action="meeting_set", weekday="jueves", every_weeks=2)

    assert result.errors == ["needs_next_date"]
    assert result.message == ASK_NEXT_MEETING_DATE
    assert not meeting_path(tmp_path).exists()


@pytest.mark.parametrize(
    "context",
    [
        {},
        {"weekday": "pronto"},
        {"next_date": "2026-09-01", "today": "2026-09-30"},
        {"next_date": "8 de octubre"},
        {"weekday": "jueves", "every_weeks": 3},
    ],
)
def test_meeting_set_without_a_usable_day_asks_again(
    tmp_path: Path, context: dict[str, object]
) -> None:
    result = _run(tmp_path, action="meeting_set", **context)

    assert result.errors == ["needs_meeting_day"]
    assert result.message == ASK_MEETING_DAY
    assert not meeting_path(tmp_path).exists()


def test_load_tells_whether_the_meeting_day_is_known(tmp_path: Path) -> None:
    assert _run(tmp_path, action="load").meeting_schedule is None

    save_schedule(tmp_path, _weekly_thursday())

    assert _run(tmp_path, action="load").meeting_schedule == _weekly_thursday()


def test_the_real_module_answers_the_door(tmp_path: Path) -> None:
    _ready(tmp_path)
    payload = json.dumps(
        {"action": "opening", "base_path": str(tmp_path), "today": "2026-09-28"}
    )

    done = subprocess.run(
        [sys.executable, "-m", "coaching.tracker"],
        input=payload,
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    )

    out = json.loads(done.stdout)
    assert out["message"] == "Tu reunión del grupo es el jueves. ¿Reviso tu hoja?"
    assert out["meeting"] == "2026-10-01"
