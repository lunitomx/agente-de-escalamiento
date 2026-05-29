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


class MemoryHandler:
    """Handle memory & knowledge graph API (SQLite-backed)."""

    def __init__(self, db_path: str = ":memory:"):
        from .memory_engine import MemoryEngine
        from .graph_engine import GraphEngine

        self.memory = MemoryEngine(db_path)
        self.graph = GraphEngine(db_path)

    # ── fact endpoints ────────────────────────────────────────────

    def list_facts(
        self,
        query: str = "",
        category: str | None = None,
        tags: str | None = None,
        min_trust: float = 0.0,
    ) -> dict:
        """GET /api/memory/facts — search/list facts."""
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        results = self.memory.search_facts(
            query=query or "",
            category=category,
            tags=tag_list,
            min_trust=min_trust,
        )
        return {"data": results, "status": "ok"}

    def create_fact(self, payload: dict) -> dict:
        """POST /api/memory/facts — create a fact."""
        content = payload.get("content", "")
        if not content:
            return {"status": "error", "message": "content is required"}
        fid = self.memory.add_fact(
            content=content,
            category=payload.get("category", ""),
            tags=payload.get("tags", []),
            source=payload.get("source", ""),
        )
        return {"data": {"id": fid}, "status": "ok"}

    def context(self, company_context: dict | None = None) -> dict:
        """GET /api/memory/context — relevant facts for session context."""
        facts = self.memory.get_relevant_facts(company_context)
        return {"data": facts, "status": "ok"}

    # ── entity endpoints ──────────────────────────────────────────

    def get_entity(self, entity_id: int) -> dict:
        """GET /api/memory/graph/{entity_id} — entity + relationships."""
        conn = self.memory._conn()
        row = conn.execute(
            "SELECT id, type, name, properties, created_at, updated_at "
            "FROM entities WHERE id = ?",
            (entity_id,),
        ).fetchone()
        if row is None:
            return {"status": "error", "message": f"Entity {entity_id} not found"}

        entity = {
            "id": row["id"],
            "type": row["type"],
            "name": row["name"],
            "properties": json.loads(row["properties"]) if row["properties"] else {},
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

        related = self.graph.get_related_entities(entity_id, depth=1)
        facts = self.graph.get_entity_facts(entity_id)

        return {
            "data": {
                "entity": entity,
                "related": related,
                "facts": facts,
                "fact_count": len(facts),
            },
            "status": "ok",
        }

    def create_entity(self, payload: dict) -> dict:
        """POST /api/memory/entities — create an entity."""
        name = payload.get("name", "")
        if not name:
            return {"status": "error", "message": "name is required"}
        eid = self.graph.add_entity(
            name=name,
            entity_type=payload.get("type", "generic"),
            properties=payload.get("properties", {}),
        )
        return {"data": {"id": eid}, "status": "ok"}

    def create_relationship(self, payload: dict) -> dict:
        """POST /api/memory/relationships — create a relationship."""
        source = payload.get("source_id")
        target = payload.get("target_id")
        if source is None or target is None:
            return {
                "status": "error",
                "message": "source_id and target_id are required",
            }
        rid = self.graph.add_relationship(
            source_id=int(source),
            target_id=int(target),
            relation_type=payload.get("type", "related_to"),
            weight=float(payload.get("weight", 1.0)),
        )
        return {"data": {"id": rid}, "status": "ok"}


# ── helpers ──────────────────────────────────────────────────────────

def _serialise(value: Any) -> str | None:
    """Stringify a value for storage in changes_log."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)
