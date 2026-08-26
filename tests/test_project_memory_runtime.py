"""Contract tests for project-scoped SQLite business memory."""

import sqlite3
from pathlib import Path

import pytest

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


def test_health_rejects_a_database_with_only_a_subset_of_the_e18_schema(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / ".scaleup" / "memory" / "escala.db"
    db_path.parent.mkdir(parents=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE _meta (key TEXT PRIMARY KEY, value TEXT)")
        connection.execute("CREATE TABLE companies (id TEXT PRIMARY KEY, name TEXT)")
        connection.execute("CREATE TABLE memory_facts (id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE entities (id INTEGER PRIMARY KEY)")
        connection.execute(
            "INSERT INTO _meta (key, value) VALUES ('schema_version', '1')"
        )

    result = ProjectMemoryRuntime(tmp_path).health()

    assert result.ready is False
    assert result.reason == "local database schema is incomplete"


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


@pytest.mark.parametrize("linked_part", [".scaleup", "memory"])
def test_ensure_memory_rejects_memory_directory_symlinked_outside_project(
    tmp_path: Path, linked_part: str
) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    if linked_part == ".scaleup":
        (tmp_path / ".scaleup").symlink_to(outside, target_is_directory=True)
    else:
        scaleup = tmp_path / ".scaleup"
        scaleup.mkdir()
        (scaleup / "memory").symlink_to(outside, target_is_directory=True)

    result = ProjectMemoryRuntime(tmp_path).ensure_memory()

    assert result.ready is False
    assert not (outside / "escala.db").exists()


def test_backup_rejects_a_backups_directory_symlinked_outside_project(
    tmp_path: Path,
) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    runtime.backups_root.symlink_to(outside, target_is_directory=True)

    result = runtime.backup()

    assert result.ready is False
    assert not (outside / "escala-backup.db").exists()


def test_restore_rejects_a_database_destination_symlinked_outside_project(
    tmp_path: Path,
) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    backup = runtime.backup()
    assert backup.ready is True
    outside = tmp_path.parent / f"{tmp_path.name}-outside.db"
    runtime.db_path.unlink()
    runtime.db_path.symlink_to(outside)

    result = runtime.restore(backup.backup_path)

    assert result.ready is False
    assert not outside.exists()


def test_restore_checkpoints_wal_and_removes_stale_sidecars(tmp_path: Path) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    backup = runtime.backup()
    assert backup.ready is True

    live = sqlite3.connect(runtime.db_path)
    live.execute("PRAGMA journal_mode=WAL")
    live.execute("INSERT INTO companies (id, name) VALUES ('new', 'New data')")
    live.commit()
    assert runtime.db_path.with_name("escala.db-wal").exists()
    live.close()

    restored = runtime.restore(backup.backup_path)

    assert restored.ready is True
    assert not runtime.db_path.with_name("escala.db-wal").exists()
    assert not runtime.db_path.with_name("escala.db-shm").exists()
    with sqlite3.connect(runtime.db_path) as connection:
        assert connection.execute("SELECT name FROM companies").fetchall() == []


def test_restore_fails_without_replacing_database_when_wal_reader_is_active(
    tmp_path: Path,
) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    backup = runtime.backup()
    assert backup.ready is True
    with sqlite3.connect(runtime.db_path) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("INSERT INTO companies (id, name) VALUES ('live', 'Live data')")

    reader = sqlite3.connect(runtime.db_path)
    reader.execute("BEGIN")
    reader.execute("SELECT * FROM companies").fetchall()
    try:
        restored = runtime.restore(backup.backup_path)
    finally:
        reader.close()

    assert restored.ready is False
    with sqlite3.connect(runtime.db_path) as connection:
        assert connection.execute("SELECT name FROM companies").fetchall() == [
            ("Live data",)
        ]
