# pyright: strict
"""S84.3: memory of the owner's board decisions (absorbed from E73)."""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from coaching.dashboard.boards.memory import (
    BoardDecision,
    declined_boards,
    index_path,
    read_decisions,
    record_decision,
)
from coaching.dashboard.boards.patterns import PATTERNS

ROOT = Path(__file__).resolve().parents[4]
DAY = date(2026, 10, 1)


def test_index_lives_under_my_company_tableros(tmp_path: Path) -> None:
    assert index_path(tmp_path) == (
        tmp_path / ".escala" / "my-company" / "tableros" / "index.yaml"
    )


def test_the_index_is_ignored_by_git() -> None:
    relative = ".escala/my-company/tableros/index.yaml"
    result = subprocess.run(
        ["git", "check-ignore", "-q", relative], cwd=ROOT, check=False
    )
    assert result.returncode == 0


def test_missing_file_means_no_decisions(tmp_path: Path) -> None:
    assert read_decisions(tmp_path).records == []
    assert declined_boards(tmp_path) == {}


def test_record_and_read_back(tmp_path: Path) -> None:
    record_decision(
        tmp_path, BoardDecision(decided_on=DAY, board_id="ventas-etapas", outcome="no")
    )
    record_decision(
        tmp_path,
        BoardDecision(decided_on=DAY, board_id="equipo-carga", outcome="construir"),
    )
    records = read_decisions(tmp_path).records
    assert [r.board_id for r in records] == ["ventas-etapas", "equipo-carga"]
    assert declined_boards(tmp_path) == {"ventas-etapas": DAY}


def test_waiting_requires_a_date(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        BoardDecision(decided_on=DAY, board_id="ventas-etapas", outcome="esperar")
    ok = BoardDecision(
        decided_on=DAY,
        board_id="ventas-etapas",
        outcome="esperar",
        review_on=date(2026, 10, 15),
    )
    record_decision(tmp_path, ok)
    assert declined_boards(tmp_path) == {"ventas-etapas": DAY}


def test_only_catalogue_boards_are_stored(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        BoardDecision(decided_on=DAY, board_id="mi tablero secreto", outcome="no")


def test_the_latest_decline_wins(tmp_path: Path) -> None:
    for day in (date(2026, 9, 1), date(2026, 9, 20)):
        record_decision(
            tmp_path,
            BoardDecision(decided_on=day, board_id="ventas-etapas", outcome="no"),
        )
    assert declined_boards(tmp_path) == {"ventas-etapas": date(2026, 9, 20)}


def test_a_corrupt_index_never_turns_into_nagging(tmp_path: Path) -> None:
    path = index_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("::: no es yaml [", encoding="utf-8")
    declined = declined_boards(tmp_path)
    assert set(declined) == set(PATTERNS)


def test_a_corrupt_index_is_kept_aside_before_writing(tmp_path: Path) -> None:
    path = index_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("::: no es yaml [", encoding="utf-8")
    _, backup = record_decision(
        tmp_path, BoardDecision(decided_on=DAY, board_id="ventas-etapas", outcome="no")
    )
    assert backup is not None and backup.name == "index.yaml.bak"
    assert backup.read_text(encoding="utf-8") == "::: no es yaml ["
    assert len(read_decisions(tmp_path).records) == 1
