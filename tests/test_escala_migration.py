"""Tests for escala_server.migrate — YAML migration.

Tests the migration from sample YAML data to SQLite.
Uses the actual .scaleup/ directory in the project as source data.
"""

import json
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from escala_server.daos import init_db
from escala_server.migrate import migrate_from_yaml, read_yaml_file, _parse_simple_yaml


# ─── Simple YAML Parser Tests ──────────────────────────────────


class TestSimpleYamlParser:
    """Test the built-in simple YAML parser."""

    def test_key_value_pairs(self):
        text = "name: Test Corp\nindustry: Tech\n"
        result = _parse_simple_yaml(text)
        assert result == {"name": "Test Corp", "industry": "Tech"}

    def test_integers_and_floats(self):
        text = "count: 42\nprice: 9.99\n"
        result = _parse_simple_yaml(text)
        assert result == {"count": 42, "price": 9.99}

    def test_booleans(self):
        text = "active: true\ndisabled: false\n"
        result = _parse_simple_yaml(text)
        assert result == {"active": True, "disabled": False}

    def test_null_values(self):
        text = "empty: null\nnone: ~\n"
        result = _parse_simple_yaml(text)
        assert result == {"empty": None, "none": None}

    def test_list_with_items(self):
        text = "items:\n- apple\n- banana\n- cherry\n"
        result = _parse_simple_yaml(text)
        assert result == {"items": ["apple", "banana", "cherry"]}

    def test_indentless_list_with_nested_mappings_and_list(self):
        text = (
            "pulses:\n"
            "- date: '2026-05-06'\n"
            "  answers:\n"
            "    execution: -1\n"
            "  course_corrections:\n"
            "  - Run execution review\n"
        )
        result = _parse_simple_yaml(text)
        assert result == {
            "pulses": [
                {
                    "date": "2026-05-06",
                    "answers": {"execution": -1},
                    "course_corrections": ["Run execution review"],
                }
            ]
        }

    def test_comments(self):
        text = "# This is a comment\nname: value\n# another comment\nkey: 42\n"
        result = _parse_simple_yaml(text)
        assert result == {"name": "value", "key": 42}

    def test_empty_list(self):
        text = "items: []\nname: test\n"
        result = _parse_simple_yaml(text)
        assert result == {"items": [], "name": "test"}

    def test_quoted_strings(self):
        text = 'name: "Test Corp"\ndesc: \'A great company\'\n'
        result = _parse_simple_yaml(text)
        assert result == {"name": "Test Corp", "desc": "A great company"}

    def test_nested_mapping(self):
        text = "person:\n  name: John\n  age: 30\n"
        result = _parse_simple_yaml(text)
        assert result == {"person": {"name": "John", "age": 30}}

    def test_block_scalar(self):
        text = "summary: >\n  This is a long\n  description that\n  spans multiple lines\n"
        result = _parse_simple_yaml(text)
        assert "summary" in result
        assert "description" in result["summary"]


# ─── read_yaml_file Tests ──────────────────────────────────────


class TestReadYamlFile:
    """Test reading YAML files from the actual .scaleup/ directory."""

    def test_read_pulse_history_yaml(self):
        """Read pulse-history.yaml and verify structure."""
        project_root = Path(__file__).resolve().parent.parent
        yaml_path = project_root / ".scaleup" / "my-company" / "pulse-history.yaml"
        if not yaml_path.exists():
            pytest.skip("pulse-history.yaml not found")

        data = read_yaml_file(yaml_path)
        assert data is not None
        assert "pulses" in data
        assert isinstance(data["pulses"], list)
        assert len(data["pulses"]) > 0
        # Each pulse should have date and answers
        for pulse in data["pulses"]:
            assert "date" in pulse
            assert "answers" in pulse

    def test_read_knowledge_yaml(self):
        """Read a knowledge base YAML file."""
        project_root = Path(__file__).resolve().parent.parent
        yaml_path = (
            project_root / ".scaleup" / "knowledge" / "strategy" / "concepts" / "brand-promise.yaml"
        )
        if not yaml_path.exists():
            pytest.skip("brand-promise.yaml not found")

        data = read_yaml_file(yaml_path)
        assert data is not None
        assert "id" in data
        assert "type" in data
        assert "name" in data


# ─── Migration Tests ───────────────────────────────────────────


class TestMigration:
    """Test migration from YAML to SQLite."""

    def test_migration_creates_tables(self):
        """Migration initializes the database with required tables."""
        project_root = Path(__file__).resolve().parent.parent
        yaml_root = str(project_root / ".scaleup")

        if not Path(yaml_root).is_dir():
            pytest.skip(".scaleup/ directory not found")

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            result = migrate_from_yaml(db_path, yaml_root)
            assert result["status"] == "ok"

            # Verify tables exist
            conn = sqlite3.connect(db_path)
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {t[0] for t in tables}
            assert "companies" in table_names
            assert "worksheets" in table_names
            assert "changes" in table_names
            assert "sessions" in table_names
            conn.close()
        finally:
            os.unlink(db_path)

    def test_migration_is_idempotent(self):
        """Running migration twice produces same results."""
        project_root = Path(__file__).resolve().parent.parent
        yaml_root = str(project_root / ".scaleup")

        if not Path(yaml_root).is_dir():
            pytest.skip(".scaleup/ directory not found")

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            result1 = migrate_from_yaml(db_path, yaml_root)
            assert result1["status"] == "ok"

            result2 = migrate_from_yaml(db_path, yaml_root)
            assert result2["status"] == "ok"

            # Second run should have zero new imports (all skipped)
            assert result2["counts"]["companies"] == 0
            # Session count may include 1 new if there's a session.md, but no more than first run
            assert result2["counts"]["sessions"] <= result1["counts"]["sessions"]
            assert result2["counts"]["skipped"] >= result1["counts"]["skipped"]
        finally:
            os.unlink(db_path)

    def test_migration_imports_sessions(self):
        """Migration imports session markdown files."""
        project_root = Path(__file__).resolve().parent.parent
        yaml_root = str(project_root / ".scaleup")

        if not Path(yaml_root).is_dir():
            pytest.skip(".scaleup/ directory not found")

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            migrate_from_yaml(db_path, yaml_root)
            conn = sqlite3.connect(db_path)
            sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            conn.close()
            assert sessions > 0
        finally:
            os.unlink(db_path)

    def test_migration_imports_worksheets(self):
        """Migration imports worksheet/knowledge YAML files."""
        project_root = Path(__file__).resolve().parent.parent
        yaml_root = str(project_root / ".scaleup")

        if not Path(yaml_root).is_dir():
            pytest.skip(".scaleup/ directory not found")

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            migrate_from_yaml(db_path, yaml_root)
            conn = sqlite3.connect(db_path)
            worksheets = conn.execute("SELECT COUNT(*) FROM worksheets").fetchone()[0]
            conn.close()
            assert worksheets > 0
        finally:
            os.unlink(db_path)

    def test_migration_writes_log(self):
        """Migration writes a log file."""
        project_root = Path(__file__).resolve().parent.parent
        yaml_root = str(project_root / ".scaleup")

        if not Path(yaml_root).is_dir():
            pytest.skip(".scaleup/ directory not found")

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            result = migrate_from_yaml(db_path, yaml_root)
            log_path = Path(result["log_path"])
            assert log_path.exists()
            log_content = log_path.read_text()
            assert "Migration started" in log_content
            assert "Migration complete" in log_content
        finally:
            os.unlink(db_path)

    def test_migration_with_nonexistent_source(self):
        """Migration handles nonexistent source directory gracefully."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            result = migrate_from_yaml(db_path, "/nonexistent/path")
            assert result["status"] == "ok"
            assert result["counts"]["errors"] == 0
        finally:
            os.unlink(db_path)
