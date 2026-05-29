"""Knowledge Handler — search and context API for the Escala knowledge graph.

Provides semantic search over entities, entity detail retrieval, and
context-aware entity lookups for coaching sessions.

Usage::

    from escala_server.knowledge_handler import KnowledgeHandler
    from escala_server.graph_engine import GraphEngine

    graph = GraphEngine("data/escala.db")
    handler = KnowledgeHandler(graph)

    results = handler.search("cash")
    # -> {"entities": [...], "count": N, "status": "ok"}

    entity = handler.get_entity("Power of One")
    # -> {"entity": {...}, "related": [...], "relationships": {...}, "status": "ok"}

    ctx = handler.get_context(category="cash")
    # -> {"entities": [...], "related": [...], "principles": [...], "habits": [...], "status": "ok"}

Types: concept, tool, metric, habit, principle, decision
Categories: cash, strategy, people, execution
"""

from __future__ import annotations

import json
from typing import Any

from .graph_engine import GraphEngine

# Entities whose keywords or name signal membership in each category
_CATEGORY_SIGNALS: dict[str, list[str]] = {
    "cash": [
        "cash", "cash flow", "ccc", "working capital", "revenue",
        "gross margin", "profit", "power of one", "financial",
        "operating cash", "receivables", "inventory", "payables",
        "capex", "capital", "balance sheet", "income statement",
    ],
    "strategy": [
        "strategy", "strategic", "swot", "swt", "bhag", "brand promise",
        "core purpose", "core values", "core customer", "sandbox",
        "x factor", "profit per x", "7 strata", "one-page",
        "opsp", "differentiation", "promise", "mission",
    ],
    "people": [
        "people", "topgrading", "fac", "functions", "accountability",
        "responsibility", "talent", "hiring", "culture", "values",
        "engagement", "net promoter", "nps", "quarterly conversation",
        "feedback", "coaching", "a-player",
    ],
    "execution": [
        "execution", "priority", "critical number", "theme",
        "quarterly", "rhythm", "huddle", "weekly meeting",
        "pace", "process", "routine", "habit", "scoreboard",
        "kpi", "no surprises", "same page", "alignment",
    ],
}


class KnowledgeHandler:
    """Search and context API over the Escala knowledge graph."""

    def __init__(self, graph_engine: GraphEngine) -> None:
        """Wrap an existing GraphEngine instance.

        Args:
            graph_engine: Initialised GraphEngine (shares the same db connection).
        """
        self.graph = graph_engine

    # ── search ────────────────────────────────────────────────────────

    def search(self, query: str, type_filter: str | None = None) -> dict:
        """Search entities by name, description, or keywords.

        Args:
            query:       Substring to search for (case-insensitive).
            type_filter: Optional entity type to restrict results to
                         (concept, tool, metric, habit, principle, decision).

        Returns:
            dict with ``entities`` list, ``count``, and ``status``.
        """
        conn = self.graph._conn()
        rows = conn.execute(
            "SELECT id, type, name, properties, created_at, updated_at "
            "FROM entities ORDER BY name"
        ).fetchall()

        query_lower = query.lower()
        matches: list[dict[str, Any]] = []

        for row in rows:
            name = row["name"]
            entity_type = row["type"]
            props = json.loads(row["properties"]) if row["properties"] else {}

            # Type filter
            if type_filter is not None and entity_type != type_filter:
                continue

            # Check for match in name
            if query_lower in name.lower():
                matches.append(_entity_to_search_dict(row, props))
                continue

            # Check description
            desc = props.get("description", "")
            if query_lower in desc.lower():
                matches.append(_entity_to_search_dict(row, props))
                continue

            # Check keywords
            keywords: list[str] = props.get("keywords", [])
            if any(query_lower in kw.lower() for kw in keywords):
                matches.append(_entity_to_search_dict(row, props))
                continue

        return {"entities": matches, "count": len(matches), "status": "ok"}

    # ── get_entity ────────────────────────────────────────────────────

    def get_entity(self, entity_name: str) -> dict:
        """Get entity details by name (exact match or slug match).

        Args:
            entity_name: Display name or JSON-id slug (e.g. "Power of One"
                         or "power-of-one").

        Returns:
            dict with ``entity``, ``related``, ``relationships``, and ``status``.
            Returns 404-style error dict if not found.
        """
        conn = self.graph._conn()

        # 1. Try exact name match
        row = conn.execute(
            "SELECT id, type, name, properties, created_at, updated_at "
            "FROM entities WHERE name = ?",
            (entity_name,),
        ).fetchone()

        # 2. Try slug match (slugify: replace spaces with hyphens, lowercase)
        if row is None:
            slug = entity_name.lower().replace(" ", "-")
            # Search all entities for slug match via JSON id pattern
            all_rows = conn.execute(
                "SELECT id, type, name, properties, created_at, updated_at "
                "FROM entities"
            ).fetchall()
            for r in all_rows:
                candidate_slug = r["name"].lower().replace(" ", "-")
                # Also strip parenthesised parts for slug matching
                candidate_slug_simple = candidate_slug.split("(")[0].strip("-")
                if slug == candidate_slug or slug == candidate_slug_simple:
                    row = r
                    break

        if row is None:
            return {
                "status": "error",
                "message": f"Entity '{entity_name}' not found",
            }

        props = json.loads(row["properties"]) if row["properties"] else {}
        entity = {
            "id": row["id"],
            "type": row["type"],
            "name": row["name"],
            "properties": props,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

        # 3. Get related entities (depth 1)
        related = self.graph.get_related_entities(row["id"], depth=1)

        # 4. Build separate incoming / outgoing relationship lists
        entity_id = row["id"]
        rel_rows = conn.execute(
            "SELECT r.id, r.source_entity_id, r.target_entity_id, "
            "       r.relation_type, r.properties, "
            "       src.name AS source_name, tgt.name AS target_name "
            "FROM relationships r "
            "JOIN entities src ON src.id = r.source_entity_id "
            "JOIN entities tgt ON tgt.id = r.target_entity_id "
            "WHERE r.source_entity_id = ? OR r.target_entity_id = ?",
            (entity_id, entity_id),
        ).fetchall()

        outgoing: list[dict[str, Any]] = []
        incoming: list[dict[str, Any]] = []
        for rel in rel_rows:
            rel_props = (
                json.loads(rel["properties"]) if rel["properties"] else {}
            )
            rel_dict = {
                "id": rel["id"],
                "type": rel["relation_type"],
                "weight": rel_props.get("weight", 1.0),
                "source_name": rel["source_name"],
                "target_name": rel["target_name"],
            }
            if rel["source_entity_id"] == entity_id:
                outgoing.append(rel_dict)
            else:
                incoming.append(rel_dict)

        # Build related entity names list
        related_names: list[str] = []
        for r in related:
            if r["entity"]["id"] != entity_id:
                related_names.append(r["entity"]["name"])

        return {
            "entity": entity,
            "related": related,
            "relationships": {
                "outgoing": outgoing,
                "incoming": incoming,
            },
            "related_names": related_names,
            "status": "ok",
        }

    # ── get_context ───────────────────────────────────────────────────

    def get_context(
        self, tool: str | None = None, category: str | None = None
    ) -> dict:
        """Return relevant context for a session.

        Args:
            tool:     Entity name to use as the focal point.
            category: Category to filter by (cash, strategy, people, execution).

        Returns:
            dict with ``entities``, ``related``, ``principles``, ``habits``,
            and ``status``.
        """
        if not tool and not category:
            return {"status": "error", "message": "requires 'tool' or 'category' parameter"}
        conn = self.graph._conn()

        # Determine the set of relevant entity names via category signals
        category_names: set[str] | None = None
        if category:
            signals = _CATEGORY_SIGNALS.get(category, [])
            all_rows = conn.execute(
                "SELECT id, name, properties FROM entities"
            ).fetchall()
            category_names = set()
            for row in all_rows:
                name_lower = row["name"].lower()
                props = json.loads(row["properties"]) if row["properties"] else {}
                keywords: list[str] = props.get("keywords", [])
                desc = props.get("description", "").lower()

                if any(s in name_lower for s in signals) or any(
                    any(s in kw.lower() for s in signals) for kw in keywords
                ) or any(s in desc for s in signals):
                    category_names.add(row["name"])

        # If tool is provided, find its entity
        tool_result: dict | None = None
        if tool:
            tool_result = self.get_entity(tool)
            if tool_result.get("status") != "ok":
                return tool_result

        # If both provided, intersect tool's related with category
        if tool and category and tool_result:
            tool_entity = tool_result.get("entity", {})
            tool_related = tool_result.get("related", [])
            tool_related_names = tool_result.get("related_names", [])

            # Entities in both tool's scope and category
            ctx_entities: list[dict[str, Any]] = []
            if category_names and tool_entity.get("name") in category_names:
                ctx_entities.append(tool_entity)

            for rel in tool_related:
                if rel["entity"]["name"] in category_names:
                    ctx_entities.append(rel["entity"])

            # Principles and habits from the intersection
            principles = [
                e for e in ctx_entities if e["type"] == "principle"
            ]
            habits = [
                e for e in ctx_entities if e["type"] == "habit"
            ]

            return {
                "tool": tool_entity,
                "entities": ctx_entities,
                "principles": principles,
                "habits": habits,
                "category": category,
                "status": "ok",
            }

        if tool and tool_result:
            tool_entity = tool_result.get("entity", {})
            related_list = tool_result.get("related", [])

            # Extract principles and habits from related
            all_entities = [tool_entity] + [
                r["entity"] for r in related_list if r["entity"]["id"] != tool_entity.get("id")
            ]
            principles = [
                e for e in all_entities if e.get("type") == "principle"
            ]
            habits = [
                e for e in all_entities if e.get("type") == "habit"
            ]

            return {
                "tool": tool_entity,
                "entities": all_entities,
                "principles": principles,
                "habits": habits,
                "status": "ok",
            }

        if category and category_names:
            all_rows = conn.execute(
                "SELECT id, type, name, properties, created_at, updated_at "
                "FROM entities ORDER BY name"
            ).fetchall()

            ctx_entities: list[dict[str, Any]] = []
            for row in all_rows:
                if row["name"] in category_names:
                    props = json.loads(row["properties"]) if row["properties"] else {}
                    ctx_entities.append({
                        "id": row["id"],
                        "type": row["type"],
                        "name": row["name"],
                        "properties": props,
                    })

            principles = [
                e for e in ctx_entities if e["type"] == "principle"
            ]
            habits = [
                e for e in ctx_entities if e["type"] == "habit"
            ]

            return {
                "entities": ctx_entities,
                "principles": principles,
                "habits": habits,
                "category": category,
                "status": "ok",
            }

        return {
            "entities": [],
            "principles": [],
            "habits": [],
            "status": "ok",
        }


# ── helpers ──────────────────────────────────────────────────────────


def _entity_to_search_dict(
    row: Any, props: dict[str, Any]
) -> dict[str, Any]:
    """Convert an entity row + parsed properties into a search result dict."""
    return {
        "id": row["id"],
        "type": row["type"],
        "name": row["name"],
        "description": props.get("description", ""),
        "keywords": props.get("keywords", []),
    }