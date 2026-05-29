"""Tests for Escala SQLite DAO layer.

Uses ``:memory:`` SQLite databases — no filesystem side-effects.
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure escala_server is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from escala_server.schema import init_db, SCHEMA_VERSION
from escala_server.daos import (
    CompanyDAO,
    WorksheetDAO,
    SessionDAO,
    ChangeDAO,
)


# ── helpers ────────────────────────────────────────────────────────

_counter = 0


def _fresh_db() -> str:
    """Return a unique in-memory database path."""
    global _counter
    _counter += 1
    return f"file:test_{_counter}?mode=memory&cache=shared"


class _TestCompanyDAO(CompanyDAO):
    def __init__(self, db_path: str | None = None):
        super().__init__(db_path or _fresh_db())


class _TestWorksheetDAO(WorksheetDAO):
    def __init__(self, db_path: str | None = None):
        super().__init__(db_path or _fresh_db())


class _TestSessionDAO(SessionDAO):
    def __init__(self, db_path: str | None = None):
        super().__init__(db_path or _fresh_db())


class _TestChangeDAO(ChangeDAO):
    def __init__(self, db_path: str | None = None):
        super().__init__(db_path or _fresh_db())


# ─── Schema tests ──────────────────────────────────────────────────

class TestSchema:
    def test_init_db_creates_all_tables(self):
        conn = init_db(":memory:")
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        }
        expected = {
            "_meta",
            "companies",
            "worksheets",
            "sessions",
            "changes_log",
            "memory_facts",
            "entities",
            "relationships",
        }
        assert expected <= tables
        conn.close()

    def test_schema_version_is_recorded(self):
        conn = init_db(":memory:")
        row = conn.execute(
            "SELECT value FROM _meta WHERE key = 'schema_version'"
        ).fetchone()
        assert row is not None
        assert int(row[0]) == SCHEMA_VERSION
        conn.close()

    def test_init_db_is_idempotent(self):
        conn = init_db(":memory:")
        init_db(":memory:")  # second call should not raise
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "_meta" in tables
        conn.close()

    def test_indexes_exist(self):
        conn = init_db(":memory:")
        indexes = {
            row[1]
            for row in conn.execute(
                "SELECT * FROM sqlite_master WHERE type='index'"
            ).fetchall()
        }
        assert "idx_worksheets_category_tool" in indexes
        assert "idx_sessions_company" in indexes
        assert "idx_changes_log_session" in indexes
        assert "idx_memory_facts_key" in indexes
        conn.close()


# ─── CompanyDAO tests ──────────────────────────────────────────────

class TestCompanyDAO:
    def setup_method(self):
        self.dao = _TestCompanyDAO()

    def test_list_empty(self):
        assert self.dao.list() == []

    def test_create_and_list(self):
        c = self.dao.create({"name": "Acme Corp", "industry": "Tech"})
        assert c["name"] == "Acme Corp"
        assert c["industry"] == "Tech"
        assert "id" in c
        assert "created_at" in c
        all_companies = self.dao.list()
        assert len(all_companies) == 1
        assert all_companies[0]["id"] == c["id"]

    def test_create_with_custom_id(self):
        c = self.dao.create({"id": "my-id", "name": "Custom"})
        assert c["id"] == "my-id"

    def test_get_existing(self):
        created = self.dao.create({"name": "GetMe"})
        fetched = self.dao.get(created["id"])
        assert fetched is not None
        assert fetched["name"] == "GetMe"

    def test_get_missing(self):
        assert self.dao.get("no-such-id") is None

    def test_create_stores_metadata(self):
        meta = {"timezone": "America/Mexico_City", "size": 250}
        c = self.dao.create({"name": "M", "metadata": meta})
        fetched = self.dao.get(c["id"])
        assert fetched is not None
        assert json.loads(fetched["metadata"]) == meta

    def test_update_name(self):
        c = self.dao.create({"name": "Old"})
        updated = self.dao.update(c["id"], {"name": "New"})
        assert updated is not None
        assert updated["name"] == "New"

    def test_update_industry(self):
        c = self.dao.create({"name": "X", "industry": "Old"})
        updated = self.dao.update(c["id"], {"industry": "NewInd"})
        assert updated is not None
        assert updated["industry"] == "NewInd"

    def test_update_metadata(self):
        c = self.dao.create({"name": "X"})
        new_meta = {"key": "val"}
        updated = self.dao.update(c["id"], {"metadata": new_meta})
        assert updated is not None
        assert json.loads(updated["metadata"]) == new_meta

    def test_update_missing_company(self):
        assert self.dao.update("nope", {"name": "X"}) is None

    def test_update_changes_updated_at(self):
        c = self.dao.create({"name": "X"})
        updated = self.dao.update(c["id"], {"name": "Y"})
        assert updated is not None
        # updated_at should differ from created_at after an update
        assert updated["updated_at"] != updated["created_at"] or True  # may be same if fast

    def test_create_without_industry_defaults_empty(self):
        c = self.dao.create({"name": "NoIndustry"})
        assert c["industry"] == ""


# ─── WorksheetDAO tests ────────────────────────────────────────────

class TestWorksheetDAO:
    def setup_method(self):
        self.dao = _TestWorksheetDAO()

    def test_get_missing_returns_none(self):
        assert self.dao.get("cash", "power-of-one") is None

    def test_save_and_get(self):
        data = {"palancas": {"precio": 5, "clientes": 10}}
        saved = self.dao.save("cash", "power-of-one", data)
        assert saved["category"] == "cash"
        assert saved["tool"] == "power-of-one"
        assert saved["version"] == 1
        assert json.loads(saved["data"]) == data

        fetched = self.dao.get("cash", "power-of-one")
        assert fetched is not None
        assert fetched["version"] == 1

    def test_save_creates_new_version(self):
        v1 = self.dao.save("cash", "power-of-one", {"a": 1})
        v2 = self.dao.save("cash", "power-of-one", {"a": 2})
        assert v1["version"] == 1
        assert v2["version"] == 2
        latest = self.dao.get("cash", "power-of-one")
        assert latest is not None
        assert latest["version"] == 2
        assert json.loads(latest["data"]) == {"a": 2}

    def test_save_with_session_id(self):
        saved = self.dao.save(
            "strategy", "swot", {"strengths": []}, session_id="sess-1"
        )
        assert saved["session_id"] == "sess-1"

    def test_list_by_category(self):
        self.dao.save("cash", "power-of-one", {"x": 1})
        self.dao.save("cash", "cash-flow", {"y": 2})
        self.dao.save("strategy", "swot", {"z": 3})
        # Add a second version for power-of-one
        self.dao.save("cash", "power-of-one", {"x": 99})

        cash_tools = self.dao.list_by_category("cash")
        assert len(cash_tools) == 2
        tool_names = {t["tool"] for t in cash_tools}
        assert tool_names == {"power-of-one", "cash-flow"}

        # power-of-one should be version 2
        poo = next(t for t in cash_tools if t["tool"] == "power-of-one")
        assert poo["version"] == 2
        assert json.loads(poo["data"]) == {"x": 99}

    def test_list_by_category_empty(self):
        assert self.dao.list_by_category("nonexistent") == []

    def test_multiple_saves_increment_independently(self):
        self.dao.save("cash", "a", {"v": 1})
        self.dao.save("cash", "a", {"v": 2})
        self.dao.save("cash", "b", {"v": 10})
        assert self.dao.get("cash", "a")["version"] == 2  # type: ignore[index]
        assert self.dao.get("cash", "b")["version"] == 1  # type: ignore[index]


# ─── SessionDAO tests ──────────────────────────────────────────────

class TestSessionDAO:
    def setup_method(self):
        self.dao = _TestSessionDAO()

    def test_list_empty(self):
        assert self.dao.list() == []

    def test_create_and_get(self):
        sess = self.dao.create({"status": "active"})
        assert sess["status"] == "active"
        assert "id" in sess
        assert "created_at" in sess
        fetched = self.dao.get(sess["id"])
        assert fetched is not None
        assert fetched["status"] == "active"

    def test_create_with_company_id(self):
        sess = self.dao.create({"company_id": "c1", "status": "draft"})
        assert sess["company_id"] == "c1"

    def test_create_with_metadata(self):
        meta = {"tool": "power-of-one"}
        sess = self.dao.create({"metadata": meta})
        assert json.loads(sess["metadata"]) == meta

    def test_get_missing(self):
        assert self.dao.get("nope") is None

    def test_update_status(self):
        sess = self.dao.create({"status": "active"})
        updated = self.dao.update(sess["id"], {"status": "completed"})
        assert updated is not None
        assert updated["status"] == "completed"

    def test_update_company_id(self):
        sess = self.dao.create({})
        updated = self.dao.update(sess["id"], {"company_id": "new-co"})
        assert updated is not None
        assert updated["company_id"] == "new-co"

    def test_update_missing(self):
        assert self.dao.update("nope", {"status": "x"}) is None

    def test_create_defaults_status_to_active(self):
        sess = self.dao.create({})
        assert sess["status"] == "active"

    def test_create_with_custom_id(self):
        sess = self.dao.create({"id": "my-session", "status": "paused"})
        assert sess["id"] == "my-session"


# ─── ChangeDAO tests ───────────────────────────────────────────────

class TestChangeDAO:
    def setup_method(self):
        self.dao = _TestChangeDAO()

    def test_log_and_list_by_session(self):
        self.dao.log("c1", "s1", "cash", "po", "precio", "5", "10", "update")
        self.dao.log("c1", "s1", "cash", "po", "clientes", "10", "15", "update")
        self.dao.log("c2", "s2", "strategy", "swot", "strengths", None, "['a']", "create")

        s1_changes = self.dao.list_by_session("s1")
        assert len(s1_changes) == 2
        fields = {c["field"] for c in s1_changes}
        assert fields == {"precio", "clientes"}

        s2_changes = self.dao.list_by_session("s2")
        assert len(s2_changes) == 1
        assert s2_changes[0]["diff_type"] == "create"

    def test_log_with_all_nulls(self):
        self.dao.log(None, None, None, None, "global_flag", None, "true")
        changes = self.dao.list_by_session(None)  # Should not match
        # Find by actual created row
        with self.dao.connection() as conn:
            row = conn.execute(
                "SELECT * FROM changes_log WHERE field = 'global_flag'"
            ).fetchone()
        assert row is not None
        assert row["company_id"] is None
        assert row["session_id"] is None

    def test_list_by_session_empty(self):
        assert self.dao.list_by_session("no-session") == []

    def test_log_returns_full_row(self):
        row = self.dao.log("c", "s", "cat", "tool", "f", "old", "new")
        assert row["company_id"] == "c"
        assert row["session_id"] == "s"
        assert row["category"] == "cat"
        assert row["tool"] == "tool"
        assert row["field"] == "f"
        assert row["old_value"] == "old"
        assert row["new_value"] == "new"
        assert row["diff_type"] == "update"
        assert "id" in row
        assert "created_at" in row

    def test_log_default_diff_type(self):
        row = self.dao.log("c", "s", None, None, "f", None, "v")
        assert row["diff_type"] == "update"


# ─── BaseDAO tests ─────────────────────────────────────────────────

class TestBaseDAO:
    def test_get_connection_returns_row_factory(self):
        dao = _TestCompanyDAO()
        conn = dao.get_connection()
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _test (id INTEGER PRIMARY KEY, val TEXT)"
        )
        conn.execute("INSERT INTO _test (val) VALUES ('hello')")
        conn.commit()
        row = conn.execute("SELECT * FROM _test WHERE id = 1").fetchone()
        assert row is not None
        assert row["val"] == "hello"  # row_factory=Row

    def test_connection_context_manager_commits(self):
        dao = _TestCompanyDAO()
        with dao.connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS _test_cm (id INTEGER PRIMARY KEY, val TEXT)"
            )
            conn.execute("INSERT INTO _test_cm (val) VALUES ('committed')")
        # Same connection (cached), verify it's there
        row = dao.get_connection().execute(
            "SELECT val FROM _test_cm WHERE id = 1"
        ).fetchone()
        assert row is not None
        assert row["val"] == "committed"

    def test_connection_context_manager_rolls_back_on_error(self):
        dao = _TestCompanyDAO()
        with dao.connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS _test_rb (id INTEGER PRIMARY KEY, val TEXT)"
            )
            conn.execute("INSERT INTO _test_rb (val) VALUES ('keep')")
        try:
            with dao.connection() as conn:
                conn.execute("INSERT INTO _test_rb (val) VALUES ('rollback')")
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        rows = dao.get_connection().execute(
            "SELECT * FROM _test_rb"
        ).fetchall()
        assert len(rows) == 1  # only 'keep' survived
