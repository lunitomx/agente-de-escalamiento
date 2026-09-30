"""Memory of the journey question: ``.escala/my-company/journey/asks.yaml``."""

from __future__ import annotations

import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from coaching.journey.asks import (
    AskRecord,
    asks_path,
    last_declined_on,
    load_asks,
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
    first = record_ask(tmp_path, _record(1, "despues"))
    record_ask(tmp_path, _record(20, "si", "T2"))

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


def test_corrupt_file_is_treated_as_empty(tmp_path: Path) -> None:
    path = asks_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("asks: [roto", encoding="utf-8")

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
