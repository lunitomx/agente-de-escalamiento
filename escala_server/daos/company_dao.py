"""CompanyDAO — CRUD for company profiles in the Escala database."""

import json
import uuid
from typing import Any, Optional

from .base import BaseDAO


class CompanyDAO(BaseDAO):
    """Data access for companies.

    Usage::

        dao = CompanyDAO("data/escala.db")
        companies = dao.list()
        company   = dao.get("abc123")
        new_cid   = dao.create({"name": "Acme", "industry": "Tech"})
        dao.update("abc123", {"industry": "Healthcare"})
    """

    # ── list ────────────────────────────────────────────────────────

    def list(self) -> list[dict[str, Any]]:
        """Return all companies ordered by creation time (newest first).

        Returns:
            A list of company dicts, each including 'id', 'name',
            'industry', 'metadata', 'created_at', 'updated_at'.
        """
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM companies ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    # ── get ─────────────────────────────────────────────────────────

    def get(self, company_id: str) -> Optional[dict[str, Any]]:
        """Look up a single company by its id.

        Args:
            company_id: The company id string.

        Returns:
            A company dict or None if not found.
        """
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM companies WHERE id = ?", (company_id,)
            ).fetchone()
        return dict(row) if row else None

    # ── create ──────────────────────────────────────────────────────

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a new company.

        Args:
            data: Dict with at least 'name'.  Optional keys: 'industry',
                  'metadata'.  If 'id' is absent, one is auto-generated.

        Returns:
            The full company dict as stored (including generated id).
        """
        company_id = data.get("id") or str(uuid.uuid4())[:8]
        name = data.get("name", "")
        industry = data.get("industry", "")
        metadata = json.dumps(data.get("metadata", {}))

        with self.connection() as conn:
            conn.execute(
                """INSERT INTO companies (id, name, industry, metadata)
                   VALUES (?, ?, ?, ?)""",
                (company_id, name, industry, metadata),
            )
        return self.get(company_id)  # type: ignore[return-value]

    # ── update ──────────────────────────────────────────────────────

    def update(self, company_id: str, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Update fields on an existing company.

        Args:
            company_id: The company to update.
            data: Dict of fields to change.  Allowed keys: 'name',
                  'industry', 'metadata'.  Unknown keys are ignored.

        Returns:
            The updated company dict, or None if the company does not exist.
        """
        existing = self.get(company_id)
        if existing is None:
            return None

        updates: dict[str, Any] = {}
        if "name" in data:
            updates["name"] = data["name"]
        if "industry" in data:
            updates["industry"] = data["industry"]
        if "metadata" in data:
            updates["metadata"] = json.dumps(data["metadata"])

        if not updates:
            return existing

        updates["updated_at"] = "datetime('now')"

        set_clause = ", ".join(f"{k} = ?" for k in updates if k != "updated_at")
        set_clause += ", updated_at = datetime('now')"
        values = [updates[k] for k in updates if k != "updated_at"]

        with self.connection() as conn:
            conn.execute(
                f"UPDATE companies SET {set_clause} WHERE id = ?",
                (*values, company_id),
            )
        return self.get(company_id)
