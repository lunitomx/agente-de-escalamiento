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
            "manifest_sha256": source_manifest_hash(manifest),
            "unit_count": 2,
            "units": [
                {
                    "source_id": unit.source_id,
                    "unit_id": unit.unit_id,
                    "line_start": unit.line_start,
                    "line_end": unit.line_end,
                    "content_type": unit.content_type,
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
