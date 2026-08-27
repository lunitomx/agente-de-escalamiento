from __future__ import annotations

import json

import pytest

from scripts.check_execution_external_references import (
    load_private_terms,
    scan_reference_locators,
)
from validators.domain_coverage import DomainInventory


def _inventory() -> DomainInventory:
    return DomainInventory.model_validate(
        {
            "schema_version": 1,
            "source_id": "source.example",
            "domain": "execution",
            "range": {"line_start": 1, "line_end": 2},
            "manifest_sha256": "0" * 64,
            "unit_count": 1,
            "units": [
                {
                    "source_id": "source.example",
                    "unit_id": "source.example.u0001",
                    "line_start": 1,
                    "line_end": 2,
                    "content_type": "section",
                    "sha256": "1" * 64,
                    "domain": "execution",
                    "classification_status": "handoff",
                    "exclusion_reason": None,
                }
            ],
        }
    )


def test_private_terms_drive_exact_locator_scan_without_public_vocabulary(
    tmp_path,
) -> None:
    terms_path = tmp_path / "terms.json"
    terms_path.write_text(
        json.dumps({"Reference One": r"\bReference One\b"}), encoding="utf-8"
    )
    source = tmp_path / "source.md"
    source.write_text("Reference One appears here.\nOther text.\n", encoding="utf-8")

    assert scan_reference_locators(
        _inventory(), source, load_private_terms(terms_path)
    ) == {"source.example.u0001": {"Reference One"}}


def test_private_terms_fail_closed_when_not_a_nonempty_string_mapping(tmp_path) -> None:
    terms_path = tmp_path / "terms.json"
    terms_path.write_text(json.dumps({"Reference One": 2}), encoding="utf-8")

    with pytest.raises(ValueError, match="non-empty strings"):
        load_private_terms(terms_path)
