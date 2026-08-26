"""Contract tests for project-scoped SQLite business memory."""

import sqlite3
from pathlib import Path

import pytest

from escala_server.project_memory import ProjectMemoryRuntime
from escala_server.schema import DDL_STATEMENTS, INDEX_STATEMENTS


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


@pytest.mark.parametrize("project_name", ["question?mark", "hash#mark"])
def test_sqlite_uri_operations_keep_special_project_paths_exact(
    tmp_path: Path, project_name: str
) -> None:
    runtime = ProjectMemoryRuntime(tmp_path / project_name)

    created = runtime.ensure_memory()
    backup = runtime.backup()
    restored = runtime.restore(backup.backup_path)

    assert created.ready is True
    assert runtime.health().ready is True
    assert backup.ready is True
    assert restored.ready is True
    assert (
        runtime.db_path == tmp_path / project_name / ".scaleup" / "memory" / "escala.db"
    )
    assert runtime.db_path.is_file()


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


@pytest.mark.parametrize(
    "replacement",
    [
        ("name TEXT NOT NULL", "name TEXT"),
        ("industry TEXT DEFAULT ''", "industry TEXT DEFAULT 'wrong'"),
        ("id TEXT PRIMARY KEY", "id TEXT"),
    ],
)
def test_health_rejects_matching_columns_with_wrong_constraints(
    tmp_path: Path, replacement: tuple[str, str]
) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    with sqlite3.connect(runtime.db_path) as connection:
        connection.execute("DROP TABLE companies")
        original, altered = replacement
        definition = """id TEXT PRIMARY KEY, name TEXT NOT NULL,
            industry TEXT DEFAULT '', metadata TEXT DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))""".replace(
            original, altered
        )
        connection.execute(f"CREATE TABLE companies ({definition})")

    result = runtime.health()

    assert result.ready is False
    assert result.reason == "local database schema structure is invalid"


def test_health_rejects_missing_unique_constraint_with_matching_columns(
    tmp_path: Path,
) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    with sqlite3.connect(runtime.db_path) as connection:
        connection.execute("DROP TABLE memory_facts")
        connection.execute(
            """CREATE TABLE memory_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )"""
        )

    result = runtime.health()

    assert result.ready is False
    assert result.reason == "local database schema structure is invalid"


def test_health_rejects_missing_required_index(tmp_path: Path) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    with sqlite3.connect(runtime.db_path) as connection:
        connection.execute("DROP INDEX idx_sessions_company")

    result = runtime.health()

    assert result.ready is False
    assert result.reason == "local database schema structure is invalid"


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


def test_restore_recreates_a_missing_database_from_a_valid_backup(
    tmp_path: Path,
) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    with sqlite3.connect(runtime.db_path) as connection:
        connection.execute(
            "INSERT INTO companies (id, name) VALUES ('lumen', 'Lumen Casa')"
        )

    backup = runtime.backup()
    assert backup.ready is True
    runtime.db_path.unlink()
    for sidecar in runtime._wal_sidecars():
        sidecar.unlink(missing_ok=True)

    restored = runtime.restore(backup.backup_path)

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


def test_backup_returns_failure_when_its_temporary_path_is_a_directory(
    tmp_path: Path,
) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    temporary = runtime._backup_path(None).with_suffix(".tmp")
    temporary.mkdir(parents=True)

    result = runtime.backup()

    assert result.ready is False
    assert temporary.is_dir()


def test_restore_returns_failure_when_its_temporary_path_is_a_directory(
    tmp_path: Path,
) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    backup = runtime.backup()
    assert backup.ready is True
    temporary = runtime.db_path.with_suffix(".restore.tmp")
    temporary.mkdir()

    result = runtime.restore(backup.backup_path)

    assert result.ready is False
    assert temporary.is_dir()


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


def test_restore_checkpoints_wal_data_when_database_has_no_users(
    tmp_path: Path,
) -> None:
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


def test_restore_blocks_a_writer_after_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    backup = runtime.backup()
    assert backup.ready is True

    for sidecar in runtime._wal_sidecars():
        sidecar.unlink(missing_ok=True)

    original_assert = runtime._assert_database_was_not_modified

    def assert_then_write(expected_fingerprint: bytes) -> None:
        writer = sqlite3.connect(runtime.db_path, timeout=0)
        try:
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                writer.execute(
                    "INSERT INTO companies (id, name) VALUES ('late', 'Late writer')"
                )
        finally:
            writer.close()
        original_assert(expected_fingerprint)

    monkeypatch.setattr(runtime, "_assert_database_was_not_modified", assert_then_write)
    restored = runtime.restore(backup.backup_path)

    assert restored.ready is True


@pytest.mark.parametrize(
    "removed_constraint",
    (
        "CHECK(origin = 'explicit_user_statement')",
        "FOREIGN KEY(replaces_entry_id) REFERENCES confirmed_memory_entries(id)",
    ),
)
def test_health_rejects_recreated_consent_table_missing_check_or_foreign_key(
    tmp_path: Path, removed_constraint: str
) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready is True
    proposal_ddl = next(
        statement
        for statement in DDL_STATEMENTS
        if "CREATE TABLE IF NOT EXISTS session_memory_proposals" in statement
    ).replace("IF NOT EXISTS ", "")
    if removed_constraint.startswith("FOREIGN KEY"):
        proposal_ddl = proposal_ddl.replace(f",\n        {removed_constraint}", "")
    else:
        proposal_ddl = proposal_ddl.replace(removed_constraint, "")
    proposal_index = next(
        statement
        for statement in INDEX_STATEMENTS
        if "idx_session_memory_proposals_session_state" in statement
    ).replace("IF NOT EXISTS ", "")
    with sqlite3.connect(runtime.db_path) as connection:
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("DROP TABLE session_memory_proposals")
        connection.execute(proposal_ddl)
        connection.execute(proposal_index)

    result = runtime.health()

    assert result.ready is False
    assert result.reason == "local database schema structure is invalid"
