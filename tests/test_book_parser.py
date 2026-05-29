#!/usr/bin/env python3
"""
Tests for the book parser.
Validates that the parser:
  - Produces valid JSON with expected structure
  - Extracts at least 30 entities
  - Extracts at least 50 relationships
  - Contains specific known entities from Scaling Up
  - Builds a valid chapter tree
"""

import json
import os
import pytest
import sys
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from escala_server.data.book_parser import parse_book

OUTPUT_FILE = PROJECT_ROOT / "escala_server" / "data" / "book-knowledge.json"


class TestBookParser:
    """Test suite for the Book Parser."""

    @pytest.fixture(scope="class")
    def result(self):
        """Parse the book once and reuse for all tests."""
        data = parse_book()
        # Also write it so the output file is always up to date
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return data

    # ── Structure tests ──────────────────────────────────────────────────

    def test_produces_valid_json_structure(self, result):
        """Result must have meta, chapters, entities, and relationships keys."""
        assert isinstance(result, dict)
        assert "meta" in result
        assert "chapters" in result
        assert "entities" in result
        assert "relationships" in result

    def test_meta_has_required_fields(self, result):
        """Meta must contain source, entities_count, relationships_count."""
        meta = result["meta"]
        assert "source" in meta
        assert meta["source"] == "scaling_up_llamaparse.md"
        assert "entities_count" in meta
        assert "relationships_count" in meta
        assert meta["entities_count"] > 0
        assert meta["relationships_count"] > 0

    # ── Entity count tests ───────────────────────────────────────────────

    def test_minimum_30_entities(self, result):
        """Must extract at least 30 entities."""
        assert len(result["entities"]) >= 30, (
            f"Expected >= 30 entities, got {len(result['entities'])}"
        )

    def test_minimum_50_relationships(self, result):
        """Must extract at least 50 relationships."""
        assert len(result["relationships"]) >= 50, (
            f"Expected >= 50 relationships, got {len(result['relationships'])}"
        )

    # ── Entity structure tests ───────────────────────────────────────────

    def test_entities_have_required_fields(self, result):
        """Each entity must have id, name, type, description, keywords, line_refs, chapter_ids."""
        for entity in result["entities"]:
            assert "id" in entity, f"Entity missing 'id': {entity}"
            assert "name" in entity, f"Entity {entity.get('id')} missing 'name'"
            assert "type" in entity, f"Entity {entity.get('id')} missing 'type'"
            assert entity["type"] in ("concept", "tool", "metric", "habit", "principle", "decision"), (
                f"Entity {entity.get('id')} has invalid type: {entity['type']}"
            )
            assert "description" in entity, f"Entity {entity['id']} missing 'description'"
            assert "keywords" in entity, f"Entity {entity['id']} missing 'keywords'"
            assert isinstance(entity["keywords"], list)
            assert "line_refs" in entity, f"Entity {entity['id']} missing 'line_refs'"
            assert isinstance(entity["line_refs"], list)
            assert "chapter_ids" in entity, f"Entity {entity['id']} missing 'chapter_ids'"
            assert isinstance(entity["chapter_ids"], list)

    # ── Specific entity tests ────────────────────────────────────────────

    def test_entity_power_of_one_exists(self, result):
        """Power of One must be extracted."""
        entity = _find_entity(result, "power-of-one")
        assert entity is not None, "Power of One entity not found"
        assert entity["type"] == "concept"
        assert len(entity["description"]) > 20

    def test_entity_rockefeller_habits_exists(self, result):
        """Rockefeller Habits must be extracted."""
        entity = _find_entity(result, "rockefeller-habits")
        assert entity is not None, "Rockefeller Habits entity not found"
        assert entity["type"] == "concept"

    def test_entity_face_exists(self, result):
        """FACe must be extracted."""
        entity = _find_entity(result, "face")
        assert entity is not None, "FACe entity not found"
        assert entity["type"] == "tool"

    def test_entity_pace_exists(self, result):
        """PACe must be extracted."""
        entity = _find_entity(result, "pace")
        assert entity is not None, "PACe entity not found"

    def test_entity_opsps_exists(self, result):
        """One-Page Strategic Plan must be extracted."""
        entity = _find_entity(result, "one-page-strategic-plan")
        assert entity is not None, "OPSP entity not found"

    def test_entity_7_strata_exists(self, result):
        """7 Strata of Strategy must be extracted."""
        entity = _find_entity(result, "7-strata-of-strategy")
        assert entity is not None, "7 Strata of Strategy entity not found"

    def test_entity_daily_huddle_exists(self, result):
        """Daily Huddle must be extracted."""
        entity = _find_entity(result, "daily-huddle")
        assert entity is not None, "Daily Huddle entity not found"
        assert entity["type"] == "habit"

    def test_entity_ccc_exists(self, result):
        """Cash Conversion Cycle must be extracted."""
        entity = _find_entity(result, "cash-conversion-cycle")
        assert entity is not None, "CCC entity not found"

    def test_entity_bhag_exists(self, result):
        """BHAG must be extracted."""
        entity = _find_entity(result, "bhag")
        assert entity is not None, "BHAG entity not found"

    def test_entity_topgrading_exists(self, result):
        """Topgrading must be extracted."""
        entity = _find_entity(result, "topgrading")
        assert entity is not None, "Topgrading entity not found"

    def test_entity_core_values_exists(self, result):
        """Core Values must be extracted."""
        entity = _find_entity(result, "core-values")
        assert entity is not None, "Core Values entity not found"

    def test_entity_net_promoter_exists(self, result):
        """Net Promoter Score must be extracted."""
        entity = _find_entity(result, "net-promoter-score")
        assert entity is not None, "NPS entity not found"

    def test_entity_profit_per_x_exists(self, result):
        """Profit per X must be extracted."""
        entity = _find_entity(result, "profit-per-x")
        assert entity is not None, "Profit per X entity not found"

    def test_entities_have_line_refs(self, result):
        """Most entities should have at least one line reference."""
        entities_with_refs = [e for e in result["entities"] if len(e["line_refs"]) > 0]
        assert len(entities_with_refs) > len(result["entities"]) * 0.5, (
            f"Only {len(entities_with_refs)}/{len(result['entities'])} entities have line refs"
        )

    # ── Relationship tests ───────────────────────────────────────────────

    def test_relationships_have_required_fields(self, result):
        """Each relationship must have source, target, type, weight."""
        for rel in result["relationships"]:
            assert "source" in rel, f"Relationship missing 'source'"
            assert "target" in rel, f"Relationship missing 'target'"
            assert "type" in rel, f"Relationship missing 'type'"
            assert "weight" in rel, f"Relationship missing 'weight'"
            assert 0 < rel["weight"] <= 1.0, f"Invalid weight: {rel['weight']}"

    def test_specific_relationships_exist(self, result):
        """Verify key expected relationships."""
        rel_pairs = {(r["source"], r["target"], r["type"]) for r in result["relationships"]}

        expected = [
            ("daily-huddle", "rockefeller-habits", "contained_in"),
            ("face", "people-decision", "is_tool_for"),
            ("power-of-one", "cash-decision", "belongs_to"),
            ("ccc-days", "cash-conversion-cycle", "measures"),
        ]

        for src, tgt, rtype in expected:
            assert (src, tgt, rtype) in rel_pairs, (
                f"Expected relationship ({src} → {tgt}, {rtype}) not found"
            )

    # ── Chapter tests ────────────────────────────────────────────────────

    def test_chapters_array_exists(self, result):
        """Chapters array must exist and contain entries."""
        assert len(result["chapters"]) > 0, "Chapters array is empty"

    def test_chapters_have_correct_structure(self, result):
        """Each chapter must have id, title, level, line_start, line_end, slug."""
        for chapter in result["chapters"]:
            assert "id" in chapter, f"Chapter missing 'id'"
            assert "title" in chapter, f"Chapter {chapter.get('id')} missing 'title'"
            assert "level" in chapter, f"Chapter {chapter.get('id')} missing 'level'"
            assert chapter["level"] in (1, 2, 3), f"Invalid level: {chapter['level']}"
            assert "line_start" in chapter, f"Chapter {chapter['id']} missing 'line_start'"
            assert "line_end" in chapter, f"Chapter {chapter['id']} missing 'line_end'"
            assert chapter["line_end"] >= chapter["line_start"]
            assert "slug" in chapter, f"Chapter {chapter['id']} missing 'slug'"

    def test_chapters_are_sequential(self, result):
        """Chapter IDs should be sequential starting from 1."""
        ids = [c["id"] for c in result["chapters"]]
        assert ids[0] == 1
        for i in range(1, len(ids)):
            assert ids[i] == ids[i - 1] + 1, f"Non-sequential chapter IDs: {ids[i-1]} → {ids[i]}"

    # ── Cross-reference integrity tests ──────────────────────────────────

    def test_relationship_sources_exist(self, result):
        """All relationship sources should reference existing entities."""
        entity_ids = {e["id"] for e in result["entities"]}
        for rel in result["relationships"]:
            assert rel["source"] in entity_ids, (
                f"Relationship source '{rel['source']}' not found in entities"
            )

    def test_relationship_targets_exist(self, result):
        """All relationship targets should reference existing entities."""
        entity_ids = {e["id"] for e in result["entities"]}
        for rel in result["relationships"]:
            assert rel["target"] in entity_ids, (
                f"Relationship target '{rel['target']}' not found in entities"
            )

    def test_entity_chapter_ids_are_valid(self, result):
        """Entity chapter_ids should reference valid chapter IDs."""
        chapter_ids = {c["id"] for c in result["chapters"]}
        for entity in result["entities"]:
            for cid in entity["chapter_ids"]:
                assert cid in chapter_ids, (
                    f"Entity '{entity['id']}' references non-existent chapter {cid}"
                )

    def test_entity_types_present(self, result):
        """All entity types should be present."""
        types_found = {e["type"] for e in result["entities"]}
        for expected_type in ("concept", "tool", "metric", "habit", "principle", "decision"):
            assert expected_type in types_found, f"Entity type '{expected_type}' not found"

    # ── Output file tests ────────────────────────────────────────────────

    def test_output_file_exists(self):
        """The output JSON file should exist."""
        assert OUTPUT_FILE.exists(), f"Output file {OUTPUT_FILE} not found"

    def test_output_file_is_valid_json(self):
        """The output file should contain valid JSON."""
        data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        assert "meta" in data
        assert "chapters" in data
        assert "entities" in data
        assert "relationships" in data


# ── Helpers ─────────────────────────────────────────────────────────────────

def _find_entity(result: dict, entity_id: str) -> dict | None:
    """Find an entity by ID."""
    for e in result["entities"]:
        if e["id"] == entity_id:
            return e
    return None


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
