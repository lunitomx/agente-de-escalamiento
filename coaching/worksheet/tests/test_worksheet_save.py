"""Tests for worksheet save behavior, including backup of completed worksheets."""

from __future__ import annotations

from pathlib import Path

from coaching.core import read_yaml, write_yaml
from coaching.worksheet import run


def _seed_registry(base: Path) -> None:
    registry = base / ".escala" / "knowledge" / "registry"
    registry.mkdir(parents=True)
    write_yaml(
        registry / "worksheets.yaml",
        {
            "worksheets": [
                {
                    "id": "test-ws",
                    "name": "Test Worksheet",
                    "decision": "cash",
                    "difficulty": "easy",
                    "time_estimate": "10m",
                    "node_path": "cash/tools/test.yaml",
                }
            ]
        },
    )
    node = base / ".escala" / "knowledge" / "cash" / "tools"
    node.mkdir(parents=True)
    write_yaml(
        node / "test.yaml",
        {"metadata": {"fields": ["q1", "q2"]}, "summary": "Test worksheet"},
    )


def test_save_creates_backup_when_overwriting_completed(tmp_path: Path) -> None:
    base = tmp_path
    _seed_registry(base)

    state_dir = base / ".escala" / "my-company" / "worksheets"
    state_dir.mkdir(parents=True)
    old_data = {
        "worksheet_id": "test-ws",
        "worksheet_name": "Test Worksheet",
        "decision": "cash",
        "fields": {"old": "data"},
        "completed": "2026-01-01",
        "status": "completed",
    }
    write_yaml(state_dir / "test-ws.yaml", old_data)

    result = run({"action": "save", "worksheet_name": "test-ws", "base_path": str(base)})

    assert result["errors"] == []
    backups = sorted(state_dir.glob("test-ws-*.yaml"))
    assert len(backups) == 1, f"Expected one backup, found: {backups}"

    backup_data = read_yaml(backups[0])
    assert backup_data["status"] == "completed"
    assert backup_data["fields"] == {"old": "data"}

    new_data = read_yaml(state_dir / "test-ws.yaml")
    assert new_data["status"] == "completed"


def test_save_does_not_backup_in_progress_state(tmp_path: Path) -> None:
    base = tmp_path
    _seed_registry(base)

    state_dir = base / ".escala" / "my-company" / "worksheets"
    state_dir.mkdir(parents=True)
    in_progress = {
        "worksheet_id": "test-ws",
        "worksheet_name": "Test Worksheet",
        "decision": "cash",
        "fields": {"q1": "answer"},
        "current_step": 1,
        "status": "in_progress",
    }
    write_yaml(state_dir / "test-ws.yaml", in_progress)

    result = run({"action": "save", "worksheet_name": "test-ws", "base_path": str(base)})

    assert result["errors"] == []
    backups = list(state_dir.glob("test-ws-*.yaml"))
    assert len(backups) == 0, f"Unexpected backups: {backups}"

    new_data = read_yaml(state_dir / "test-ws.yaml")
    assert new_data["status"] == "completed"


def test_save_first_time_creates_no_backup(tmp_path: Path) -> None:
    base = tmp_path
    _seed_registry(base)

    # Simulate an in-progress state so save has fields to preserve.
    state_dir = base / ".escala" / "my-company" / "worksheets"
    state_dir.mkdir(parents=True)
    write_yaml(
        state_dir / "test-ws.yaml",
        {
            "worksheet_id": "test-ws",
            "worksheet_name": "Test Worksheet",
            "decision": "cash",
            "fields": {"q1": "answer"},
            "current_step": 1,
            "status": "in_progress",
        },
    )

    result = run({"action": "save", "worksheet_name": "test-ws", "base_path": str(base)})

    assert result["errors"] == []
    backups = list(state_dir.glob("test-ws-*.yaml"))
    assert len(backups) == 0
