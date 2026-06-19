from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/voice_of_customer"
SPEC = importlib.util.spec_from_file_location(
    "voice_of_customer_validator",
    ROOT / "validators/voice_of_customer.py",
)
assert SPEC is not None
assert SPEC.loader is not None
VOICE_OF_CUSTOMER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VOICE_OF_CUSTOMER)

load_evidence_records = VOICE_OF_CUSTOMER.load_evidence_records
map_evidence_to_strategy = VOICE_OF_CUSTOMER.map_evidence_to_strategy


def test_approved_evidence_maps_to_cited_strategy_inputs() -> None:
    records = load_evidence_records(FIXTURES / "strategy_mapping.yaml")

    result = map_evidence_to_strategy(records)

    categories = {item.category for item in result.inputs}
    assert "customer_segment" in categories
    assert "desired_outcome" in categories
    assert "promised_value" in categories
    assert "proof" in categories
    assert all(item.evidence_ids for item in result.inputs)
    assert any(
        item.category == "promised_value" and item.evidence_ids == ["voc-map-001"]
        for item in result.inputs
    )


def test_draft_and_fixture_evidence_do_not_create_strategy_claims() -> None:
    records = load_evidence_records(FIXTURES / "strategy_mapping.yaml")

    result = map_evidence_to_strategy(records)

    cited_ids = {
        evidence_id for item in result.inputs for evidence_id in item.evidence_ids
    }
    assert "voc-map-003" not in cited_ids


def test_missing_categories_create_explicit_gaps() -> None:
    records = load_evidence_records(FIXTURES / "valid.yaml")

    result = map_evidence_to_strategy(records)

    gap_categories = {gap.category for gap in result.gaps}
    assert "objection" in gap_categories
    assert "proof" in gap_categories
    assert all("No approved evidence" in gap.reason for gap in result.gaps)


def test_contradictory_evidence_remains_visible() -> None:
    records = load_evidence_records(FIXTURES / "strategy_mapping.yaml")

    result = map_evidence_to_strategy(records)

    assert result.contradictions == [
        {
            "category": "objection",
            "positive_evidence_ids": ["voc-map-001", "voc-map-002"],
            "negative_evidence_ids": ["voc-map-004"],
        }
    ]
