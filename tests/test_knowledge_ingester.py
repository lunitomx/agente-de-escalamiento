"""Tests for the Knowledge Ingester (S19.2).

Validates that the KnowledgeIngester:
  - Creates all 42 entities from book-knowledge.json
  - Creates all 59 relationships
  - Is idempotent (second call skips all)
  - Returns correct counts
  - Stores entity properties correctly (description, keywords, line_refs in properties dict)
"""

import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "escala_server"))

from escala_server.data.knowledge_ingester import KnowledgeIngester
from escala_server.graph_engine import _conn_cache as _graph_cache
from escala_server.memory_engine import _conn_cache as _mem_cache

JSON_PATH = PROJECT_ROOT / "escala_server" / "data" / "book-knowledge.json"


class TestKnowledgeIngester:
    """Test the KnowledgeIngester for book-knowledge.json."""

    @pytest.fixture
    def ingester(self):
        """Create a fresh in-memory KnowledgeIngester per test."""
        uri = f"file:ingest_test_{uuid.uuid4().hex}?mode=memory&cache=shared"
        ing = KnowledgeIngester(db_path=uri)
        yield ing
        # Clean up connections
        _graph_cache.pop(ing.graph_engine._db_path, None)
        _mem_cache.pop(ing.memory_engine._db_path, None)

    # ── entity count tests ──────────────────────────────────────────

    def test_ingest_all_creates_all_42_entities(self, ingester):
        """ingest_all should create exactly 42 entities."""
        result = ingester.ingest_all(json_path=str(JSON_PATH))
        assert result["entities_created"] == 42

    def test_ingest_all_creates_all_59_relationships(self, ingester):
        """ingest_all should create exactly 59 relationships."""
        result = ingester.ingest_all(json_path=str(JSON_PATH))
        assert result["relationships_created"] == 59

    # ── idempotency test ────────────────────────────────────────────

    def test_ingest_all_is_idempotent(self, ingester):
        """Second call to ingest_all should skip all entities and relationships."""
        first = ingester.ingest_all(json_path=str(JSON_PATH))
        assert first["entities_created"] == 42
        assert first["relationships_created"] == 59
        assert first["entities_skipped"] == 0

        second = ingester.ingest_all(json_path=str(JSON_PATH))
        assert second["entities_created"] == 0
        assert second["relationships_created"] == 0
        assert second["entities_skipped"] == 42

        # Graph should still have exactly 42 entities
        stats = ingester.get_stats()
        assert stats["entities"] == 42
        assert stats["relationships"] == 59

    # ── counts test ─────────────────────────────────────────────────

    def test_ingest_all_returns_correct_counts(self, ingester):
        """The result dict should contain the correct keys and counts."""
        result = ingester.ingest_all(json_path=str(JSON_PATH))

        assert "entities_created" in result
        assert "relationships_created" in result
        assert "entities_skipped" in result

        assert result["entities_created"] == 42
        assert result["relationships_created"] == 59
        assert result["entities_skipped"] == 0

        # Total entities + relationships match
        assert result["entities_created"] + result["entities_skipped"] == 42

    # ── entity properties tests ──────────────────────────────────────

    def test_entity_properties_stored_correctly(self, ingester):
        """Properties dict should contain description, keywords, line_refs."""
        ingester.ingest_all(json_path=str(JSON_PATH))

        # Look up a known entity: "Power of One"
        entity = ingester.graph_engine.get_entity_by_name("Power of One")
        assert entity is not None

        props = entity["properties"]
        assert "description" in props
        assert "keywords" in props
        assert "line_refs" in props
        assert "chapter_ids" in props

        # Check that values are not empty for this well-known entity
        assert len(props["description"]) > 0
        assert len(props["keywords"]) > 0
        assert len(props["line_refs"]) > 0
        assert len(props["chapter_ids"]) > 0

    def test_entity_properties_for_multiple_entities(self, ingester):
        """Verify properties are stored correctly for several entities."""
        ingester.ingest_all(json_path=str(JSON_PATH))

        # Test a few known entities
        tests = [
            ("Power of One", "concept", "7 levers"),
            ("Rockefeller Habits", "concept", "10 habits"),
            ("Cash Conversion Cycle (CCC)", "concept", "CCC"),
            ("One-Page Strategic Plan (OPSP)", "concept", "OPSP"),
        ]

        for name, expected_type, expected_keyword in tests:
            entity = ingester.graph_engine.get_entity_by_name(name)
            assert entity is not None, f"Entity '{name}' not found"
            assert entity["type"] == expected_type, f"'{name}' type mismatch"

            props = entity["properties"]
            assert expected_keyword in props["keywords"], (
                f"'{name}' missing keyword '{expected_keyword}'"
            )

    def test_get_stats_returns_correct_counts(self, ingester):
        """get_stats should report entity and relationship counts."""
        # Before ingest
        stats_before = ingester.get_stats()
        assert stats_before["entities"] == 0
        assert stats_before["relationships"] == 0

        # After ingest
        ingester.ingest_all(json_path=str(JSON_PATH))
        stats = ingester.get_stats()
        assert stats["entities"] == 42
        assert stats["relationships"] == 59

    # ── memory facts test ────────────────────────────────────────────

    def test_memory_facts_created_for_entities(self, ingester):
        """ingest_all should create memory facts for each entity."""
        ingester.ingest_all(json_path=str(JSON_PATH))

        facts = ingester.memory_engine.search_facts("", category="book_knowledge")
        assert len(facts) >= 42  # At least one fact per entity

        # Each fact should reference an entity name
        fact_contents = [f["content"] for f in facts]
        assert any("Power of One" in c for c in fact_contents)
        assert any("Rockefeller Habits" in c for c in fact_contents)

    # ── ingest_entity individual test ────────────────────────────────

    def test_ingest_entity_individual(self, ingester):
        """ingest_entity should create a single entity correctly."""
        entity_data = {
            "id": "test-concept",
            "name": "Test Concept",
            "type": "concept",
            "description": "A test concept for unit testing.",
            "keywords": ["test", "unit"],
            "line_refs": [1, 2, 3],
            "chapter_ids": [1],
        }
        eid = ingester.ingest_entity(entity_data)
        assert isinstance(eid, int)
        assert eid > 0

        # Verify it exists
        entity = ingester.graph_engine.get_entity_by_name("Test Concept")
        assert entity is not None
        assert entity["type"] == "concept"
        assert entity["properties"]["description"] == "A test concept for unit testing."
        assert "test" in entity["properties"]["keywords"]

        # Second call should be idempotent
        eid2 = ingester.ingest_entity(entity_data)
        assert eid2 == eid

    # ── ingest_relationship individual test ──────────────────────────

    def test_ingest_relationship_individual(self, ingester):
        """ingest_relationship should create a relationship correctly."""
        # Create two entities
        e1 = ingester.graph_engine.add_entity("Source Entity", "concept")
        e2 = ingester.graph_engine.add_entity("Target Entity", "concept")

        mapping = {"src": e1, "tgt": e2}

        rel_data = {
            "source": "src",
            "target": "tgt",
            "type": "relates_to",
            "weight": 0.8,
        }

        rid = ingester.ingest_relationship(rel_data, mapping)
        assert isinstance(rid, int)
        assert rid > 0

        # Verify via graph
        connected = ingester.graph_engine.get_related_entities(e1, depth=1)
        assert len(connected) == 2  # root + neighbour
        assert connected[1]["entity"]["name"] == "Target Entity"
        assert connected[1]["relationship"]["weight"] == 0.8
        assert connected[1]["relationship"]["type"] == "relates_to"

    def test_ingest_relationship_missing_source(self, ingester):
        """ingest_relationship should return None if source not in mapping."""
        mapping = {"tgt": 1}
        rel_data = {"source": "nonexistent", "target": "tgt"}
        result = ingester.ingest_relationship(rel_data, mapping)
        assert result is None

    def test_ingest_relationship_missing_target(self, ingester):
        """ingest_relationship should return None if target not in mapping."""
        mapping = {"src": 1}
        rel_data = {"source": "src", "target": "nonexistent"}
        result = ingester.ingest_relationship(rel_data, mapping)
        assert result is None


# ─── Route Registration Tests ──────────────────────────────────────


class TestKnowledgeIngestRoute:
    """Verify knowledge ingest route is registered correctly."""

    def test_ingest_route_registered(self):
        from escala_server.server import _build_router

        router = _build_router()
        handler, _params = router.dispatch("POST", "/api/knowledge/ingest")
        assert handler is not None
