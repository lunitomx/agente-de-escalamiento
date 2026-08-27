from __future__ import annotations

import pytest

from validators.foundations_coverage import (
    FoundationCoverageMatrix,
    validate_foundation_coverage,
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
                    "content_type": "section",
                    "sha256": "2" * 64,
                },
            ],
        }
    )


def _matrix() -> FoundationCoverageMatrix:
    manifest = _manifest()
    return FoundationCoverageMatrix.model_validate(
        {
            "schema_version": 1,
            "source_id": manifest.source_id,
            "manifest_sha256": source_manifest_hash(manifest),
            "rows": [
                {
                    "unit_id": "source.example.u0001",
                    "disposition": "foundation-mapped",
                    "rationale": "This unit maps to a foundational framework component.",
                    "node_ids": ["framework.example"],
                },
                {
                    "unit_id": "source.example.u0002",
                    "disposition": "handoff",
                    "rationale": "The implementation detail belongs to its dedicated domain epic.",
                    "handoff_epic": "E60",
                },
            ],
        }
    )


def test_foundation_coverage_is_exhaustive_and_references_known_nodes() -> None:
    validate_foundation_coverage(_matrix(), _manifest(), {"framework.example"})


def test_foundation_coverage_rejects_unknown_node() -> None:
    with pytest.raises(ValueError, match="unknown foundation node"):
        validate_foundation_coverage(_matrix(), _manifest(), set())


def test_foundation_coverage_rejects_missing_unit() -> None:
    matrix = _matrix().model_copy(update={"rows": _matrix().rows[:1]})
    with pytest.raises(ValueError, match="not exhaustive"):
        validate_foundation_coverage(matrix, _manifest(), {"framework.example"})


def test_foundation_coverage_rejects_historical_unit_hidden_as_excluded() -> None:
    manifest = SourceManifest.model_validate(
        {
            "schema_version": 1,
            "source_id": "source.example",
            "source_sha256": "0" * 64,
            "source_line_count": 1,
            "units": [
                {
                    "source_id": "source.example",
                    "unit_id": "source.example.u0001",
                    "line_start": 1,
                    "line_end": 1,
                    "content_type": "historical_example",
                    "sha256": "1" * 64,
                }
            ],
        }
    )
    matrix = FoundationCoverageMatrix.model_validate(
        {
            "schema_version": 1,
            "source_id": manifest.source_id,
            "manifest_sha256": source_manifest_hash(manifest),
            "rows": [
                {
                    "unit_id": "source.example.u0001",
                    "disposition": "excluded",
                    "rationale": "Incorrectly hides a historical example as generic context.",
                }
            ],
        }
    )
    with pytest.raises(ValueError, match="special-source coverage mismatch"):
        validate_foundation_coverage(matrix, manifest, set())
