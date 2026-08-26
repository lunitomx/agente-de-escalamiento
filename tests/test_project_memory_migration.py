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


def test_reverted_worksheet_snapshot_is_applied_again_and_keeps_history(
    tmp_path: Path,
) -> None:
    root = project(tmp_path, "complete")
    worksheet = root / ".scaleup/my-company/worksheets/focus.yaml"
    original = worksheet.read_text()
    first = ProjectMemoryMigrator(root).migrate()
    worksheet.write_text("id: focus\ndecision: people\nroles: Finanzas\n")
    changed = ProjectMemoryMigrator(root).migrate()
    worksheet.write_text(original)
    reverted = ProjectMemoryMigrator(root).migrate()

    assert first.imported["worksheet"] == 1
    assert changed.imported["worksheet"] == 1
    assert reverted.imported["worksheet"] == 1
    with sqlite3.connect(first.db_path) as connection:
        assert (
            connection.execute(
                "SELECT MAX(version) FROM worksheets WHERE category=? AND tool=?",
                ("people", "focus"),
            ).fetchone()[0]
            == 3
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM migration_sources WHERE relative_path=?",
                (".scaleup/my-company/worksheets/focus.yaml",),
            ).fetchone()[0]
            == 2
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM migration_applications WHERE relative_path=?",
                (".scaleup/my-company/worksheets/focus.yaml",),
            ).fetchone()[0]
            == 3
        )


def test_runtime_upgrades_v2_database_and_reports_healthy(tmp_path: Path) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready
    with sqlite3.connect(runtime.db_path) as connection:
        connection.execute("DROP TABLE migration_applications")
        connection.execute(
            "UPDATE _meta SET value = ? WHERE key = ?", ("2", "schema_version")
        )

    upgraded = runtime.ensure_memory()

    assert upgraded.ready
    assert runtime.health().ready
    with sqlite3.connect(runtime.db_path) as connection:
        assert (
            connection.execute(
                "SELECT value FROM _meta WHERE key = ?", ("schema_version",)
            ).fetchone()[0]
            == "3"
        )
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = ? AND name = ?",
            ("table", "migration_applications"),
        ).fetchone()


def test_migration_hashes_and_does_not_mutate_allowlisted_inputs(
    tmp_path: Path,
) -> None:
    root = project(tmp_path, "complete")
    legacy_root = project(tmp_path, "partial")
    legacy_paths = (
        legacy_root / ".scaleup/my-company/annual-goal.md",
        legacy_root / ".scaleup/my-company/quarterly-focus.md",
    )
    legacy_paths[0].write_text("Crecer con foco.\n")
    legacy_paths[1].write_text("Cerrar prioridades.\n")
    paths = (
        root / ".scaleup/agent/memory/company-profile.yaml",
        root / ".scaleup/my-company/pulse-history.yaml",
        root / ".scaleup/my-company/context/market.yaml",
        root / ".scaleup/my-company/worksheets/focus.yaml",
        root / "work/strategy/opsp.md",
        *legacy_paths,
    )
    originals = {path: path.read_bytes() for path in paths}

    result = ProjectMemoryMigrator(root).migrate()
    legacy_result = ProjectMemoryMigrator(legacy_root).migrate()

    assert all(path.read_bytes() == original for path, original in originals.items())
    for migration, migration_root, expected_paths in (
        (result, root, paths[:5]),
        (legacy_result, legacy_root, legacy_paths),
    ):
        with sqlite3.connect(migration.db_path) as connection:
            recorded = dict(
                connection.execute(
                    "SELECT relative_path, content_sha256 FROM migration_sources"
                )
            )
        for path in expected_paths:
            relative = path.relative_to(migration_root).as_posix()
            assert (
                recorded[relative]
                == ProjectMemoryMigrator(migration_root)._read(path)[1]
            )


def test_invalid_opsp_uses_legacy_fallback_and_valid_opsp_suppresses_it(
    tmp_path: Path,
) -> None:
    invalid_root = project(tmp_path, "partial")
    invalid_opsp = invalid_root / "work/strategy/opsp.md"
    invalid_opsp.parent.mkdir(parents=True)
    invalid_opsp.write_text("---\nschema: not-opsp\n---\n# Invalid\n")
    (invalid_root / ".scaleup/my-company/annual-goal.md").write_text("Crecer.\n")
    (invalid_root / ".scaleup/my-company/quarterly-focus.md").write_text("Ejecutar.\n")

    fallback = ProjectMemoryMigrator(invalid_root).migrate()

    assert fallback.imported["legacy-plan"] == 2
    assert "work/strategy/opsp.md" not in fallback.sources

    valid_root = project(tmp_path, "complete")
    legacy = valid_root / ".scaleup/my-company/annual-goal.md"
    legacy.write_text("No debe importarse.\n")
    preferred = ProjectMemoryMigrator(valid_root).migrate()

    assert preferred.imported["opsp"] == 1
    assert "legacy-plan" not in preferred.imported
    assert legacy.relative_to(valid_root).as_posix() not in preferred.sources
