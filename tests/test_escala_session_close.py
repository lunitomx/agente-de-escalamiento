"""Tests for SessionCloseOrchestrator (escala-cierra).

Uses an in-memory SQLite database with shared cache so that all DAOs
and engines share the same database instance.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from escala_server.daos.company_dao import CompanyDAO
from escala_server.daos.session_dao import SessionDAO
from escala_server.daos.worksheet_dao import WorksheetDAO
from escala_server.memory_engine import MemoryEngine
from escala_server.session.session_close import (
    SessionCloseOrchestrator,
    SessionCloseResult,
)

# Shared-cache URI so BaseDAO, MemoryEngine, and GraphEngine share
# one in-memory DB.
_DB_URI = "file:test_escala_session_close?mode=memory&cache=shared"

# Tables to clean between tests (order matters for FK constraints).
_TABLES = [
    "relationships",
    "entities",
    "changes_log",
    "worksheets",
    "memory_facts",
    "sessions",
    "companies",
]


class TestSessionCloseOrchestrator(unittest.TestCase):
    """Tests for SessionCloseOrchestrator."""

    def setUp(self) -> None:
        """Create fresh DAOs and orchestrator pointing at shared in-memory DB."""
        self.company_dao = CompanyDAO(_DB_URI)
        self.session_dao = SessionDAO(_DB_URI)
        self.worksheet_dao = WorksheetDAO(_DB_URI)
        self.memory = MemoryEngine(_DB_URI)
        self.orchestrator = SessionCloseOrchestrator(_DB_URI)

    def tearDown(self) -> None:
        """Wipe all tables between tests."""
        conn = self.company_dao.get_connection()
        for table in _TABLES:
            conn.execute(f"DELETE FROM {table}")
        conn.commit()

    # ── helpers ──────────────────────────────────────────────────

    def _seed_company(self, name: str = "TestCorp", industry: str = "Tech") -> dict:
        return self.company_dao.create({"name": name, "industry": industry})

    def _seed_session(
        self,
        company_id: str = "",
        status: str = "active",
        metadata: dict | None = None,
    ) -> dict:
        return self.session_dao.create(
            {
                "company_id": company_id,
                "status": status,
                "metadata": metadata or {},
            }
        )

    def _seed_worksheet(
        self,
        category: str,
        tool: str,
        data: dict,
        session_id: str = "",
    ) -> dict:
        return self.worksheet_dao.save(category, tool, data, session_id)

    # ── tests: close_session with learnings ───────────────────────

    def test_close_session_with_learnings_and_decisions(self) -> None:
        """close_session stores learnings and decisions as memory facts."""
        company = self._seed_company("Acme")
        session = self._seed_session(company["id"])

        with patch.object(Path, "home", return_value=Path(tempfile.mkdtemp())):
            result = self.orchestrator.close_session(
                session_id=session["id"],
                learnings="Aprendí que el flujo de caja es crítico.",
                decisions="Decidí reducir costos operativos un 10 %.",
            )

        self.assertIsInstance(result, SessionCloseResult)
        self.assertEqual(result.session_id, session["id"])
        self.assertGreater(result.new_facts_count, 0)

        # Verify session is now closed
        updated = self.session_dao.get(session["id"])
        self.assertIsNotNone(updated)
        self.assertEqual(updated["status"], "closed")

        # Verify learnings/decisions were stored as facts
        facts = self.memory.search_facts("Aprendizaje")
        self.assertGreaterEqual(len(facts), 1)
        self.assertIn("flujo de caja", facts[0]["content"])

        facts = self.memory.search_facts("Decisión")
        self.assertGreaterEqual(len(facts), 1)
        self.assertIn("reducir costos", facts[0]["content"])

    def test_close_session_without_learnings_or_decisions(self) -> None:
        """close_session works fine when learnings and decisions are None."""
        company = self._seed_company()
        session = self._seed_session(company["id"])

        with patch.object(Path, "home", return_value=Path(tempfile.mkdtemp())):
            result = self.orchestrator.close_session(
                session_id=session["id"],
            )

        self.assertEqual(result.session_id, session["id"])
        self.assertGreaterEqual(result.new_facts_count, 0)
        self.assertEqual(result.changes_count, 0)

        updated = self.session_dao.get(session["id"])
        self.assertEqual(updated["status"], "closed")

    def test_close_session_not_found(self) -> None:
        """close_session returns a result with error summary for unknown id."""
        result = self.orchestrator.close_session(session_id="nonexistent")

        self.assertEqual(result.session_id, "nonexistent")
        self.assertEqual(result.new_facts_count, 0)
        self.assertIn("not found", result.summary)

    # ── tests: change detection ──────────────────────────────────

    def test_close_session_detects_worksheet_changes(self) -> None:
        """close_session detects field-level diffs in worksheets."""
        company = self._seed_company()
        session = self._seed_session(company["id"])

        # Create a first version of a worksheet (not linked to session)
        self._seed_worksheet("cash", "power-of-one", {"value": 100})
        # Now save an update linked to this session
        self._seed_worksheet("cash", "power-of-one", {"value": 200}, session["id"])

        with patch.object(Path, "home", return_value=Path(tempfile.mkdtemp())):
            result = self.orchestrator.close_session(session_id=session["id"])

        self.assertGreater(result.changes_count, 0)
        self.assertEqual(result.changes_count, 1)

        # Verify the change was logged
        conn = self.company_dao.get_connection()
        logged = conn.execute(
            "SELECT * FROM changes_log WHERE session_id = ?",
            (session["id"],),
        ).fetchall()
        self.assertGreaterEqual(len(logged), 1)

    def test_close_session_no_changes(self) -> None:
        """close_session reports zero changes when no worksheets were modified."""
        company = self._seed_company()
        session = self._seed_session(company["id"])

        with patch.object(Path, "home", return_value=Path(tempfile.mkdtemp())):
            result = self.orchestrator.close_session(session_id=session["id"])

        self.assertEqual(result.changes_count, 0)

    def test_close_session_multiple_worksheet_changes(self) -> None:
        """Each modified field in each worksheet counts as a change."""
        company = self._seed_company()
        session = self._seed_session(company["id"])

        # Seed baseline
        self._seed_worksheet("cash", "power-of-one", {"value": 100, "unit": "MXN"})
        # Update both fields in session
        self._seed_worksheet(
            "cash",
            "power-of-one",
            {"value": 200, "unit": "USD"},
            session["id"],
        )

        with patch.object(Path, "home", return_value=Path(tempfile.mkdtemp())):
            result = self.orchestrator.close_session(session_id=session["id"])

        # Two fields changed: value and unit
        self.assertEqual(result.changes_count, 2)

    def test_close_session_new_worksheet_in_session(self) -> None:
        """Brand-new worksheet (v1) linked to session — all fields are 'create'."""
        company = self._seed_company()
        session = self._seed_session(company["id"])

        # Save a brand new worksheet directly linked to session
        self._seed_worksheet(
            "strategy",
            "swot",
            {"strengths": "brand", "weaknesses": "cashflow"},
            session["id"],
        )

        with patch.object(Path, "home", return_value=Path(tempfile.mkdtemp())):
            result = self.orchestrator.close_session(session_id=session["id"])

        # Two fields created
        self.assertEqual(result.changes_count, 2)

        # Verify diff_type is 'create'
        conn = self.company_dao.get_connection()
        logged = conn.execute(
            "SELECT diff_type FROM changes_log WHERE session_id = ?",
            (session["id"],),
        ).fetchall()
        for row in logged:
            self.assertEqual(row["diff_type"], "create")

    def test_close_session_deleted_fields(self) -> None:
        """Removing a field from a worksheet produces a 'delete' diff."""
        company = self._seed_company()
        session = self._seed_session(company["id"])

        self._seed_worksheet("cash", "breakeven", {"units": 5000, "price": 20})
        self._seed_worksheet(
            "cash", "breakeven", {"units": 5000}, session["id"]
        )  # price removed

        with patch.object(Path, "home", return_value=Path(tempfile.mkdtemp())):
            result = self.orchestrator.close_session(session_id=session["id"])

        self.assertEqual(result.changes_count, 1)

        conn = self.company_dao.get_connection()
        logged = conn.execute(
            "SELECT * FROM changes_log WHERE session_id = ?",
            (session["id"],),
        ).fetchall()
        self.assertEqual(logged[0]["diff_type"], "delete")
        self.assertEqual(logged[0]["field"], "price")
        self.assertEqual(logged[0]["old_value"], "20")
        self.assertIsNone(logged[0]["new_value"])

    # ── tests: facts from changes ────────────────────────────────

    def test_close_session_creates_facts_from_changes(self) -> None:
        """Each detected change becomes a memory fact."""
        company = self._seed_company()
        session = self._seed_session(company["id"])

        self._seed_worksheet("cash", "power-of-one", {"value": 100})
        self._seed_worksheet("cash", "power-of-one", {"value": 200}, session["id"])

        with patch.object(Path, "home", return_value=Path(tempfile.mkdtemp())):
            result = self.orchestrator.close_session(session_id=session["id"])

        self.assertEqual(result.changes_count, 1)
        # 1 change fact + 0 learnings/decisions = 1 total
        self.assertEqual(result.new_facts_count, 1)

        # Search for the auto-generated fact
        facts = self.memory.search_facts("Cambio en cash/power-of-one")
        self.assertEqual(len(facts), 1)
        self.assertIn("'value' pasó de '100' a '200'", facts[0]["content"])
        self.assertEqual(facts[0]["category"], "change")
        self.assertEqual(facts[0]["source"], session["id"])

    def test_close_session_fact_for_new_field(self) -> None:
        """Newly created fields produce 'Nuevo campo' fact text."""
        company = self._seed_company()
        session = self._seed_session(company["id"])

        self._seed_worksheet(
            "strategy", "swot", {"nueva_metrica": "abc"}, session["id"]
        )

        with patch.object(Path, "home", return_value=Path(tempfile.mkdtemp())):
            result = self.orchestrator.close_session(session_id=session["id"])

        self.assertEqual(result.changes_count, 1)
        facts = self.memory.search_facts("Nuevo campo")
        self.assertGreaterEqual(len(facts), 1)
        self.assertIn("nueva_metrica", facts[0]["content"])

    def test_close_session_fact_for_deleted_field(self) -> None:
        """Deleted fields produce 'Campo eliminado' fact text."""
        company = self._seed_company()
        session = self._seed_session(company["id"])

        self._seed_worksheet("strategy", "swot", {"removed_field": "xyz"})
        self._seed_worksheet("strategy", "swot", {}, session["id"])

        with patch.object(Path, "home", return_value=Path(tempfile.mkdtemp())):
            self.orchestrator.close_session(session_id=session["id"])

        facts = self.memory.search_facts("Campo eliminado")
        self.assertGreaterEqual(len(facts), 1)
        self.assertIn("removed_field", facts[0]["content"])

    def test_close_session_facts_and_learnings_combined(self) -> None:
        """Learnings + changes produce separate facts for each."""
        company = self._seed_company()
        session = self._seed_session(company["id"])

        self._seed_worksheet("cash", "power-of-one", {"value": 100})
        self._seed_worksheet("cash", "power-of-one", {"value": 200}, session["id"])

        with patch.object(Path, "home", return_value=Path(tempfile.mkdtemp())):
            result = self.orchestrator.close_session(
                session_id=session["id"],
                learnings="Lección aprendida.",
                decisions="Decisión tomada.",
            )

        # 1 change + 1 learning + 1 decision = 3 facts
        self.assertEqual(result.new_facts_count, 3)

        all_facts = self.memory.search_facts("", min_trust=0.0)
        contents = [f["content"] for f in all_facts]
        self.assertTrue(any("Lección aprendida" in c for c in contents))
        self.assertTrue(any("Decisión tomada" in c for c in contents))
        self.assertTrue(any("Cambio en cash/power-of-one" in c for c in contents))

    # ── tests: markdown log ──────────────────────────────────────

    def test_markdown_log_written_correctly(self) -> None:
        """close_session writes a well-formed markdown log file."""
        company = self._seed_company("Acme Corp")
        session = self._seed_session(company["id"])

        self._seed_worksheet("cash", "power-of-one", {"value": 100})
        self._seed_worksheet("cash", "power-of-one", {"value": 200}, session["id"])

        tmp_home = tempfile.mkdtemp()

        with patch.object(Path, "home", return_value=Path(tmp_home)):
            result = self.orchestrator.close_session(
                session_id=session["id"],
                learnings="Aprendí algo importante.",
                decisions="Tomé una decisión clave.",
            )

        # Check that the file exists and has expected content
        log_dir = Path(tmp_home) / ".escala" / "acme-corp" / "sessions"
        log_file = log_dir / f"session_{session['id']}.md"

        self.assertTrue(log_file.exists(), f"Expected log at {log_file}")

        content = log_file.read_text(encoding="utf-8")

        # Header
        self.assertIn(f"# Sesión: {session['id']}", content)

        # Company info
        self.assertIn("Acme Corp", content)

        # Learnings section
        self.assertIn("## Aprendizajes", content)
        self.assertIn("Aprendí algo importante", content)

        # Decisions section
        self.assertIn("## Decisiones", content)
        self.assertIn("Tomé una decisión clave", content)

        # Changes section
        self.assertIn("## Cambios detectados", content)
        self.assertIn("de cambios:** 1", content)
        self.assertIn("cash", content)
        self.assertIn("power-of-one", content)

        # Verify the result also looks good
        self.assertEqual(result.changes_count, 1)
        self.assertIn("1 cambio detectado", result.summary)

    def test_markdown_log_without_changes(self) -> None:
        """Markdown log shows 'No se detectaron cambios' when zero changes."""
        company = self._seed_company()
        session = self._seed_session(company["id"])

        tmp_home = tempfile.mkdtemp()

        with patch.object(Path, "home", return_value=Path(tmp_home)):
            result = self.orchestrator.close_session(
                session_id=session["id"],
            )

        log_dir = Path(tmp_home) / ".escala" / "testcorp" / "sessions"
        log_file = log_dir / f"session_{session['id']}.md"

        self.assertTrue(log_file.exists())

        content = log_file.read_text(encoding="utf-8")
        self.assertIn("*Sin aprendizajes registrados.*", content)
        self.assertIn("*Sin decisiones registradas.*", content)
        self.assertIn("*No se detectaron cambios.*", content)
        self.assertIn("de cambios:** 0", content)

        self.assertEqual(result.changes_count, 0)
        self.assertIn("0 cambios detectados", result.summary)

    def test_markdown_log_path_uses_sanitised_company_name(self) -> None:
        """Company name 'My Great Company' → directory 'my-great-company'."""
        company = self._seed_company("My Great Company")
        session = self._seed_session(company["id"])

        tmp_home = tempfile.mkdtemp()

        with patch.object(Path, "home", return_value=Path(tmp_home)):
            self.orchestrator.close_session(session_id=session["id"])

        log_dir = Path(tmp_home) / ".escala" / "my-great-company" / "sessions"
        log_file = log_dir / f"session_{session['id']}.md"
        self.assertTrue(log_file.exists())

    # ── tests: graph update ──────────────────────────────────────

    def test_close_session_updates_graph(self) -> None:
        """Graph entities and relationships are created for changes."""
        company = self._seed_company()
        session = self._seed_session(company["id"])

        self._seed_worksheet("cash", "power-of-one", {"value": 100})
        self._seed_worksheet("cash", "power-of-one", {"value": 200}, session["id"])

        with patch.object(Path, "home", return_value=Path(tempfile.mkdtemp())):
            self.orchestrator.close_session(session_id=session["id"])

        # Check that entities were created
        conn = self.company_dao.get_connection()
        entities = conn.execute("SELECT name, type FROM entities").fetchall()
        names = [e["name"] for e in entities]

        self.assertIn(f"session:{session['id']}", names)
        self.assertIn("tool:power-of-one", names)
        self.assertIn("field:cash.power-of-one.value", names)

        # Check relationships exist
        rels = conn.execute("SELECT relation_type FROM relationships").fetchall()
        rel_types = [r["relation_type"] for r in rels]
        self.assertIn("modified_tool", rel_types)
        self.assertIn("has_field", rel_types)
        self.assertIn("changed_field", rel_types)

    # ── tests: SessionCloseResult dataclass ──────────────────────

    def test_session_close_result_defaults(self) -> None:
        """SessionCloseResult has sensible defaults."""
        result = SessionCloseResult()
        self.assertEqual(result.session_id, "")
        self.assertEqual(result.duration, "")
        self.assertEqual(result.changes_count, 0)
        self.assertEqual(result.new_facts_count, 0)
        self.assertEqual(result.summary, "")

    # ── tests: duration computation ──────────────────────────────

    def test_close_session_includes_duration(self) -> None:
        """The result includes a human-readable duration string."""
        company = self._seed_company()
        session = self._seed_session(company["id"])

        with patch.object(Path, "home", return_value=Path(tempfile.mkdtemp())):
            result = self.orchestrator.close_session(session_id=session["id"])

        self.assertIsNotNone(result.duration)
        self.assertNotEqual(result.duration, "")
        self.assertNotEqual(result.duration, "desconocida")


if __name__ == "__main__":
    unittest.main()
