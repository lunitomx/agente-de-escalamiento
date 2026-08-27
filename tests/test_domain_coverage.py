from __future__ import annotations

import pytest

from validators.domain_coverage import (
    DomainCoverageMatrix,
    DomainInventory,
    validate_domain_coverage,
)
from validators.source_manifest import SourceManifest, source_manifest_hash


def _manifest() -> SourceManifest:
    return SourceManifest.model_validate(
        {
            "schema_version": 1,
            "source_id": "source.example",
            "source_sha256": "0" * 64,
            "source_line_count": 2,
            "units": [
                {
                    "source_id": "source.example",
                    "unit_id": "source.example.u0001",
                    "line_start": 1,
                    "line_end": 1,
                    "content_type": "section",
                    "sha256": "1" * 64,
                },
                {
                    "source_id": "source.example",
                    "unit_id": "source.example.u0002",
                    "line_start": 2,
                    "line_end": 2,
                    "content_type": "external_reference",
                    "sha256": "2" * 64,
                },
            ],
        }
    )


def _inventory() -> DomainInventory:
    manifest = _manifest()
    return DomainInventory.model_validate(
        {
            "schema_version": 1,
            "source_id": manifest.source_id,
            "domain": "strategy",
            "range": {"line_start": 1, "line_end": 2},
            "manifest_sha256": source_manifest_hash(manifest),
            "unit_count": 2,
            "units": [
                {
                    "source_id": unit.source_id,
                    "unit_id": unit.unit_id,
                    "line_start": unit.line_start,
                    "line_end": unit.line_end,
                    "content_type": unit.content_type,
                    "sha256": unit.sha256,
                    "domain": "strategy",
                    "classification_status": (
                        "classified-pending-independent-review"
                        if unit.content_type.value == "section"
                        else "special-source"
                    ),
                    "exclusion_reason": unit.exclusion_reason,
                }
                for unit in manifest.units
            ],
        }
    )


def _matrix() -> DomainCoverageMatrix:
    manifest = _manifest()
    return DomainCoverageMatrix.model_validate(
        {
            "schema_version": 1,
            "source_id": manifest.source_id,
            "domain": "strategy",
            "manifest_sha256": source_manifest_hash(manifest),
            "classification_counts": {"foundation-mapped": 1, "special-source": 1},
            "rows": [
                {
                    "unit_id": "source.example.u0001",
                    "disposition": "foundation-mapped",
                    "rationale": "This unit maps to a verified Strategy candidate.",
                    "node_ids": ["framework.example"],
                },
                {
                    "unit_id": "source.example.u0002",
                    "disposition": "special-source",
                    "rationale": "External material is retained as a bounded reference.",
                },
            ],
        }
    )


def test_domain_inventory_accepts_and_checks_declared_classification_counts() -> None:
    inventory = _inventory().model_copy(
        update={
            "classification_complete": True,
            "classification_counts": {
                "classified-pending-independent-review": 1,
                "special-source": 1,
            },
        }
    )
    assert (
        DomainInventory.model_validate(inventory.model_dump(mode="json")) == inventory
    )

    with pytest.raises(ValueError, match="classification counts"):
        DomainInventory.model_validate(
            inventory.model_dump(mode="json")
            | {"classification_counts": {"handoff": 2}}
        )


def test_domain_coverage_is_exhaustive_and_evidence_bound() -> None:
    validate_domain_coverage(
        _matrix(),
        _inventory(),
        _manifest(),
        {"framework.example": {"source.example.u0001"}},
    )


def test_domain_coverage_rejects_hidden_special_source() -> None:
    unsafe = _matrix().model_copy(
        update={
            "rows": [
                _matrix().rows[0],
                _matrix().rows[1].model_copy(update={"disposition": "excluded"}),
            ]
        }
    )
    with pytest.raises(ValueError, match="special-source"):
        validate_domain_coverage(
            unsafe,
            _inventory(),
            _manifest(),
            {"framework.example": {"source.example.u0001"}},
        )


def test_domain_coverage_rejects_inventory_drift() -> None:
    unsafe = _inventory().model_copy(update={"unit_count": 1})
    with pytest.raises(ValueError, match="unit count"):
        validate_domain_coverage(
            _matrix(),
            unsafe,
            _manifest(),
            {"framework.example": {"source.example.u0001"}},
        )


def test_domain_coverage_accepts_direct_foundation_mapping_status() -> None:
    inventory = _inventory().model_copy(
        update={
            "units": [
                _inventory()
                .units[0]
                .model_copy(update={"classification_status": "foundation-mapped"}),
                _inventory().units[1],
            ]
        }
    )
    validate_domain_coverage(
        _matrix(),
        inventory,
        _manifest(),
        {"framework.example": {"source.example.u0001"}},
    )


def test_domain_coverage_rejects_status_contradiction() -> None:
    unit = _inventory().units[0].model_copy(update={"classification_status": "handoff"})
    unsafe = _inventory().model_copy(update={"units": [unit, _inventory().units[1]]})
    with pytest.raises(ValueError, match="status differs"):
        validate_domain_coverage(
            _matrix(),
            unsafe,
            _manifest(),
            {"framework.example": {"source.example.u0001"}},
        )


def test_domain_coverage_rejects_count_drift() -> None:
    unsafe = _matrix().model_copy(update={"classification_counts": {"handoff": 2}})
    with pytest.raises(ValueError, match="counts differ"):
        DomainCoverageMatrix.model_validate(unsafe.model_dump(mode="json"))
