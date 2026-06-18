"""Tests for the Knowledge API (S19.4).

Validates the KnowledgeHandler search, get_entity, and get_context methods
as well as route registration in the server.
"""

import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "escala_server"))

from escala_server.data.knowledge_ingester import KnowledgeIngester
from escala_server.knowledge_handler import KnowledgeHandler

JSON_PATH = PROJECT_ROOT / "escala_server" / "data" / "book-knowledge.json"


class TestKnowledgeSearch:
    """Test the search() method of KnowledgeHandler."""

    @pytest.fixture
    def handler(self):
        """Create a fresh in-memory handler with ingested knowledge."""
        uri = f"file:search_test_{uuid.uuid4().hex}?mode=memory&cache=shared"
        ingester = KnowledgeIngester(db_path=uri)
        ingester.ingest_all(json_path=str(JSON_PATH))
        handler = KnowledgeHandler(ingester.graph_engine)
        yield handler
        # Clean up connections
        from escala_server.graph_engine import _conn_cache as _graph_cache
        from escala_server.memory_engine import _conn_cache as _mem_cache

        _graph_cache.pop(ingester.graph_engine._db_path, None)
        _mem_cache.pop(ingester.memory_engine._db_path, None)

    def test_search_returns_results_for_cash(self, handler):
        """Search for 'cash' should return multiple matching entities."""
        result = handler.search("cash")
        assert result["status"] == "ok"
        assert result["count"] > 0
        entities = result["entities"]
        # Should include Cash Conversion Cycle at minimum
        names = [e["name"] for e in entities]
        assert "Cash Conversion Cycle (CCC)" in names

    def test_search_returns_results_for_power(self, handler):
        """Search for 'power' should find Power of One."""
        result = handler.search("power")
        assert result["status"] == "ok"
        assert result["count"] > 0
        entities = result["entities"]
        names = [e["name"] for e in entities]
        assert "Power of One" in names

    def test_search_returns_results_for_rockefeller(self, handler):
        """Search for 'rockefeller' should find Rockefeller Habits."""
        result = handler.search("rockefeller")
        assert result["status"] == "ok"
        assert result["count"] > 0
        entities = result["entities"]
        names = [e["name"] for e in entities]
        assert "Rockefeller Habits" in names

    def test_search_with_type_filter(self, handler):
        """Search with a type filter should restrict results to that type."""
        result = handler.search("", type_filter="tool")
        assert result["status"] == "ok"
        assert result["count"] >= 1
        for entity in result["entities"]:
            assert entity["type"] == "tool"

    def test_search_type_filter_metric(self, handler):
        """Search with type=metric should find only metric entities."""
        result = handler.search("", type_filter="metric")
        assert result["status"] == "ok"
        for entity in result["entities"]:
            assert entity["type"] == "metric"

    def test_search_returns_empty_for_non_matching_queries(self, handler):
        """Search for a nonsense term should return empty results."""
        result = handler.search("xyznonexistent12345")
        assert result["status"] == "ok"
        assert result["count"] == 0
        assert result["entities"] == []

    def test_search_case_insensitive(self, handler):
        """Search should be case-insensitive."""
        lower = handler.search("cash")
        upper = handler.search("CASH")
        mixed = handler.search("CaSh")
        assert lower["count"] == upper["count"] == mixed["count"]


class TestKnowledgeGetEntity:
    """Test the get_entity() method of KnowledgeHandler."""

    @pytest.fixture
    def handler(self):
        """Create a fresh in-memory handler with ingested knowledge."""
        uri = f"file:entity_test_{uuid.uuid4().hex}?mode=memory&cache=shared"
        ingester = KnowledgeIngester(db_path=uri)
        ingester.ingest_all(json_path=str(JSON_PATH))
        handler = KnowledgeHandler(ingester.graph_engine)
        yield handler
        from escala_server.graph_engine import _conn_cache as _graph_cache
        from escala_server.memory_engine import _conn_cache as _mem_cache

        _graph_cache.pop(ingester.graph_engine._db_path, None)
        _mem_cache.pop(ingester.memory_engine._db_path, None)

    def test_get_entity_returns_properties_for_power_of_one(self, handler):
        """get_entity with 'power-of-one' slug should return full entity."""
        result = handler.get_entity("power-of-one")
        assert result["status"] == "ok"
        entity = result["entity"]
        assert entity["name"] == "Power of One"
        assert "description" in entity["properties"]
        assert "keywords" in entity["properties"]
        assert len(entity["properties"]["description"]) > 0

    def test_get_entity_with_exact_name(self, handler):
        """get_entity with exact name should work."""
        result = handler.get_entity("Power of One")
        assert result["status"] == "ok"
        assert result["entity"]["name"] == "Power of One"

    def test_get_entity_includes_relationships(self, handler):
        """get_entity should include relationship info."""
        result = handler.get_entity("Power of One")
        assert result["status"] == "ok"
        assert "relationships" in result
        relationships = result["relationships"]
        assert "outgoing" in relationships
        assert "incoming" in relationships
        # Power of One has relationships (connected to CCC, execution-decision)
        total_rels = len(relationships["outgoing"]) + len(relationships["incoming"])
        assert total_rels > 0

    def test_get_entity_includes_related_names(self, handler):
        """get_entity should include related entity names."""
        result = handler.get_entity("Power of One")
        assert result["status"] == "ok"
        assert "related_names" in result
        assert isinstance(result["related_names"], list)

    def test_get_entity_returns_404_for_nonexistent_entity(self, handler):
        """get_entity with unknown name should return error."""
        result = handler.get_entity("Completely Nonexistent Entity")
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()


class TestKnowledgeContext:
    """Test the get_context() method of KnowledgeHandler."""

    @pytest.fixture
    def handler(self):
        """Create a fresh in-memory handler with ingested knowledge."""
        uri = f"file:context_test_{uuid.uuid4().hex}?mode=memory&cache=shared"
        ingester = KnowledgeIngester(db_path=uri)
        ingester.ingest_all(json_path=str(JSON_PATH))
        handler = KnowledgeHandler(ingester.graph_engine)
        yield handler
        from escala_server.graph_engine import _conn_cache as _graph_cache
        from escala_server.memory_engine import _conn_cache as _mem_cache

        _graph_cache.pop(ingester.graph_engine._db_path, None)
        _mem_cache.pop(ingester.memory_engine._db_path, None)

    def test_context_returns_relevant_entities_for_category_cash(self, handler):
        """get_context with category='cash' should return cash-related entities."""
        result = handler.get_context(category="cash")
        assert result["status"] == "ok"
        assert "entities" in result
        assert len(result["entities"]) > 0
        # Should contain cash-related entities
        names = [e["name"] for e in result["entities"]]
        assert "Cash Conversion Cycle (CCC)" in names

    def test_context_returns_relevant_entities_for_category_strategy(self, handler):
        """get_context with category='strategy' should return strategy entities."""
        result = handler.get_context(category="strategy")
        assert result["status"] == "ok"
        assert len(result["entities"]) > 0

    def test_context_returns_relevant_entities_for_tool(self, handler):
        """get_context with a tool name should return tool and its relations."""
        result = handler.get_context(tool="FACe (Function Accountability Chart)")
        assert result["status"] == "ok"
        assert "tool" in result
        assert result["tool"]["name"] == "FACe (Function Accountability Chart)"
        assert len(result["entities"]) > 0

    def test_context_with_both_tool_and_category(self, handler):
        """get_context with both tool and category should return intersection."""
        result = handler.get_context(
            tool="FACe (Function Accountability Chart)",
            category="people",
        )
        assert result["status"] == "ok"
        assert "tool" in result
        assert "category" in result
        assert result["category"] == "people"

    def test_context_includes_principles_and_habits(self, handler):
        """get_context should include principles and habits lists."""
        result = handler.get_context(category="execution")
        assert result["status"] == "ok"
        assert "principles" in result
        assert "habits" in result
        assert isinstance(result["principles"], list)
        assert isinstance(result["habits"], list)

    def test_context_returns_error_for_nonexistent_tool(self, handler):
        """get_context with unknown tool should return error."""
        result = handler.get_context(tool="Nonexistent Tool")
        assert result["status"] == "error"

    def test_context_no_args_returns_error(self, handler):
        """get_context with no arguments should return error."""
        result = handler.get_context()
        assert result["status"] == "error"


class TestKnowledgeRoutes:
    """Test route registration in the server router."""

    def test_search_route_registered(self):
        """Verify /api/knowledge/search route is registered."""
        from escala_server.server import _build_router

        router = _build_router()
        handler_fn, params = router.dispatch("GET", "/api/knowledge/search")
        assert handler_fn is not None

    def test_entity_route_registered(self):
        """Verify /api/knowledge/entity/{entity_name} route is registered."""
        from escala_server.server import _build_router

        router = _build_router()
        handler_fn, params = router.dispatch(
            "GET", "/api/knowledge/entity/power-of-one"
        )
        assert handler_fn is not None
        assert params["entity_name"] == "power-of-one"

    def test_context_route_registered(self):
        """Verify /api/knowledge/context route is registered."""
        from escala_server.server import _build_router

        router = _build_router()
        handler_fn, params = router.dispatch("GET", "/api/knowledge/context")
        assert handler_fn is not None

    def test_search_route_not_confused_with_entity(self, handler=None):
        """'/api/knowledge/search' should not match the entity route."""
        from escala_server.server import _build_router

        router = _build_router()
        # 'search' as entity_name should still match the entity route
        handler_fn, params = router.dispatch("GET", "/api/knowledge/entity/search")
        assert handler_fn is not None
        assert params["entity_name"] == "search"


class TestKnowledgeContextHTTP:
    """Route-level integration tests for /api/knowledge/context via handler."""

    @pytest.fixture
    def handler(self):
        """Create a fresh handler with ingested knowledge."""
        uri = f"file:http_test_{uuid.uuid4().hex}?mode=memory&cache=shared"
        ingester = KnowledgeIngester(db_path=uri)
        ingester.ingest_all(json_path=str(JSON_PATH))
        handler = KnowledgeHandler(ingester.graph_engine)
        yield handler
        from escala_server.graph_engine import _conn_cache as _graph_cache
        from escala_server.memory_engine import _conn_cache as _mem_cache

        _graph_cache.pop(ingester.graph_engine._db_path, None)
        _mem_cache.pop(ingester.memory_engine._db_path, None)

    def test_context_requires_params(self, handler):
        """get_context without params should return error."""
        result = handler.get_context()
        assert result["status"] == "error"

    def test_context_with_tool_returns_data(self, handler):
        """get_context with tool should return data."""
        result = handler.get_context(tool="Power of One")
        assert result["status"] == "ok"
        assert "tool" in result
        assert result["tool"]["name"] == "Power of One"
        assert len(result["entities"]) > 0

    def test_context_with_category_returns_data(self, handler):
        """get_context with category should return entities."""
        result = handler.get_context(category="cash")
        assert result["status"] == "ok"
        names = [e["name"] for e in result["entities"]]
        assert "Cash Conversion Cycle (CCC)" in names

    def test_context_with_nonexistent_tool(self, handler):
        """get_context with invalid tool should return error."""
        result = handler.get_context(tool="Nonexistent Tool")
        assert result["status"] == "error"

    def test_context_includes_principles_and_habits(self, handler):
        """Context response should include principles and habits."""
        result = handler.get_context(category="execution")
        assert result["status"] == "ok"
        assert "principles" in result
        assert "habits" in result
