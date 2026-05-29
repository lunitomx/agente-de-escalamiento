"""WorksheetDAO — versioned persistence for coaching worksheets.

Each ``save()`` call creates a new row with an auto-incremented version.
``get()`` returns the latest version for a (category, tool) pair.
``list_by_category()`` returns all latest versions for a given category.
"""

import json
from typing import Any, Optional

from .base import BaseDAO


class WorksheetDAO(BaseDAO):
    """Data access for worksheets (versioned)."""

    # ── get (latest version) ────────────────────────────────────────

    def get(self, category: str, tool: str) -> Optional[dict[str, Any]]:
        """Return the latest version of a worksheet.

        Args:
            category: Worksheet category (e.g. 'cash', 'strategy').
            tool: Tool key (e.g. 'power-of-one', 'swot').

        Returns:
            Worksheet dict (keys: id, category, tool, data, session_id,
            version, created_at, updated_at) or None.
        """
        with self.connection() as conn:
            row = conn.execute(
                """SELECT * FROM worksheets
                   WHERE category = ? AND tool = ?
                   ORDER BY version DESC
                   LIMIT 1""",
                (category, tool),
            ).fetchone()
        return dict(row) if row else None

    # ── save (creates new version) ──────────────────────────────────

    def save(
        self,
        category: str,
        tool: str,
        data: dict[str, Any],
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Save a new version of a worksheet.

        Args:
            category: Worksheet category.
            tool: Tool key.
            data: Payload dict (serialised as JSON).
            session_id: Optional session that produced this change.

        Returns:
            The newly created worksheet row as a dict.
        """
        previous = self.get(category, tool)
        next_version = (previous["version"] + 1) if previous else 1
        data_json = json.dumps(data)

        with self.connection() as conn:
            cur = conn.execute(
                """INSERT INTO worksheets (category, tool, data, session_id, version)
                   VALUES (?, ?, ?, ?, ?)""",
                (category, tool, data_json, session_id, next_version),
            )
            new_id = cur.lastrowid

        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM worksheets WHERE id = ?", (new_id,)
            ).fetchone()
        return dict(row)  # type: ignore[arg-type]

    # ── list_by_category (latest version of each tool) ──────────────

    def list_by_category(self, category: str) -> list[dict[str, Any]]:
        """Return the latest version of every tool in the given category.

        Args:
            category: Worksheet category.

        Returns:
            List of worksheet dicts, one per distinct (category, tool).
        """
        with self.connection() as conn:
            rows = conn.execute(
                """SELECT w.* FROM worksheets w
                   INNER JOIN (
                       SELECT category, tool, MAX(version) AS max_ver
                       FROM worksheets
                       WHERE category = ?
                       GROUP BY category, tool
                   ) latest ON w.category = latest.category
                            AND w.tool = latest.tool
                            AND w.version = latest.max_ver
                   WHERE w.category = ?
                   ORDER BY w.tool""",
                (category, category),
            ).fetchall()
        return [dict(row) for row in rows]
