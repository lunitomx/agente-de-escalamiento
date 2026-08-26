"""ChangeDAO — audit log for field-level changes in worksheets."""

from typing import Any

from .base import BaseDAO


class ChangeDAO(BaseDAO):
    """Data access for the changes_log audit table."""

    # ── log ─────────────────────────────────────────────────────────

    def log(
        self,
        company_id: str | None,
        session_id: str | None,
        category: str | None,
        tool: str | None,
        field: str,
        old_value: str | None,
        new_value: str | None,
        diff_type: str = "update",
    ) -> dict[str, Any]:
        """Record a field-level change.

        Args:
            company_id: Optional company context.
            session_id: Optional session context.
            category: Optional worksheet category.
            tool: Optional tool key.
            field: The field name that changed.
            old_value: Previous value (stringified).
            new_value: New value (stringified).
            diff_type: One of 'create', 'update', 'delete' (default: 'update').

        Returns:
            The created change-log row as a dict.
        """
        with self.connection() as conn:
            cur = conn.execute(
                """INSERT INTO changes_log
                   (company_id, session_id, category, tool, field,
                    old_value, new_value, diff_type)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    company_id,
                    session_id,
                    category,
                    tool,
                    field,
                    old_value,
                    new_value,
                    diff_type,
                ),
            )
            new_id = cur.lastrowid

        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM changes_log WHERE id = ?", (new_id,)
            ).fetchone()
        return dict(row)  # type: ignore[arg-type]

    # ── list_by_session ─────────────────────────────────────────────

    def list_by_session(self, session_id: str | None) -> list[dict[str, Any]]:
        """Return all changes recorded for a given session.

        Args:
            session_id: The session id.

        Returns:
            List of change-log dicts ordered by creation time (oldest first).
        """
        with self.connection() as conn:
            rows = conn.execute(
                """SELECT * FROM changes_log
                   WHERE session_id = ?
                   ORDER BY created_at ASC""",
                (session_id,),
            ).fetchall()
        return [dict(row) for row in rows]
