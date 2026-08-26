"""SessionDAO — CRUD for coaching sessions."""

import json
import uuid
from typing import Any

from .base import BaseDAO


class SessionDAO(BaseDAO):
    """Data access for coaching sessions."""

    # ── list ────────────────────────────────────────────────────────

    def list(self) -> list[dict[str, Any]]:
        """Return all sessions ordered by creation time (newest first).

        Returns:
            List of session dicts.
        """
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    # ── get ─────────────────────────────────────────────────────────

    def get(self, session_id: str) -> dict[str, Any] | None:
        """Look up a session by id.

        Args:
            session_id: Session id string.

        Returns:
            Session dict or None.
        """
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return dict(row) if row else None

    # ── create ──────────────────────────────────────────────────────

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a new session.

        Args:
            data: Dict with optional 'company_id', 'status', 'metadata'.
                  If 'id' is absent, one is auto-generated.

        Returns:
            The full session dict as stored.
        """
        session_id = data.get("id") or str(uuid.uuid4())[:8]
        company_id = data.get("company_id")
        status = data.get("status", "active")
        metadata = json.dumps(data.get("metadata", {}))

        with self.connection() as conn:
            conn.execute(
                """INSERT INTO sessions (id, company_id, status, metadata)
                   VALUES (?, ?, ?, ?)""",
                (session_id, company_id, status, metadata),
            )
        return self.get(session_id)  # type: ignore[return-value]

    # ── update ──────────────────────────────────────────────────────

    def update(self, session_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update fields on an existing session.

        Args:
            session_id: Session to update.
            data: Dict with optional 'company_id', 'status', 'metadata'.

        Returns:
            The updated session dict, or None if not found.
        """
        existing = self.get(session_id)
        if existing is None:
            return None

        updates: dict[str, Any] = {}
        if "company_id" in data:
            updates["company_id"] = data["company_id"]
        if "status" in data:
            updates["status"] = data["status"]
        if "metadata" in data:
            updates["metadata"] = json.dumps(data["metadata"])

        if not updates:
            return existing

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        values = list(updates.values())

        with self.connection() as conn:
            conn.execute(
                f"UPDATE sessions SET {set_clause} WHERE id = ?",
                (*values, session_id),
            )
        return self.get(session_id)
