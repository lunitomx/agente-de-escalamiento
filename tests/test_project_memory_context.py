"""Contracts for the read-only project-local session context bridge."""

from __future__ import annotations

import json
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
        application_id, applied_at = connection.execute(
            """SELECT id, applied_at FROM migration_applications
            WHERE relative_path = ? ORDER BY id DESC LIMIT 1""",
            (".scaleup/agent/memory/company-profile.yaml",),
        ).fetchone()
        facts = (
            ("profile.name", "Lumen Casa"),
            ("diagnosis.cash", 4),
            ("profile.focus.current_decision", "people"),
        )
        connection.execute("DELETE FROM migration_fact_applications")
        connection.execute("DELETE FROM memory_facts")
        for key, value in facts:
            raw_value = json.dumps(value)
            connection.execute(
                "INSERT INTO memory_facts (key, value, updated_at) VALUES (?, ?, ?)",
                (key, raw_value, applied_at),
            )
            connection.execute(
                """INSERT INTO migration_fact_applications (
                    fact_key, value_sha256, migration_application_id, applied_at
                ) VALUES (?, ?, ?, ?)""",
                (
                    key,
                    sha256(raw_value.encode()).hexdigest(),
                    application_id,
                    applied_at,
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


def test_facts_require_matching_application_and_provenance_timestamps(
    tmp_path: Path,
) -> None:
    root = migrated_project(tmp_path)
    runtime = ProjectMemoryRuntime(root)
    with sqlite3.connect(runtime.db_path) as connection:
        row = connection.execute(
            """SELECT applications.id, applications.applied_at
            FROM migration_applications AS applications
            WHERE applications.relative_path = ?
            ORDER BY applications.id DESC LIMIT 1""",
            (".scaleup/agent/memory/company-profile.yaml",),
        ).fetchone()
        application_id, applied_at = row
        connection.execute(
            "UPDATE memory_facts SET updated_at = ? WHERE key = ?",
            ("tampered", "profile.name"),
        )
        connection.execute(
            "UPDATE migration_fact_applications SET applied_at = ? WHERE fact_key = ?",
            ("tampered", "diagnosis.cash"),
        )

    result = ProjectMemorySessionContext(root).load()

    assert all(item.key != "profile.name" for item in result.items)
    assert all(item.key != "diagnosis.cash" for item in result.items)
    assert "profile.industry" in {item.key for item in result.items}
    assert all(
        item.observed_at == applied_at for item in result.items if item.kind == "fact"
    )
    assert application_id


def test_sensitive_and_oversized_fact_values_are_not_recovered(tmp_path: Path) -> None:
    root = migrated_project(tmp_path)
    profile = root / ".scaleup/agent/memory/company-profile.yaml"
    profile.write_text(
        "company:\n"
        "  name: Lumen Casa\n"
        "  apiKey: never-show\n"
        "  db_password: never-show\n"
        "  accessToken: never-show\n"
        "  description: " + ("x" * 241) + "\n",
        encoding="utf-8",
    )
    assert ProjectMemoryMigrator(root).migrate().ready

    result = ProjectMemorySessionContext(root).load()

    assert result.ready
    assert all(
        token not in item.key.lower()
        for item in result.items
        for token in ("apikey", "password", "token", "description")
    )


def test_changes_are_independent_from_company_and_profile_ledger(
    tmp_path: Path,
) -> None:
    root = migrated_project(tmp_path)
    runtime = ProjectMemoryRuntime(root)
    with sqlite3.connect(runtime.db_path) as connection:
        connection.execute("DELETE FROM companies")
        connection.execute(
            "DELETE FROM migration_applications WHERE relative_path = ?",
            (".scaleup/agent/memory/company-profile.yaml",),
        )

    result = ProjectMemorySessionContext(root).load()

    assert result.ready
    assert result.items
    assert all(item.kind == "change" for item in result.items)


def test_sensitive_or_oversized_worksheet_metadata_is_not_recovered(
    tmp_path: Path,
) -> None:
    root = migrated_project(tmp_path)
    runtime = ProjectMemoryRuntime(root)
    with sqlite3.connect(runtime.db_path) as connection:
        connection.execute(
            "UPDATE worksheets SET category = ? WHERE category = ?",
            ("apiKey", "context"),
        )
        connection.execute(
            "UPDATE worksheets SET tool = ? WHERE tool = ?",
            ("x" * 97, "focus"),
        )

    result = ProjectMemorySessionContext(root).load()

    assert all("apiKey" not in item.key for item in result.items)
    assert all("x" * 97 not in item.key for item in result.items)


@pytest.mark.parametrize(
    ("sensitive_name", "metadata_field"),
    (
        ("APIKey", "category"),
        ("DBPassword", "tool"),
        ("apikey", "category"),
        ("dbpassword", "tool"),
        ("clientsecret", "category"),
        ("ClientSecret", "tool"),
    ),
)
def test_sensitive_fact_and_worksheet_metadata_are_not_recovered(
    tmp_path: Path, sensitive_name: str, metadata_field: str
) -> None:
    root = migrated_project(tmp_path)
    profile = root / ".scaleup/agent/memory/company-profile.yaml"
    profile.write_text(
        f"company:\n  name: Lumen Casa\n  {sensitive_name}: never-show\n",
        encoding="utf-8",
    )
    assert ProjectMemoryMigrator(root).migrate().ready
    runtime = ProjectMemoryRuntime(root)
    with sqlite3.connect(runtime.db_path) as connection:
        if metadata_field == "category":
            connection.execute(
                "UPDATE worksheets SET category = ? WHERE category = ?",
                (sensitive_name, "context"),
            )
        else:
            connection.execute(
                "UPDATE worksheets SET tool = ? WHERE tool = ?",
                (sensitive_name, "focus"),
            )

    result = ProjectMemorySessionContext(root).load()

    assert result.ready
    assert all(sensitive_name.lower() not in item.key.lower() for item in result.items)


def test_v4_context_remains_readable_before_and_after_explicit_upgrade(
    tmp_path: Path,
) -> None:
    root = migrated_project(tmp_path)
    runtime = ProjectMemoryRuntime(root)
    with sqlite3.connect(runtime.db_path) as connection:
        connection.execute("DROP TABLE session_memory_proposals")
        connection.execute("DROP TABLE confirmed_memory_entries")
        connection.execute("DROP TABLE project_memory_sessions")
        connection.execute(
            "UPDATE _meta SET value = ? WHERE key = ?", ("4", "schema_version")
        )

    before_bytes = runtime.db_path.read_bytes()
    before = ProjectMemorySessionContext(root).load()

    assert before.ready
    assert before.items
    assert runtime.db_path.read_bytes() == before_bytes
    assert runtime.ensure_memory().ready

    after = ProjectMemorySessionContext(root).load()
    assert after.ready
    assert after.items == before.items
