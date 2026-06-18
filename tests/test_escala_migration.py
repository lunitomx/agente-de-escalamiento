"""Tests for escala_server.migrate — YAML migration.

Tests the migration from sample YAML data to SQLite.
Uses the actual .scaleup/ directory in the project as source data.
"""

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest
import yaml

from escala_server.migrate import migrate_from_yaml, read_yaml_file


def sample_scaleup_root(tmp_path: Path) -> Path:
    """Create deterministic .scaleup fixture data for migration assertions."""
    root = tmp_path / ".scaleup"
    company_dir = root / "my-company"
    sessions_dir = company_dir / "sessions"
    worksheet_dir = root / "knowledge" / "strategy" / "worksheets"

    sessions_dir.mkdir(parents=True)
    worksheet_dir.mkdir(parents=True)

    (company_dir / "profile.md").write_text("# My Company\n", encoding="utf-8")
    (company_dir / "pulse-history.yaml").write_text(
        "pulses:\n  - date: 2026-01-01\n    answers:\n      cash: 3\n",
        encoding="utf-8",
    )
    (sessions_dir / "session.md").write_text(
        "---\ndate: 2026-01-01\n---\nSession notes\n",
        encoding="utf-8",
    )
    (worksheet_dir / "opsp.yaml").write_text(
        "id: opsp\ntype: worksheet\nname: One Page Strategic Plan\n",
        encoding="utf-8",
    )

    return root


# ─── Simple YAML Parser Tests ──────────────────────────────────


class TestSimpleYamlParser:
    """Test the built-in simple YAML parser."""

    def test_key_value_pairs(self):
        text = "name: Test Corp\nindustry: Tech\n"
        result = yaml.safe_load(text)
        assert result == {"name": "Test Corp", "industry": "Tech"}

    def test_integers_and_floats(self):
        text = "count: 42\nprice: 9.99\n"
        result = yaml.safe_load(text)
        assert result == {"count": 42, "price": 9.99}

    def test_booleans(self):
        text = "active: true\ndisabled: false\n"
        result = yaml.safe_load(text)
        assert result == {"active": True, "disabled": False}

    def test_null_values(self):
        text = "empty: null\nnone: ~\n"
        result = yaml.safe_load(text)
        assert result == {"empty": None, "none": None}

    def test_list_with_items(self):
        text = "items:\n- apple\n- banana\n- cherry\n"
        result = yaml.safe_load(text)
        assert result == {"items": ["apple", "banana", "cherry"]}

    def test_comments(self):
        text = "# This is a comment\nname: value\n# another comment\nkey: 42\n"
        result = yaml.safe_load(text)
        assert result == {"name": "value", "key": 42}

    def test_empty_list(self):
        text = "items: []\nname: test\n"
        result = yaml.safe_load(text)
        assert result == {"items": [], "name": "test"}

    def test_quoted_strings(self):
        text = "name: \"Test Corp\"\ndesc: 'A great company'\n"
        result = yaml.safe_load(text)
        assert result == {"name": "Test Corp", "desc": "A great company"}

    def test_nested_mapping(self):
        text = "person:\n  name: John\n  age: 30\n"
        result = yaml.safe_load(text)
        assert result == {"person": {"name": "John", "age": 30}}

    def test_block_scalar(self):
        text = (
            "summary: >\n  This is a long\n  description that\n  spans multiple lines\n"
        )
        result = yaml.safe_load(text)
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
            project_root
            / ".scaleup"
            / "knowledge"
            / "strategy"
            / "concepts"
            / "brand-promise.yaml"
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

    def test_migration_creates_tables(self, tmp_path):
        """Migration initializes the database with required tables."""
        yaml_root = str(sample_scaleup_root(tmp_path))

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
            assert "changes_log" in table_names
            assert "sessions" in table_names
            conn.close()
        finally:
            os.unlink(db_path)

    def test_migration_is_idempotent(self, tmp_path):
        """Running migration twice produces same results."""
        yaml_root = str(sample_scaleup_root(tmp_path))

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

    def test_migration_imports_sessions(self, tmp_path):
        """Migration imports session markdown files."""
        yaml_root = str(sample_scaleup_root(tmp_path))

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

    def test_migration_imports_worksheets(self, tmp_path):
        """Migration imports worksheet/knowledge YAML files."""
        yaml_root = str(sample_scaleup_root(tmp_path))

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

    def test_migration_writes_log(self, tmp_path):
        """Migration writes a log file."""
        yaml_root = str(sample_scaleup_root(tmp_path))

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
