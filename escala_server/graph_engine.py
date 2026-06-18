"""Graph Engine — entity relationship graph backed by SQLite.

Operates on the ``entities`` and ``relationships`` tables.  Relationship
weights are stored in the ``properties`` JSON column.

Usage::

    eng = GraphEngine("data/escala.db")
    e1 = eng.add_entity("Acme Corp", "company", {"industry": "Tech"})
    e2 = eng.add_entity("Jane Smith", "person", {"role": "CEO"})
    eng.add_relationship(e1, e2, "employee_of", weight=1.0)

    related = eng.get_related_entities(e1, depth=2)
    merged = eng.resolve_entities("Acme", "Acme Corp")
    facts = eng.get_entity_facts(e1)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sqlite3


class GraphEngine:
    """Manage entity/relationship graph in SQLite."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = _resolve_path(db_path)
        from .schema import init_db

        if self._db_path not in _conn_cache:
            _conn_cache[self._db_path] = init_db(self._db_path)

    def _conn(self) -> sqlite3.Connection:
        return _conn_cache[self._db_path]

    # ── add_entity ───────────────────────────────────────────────────

    def add_entity(
        self,
        name: str,
        entity_type: str,
        properties: dict[str, Any] | None = None,
    ) -> int:
        """Create a new entity. Returns the new row id.

        Args:
            name:        Display name (e.g. "Acme Corp").
            entity_type: Entity kind (e.g. "company", "person", "metric").
            properties:  Optional dict of key-value metadata.
        """
        props_json = json.dumps(properties or {}, ensure_ascii=False)
        conn = self._conn()
        conn.execute(
            "INSERT INTO entities (type, name, properties) VALUES (?, ?, ?)",
            (entity_type, name, props_json),
        )
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # ── add_relationship ─────────────────────────────────────────────

    def add_relationship(
        self,
        source_id: int,
        target_id: int,
        relation_type: str,
        weight: float = 1.0,
    ) -> int:
        """Create a directed relationship between two entities.

        Args:
            source_id:     ID of the source entity.
            target_id:     ID of the target entity.
            relation_type: Label for the relationship (e.g. "employee_of").
            weight:        Optional weight (stored in properties JSON).

        Returns the new relationship row id.
        """
        props_json = json.dumps({"weight": weight}, ensure_ascii=False)
        conn = self._conn()
        conn.execute(
            """INSERT INTO relationships
               (source_entity_id, target_entity_id, relation_type, properties)
               VALUES (?, ?, ?, ?)""",
            (source_id, target_id, relation_type, props_json),
        )
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # ── get_related_entities ─────────────────────────────────────────

    def get_related_entities(
        self, entity_id: int, depth: int = 1
    ) -> list[dict[str, Any]]:
        """BFS traversal from *entity_id* up to *depth* hops.

        Returns a list of dicts, each containing::

            {
                "entity":       dict with id, type, name, properties,
                "distance":     hops from the root,
                "relationship": dict for the incoming edge (None for root),
            }
        """
        conn = self._conn()

        # Load the root entity
        root = conn.execute(
            "SELECT id, type, name, properties, created_at, updated_at FROM entities WHERE id = ?",
            (entity_id,),
        ).fetchone()
        if root is None:
            return []

        visited: set[int] = {entity_id}
        result: list[dict[str, Any]] = [
            {
                "entity": _entity_to_dict(root),
                "distance": 0,
                "relationship": None,
            }
        ]

        frontier = [(entity_id, 0)]

        for current_depth in range(depth):
            next_frontier: list[tuple[int, int]] = []
            for current_id, _ in frontier:
                # Outgoing relationships (source → target)
                out_rows = conn.execute(
                    """SELECT r.id AS rel_id, r.source_entity_id, r.target_entity_id,
                              r.relation_type, r.properties AS rel_properties, r.created_at AS rel_created_at,
                              e.id AS eid, e.type AS etype, e.name AS ename,
                              e.properties AS eproperties, e.created_at AS ecreated_at, e.updated_at AS eupdated_at
                       FROM relationships r
                       JOIN entities e ON e.id = r.target_entity_id
                       WHERE r.source_entity_id = ?""",
                    (current_id,),
                ).fetchall()

                # Incoming relationships (target ← source)
                in_rows = conn.execute(
                    """SELECT r.id AS rel_id, r.source_entity_id, r.target_entity_id,
                              r.relation_type, r.properties AS rel_properties, r.created_at AS rel_created_at,
                              e.id AS eid, e.type AS etype, e.name AS ename,
                              e.properties AS eproperties, e.created_at AS ecreated_at, e.updated_at AS eupdated_at
                       FROM relationships r
                       JOIN entities e ON e.id = r.source_entity_id
                       WHERE r.target_entity_id = ?""",
                    (current_id,),
                ).fetchall()

                for row in out_rows + in_rows:
                    neighbour_id = (
                        row["target_entity_id"]
                        if row["source_entity_id"] == current_id
                        else row["source_entity_id"]
                    )
                    if neighbour_id in visited:
                        continue
                    visited.add(neighbour_id)

                    rel_dict = {
                        "id": row["rel_id"],
                        "type": row["relation_type"],
                        "weight": _get_weight(row["rel_properties"]),
                    }

                    entity_dict = {
                        "id": row["eid"],
                        "type": row["etype"],
                        "name": row["ename"],
                        "properties": json.loads(row["eproperties"])
                        if row["eproperties"]
                        else {},
                    }

                    result.append(
                        {
                            "entity": entity_dict,
                            "distance": current_depth + 1,
                            "relationship": rel_dict,
                        }
                    )
                    next_frontier.append((neighbour_id, current_depth + 1))

            frontier = next_frontier

        return result

    # ── resolve_entities ─────────────────────────────────────────────

    def resolve_entities(self, name1: str, name2: str) -> int | None:
        """Merge two entities with similar names.

        All relationships to *name2* are re-pointed to *name1*'s entity,
        and *name2*'s entity is deleted.  Properties are merged (name1
        takes precedence on conflicts).

        Returns the surviving entity id, or None if either is not found.
        """
        conn = self._conn()

        row1 = conn.execute(
            "SELECT id, name, properties FROM entities WHERE name = ?",
            (name1,),
        ).fetchone()
        row2 = conn.execute(
            "SELECT id, name, properties FROM entities WHERE name = ?",
            (name2,),
        ).fetchone()

        if row1 is None or row2 is None:
            return None
        if row1["id"] == row2["id"]:
            return row1["id"]

        id1, id2 = row1["id"], row2["id"]

        # Merge properties (id1 wins conflicts)
        props1 = json.loads(row1["properties"]) if row1["properties"] else {}
        props2 = json.loads(row2["properties"]) if row2["properties"] else {}
        merged_props = {**props2, **props1}  # id1 overwrites

        conn.execute(
            "UPDATE entities SET properties = ? WHERE id = ?",
            (json.dumps(merged_props, ensure_ascii=False), id1),
        )

        # Re-point relationships: source = id2 → id1
        conn.execute(
            "UPDATE relationships SET source_entity_id = ? WHERE source_entity_id = ?",
            (id1, id2),
        )
        # Re-point relationships: target = id2 → id1
        conn.execute(
            "UPDATE relationships SET target_entity_id = ? WHERE target_entity_id = ?",
            (id1, id2),
        )

        # Remove self-referencing relationships
        conn.execute(
            "DELETE FROM relationships WHERE source_entity_id = target_entity_id"
        )

        # Delete the merged entity
        conn.execute("DELETE FROM entities WHERE id = ?", (id2,))

        conn.commit()
        return id1

    # ── get_entity_by_name ───────────────────────────────────────────

    def get_entity_by_name(self, name: str) -> dict[str, Any] | None:
        """Look up an entity by exact name match.

        Returns:
            Entity dict with id, type, name, properties, or None if not found.
        """
        conn = self._conn()
        row = conn.execute(
            "SELECT id, type, name, properties, created_at, updated_at "
            "FROM entities WHERE name = ?",
            (name,),
        ).fetchone()
        if row is None:
            return None
        return _entity_to_dict(row)

    # ── get_entity_facts ─────────────────────────────────────────────

    def get_entity_facts(self, entity_id: int) -> list[dict[str, Any]]:
        """Return memory facts that mention this entity by name.

        Performs a content-based search: looks for the entity name
        inside fact values.  Falls back to id-prefix matching.

        Args:
            entity_id: The entity to find facts for.

        Returns:
            List of fact dicts (id, content, category, tags, trust_score, ...).
        """
        conn = self._conn()
        entity = conn.execute(
            "SELECT name FROM entities WHERE id = ?", (entity_id,)
        ).fetchone()
        if entity is None:
            return []

        entity_name = entity["name"]
        name_lower = entity_name.lower()

        # Search for entity name in fact content
        rows = conn.execute(
            "SELECT id, key, value, created_at, updated_at FROM memory_facts"
        ).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            try:
                data = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                continue
            content = data.get("content", "")
            if name_lower in content.lower():
                results.append(
                    {
                        "id": row["id"],
                        "key": row["key"],
                        "content": content,
                        "category": data.get("category", ""),
                        "tags": data.get("tags", []),
                        "source": data.get("source", ""),
                        "trust_score": data.get("trust_score", 1.0),
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                )

        return results


# ── helpers ──────────────────────────────────────────────────────────

_conn_cache: dict[str, sqlite3.Connection] = {}


def _resolve_path(db_path: str) -> str:
    if db_path == ":memory:" or db_path.startswith("file:"):
        return db_path
    return str(Path(db_path).resolve())


def _entity_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "type": row["type"],
        "name": row["name"],
        "properties": json.loads(row["properties"]) if row["properties"] else {},
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _get_weight(properties_json: str) -> float:
    try:
        props = json.loads(properties_json)
        return props.get("weight", 1.0)
    except (json.JSONDecodeError, TypeError):
        return 1.0
