"""Contract tests for project-scoped SQLite business memory."""

import sqlite3
from pathlib import Path

from escala_server.project_memory import ProjectMemoryRuntime


def test_ensure_memory_creates_only_the_project_database(tmp_path: Path) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)

    result = runtime.ensure_memory()

    expected = tmp_path / ".scaleup" / "memory" / "escala.db"
    assert result.ready is True
    assert result.db_path == expected
    assert expected.is_file()
    assert Path.home() not in expected.parents


def test_ensure_memory_initializes_the_existing_schema(tmp_path: Path) -> None:
    result = ProjectMemoryRuntime(tmp_path).ensure_memory()

    assert result.ready is True
    assert ProjectMemoryRuntime(tmp_path).health().ready is True


def test_health_reports_a_corrupt_database_without_raising(tmp_path: Path) -> None:
    db_path = tmp_path / ".scaleup" / "memory" / "escala.db"
    db_path.parent.mkdir(parents=True)
    db_path.write_bytes(b"not a sqlite database")

    result = ProjectMemoryRuntime(tmp_path).health()

    assert result.ready is False
    assert result.reason


def test_unwritable_runtime_path_degrades_safely() -> None:
    result = ProjectMemoryRuntime("/proc/scaleup-no-write").ensure_memory()

    assert result.ready is False


def test_backup_and_restore_preserve_companies(tmp_path: Path) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    with sqlite3.connect(runtime.db_path) as connection:
        connection.execute(
            "INSERT INTO companies (id, name) VALUES ('lumen', 'Lumen Casa')"
        )

    backup = runtime.backup()
    runtime.db_path.write_bytes(b"damaged")
    restored = runtime.restore(backup.backup_path)

    assert backup.ready is True
    assert restored.ready is True
    with sqlite3.connect(runtime.db_path) as connection:
        assert (
            connection.execute(
                "SELECT name FROM companies WHERE id = 'lumen'"
            ).fetchone()[0]
            == "Lumen Casa"
        )


def test_invalid_backup_never_replaces_a_healthy_database(tmp_path: Path) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    invalid_backup = runtime.backups_root / "invalid.db"
    invalid_backup.parent.mkdir(parents=True)
    invalid_backup.write_bytes(b"damaged")

    result = runtime.restore(invalid_backup)

    assert result.ready is False
