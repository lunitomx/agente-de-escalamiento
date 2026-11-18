"""S88.5: reopen a completed sheet with a backup (epic design section 3)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from coaching.core import read_yaml, write_yaml
from coaching.worksheet import get_completed_ids, run

SWT_ID = "worksheet-swt"


def _folder(base: Path) -> Path:
    return base / ".escala" / "my-company" / "worksheets"


def _seed_completed_swt(base: Path) -> dict[str, Any]:
    old = {
        "worksheet_id": SWT_ID,
        "worksheet_name": "SWT Analysis Worksheet",
        "decision": "strategy",
        "fields": {"fortalezas": "Masa antes de las 7 (2025)"},
        "completed": "2025-11-20",
        "status": "completed",
    }
    _folder(base).mkdir(parents=True)
    write_yaml(_folder(base) / f"{SWT_ID}.yaml", old)
    return old


def _run(base: Path, action: str, **extra: Any) -> dict[str, Any]:
    return run(
        {"action": action, "worksheet_name": SWT_ID, "base_path": str(base), **extra}
    )


# --- Reopen a completed sheet (epic design section 3) ---


def test_start_on_a_completed_sheet_backs_it_up_and_starts_at_step_one(
    tmp_path: Path,
) -> None:
    old = _seed_completed_swt(tmp_path)

    result = _run(tmp_path, "start")

    assert result["errors"] == []
    backups = sorted(_folder(tmp_path).glob(f"{SWT_ID}-*.yaml"))
    assert len(backups) == 1
    assert re.fullmatch(rf"{SWT_ID}-\d{{8}}-\d{{6}}\.yaml", backups[0].name)
    assert read_yaml(backups[0]) == old
    assert result["artifacts"]["current_step"] == 0
    assert result["artifacts"]["backup_path"] == str(backups[0])
    output = result["output"]
    assert "Ya llenaste esta hoja el 2025-11-20." in output
    relative = backups[0].relative_to(tmp_path).as_posix()
    assert f"Guardé esa versión en {relative}." in output
    assert "Empiezas una versión nueva." in output
    assert "### Paso 1: Información General" in output
    state = read_yaml(_folder(tmp_path) / f"{SWT_ID}.yaml")
    assert state["status"] == "in_progress"
    assert state["fields"] == {}


def test_resume_on_a_completed_sheet_asks_for_start(tmp_path: Path) -> None:
    old = _seed_completed_swt(tmp_path)

    result = _run(tmp_path, "resume")

    assert result["errors"] == []
    assert result["output"] == (
        "Esta hoja ya está completada. "
        f"Escribe `start {SWT_ID}` para hacer una versión nueva."
    )
    assert read_yaml(_folder(tmp_path) / f"{SWT_ID}.yaml") == old
    assert list(_folder(tmp_path).glob(f"{SWT_ID}-*.yaml")) == []


def test_completed_ids_read_only_the_sheet_own_file(tmp_path: Path) -> None:
    _folder(tmp_path).mkdir(parents=True)
    write_yaml(
        _folder(tmp_path) / f"{SWT_ID}-20251120-090000.yaml",
        {"worksheet_id": SWT_ID, "status": "completed", "fields": {}},
    )

    assert get_completed_ids(tmp_path) == []


def _list_status(base: Path) -> str:
    output = run({"action": "list", "base_path": str(base)})["output"]
    line = next(row for row in output.splitlines() if f"(`{SWT_ID}`)" in row)
    return line.rstrip(" |").rsplit("|", 1)[-1].strip()


def test_list_shows_open_after_reopen_and_done_after_save(tmp_path: Path) -> None:
    _seed_completed_swt(tmp_path)
    assert _list_status(tmp_path) == "✅"

    _run(tmp_path, "start")
    assert _list_status(tmp_path) == "⬜"

    _run(tmp_path, "step", fields={"fortalezas": "Reparto propio (2026)"})
    saved = _run(tmp_path, "save")

    assert saved["errors"] == []
    assert _list_status(tmp_path) == "✅"
    files = sorted(p.name for p in _folder(tmp_path).glob(f"{SWT_ID}*.yaml"))
    assert len(files) == 2
    new = read_yaml(_folder(tmp_path) / f"{SWT_ID}.yaml")
    assert new["fields"] == {"fortalezas": "Reparto propio (2026)"}
