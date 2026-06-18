"""SessionStartOrchestrator — escala-inicia (Session Start Orchestrator).

Orchestrates the session startup flow for the Escala coaching server:
loads company profile, recent sessions, memory facts, detects worksheet
changes, and reports server health.
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from typing import Any

from ..daos.company_dao import CompanyDAO
from ..daos.session_dao import SessionDAO
from ..daos.worksheet_dao import WorksheetDAO
from ..memory_engine import MemoryEngine


@dataclass
class SessionContext:
    """Context snapshot assembled at session start.

    Attributes:
        company_name: Display name of the company.
        company_id: Unique identifier of the company.
        last_session_date: ISO-8601 timestamp of the most recent session,
            or None when no prior sessions exist.
        changes_detected_count: Number of worksheet records created since
            the last session.
        recent_session_summaries: Up to 3 most recent sessions with id,
            status, created_at, and metadata summary.
        relevant_facts: Top 5 memory facts ranked by trust score.
        server_running: Whether the Escala HTTP server is reachable.
    """

    company_name: str = ""
    company_id: str = ""
    last_session_date: str | None = None
    changes_detected_count: int = 0
    recent_session_summaries: list[dict[str, Any]] = field(default_factory=list)
    relevant_facts: list[dict[str, Any]] = field(default_factory=list)
    server_running: bool = False


class SessionStartOrchestrator:
    """Orchestrates the session-start flow for Escala.

    Usage::

        orch = SessionStartOrchestrator("data/escala.db")
        ctx = orch.start_session(company_id="abc123")
        print(orch.get_context_prompt())
        # Bienvenido Acme Corp. Última sesión: 2026-05-28 10:00:00.
        # 3 cambios detectados.
    """

    def __init__(self, db_path: str) -> None:
        """Initialise all DAOs and the memory engine.

        Args:
            db_path: Path to the SQLite database (or ``:memory:``).
        """
        self._db_path = db_path
        self._company_dao = CompanyDAO(db_path)
        self._session_dao = SessionDAO(db_path)
        self._worksheet_dao = WorksheetDAO(db_path)
        self._memory = MemoryEngine(db_path)
        self._current_context: SessionContext | None = None

    # ── main entry point ─────────────────────────────────────────

    def start_session(self, company_id: str | None = None) -> SessionContext:
        """Load full context and return a SessionContext snapshot.

        Steps performed:
        1. Load company profile (by *company_id* or first available).
        2. Load last 3 sessions from SessionDAO.
        3. Load top-5 relevant memory facts.
        4. Detect worksheet changes since the last session.
        5. Check server health.

        Args:
            company_id: Optional company id.  If omitted the first
                company in the database is used.  If the database has
                no companies a default context is returned.

        Returns:
            A fully populated SessionContext.
        """
        # 1. Company profile
        if company_id:
            company = self._company_dao.get(company_id)
        else:
            companies = self._company_dao.list()
            company = companies[0] if companies else None

        company_name = company["name"] if company else "Empresa"
        actual_company_id = company["id"] if company else ""

        # 2. Last 3 sessions
        all_sessions = self._session_dao.list()
        last_sessions = all_sessions[:3]
        last_session_date = last_sessions[0]["created_at"] if last_sessions else None

        # 3. Relevant memory facts (top 5)
        company_context: dict[str, Any] | None = None
        if company:
            company_context = {
                "industry": company.get("industry", ""),
                "name": company.get("name", ""),
            }
        relevant_facts = self._memory.get_relevant_facts(company_context, limit=5)

        # 4. Detect changes since last session
        changes_count = self._count_changes_since(last_session_date)

        # 5. Server health
        health = self.check_health()
        server_running = health.get("running", False)

        # Build session summaries with decoded metadata
        summaries: list[dict[str, Any]] = []
        for s in last_sessions:
            metadata_raw = s.get("metadata", "{}")
            if isinstance(metadata_raw, str):
                try:
                    metadata_raw = json.loads(metadata_raw)
                except (json.JSONDecodeError, TypeError):
                    metadata_raw = {}
            summaries.append(
                {
                    "id": s["id"],
                    "status": s.get("status", ""),
                    "created_at": s.get("created_at", ""),
                    "summary": metadata_raw.get("summary", "")
                    if isinstance(metadata_raw, dict)
                    else "",
                }
            )

        ctx = SessionContext(
            company_name=company_name,
            company_id=actual_company_id,
            last_session_date=last_session_date,
            changes_detected_count=changes_count,
            recent_session_summaries=summaries,
            relevant_facts=relevant_facts,
            server_running=server_running,
        )
        self._current_context = ctx
        return ctx

    # ── helpers ──────────────────────────────────────────────────

    def _count_changes_since(self, since_date: str | None) -> int:
        """Count worksheet records created after *since_date*.

        Args:
            since_date: ISO-8601 timestamp or None.

        Returns:
            Number of worksheet rows with ``created_at > since_date``.
        """
        if not since_date:
            return 0
        conn = self._company_dao.get_connection()
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM worksheets WHERE created_at >= ?",
            (since_date,),
        ).fetchone()
        return row["cnt"] if row else 0

    # ── health check ─────────────────────────────────────────────

    def check_health(self) -> dict[str, Any]:
        """Check whether the Escala HTTP server is reachable.

        Attempts a TCP connection to localhost on the default Escala
        port (8080).

        Returns:
            Dict with ``running`` (bool), ``message``, ``host``, ``port``.
        """
        host = "localhost"
        port = 8080
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return {
                    "running": True,
                    "message": "Server is reachable on port 8080",
                    "host": host,
                    "port": port,
                }
            return {
                "running": False,
                "message": "Server is not reachable",
                "host": host,
                "port": port,
            }
        except OSError as exc:
            return {
                "running": False,
                "message": f"Health check failed: {exc}",
                "host": host,
                "port": port,
            }

    # ── context prompt ───────────────────────────────────────────

    def get_context_prompt(self) -> str:
        """Return a human-readable welcome / context prompt.

        Format:
            ``Bienvenido {empresa}. Última sesión: {fecha}.
            {N} cambios detectados.``
        """
        if not self._current_context:
            return "Bienvenido. No hay sesión activa."

        ctx = self._current_context
        company = ctx.company_name
        fecha = ctx.last_session_date or "sin sesiones previas"
        cambios = ctx.changes_detected_count

        return (
            f"Bienvenido {company}. Última sesión: {fecha}. "
            f"{cambios} cambios detectados."
        )
