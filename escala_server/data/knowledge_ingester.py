"""Knowledge Ingester — ingests parsed book knowledge into the Escala knowledge graph.

Reads the structured JSON output from the book parser and populates the
graph engine and memory engine with entities, relationships, and facts.

Usage::

    from escala_server.data.knowledge_ingester import KnowledgeIngester

    ingester = KnowledgeIngester(db_path=":memory:")
    result = ingester.ingest_all()
    print(result)  # {"entities_created": 42, "relationships_created": 59, "entities_skipped": 0}

    # Second call is idempotent:
    result2 = ingester.ingest_all()
    print(result2)  # {"entities_created": 0, "relationships_created": 0, "entities_skipped": 42}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from escala_server.graph_engine import GraphEngine
from escala_server.memory_engine import MemoryEngine


class KnowledgeIngester:
    """Ingest parsed book knowledge into the graph and memory engines."""

    def __init__(self, db_path: str = ":memory:") -> None:
        """Initialize GraphEngine and MemoryEngine with the same db_path."""
        self.graph_engine = GraphEngine(db_path)
        self.memory_engine = MemoryEngine(db_path)

    # ── ingest_all ──────────────────────────────────────────────────

    def ingest_all(
        self,
        json_path: str = "escala_server/data/book-knowledge.json",
    ) -> dict[str, int]:
        """Main entry point. Reads JSON, ingests entities and relationships.

        For each entity in the JSON:
            - Check if entity already exists via graph_engine.get_entity_by_name(name)
            - If not, add_entity(name, type, properties=...)
            - Store mapping from entity "id" (from JSON) to actual entity_id (from DB)

        For each relationship in the JSON:
            - Look up source and target entity_ids from mapping
            - add_relationship(source_id, target_id, type, weight)

        For each entity, also add a memory fact describing it.

        Returns dict with counts:
            {"entities_created": N, "relationships_created": N, "entities_skipped": N}
        """
        # 1. Load JSON
        resolved = _resolve_json_path(json_path)
        with open(resolved, "r", encoding="utf-8") as f:
            data = json.load(f)

        entities = data.get("entities", [])
        relationships_list = data.get("relationships", [])

        entities_created = 0
        entities_skipped = 0
        relationships_created = 0

        # 2. For each entity, check existence and add if new
        entity_mapping: dict[str, int] = {}
        for entity_data in entities:
            name = entity_data["name"]
            existing = self.graph_engine.get_entity_by_name(name)

            if existing is not None:
                # Entity already exists — use its id
                entity_mapping[entity_data["id"]] = existing["id"]
                entities_skipped += 1
            else:
                # Create new entity
                eid = self.ingest_entity(entity_data)
                entity_mapping[entity_data["id"]] = eid
                entities_created += 1

        # 3. For each relationship, look up source/target ids and add
        for rel_data in relationships_list:
            source_json_id = rel_data["source"]
            target_json_id = rel_data["target"]
            source_id = entity_mapping.get(source_json_id)
            target_id = entity_mapping.get(target_json_id)

            if source_id is None or target_id is None:
                continue

            # Check if relationship already exists (idempotency)
            if not _relationship_exists(
                self.graph_engine, source_id, target_id, rel_data.get("type", "related_to")
            ):
                self.graph_engine.add_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=rel_data.get("type", "related_to"),
                    weight=rel_data.get("weight", 1.0),
                )
                relationships_created += 1

        # 4. For each entity, add a memory fact describing it
        for entity_data in entities:
            self.memory_engine.add_fact(
                content=f"[{entity_data.get('type', 'concept')}] {entity_data['name']}: {entity_data.get('description', '')}",
                category="book_knowledge",
                tags=(entity_data.get("keywords", []) or [])[:5],
                source="knowledge_ingester",
            )

        return {
            "entities_created": entities_created,
            "relationships_created": relationships_created,
            "entities_skipped": entities_skipped,
        }

    # ── ingest_entity ────────────────────────────────────────────────

    def ingest_entity(self, entity_data: dict[str, Any]) -> int:
        """Ingest a single entity.

        Checks if entity already exists by name. If it does, returns the
        existing entity id. Otherwise creates a new entity.

        Returns the entity id (existing or newly created).
        """
        name = entity_data["name"]
        existing = self.graph_engine.get_entity_by_name(name)
        if existing is not None:
            return existing["id"]

        return self.graph_engine.add_entity(
            name=name,
            entity_type=entity_data.get("type", "concept"),
            properties={
                "description": entity_data.get("description", ""),
                "keywords": entity_data.get("keywords", []),
                "line_refs": entity_data.get("line_refs", []),
                "chapter_ids": entity_data.get("chapter_ids", []),
            },
        )

    # ── ingest_relationship ──────────────────────────────────────────

    def ingest_relationship(
        self,
        rel_data: dict[str, Any],
        entity_mapping: dict[str, int],
    ) -> int | None:
        """Ingest a single relationship.

        Looks up source and target entity_ids from the mapping and
        adds the relationship to the graph engine.

        Returns the relationship id, or None if source/target not found.
        """
        source_json_id = rel_data["source"]
        target_json_id = rel_data["target"]

        source_id = entity_mapping.get(source_json_id)
        target_id = entity_mapping.get(target_json_id)

        if source_id is None or target_id is None:
            return None

        return self.graph_engine.add_relationship(
            source_id=source_id,
            target_id=target_id,
            relation_type=rel_data.get("type", "related_to"),
            weight=rel_data.get("weight", 1.0),
        )

    # ── get_stats ────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, int]:
        """Return current counts of entities and relationships in the graph."""
        conn = self.graph_engine._conn()
        entity_count = conn.execute(
            "SELECT COUNT(*) FROM entities"
        ).fetchone()[0]
        rel_count = conn.execute(
            "SELECT COUNT(*) FROM relationships"
        ).fetchone()[0]
        return {"entities": entity_count, "relationships": rel_count}


# ── internal helpers ─────────────────────────────────────────────────


def _resolve_json_path(json_path: str) -> Path:
    """Resolve the JSON path relative to the project root.

    If json_path is already absolute, use it as-is.
    Otherwise resolve relative to the project root (2 levels up from
    escala_server/data/).
    """
    p = Path(json_path)
    if p.is_absolute():
        return p
    # Relative to the project root
    data_dir = Path(__file__).resolve().parent  # escala_server/data/
    project_root = data_dir.parent.parent  # project root
    return project_root / json_path


def _relationship_exists(
    graph_engine: GraphEngine,
    source_id: int,
    target_id: int,
    relation_type: str,
) -> bool:
    """Check if a relationship already exists between two entities."""
    conn = graph_engine._conn()
    row = conn.execute(
        """SELECT id FROM relationships
           WHERE source_entity_id = ?
             AND target_entity_id = ?
             AND relation_type = ?""",
        (source_id, target_id, relation_type),
    ).fetchone()
    return row is not None
