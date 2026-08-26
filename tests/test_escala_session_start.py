"""Tests for SessionStartOrchestrator (escala-inicia).

Uses an in-memory SQLite database with shared cache so that all DAOs
and the memory engine share the same database instance.
"""

from __future__ import annotations

import unittest

from escala_server.daos.company_dao import CompanyDAO
from escala_server.daos.session_dao import SessionDAO
from escala_server.daos.worksheet_dao import WorksheetDAO
from escala_server.memory_engine import MemoryEngine
from escala_server.session.session_start import (
    SessionContext,
    SessionStartOrchestrator,
)

# Shared-cache URI so BaseDAO and MemoryEngine share one in-memory DB.
_DB_URI = "file:test_escala_session_start?mode=memory&cache=shared"

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


class TestSessionStartOrchestrator(unittest.TestCase):
    """Tests for SessionStartOrchestrator."""

    def setUp(self) -> None:
        """Create fresh DAOs and orchestrator pointing at shared in-memory DB."""
        self.company_dao = CompanyDAO(_DB_URI)
        self.session_dao = SessionDAO(_DB_URI)
        self.worksheet_dao = WorksheetDAO(_DB_URI)
        self.memory = MemoryEngine(_DB_URI)
        self.orchestrator = SessionStartOrchestrator(_DB_URI)

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
        company_id: str,
        status: str = "completed",
        summary: str = "",
    ) -> dict:
        return self.session_dao.create(
            {
                "company_id": company_id,
                "status": status,
                "metadata": {"summary": summary},
            }
        )

    # ── tests ────────────────────────────────────────────────────

    def test_start_session_no_prior_sessions(self) -> None:
        """start_session with a company but no prior sessions."""
        company = self._seed_company()

        ctx = self.orchestrator.start_session(company["id"])

        self.assertIsInstance(ctx, SessionContext)
        self.assertEqual(ctx.company_name, "TestCorp")
        self.assertEqual(ctx.company_id, company["id"])
        self.assertIsNone(ctx.last_session_date)
        self.assertEqual(ctx.changes_detected_count, 0)
        self.assertEqual(len(ctx.recent_session_summaries), 0)
        self.assertEqual(len(ctx.relevant_facts), 0)
        self.assertIsInstance(ctx.server_running, bool)

    def test_start_session_with_prior_sessions(self) -> None:
        """start_session picks up last 3 sessions, facts, and worksheet changes."""
        company = self._seed_company()

        # Create 4 sessions — only last 3 should appear in context
        s1 = self._seed_session(company["id"], "completed", "Primera sesión")
        s2 = self._seed_session(company["id"], "completed", "Segunda sesión")
        s3 = self._seed_session(company["id"], "active", "Tercera sesión")
        self._seed_session(company["id"], "completed", "Cuarta (extra)")

        # Create worksheet changes associated with sessions
        self.worksheet_dao.save("cash", "power-of-one", {"value": 100}, s1["id"])
        self.worksheet_dao.save("strategy", "swot", {"data": "test"}, s2["id"])
        self.worksheet_dao.save("cash", "breakeven", {"units": 5000}, s3["id"])

        # Seed memory facts
        self.memory.add_fact(
            "Revenue grew 20% in Q1", "finance", ["revenue", "q1"], s1["id"]
        )
        self.memory.add_fact(
            "Team expanded to 10 people", "people", ["team", "growth"], s2["id"]
        )
        self.memory.add_fact(
            "New product launch in June", "strategy", ["product", "launch"], s3["id"]
        )

        ctx = self.orchestrator.start_session(company["id"])

        # Company
        self.assertEqual(ctx.company_name, "TestCorp")
        self.assertEqual(ctx.company_id, company["id"])

        # Last session date should be set
        self.assertIsNotNone(ctx.last_session_date)

        # Only 3 most recent sessions
        self.assertEqual(len(ctx.recent_session_summaries), 3)

        # Worksheet changes: all 3 were created after the oldest session
        # (actually, they're all after the first session, so count should be >= 2)
        self.assertGreater(ctx.changes_detected_count, 0)

        # Memory facts — we seeded 3, all should be returned (limit 5)
        self.assertGreater(len(ctx.relevant_facts), 0)
        self.assertLessEqual(len(ctx.relevant_facts), 5)

        # Verify summaries contain the right data
        summaries = ctx.recent_session_summaries
        self.assertIn("id", summaries[0])
        self.assertIn("status", summaries[0])
        self.assertIn("created_at", summaries[0])
        self.assertIn("summary", summaries[0])

    def test_start_session_no_company(self) -> None:
        """start_session with empty database returns default context."""
        ctx = self.orchestrator.start_session()

        self.assertEqual(ctx.company_name, "Empresa")
        self.assertEqual(ctx.company_id, "")
        self.assertIsNone(ctx.last_session_date)
        self.assertEqual(ctx.changes_detected_count, 0)
        self.assertEqual(len(ctx.recent_session_summaries), 0)
        self.assertEqual(len(ctx.relevant_facts), 0)

    def test_start_session_explicit_company_id(self) -> None:
        """start_session(company_id=...) loads the correct company."""
        company_a = self._seed_company("Alpha", "Finance")
        self._seed_company("Beta", "Healthcare")

        ctx = self.orchestrator.start_session(company_id=company_a["id"])

        self.assertEqual(ctx.company_name, "Alpha")
        self.assertEqual(ctx.company_id, company_a["id"])

    def test_check_health_structure(self) -> None:
        """check_health returns the expected dict structure."""
        result = self.orchestrator.check_health()

        self.assertIn("running", result)
        self.assertIn("message", result)
        self.assertIn("host", result)
        self.assertIn("port", result)
        self.assertIsInstance(result["running"], bool)
        self.assertIsInstance(result["message"], str)
        self.assertEqual(result["host"], "localhost")
        self.assertEqual(result["port"], 8080)

    def test_get_context_prompt_formatting(self) -> None:
        """get_context_prompt returns well-formed welcome string."""
        company = self._seed_company("Acme Corp")
        self._seed_session(company["id"], "completed", "Primera")
        self.worksheet_dao.save("cash", "power-of-one", {"value": 42})

        self.orchestrator.start_session(company["id"])
        prompt = self.orchestrator.get_context_prompt()

        self.assertIn("Bienvenido Acme Corp", prompt)
        self.assertIn("Última sesión:", prompt)
        self.assertIn("cambios detectados", prompt)
        # Should mention the one worksheet change
        self.assertIn("1 cambios detectados", prompt)

    def test_get_context_prompt_no_active_session(self) -> None:
        """get_context_prompt without calling start_session returns fallback."""
        orch = SessionStartOrchestrator(_DB_URI)
        prompt = orch.get_context_prompt()

        self.assertIn("Bienvenido", prompt)
        self.assertIn("No hay sesión activa", prompt)

    def test_context_prompt_sin_sesiones_previas(self) -> None:
        """Prompt shows 'sin sesiones previas' when no prior sessions exist."""
        self._seed_company("SoloCorp")

        self.orchestrator.start_session()
        prompt = self.orchestrator.get_context_prompt()

        self.assertIn("sin sesiones previas", prompt)
        self.assertIn("0 cambios detectados", prompt)

    def test_session_context_is_dataclass(self) -> None:
        """SessionContext is a proper dataclass with defaults."""
        ctx = SessionContext()
        self.assertEqual(ctx.company_name, "")
        self.assertEqual(ctx.company_id, "")
        self.assertIsNone(ctx.last_session_date)
        self.assertEqual(ctx.changes_detected_count, 0)
        self.assertEqual(ctx.recent_session_summaries, [])
        self.assertEqual(ctx.relevant_facts, [])
        self.assertFalse(ctx.server_running)


if __name__ == "__main__":
    unittest.main()
