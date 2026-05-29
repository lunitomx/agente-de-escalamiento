"""SQLite-backed data handlers for the Escala server API.

These handlers wrap the SQLite-backed DAO classes and maintain
the same API contract as the original in-memory handlers.
"""

import json
from typing import Any

from .daos import CompanyDAO, WorksheetDAO, ChangeDAO, SessionDAO
from .diff import dict_diff


class CompaniesHandler:
    """Handle CRUD for company profiles (SQLite-backed)."""

    def __init__(self, db_path: str = ":memory:"):
        self.dao = CompanyDAO(db_path)

    # ── public API (matches in-memory contract) ────────────────────

    def list_companies(self) -> dict:
        rows = self.dao.list()
        return {"data": rows, "status": "ok"}

    def create_company(self, company_data: dict) -> dict:
        company = self.dao.create(company_data)
        return {"data": company, "status": "ok"}

    def get_company(self, company_id: str) -> dict:
        company = self.dao.get(company_id)
        if company is None:
            return {"status": "error", "message": f"Company {company_id} not found"}
        return {"data": company, "status": "ok"}

    def update_company(self, company_id: str, updates: dict) -> dict:
        updated = self.dao.update(company_id, updates)
        if updated is None:
            return {"status": "error", "message": f"Company {company_id} not found"}
        return {"data": updated, "status": "ok"}


class WorksheetsHandler:
    """Handle CRUD for worksheet data (SQLite-backed).

    Each save creates a change log entry tracking field-level diffs.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.worksheet_dao = WorksheetDAO(db_path)
        self.change_dao = ChangeDAO(db_path)

    # ── public API ────────────────────────────────────────────────

    def get_worksheets(self, category: str, tool: str) -> dict:
        row = self.worksheet_dao.get(category, tool)
        data = json.loads(row["data"]) if row else {}
        return {"data": data, "status": "ok"}

    def save_worksheet(
        self,
        category: str,
        tool: str,
        payload: dict,
        session_id: str | None = None,
    ) -> dict:
        # Get current data for diff
        current = self.worksheet_dao.get(category, tool)
        current_data = json.loads(current["data"]) if current else {}

        # Save the new version
        saved = self.worksheet_dao.save(category, tool, payload, session_id=session_id)

        # Compute and log field-level changes
        if current_data:
            changes = dict_diff(current_data, payload)
            for ch in changes:
                self.change_dao.log(
                    company_id=None,
                    session_id=session_id,
                    category=category,
                    tool=tool,
                    field=ch["field"],
                    old_value=_serialise(ch.get("old_value")),
                    new_value=_serialise(ch.get("new_value")),
                    diff_type="update",
                )

        response_data = json.loads(saved["data"])
        return {"data": response_data, "status": "ok"}

    def get_changes(self, category: str, tool: str) -> list[dict[str, Any]]:
        """Return raw change-log rows for a (category, tool) pair."""
        with self.change_dao.connection() as conn:
            rows = conn.execute(
                """SELECT * FROM changes_log
                   WHERE category = ? AND tool = ?
                   ORDER BY created_at ASC""",
                (category, tool),
            ).fetchall()
        return [dict(r) for r in rows]


class SessionsHandler:
    """Handle session management (SQLite-backed)."""

    def __init__(self, db_path: str = ":memory:"):
        self.dao = SessionDAO(db_path)

    # ── public API ────────────────────────────────────────────────

    def list_sessions(self) -> dict:
        rows = self.dao.list()
        return {"data": rows, "status": "ok"}

    def create_session(self, session_data: dict) -> dict:
        session = self.dao.create(session_data)
        return {"data": session, "status": "ok"}

    def get_session(self, session_id: str) -> dict:
        session = self.dao.get(session_id)
        if session is None:
            return {"status": "error", "message": f"Session {session_id} not found"}
        return {"data": session, "status": "ok"}


# ── helpers ──────────────────────────────────────────────────────────

def _serialise(value: Any) -> str | None:
    """Stringify a value for storage in changes_log."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)
