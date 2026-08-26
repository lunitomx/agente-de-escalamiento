"""Contract tests for project-scoped SQLite business memory."""

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
