"""Integrity tests for E19 — Book Knowledge Graph coverage.

Verifies that the knowledge graph covers the full book structure.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = PROJECT_ROOT / "escala_server" / "data" / "book-knowledge.json"


def _get_data():
    with open(JSON_PATH) as f:
        return json.load(f)


class TestBookCoverage:
    """Verify the knowledge graph covers all key book sections."""

    def test_people_entities_exist(self):
        data = _get_data()
        names = [e["name"].lower() for e in data["entities"]]
        for name in ["face", "pace", "oppp", "topgrading", "core values"]:
            assert any(name in n for n in names), f"Missing PEOPLE entity: {name}"

    def test_strategy_entities_exist(self):
        data = _get_data()
        names = [e["name"].lower() for e in data["entities"]]
        for name in ["brand promise", "core customers", "bhag", "7 strata"]:
            assert any(name in n for n in names), f"Missing STRATEGY entity: {name}"

    def test_execution_entities_exist(self):
        data = _get_data()
        names = [e["name"].lower() for e in data["entities"]]
        for name in [
            "daily huddle",
            "weekly meeting",
            "quarterly planning",
            "rockefeller habits",
        ]:
            assert any(name in n for n in names), f"Missing EXECUTION entity: {name}"

    def test_cash_entities_exist(self):
        data = _get_data()
        names = [e["name"].lower() for e in data["entities"]]
        for name in ["power of one", "cash conversion cycle", "gross margin"]:
            assert any(name in n for n in names), f"Missing CASH entity: {name}"

    def test_decision_entities_exist(self):
        data = _get_data()
        types = {e["type"] for e in data["entities"]}
        assert "decision" in types, "No decision-type entities found"

    def test_minimum_entities(self):
        data = _get_data()
        count = len(data["entities"])
        assert count >= 30, f"Only {count} entities, need 30+"

    def test_minimum_relationships(self):
        data = _get_data()
        count = len(data["relationships"])
        assert count >= 50, f"Only {count} relationships, need 50+"

    def test_all_entities_have_required_fields(self):
        data = _get_data()
        for e in data["entities"]:
            assert e.get("id"), f"Entity missing id: {e}"
            assert e.get("name"), f"Entity missing name: {e}"
            assert e.get("type"), f"Entity {e['name']} missing type"
            assert e.get("description"), f"Entity {e['name']} missing description"

    def test_all_relationships_are_consistent(self):
        data = _get_data()
        entity_ids = {e["id"].lower() for e in data["entities"]}
        for rel in data["relationships"]:
            src = rel["source"].lower()
            tgt = rel["target"].lower()
            assert src in entity_ids, f"Relationship source '{src}' not in entities"
            assert tgt in entity_ids, f"Relationship target '{tgt}' not in entities"

    def test_chapters_are_parsed(self):
        data = _get_data()
        assert len(data["chapters"]) >= 100, f"Only {len(data['chapters'])} chapters"
        for ch in data["chapters"][:5]:
            assert ch.get("id"), "Chapter missing id"
            assert ch.get("title"), "Chapter missing title"
            assert ch.get("level") in [1, 2, 3], "Chapter has invalid level"

    def test_json_file_exists_and_valid(self):
        assert JSON_PATH.exists(), "book-knowledge.json not found"
        data = _get_data()
        assert "entities" in data
        assert "relationships" in data
        assert "chapters" in data
        assert "meta" in data

    def test_meta_source_correct(self):
        data = _get_data()
        assert "scaling_up" in data["meta"].get("source", "").lower()
