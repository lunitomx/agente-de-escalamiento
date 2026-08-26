"""Contracts for the read-only project-local session context bridge."""

from __future__ import annotations

import shutil
import sqlite3
from hashlib import sha256
from pathlib import Path

import pytest

from escala_server.project_memory import ProjectMemoryRuntime
from escala_server.project_memory_context import ProjectMemorySessionContext
from escala_server.project_memory_migration import ProjectMemoryMigrator

FIXTURES = Path(__file__).parent / "fixtures" / "project_memory_migration"


def migrated_project(tmp_path: Path, fixture: str = "complete") -> Path:
    """Copy a business fixture and migrate it into its own local database."""
    root = tmp_path / fixture
    shutil.copytree(FIXTURES / fixture, root)
    assert ProjectMemoryMigrator(root).migrate().ready
    return root


def database_digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def table_counts(path: Path) -> dict[str, int]:
    tables = (
        "companies",
        "worksheets",
        "memory_facts",
        "migration_sources",
        "migration_applications",
    )
    with sqlite3.connect(path) as connection:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in tables
        }


def test_contract_is_immutable_and_absent_memory_falls_back(tmp_path: Path) -> None:
    result = ProjectMemorySessionContext(tmp_path).load()

    assert result.ready is False
    assert result.items == ()
    assert result.reason
    assert result.user_message is None
    assert not (tmp_path / ".scaleup").exists()
    with pytest.raises(AttributeError):
        result.ready = True  # type: ignore[misc]


def test_healthy_empty_memory_is_ready_and_silent(tmp_path: Path) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready
    before = database_digest(runtime.db_path)

    result = ProjectMemorySessionContext(tmp_path).load()

    assert result.ready is True
    assert result.items == ()
    assert result.user_message is None
    assert database_digest(runtime.db_path) == before


def test_recovers_only_ledger_verified_allowlisted_facts(tmp_path: Path) -> None:
    root = migrated_project(tmp_path)
    runtime = ProjectMemoryRuntime(root)
    with sqlite3.connect(runtime.db_path) as connection:
        connection.execute(
            "INSERT INTO memory_facts (key, value) VALUES (?, ?)",
            ("fact.free", '"not confirmed"'),
        )
        connection.execute(
            "INSERT INTO memory_facts (key, value) VALUES (?, ?)",
            ("profile.secret", '"password should never appear"'),
        )
        connection.execute(
            "INSERT INTO memory_facts (key, value) VALUES (?, ?)",
            ("profile.broken", "{not-json"),
        )

    result = ProjectMemorySessionContext(root).load()

    assert result.ready is True
    assert result.items
    assert all(item.kind == "fact" for item in result.items)
    assert all(item.confirmed for item in result.items)
    assert all(
        item.source == ".scaleup/agent/memory/company-profile.yaml"
        for item in result.items
    )
    assert all(
        item.key not in {"fact.free", "profile.secret", "profile.broken"}
        for item in result.items
    )
    assert all("password" not in item.value for item in result.items)


def test_ranks_facts_before_verified_changes_and_limits_globally(
    tmp_path: Path,
) -> None:
    root = migrated_project(tmp_path)
    runtime = ProjectMemoryRuntime(root)
    with sqlite3.connect(runtime.db_path) as connection:
        connection.execute("DELETE FROM memory_facts")
        connection.executemany(
            "INSERT INTO memory_facts (key, value, updated_at) VALUES (?, ?, ?)",
            (
                ("profile.name", '"Lumen Casa"', "2026-08-01 00:00:00"),
                ("diagnosis.cash", "4", "2026-08-02 00:00:00"),
                (
                    "profile.focus.current_decision",
                    '"people"',
                    "2026-08-03 00:00:00",
                ),
            ),
        )

    result = ProjectMemorySessionContext(root).load()

    assert [(item.kind, item.key) for item in result.items] == [
        ("fact", "profile.focus.current_decision"),
        ("fact", "diagnosis.cash"),
        ("fact", "profile.name"),
        ("change", "context:context/market"),
        ("change", "opsp:strategy/opsp"),
    ]
    assert len(result.items) <= 5
    assert all("Ventas" not in item.value for item in result.items)
    assert all("competitors" not in item.value for item in result.items)


def test_load_is_project_isolated_and_does_not_mutate_data_or_sources(
    tmp_path: Path,
) -> None:
    root = migrated_project(tmp_path, "complete")
    other = migrated_project(tmp_path, "partial")
    runtime = ProjectMemoryRuntime(root)
    conversation = root / ".scaleup" / "agent" / "memory" / "conversation.yaml"
    conversation.write_text("turns: [confidential conversation]\n", encoding="utf-8")
    before_db = database_digest(runtime.db_path)
    before_counts = table_counts(runtime.db_path)
    before_conversation = conversation.read_bytes()

    result = ProjectMemorySessionContext(root).load()
    other_result = ProjectMemorySessionContext(other).load()

    assert result.ready and other_result.ready
    assert {item.value for item in result.items} != {
        item.value for item in other_result.items
    }
    assert database_digest(runtime.db_path) == before_db
    assert table_counts(runtime.db_path) == before_counts
    assert conversation.read_bytes() == before_conversation
    assert all("confidential conversation" not in item.value for item in result.items)


def test_corrupt_database_and_bad_worksheet_row_degrade_safely(tmp_path: Path) -> None:
    root = migrated_project(tmp_path)
    runtime = ProjectMemoryRuntime(root)
    with sqlite3.connect(runtime.db_path) as connection:
        connection.execute(
            "INSERT INTO worksheets (category, tool, data, version) VALUES (?, ?, ?, ?)",
            ("people", "malformed", "{not-json", 1),
        )

    usable = ProjectMemorySessionContext(root).load()

    assert usable.ready is True
    assert all(item.key != "worksheet:people/malformed" for item in usable.items)
    runtime.db_path.write_bytes(b"not sqlite")

    fallback = ProjectMemorySessionContext(root).load()

    assert fallback.ready is False
    assert fallback.items == ()
    assert fallback.user_message is None
