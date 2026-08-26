"""Contract tests for local idempotent business-memory migration."""

import shutil
import sqlite3
from pathlib import Path

from escala_server.project_memory import ProjectMemoryRuntime
from escala_server.project_memory_migration import ProjectMemoryMigrator

FIXTURES = Path(__file__).parent / "fixtures" / "project_memory_migration"


def project(tmp_path: Path, fixture: str) -> Path:
    root = tmp_path / fixture
    shutil.copytree(FIXTURES / fixture, root)
    return root


def count(db: Path, table: str) -> int:
    with sqlite3.connect(db) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_migrates_complete_project_once_and_preserves_sources(tmp_path: Path) -> None:
    root = project(tmp_path, "complete")
    profile = root / ".scaleup/agent/memory/company-profile.yaml"
    original = profile.read_bytes()
    first = ProjectMemoryMigrator(root).migrate()
    second = ProjectMemoryMigrator(root).migrate()
    assert first.ready and first.imported["company-profile"] == 1
    assert first.imported["opsp"] == 1 and first.imported["worksheet"] == 1
    assert second.imported == {}
    assert second.skipped[".scaleup/agent/memory/company-profile.yaml"] == "unchanged"
    assert count(first.db_path, "companies") == 1
    assert count(first.db_path, "migration_sources") == len(first.sources)
    assert profile.read_bytes() == original
    assert all(
        "conversation" not in source and "knowledge" not in source
        for source in first.sources
    )


def test_change_versions_worksheet_once_and_keeps_projects_isolated(
    tmp_path: Path,
) -> None:
    root = project(tmp_path, "complete")
    other = project(tmp_path, "partial")
    first = ProjectMemoryMigrator(root).migrate()
    ProjectMemoryMigrator(other).migrate()
    (root / ".scaleup/my-company/worksheets/focus.yaml").write_text(
        "id: focus\ndecision: people\nroles: Ventas y Operaciones\n"
    )
    changed = ProjectMemoryMigrator(root).migrate()
    assert changed.imported["worksheet"] == 1
    assert ProjectMemoryMigrator(root).migrate().imported == {}
    with sqlite3.connect(first.db_path) as connection:
        assert (
            connection.execute(
                "SELECT MAX(version) FROM worksheets WHERE category='people' AND tool='focus'"
            ).fetchone()[0]
            == 2
        )
    assert first.db_path != other / ".scaleup/memory/escala.db"


def test_corrupt_and_missing_sources_do_not_block_valid_migration(
    tmp_path: Path,
) -> None:
    root = project(tmp_path, "partial")
    result = ProjectMemoryMigrator(root).migrate()
    assert result.ready
    assert ".scaleup/my-company/worksheets/broken.yaml" in result.errors
    assert result.skipped["work/strategy/opsp.md"] == "missing"
    assert result.imported["company-profile"] == 1
    assert ProjectMemoryRuntime(root).health().ready


def test_yaml_whitespace_and_key_order_are_idempotent(tmp_path: Path) -> None:
    root = project(tmp_path, "complete")
    profile = root / ".scaleup/agent/memory/company-profile.yaml"
    ProjectMemoryMigrator(root).migrate()
    profile.write_text(
        "focus: {current_decision: people}\nscores: {strategy: 6, people: 5}\ncompany: {employees: 12, industry: Interiores, name: Lumen Casa}\n"
    )
    result = ProjectMemoryMigrator(root).migrate()
    assert result.imported == {}
    assert result.skipped[".scaleup/agent/memory/company-profile.yaml"] == "unchanged"


def test_legacy_markdown_without_frontmatter_is_imported(tmp_path: Path) -> None:
    root = project(tmp_path, "partial")
    (root / ".scaleup/my-company/annual-goal.md").write_text("Crecer con foco.\n")
    assert ProjectMemoryMigrator(root).migrate().imported["legacy-plan"] == 1


def test_invalid_profile_type_does_not_create_company_or_ledger(tmp_path: Path) -> None:
    root = project(tmp_path, "partial")
    (root / ".scaleup/agent/memory/company-profile.yaml").write_text("- no perfil\n")
    result = ProjectMemoryMigrator(root).migrate()
    assert ".scaleup/agent/memory/company-profile.yaml" in result.errors
    assert count(result.db_path, "companies") == 0
    assert count(result.db_path, "migration_sources") == 0
