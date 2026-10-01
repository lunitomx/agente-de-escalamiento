"""Memory of the journey question: ``.escala/my-company/journey/asks.yaml``."""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from coaching.journey.asks import (
    AskRecord,
    asks_path,
    declined_on,
    last_declined_on,
    load_asks,
    read_asks,
    record_ask,
)

ROOT = Path(__file__).resolve().parents[3]


def _record(day: int, outcome: str, reason: str = "T1") -> AskRecord:
    return AskRecord.model_validate(
        {"asked_on": date(2026, 9, day), "outcome": outcome, "reason": reason}
    )


def test_asks_live_under_my_company_journey(tmp_path: Path) -> None:
    assert asks_path(tmp_path) == tmp_path / ".escala/my-company/journey/asks.yaml"


def test_record_appends_and_reloads(tmp_path: Path) -> None:
    first, backup = record_ask(tmp_path, _record(1, "despues"))
    record_ask(tmp_path, _record(20, "si", "T2"))

    assert backup is None

    assert first == asks_path(tmp_path)
    assert load_asks(tmp_path) == [_record(1, "despues"), _record(20, "si", "T2")]
    raw = yaml.safe_load(first.read_text(encoding="utf-8"))
    assert raw == {
        "asks": [
            {"asked_on": "2026-09-01", "outcome": "despues", "reason": "T1"},
            {"asked_on": "2026-09-20", "outcome": "si", "reason": "T2"},
        ]
    }


def test_no_file_means_never_asked(tmp_path: Path) -> None:
    assert load_asks(tmp_path) == []


def test_last_decline_is_the_latest_no_or_later_and_yes_does_not_count() -> None:
    records = [_record(1, "no"), _record(10, "despues"), _record(25, "si")]

    assert last_declined_on(records) == date(2026, 9, 10)
    assert last_declined_on([_record(25, "si")]) is None
    assert last_declined_on([]) is None


def test_the_record_keeps_only_a_code_never_the_owners_words() -> None:
    with pytest.raises(ValidationError):
        AskRecord.model_validate(
            {"asked_on": "2026-09-01", "outcome": "no", "reason": "pocos compran"}
        )
    with pytest.raises(ValidationError):
        AskRecord.model_validate(
            {"asked_on": "2026-09-01", "outcome": "no", "reason": "T1", "text": "x"}
        )


def test_journey_folder_is_ignored_by_git() -> None:
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")

    result = subprocess.run(
        ["git", "check-ignore", "-q", ".escala/my-company/journey/asks.yaml"],
        cwd=ROOT,
        check=False,
    )

    assert result.returncode == 0


def _corrupt(base: Path, on: date, text: str = "asks: [roto") -> Path:
    path = asks_path(base)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    stamp = datetime(on.year, on.month, on.day, 12).timestamp()
    os.utime(path, (stamp, stamp))
    return path


@pytest.mark.parametrize(
    "text", ["asks: [roto", "hola", "", "asks: [{x: 1}]", "::: x [", "otra: 1"]
)
def test_corrupt_file_counts_as_declined_on_its_last_change(
    tmp_path: Path, text: str
) -> None:
    _corrupt(tmp_path, date(2026, 9, 10), text)

    memory = read_asks(tmp_path)

    assert memory.records == []
    assert memory.corrupt_on == date(2026, 9, 10)
    assert declined_on(tmp_path) == date(2026, 9, 10)


def test_a_dict_without_asks_is_backed_up_like_any_corrupt_file(
    tmp_path: Path,
) -> None:
    path = _corrupt(tmp_path, date(2026, 9, 10), "::: x [")

    _, backup = record_ask(tmp_path, _record(20, "si"))

    assert backup == path.with_name("asks.yaml.bak")
    assert backup is not None and backup.read_text(encoding="utf-8") == "::: x ["


def test_readable_file_is_not_corrupt(tmp_path: Path) -> None:
    record_ask(tmp_path, _record(3, "no"))

    assert read_asks(tmp_path).corrupt_on is None
    assert declined_on(tmp_path) == date(2026, 9, 3)
    assert declined_on(tmp_path / "otra") is None


def test_recording_over_a_corrupt_file_keeps_a_backup(tmp_path: Path) -> None:
    path = _corrupt(tmp_path, date(2026, 9, 10))

    saved, backup = record_ask(tmp_path, _record(20, "si"))

    assert saved == path
    assert backup == path.with_name("asks.yaml.bak")
    assert backup is not None and backup.read_text(encoding="utf-8") == "asks: [roto"
    assert load_asks(tmp_path) == [_record(20, "si")]


def test_a_second_corruption_never_overwrites_the_first_backup(
    tmp_path: Path,
) -> None:
    _corrupt(tmp_path, date(2026, 9, 1), "primero: [")
    record_ask(tmp_path, _record(2, "si"))
    _corrupt(tmp_path, date(2026, 9, 5), "segundo: [")

    _, backup = record_ask(tmp_path, _record(6, "no"))

    assert backup == asks_path(tmp_path).with_name("asks.yaml.bak.2")
    first = asks_path(tmp_path).with_name("asks.yaml.bak")
    assert first.read_text(encoding="utf-8") == "primero: ["
    assert backup is not None and backup.read_text(encoding="utf-8") == "segundo: ["


def test_recording_over_a_good_file_makes_no_backup(tmp_path: Path) -> None:
    record_ask(tmp_path, _record(1, "no"))

    _, backup = record_ask(tmp_path, _record(2, "si"))

    assert backup is None
