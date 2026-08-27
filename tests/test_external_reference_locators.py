from __future__ import annotations

import pytest

from validators.domain_coverage import DomainInventory
from validators.external_reference_locators import (
    ExternalReferenceLocator,
    ExternalReferenceLocatorReceipt,
    validate_external_reference_locators,
)


def _inventory() -> DomainInventory:
    return DomainInventory.model_validate(
        {
            "schema_version": 1,
            "source_id": "source.example",
            "domain": "execution",
            "range": {"line_start": 1, "line_end": 1},
            "manifest_sha256": "0" * 64,
            "unit_count": 1,
            "units": [
                {
                    "source_id": "source.example",
                    "unit_id": "source.example.u0001",
                    "line_start": 1,
                    "line_end": 1,
                    "content_type": "section",
                    "sha256": "1" * 64,
                    "domain": "execution",
                    "classification_status": "handoff",
                    "exclusion_reason": None,
                }
            ],
        }
    )


def _receipt() -> ExternalReferenceLocatorReceipt:
    return ExternalReferenceLocatorReceipt.model_validate(
        {
            "schema_version": 1,
            "domain": "execution",
            "status": "pending-independent-review",
            "rule": "External references remain source-bounded until separately reviewed.",
            "locators": [{"unit_id": "source.example.u0001", "references": ["Lean"]}],
        }
    )


def test_external_locator_matches_observed_source_scan() -> None:
    validate_external_reference_locators(
        _receipt(), _inventory(), {"source.example.u0001": {"Lean"}}
    )


def test_external_locator_rejects_unlisted_reference() -> None:
    with pytest.raises(ValueError, match="differs"):
        validate_external_reference_locators(_receipt(), _inventory(), {})


def test_external_locator_rejects_unknown_unit() -> None:
    unsafe = _receipt().model_copy(
        update={
            "locators": [
                ExternalReferenceLocator(
                    unit_id="source.example.u0002", references=["Lean"]
                )
            ]
        }
    )
    with pytest.raises(ValueError, match="unknown inventory"):
        validate_external_reference_locators(unsafe, _inventory(), {})
