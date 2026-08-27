from __future__ import annotations

import pytest

from validators.foundations_classification import (
    SpecialSourceClassificationSet,
    validate_special_source_classifications,
)
from validators.source_manifest import SourceManifest


def _manifest() -> SourceManifest:
    return SourceManifest.model_validate(
        {
            "schema_version": 1,
            "source_id": "source.example",
            "source_sha256": "0" * 64,
            "source_line_count": 4,
            "units": [
                {
                    "source_id": "source.example",
                    "unit_id": "source.example.u0001",
                    "line_start": 1,
                    "line_end": 2,
                    "content_type": "historical_example",
                    "sha256": "1" * 64,
                },
                {
                    "source_id": "source.example",
                    "unit_id": "source.example.u0002",
                    "line_start": 3,
                    "line_end": 4,
                    "content_type": "external_reference",
                    "sha256": "2" * 64,
                },
            ],
        }
    )


def _classification() -> SpecialSourceClassificationSet:
    return SpecialSourceClassificationSet.model_validate(
        {
            "schema_version": 1,
            "source_id": "source.example",
            "entries": [
                {
                    "unit_id": "source.example.u0001",
                    "kind": "historical-example",
                    "generalizable": False,
                    "knowledge_scope": "Historical case that cannot become an operating rule.",
                    "requires_additional_source": False,
                },
                {
                    "unit_id": "source.example.u0002",
                    "kind": "external-reference",
                    "generalizable": False,
                    "knowledge_scope": "The cited method remains limited to this source summary.",
                    "requires_additional_source": True,
                },
            ],
        }
    )


def test_special_source_classification_is_exhaustive() -> None:
    validate_special_source_classifications(_classification(), _manifest())


def test_external_reference_requires_primary_source() -> None:
    with pytest.raises(ValueError, match="requires its primary source"):
        SpecialSourceClassificationSet.model_validate(
            {
                "schema_version": 1,
                "source_id": "source.example",
                "entries": [
                    {
                        "unit_id": "source.example.u0002",
                        "kind": "external-reference",
                        "generalizable": False,
                        "knowledge_scope": "The cited method remains limited to this source summary.",
                        "requires_additional_source": False,
                    }
                ],
            }
        )


def test_special_source_classification_rejects_missing_manifest_unit() -> None:
    classification = _classification().model_copy(update={"entries": []})
    with pytest.raises(ValueError, match="coverage mismatch"):
        validate_special_source_classifications(classification, _manifest())
