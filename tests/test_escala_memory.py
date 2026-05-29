"""Tests for Memory Engine and Graph Engine (S18.9)."""

import json
import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "escala_server"))

from escala_server.memory_engine import MemoryEngine
from escala_server.graph_engine import GraphEngine
from escala_server.handlers import MemoryHandler
from escala_server.router import Router
from escala_server.server import EscalaRequestHandler

# Import cache modules so we can reset them between tests
from escala_server.memory_engine import _conn_cache as _mem_cache
from escala_server.graph_engine import _conn_cache as _graph_cache


# ─── MemoryEngine Tests ────────────────────────────────────────────


class TestMemoryEngine:
    """Test the MemoryEngine fact CRUD with trust_score."""

    @pytest.fixture
    def engine(self):
        """Create a fresh in-memory engine per test."""
        # Use unique URI so tests don't share a database
        uri = f"file:mem_test_{uuid.uuid4().hex}?mode=memory&cache=shared"
        eng = MemoryEngine(uri)
        yield eng
        _mem_cache.pop(eng._db_path, None)

    def test_add_fact_returns_id(self, engine):
        fid = engine.add_fact("Revenue grew 20%", "finance", ["revenue", "q1"], "test")
        assert isinstance(fid, int)
        assert fid > 0

    def test_add_fact_defaults(self, engine):
        fid = engine.add_fact("Basic fact")
        assert isinstance(fid, int)
        assert fid > 0

    def test_search_facts_by_query(self, engine):
        engine.add_fact("Revenue grew 20%", "finance", ["revenue"], "s1")
        engine.add_fact("Team size doubled", "people", ["team"], "s2")
        engine.add_fact("Revenue dipped in Q2", "finance", ["revenue"], "s3")

        results = engine.search_facts("revenue")
        assert len(results) == 2

    def test_search_facts_by_category(self, engine):
        engine.add_fact("Revenue grew", "finance", [], "")
        engine.add_fact("Hired 5 people", "people", [], "")

        results = engine.search_facts("", category="finance")
        assert len(results) == 1
        assert results[0]["category"] == "finance"

    def test_search_facts_by_tags(self, engine):
        engine.add_fact("Revenue grew", "finance", ["revenue", "q1"], "")
        engine.add_fact("Costs down", "finance", ["costs"], "")

        results = engine.search_facts("", tags=["revenue"])
        assert len(results) == 1
        assert "revenue" in results[0]["tags"]

    def test_search_facts_min_trust(self, engine):
        fid = engine.add_fact("Important fact", "strategy", [], "")
        engine.update_trust(fid, -0.95)  # drops to 0.05

        results = engine.search_facts("Important", min_trust=0.5)
        assert len(results) == 0

        results = engine.search_facts("Important", min_trust=0.0)
        assert len(results) == 1

    def test_get_relevant_facts_respects_limit(self, engine):
        for i in range(15):
            engine.add_fact(f"Fact {i}", "general", [], "")
        facts = engine.get_relevant_facts(limit=5)
        assert len(facts) == 5

    def test_get_relevant_facts_sorted_by_trust(self, engine):
        f1 = engine.add_fact("Top fact", "general", [], "")
        f2 = engine.add_fact("Mid fact", "general", [], "")
        f3 = engine.add_fact("Low fact", "general", [], "")

        engine.update_trust(f1, 0.0)  # stays at 1.0
        engine.update_trust(f2, -0.3)  # drops to 0.7
        engine.update_trust(f3, -0.8)  # very low

        facts = engine.get_relevant_facts(limit=10)
        # Should be sorted by trust desc
        trusts = [f["trust_score"] for f in facts]
        assert trusts == sorted(trusts, reverse=True)

    def test_update_trust_clamps(self, engine):
        fid = engine.add_fact("Clamp test")
        result = engine.update_trust(fid, 2.0)  # try to exceed 1.0
        assert result is not None
        assert result["trust_score"] == 1.0

        result = engine.update_trust(fid, -3.0)  # try to go below 0.0
        assert result is not None
        assert result["trust_score"] == 0.0

    def test_update_trust_nonexistent(self, engine):
        result = engine.update_trust(99999, 0.1)
        assert result is None

    def test_export_import_roundtrip(self, engine):
        engine.add_fact("Revenue 20%", "finance", ["revenue"], "s1")
        engine.add_fact("Team doubled", "people", ["team"], "s2")

        dump = engine.export_facts()
        assert len(dump) == 2
        assert "content" in dump[0]
        assert "trust_score" in dump[0]

        # Create a fresh engine and import
        uri2 = f"file:mem_import_{uuid.uuid4().hex}?mode=memory&cache=shared"
        eng2 = MemoryEngine(uri2)
        try:
            count = eng2.import_facts(dump)
            assert count == 2

            facts2 = eng2.search_facts("")
            assert len(facts2) == 2
        finally:
            _mem_cache.pop(eng2._db_path, None)

    def test_import_updates_existing_key(self, engine):
        engine.add_fact("Original", "cat1", [], "")
        dump = engine.export_facts()
        # Modify content in dump
        dump[0]["content"] = "Updated content"
        dump[0]["trust_score"] = 0.5

        engine.import_facts(dump)
        results = engine.search_facts("Updated")
        assert len(results) == 1
        assert results[0]["trust_score"] == 0.5

    def test_search_case_insensitive(self, engine):
        engine.add_fact("REVENUE GROWTH", "finance", [], "")
        results = engine.search_facts("revenue")
        assert len(results) == 1
        assert results[0]["content"] == "REVENUE GROWTH"


# ─── GraphEngine Tests ──────────────────────────────────────────────


class TestGraphEngine:
    """Test the GraphEngine entity/relationship operations."""

    @pytest.fixture
    def engine(self):
        uri = f"file:graph_test_{uuid.uuid4().hex}?mode=memory&cache=shared"
        eng = GraphEngine(uri)
        yield eng
        _graph_cache.pop(eng._db_path, None)

    def test_add_entity_returns_id(self, engine):
        eid = engine.add_entity("Acme Corp", "company", {"industry": "Tech"})
        assert isinstance(eid, int)
        assert eid > 0

    def test_add_entity_no_properties(self, engine):
        eid = engine.add_entity("Jane Doe", "person")
        assert isinstance(eid, int)

    def test_add_relationship(self, engine):
        e1 = engine.add_entity("Acme", "company")
        e2 = engine.add_entity("John", "person")
        rid = engine.add_relationship(e1, e2, "employee_of", weight=0.8)
        assert isinstance(rid, int)
        assert rid > 0

    def test_get_related_entities_depth_1(self, engine):
        e1 = engine.add_entity("Acme", "company")
        e2 = engine.add_entity("John", "person")
        e3 = engine.add_entity("Jane", "person")
        engine.add_relationship(e1, e2, "employee_of")
        engine.add_relationship(e1, e3, "employee_of")

        related = engine.get_related_entities(e1, depth=1)
        # Root + 2 direct neighbours = 3
        assert len(related) == 3
        assert related[0]["distance"] == 0  # root
        assert related[1]["distance"] == 1

    def test_get_related_entities_depth_2(self, engine):
        """A -> B -> C. Depth 2 from A should reach C."""
        a = engine.add_entity("A", "node")
        b = engine.add_entity("B", "node")
        c = engine.add_entity("C", "node")
        engine.add_relationship(a, b, "connects")
        engine.add_relationship(b, c, "connects")

        related = engine.get_related_entities(a, depth=2)
        # A (0), B (1), C (2) = 3
        assert len(related) == 3
        distances = {r["entity"]["name"]: r["distance"] for r in related}
        assert distances["A"] == 0
        assert distances["B"] == 1
        assert distances["C"] == 2

    def test_get_related_entities_reverse_direction(self, engine):
        """B -> A. From A, depth=1 should find B via incoming edge."""
        a = engine.add_entity("A", "node")
        b = engine.add_entity("B", "node")
        engine.add_relationship(b, a, "connects")

        related = engine.get_related_entities(a, depth=1)
        assert len(related) == 2  # A + B
        assert any(r["entity"]["name"] == "B" for r in related)

    def test_resolve_entities_merge(self, engine):
        e1 = engine.add_entity("Acme Corp", "company", {"revenue": "10M"})
        e2 = engine.add_entity("Acme", "company", {"employees": 50})
        e3 = engine.add_entity("John", "person")
        engine.add_relationship(e2, e3, "employee_of")

        survivor = engine.resolve_entities("Acme Corp", "Acme")
        assert survivor == e1

        # e2 should be gone
        conn = engine._conn()
        row = conn.execute("SELECT id FROM entities WHERE name = 'Acme'").fetchone()
        assert row is None

        # Relationship should now point to e1
        rels = conn.execute(
            "SELECT * FROM relationships WHERE source_entity_id = ?", (e1,)
        ).fetchall()
        assert len(rels) == 1
        assert rels[0]["target_entity_id"] == e3

    def test_resolve_entities_same_name(self, engine):
        eid = engine.add_entity("Acme", "company")
        result = engine.resolve_entities("Acme", "Acme")
        assert result == eid

    def test_resolve_entities_not_found(self, engine):
        engine.add_entity("Acme", "company")
        result = engine.resolve_entities("Acme", "Ghost")
        assert result is None

    def test_get_entity_facts(self, engine):
        eid = engine.add_entity("Acme Corp", "company")

        # Add facts directly through the shared connection
        conn = engine._conn()
        conn.execute(
            "INSERT INTO memory_facts (key, value) VALUES (?, ?)",
            ("fact:1", json.dumps({
                "content": "Acme Corp grew 20%",
                "category": "finance",
                "tags": [],
                "source": "",
                "trust_score": 1.0,
            })),
        )
        conn.execute(
            "INSERT INTO memory_facts (key, value) VALUES (?, ?)",
            ("fact:2", json.dumps({
                "content": "Unrelated fact about other company",
                "category": "general",
                "tags": [],
                "source": "",
                "trust_score": 1.0,
            })),
        )
        conn.commit()

        facts = engine.get_entity_facts(eid)
        assert len(facts) == 1  # only the Acme Corp fact
        assert "Acme Corp grew" in facts[0]["content"]

        # Verify unrelated fact is NOT returned
        assert not any("Unrelated" in f["content"] for f in facts)

    def test_relationship_weight_stored(self, engine):
        e1 = engine.add_entity("A", "node")
        e2 = engine.add_entity("B", "node")
        engine.add_relationship(e1, e2, "links", weight=0.6)

        related = engine.get_related_entities(e1, depth=1)
        edge = related[1]["relationship"]
        assert edge["weight"] == 0.6

    def test_graph_no_cycles_infinite(self, engine):
        """Ensure BFS doesn't loop on cycles."""
        a = engine.add_entity("A", "node")
        b = engine.add_entity("B", "node")
        engine.add_relationship(a, b, "connects")
        engine.add_relationship(b, a, "connects")  # cycle

        related = engine.get_related_entities(a, depth=3)
        # Should only have A and B, no duplicates
        assert len(related) == 2


# ─── MemoryHandler (API) Tests ─────────────────────────────────────


class TestMemoryHandler:
    """Test the MemoryHandler API layer."""

    @pytest.fixture
    def handler(self):
        uri = f"file:handler_test_{uuid.uuid4().hex}?mode=memory&cache=shared"
        h = MemoryHandler(uri)
        yield h
        _mem_cache.pop(h.memory._db_path, None)
        _graph_cache.pop(h.graph._db_path, None)

    def test_create_and_list_facts(self, handler):
        result = handler.create_fact({
            "content": "Revenue grew 20%",
            "category": "finance",
            "tags": ["revenue"],
            "source": "test",
        })
        assert result["status"] == "ok"
        fid = result["data"]["id"]
        assert isinstance(fid, int)

        # List all
        listing = handler.list_facts()
        assert listing["status"] == "ok"
        assert len(listing["data"]) == 1
        assert listing["data"][0]["content"] == "Revenue grew 20%"

    def test_create_fact_no_content(self, handler):
        result = handler.create_fact({"category": "finance"})
        assert result["status"] == "error"
        assert "content is required" in result["message"]

    def test_list_facts_with_category_filter(self, handler):
        handler.create_fact({"content": "Fact 1", "category": "finance"})
        handler.create_fact({"content": "Fact 2", "category": "people"})

        result = handler.list_facts(category="finance")
        assert len(result["data"]) == 1
        assert result["data"][0]["category"] == "finance"

    def test_context_endpoint(self, handler):
        handler.create_fact({"content": "Important context", "category": "strategy"})
        result = handler.context()
        assert result["status"] == "ok"
        assert len(result["data"]) >= 1

    def test_create_entity(self, handler):
        result = handler.create_entity({
            "name": "Acme Corp",
            "type": "company",
            "properties": {"industry": "Tech"},
        })
        assert result["status"] == "ok"
        assert result["data"]["id"] > 0

    def test_create_entity_no_name(self, handler):
        result = handler.create_entity({"type": "company"})
        assert result["status"] == "error"

    def test_create_relationship(self, handler):
        e1 = handler.create_entity({"name": "A", "type": "node"})
        e2 = handler.create_entity({"name": "B", "type": "node"})

        result = handler.create_relationship({
            "source_id": e1["data"]["id"],
            "target_id": e2["data"]["id"],
            "type": "connects",
            "weight": 0.5,
        })
        assert result["status"] == "ok"
        assert result["data"]["id"] > 0

    def test_create_relationship_missing_ids(self, handler):
        result = handler.create_relationship({"type": "connects"})
        assert result["status"] == "error"

    def test_get_entity_with_relationships(self, handler):
        result_acme = handler.create_entity({"name": "Acme", "type": "company"})
        eid = result_acme["data"]["id"]

        result_john = handler.create_entity({"name": "John", "type": "person"})
        john_id = result_john["data"]["id"]

        handler.create_relationship({
            "source_id": eid,
            "target_id": john_id,
            "type": "employee_of",
        })

        result = handler.get_entity(eid)
        assert result["status"] == "ok"
        assert result["data"]["entity"]["name"] == "Acme"
        assert len(result["data"]["related"]) == 2  # root + neighbour

    def test_get_entity_not_found(self, handler):
        result = handler.get_entity(99999)
        assert result["status"] == "error"


# ─── Route Registration Tests ──────────────────────────────────────


class TestMemoryRoutes:
    """Verify routes are registered correctly on the router."""

    def test_context_route_registered(self):
        from escala_server.server import _build_router

        router = _build_router()
        handler, params = router.dispatch("GET", "/api/memory/context")
        assert handler is not None

    def test_facts_list_route_registered(self):
        from escala_server.server import _build_router

        router = _build_router()
        handler, params = router.dispatch("GET", "/api/memory/facts")
        assert handler is not None

    def test_facts_create_route_registered(self):
        from escala_server.server import _build_router

        router = _build_router()
        handler, params = router.dispatch("POST", "/api/memory/facts")
        assert handler is not None

    def test_entity_route_registered(self):
        from escala_server.server import _build_router

        router = _build_router()
        handler, params = router.dispatch("GET", "/api/memory/graph/1")
        assert handler is not None
        assert params.get("entity_id") == "1"

    def test_entity_create_route_registered(self):
        from escala_server.server import _build_router

        router = _build_router()
        handler, params = router.dispatch("POST", "/api/memory/entities")
        assert handler is not None

    def test_relationship_create_route_registered(self):
        from escala_server.server import _build_router

        router = _build_router()
        handler, params = router.dispatch("POST", "/api/memory/relationships")
        assert handler is not None
