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
validate_evidence_file = VOICE_OF_CUSTOMER.validate_evidence_file


def test_valid_customer_evidence_is_strategy_usable() -> None:
    records = load_evidence_records(FIXTURES / "valid.yaml")

    assert len(records) == 1
    assert records[0].id == "voc-001"
    assert records[0].strategy_usable is True
    assert records[0].is_fixture is False


def test_missing_provenance_returns_readable_errors() -> None:
    errors = validate_evidence_file(FIXTURES / "missing_provenance.yaml")

    assert any("source_label" in error for error in errors)
    assert any("captured_at" in error for error in errors)
    assert any("context" in error for error in errors)


def test_fixture_evidence_validates_but_is_not_strategy_usable() -> None:
    records = load_evidence_records(FIXTURES / "fixture.yaml")

    assert records[0].is_fixture is True
    assert records[0].strategy_usable is False


def test_invalid_review_status_is_rejected() -> None:
    errors = validate_evidence_file(FIXTURES / "invalid_status.yaml")

    assert any("review_status" in error for error in errors)
