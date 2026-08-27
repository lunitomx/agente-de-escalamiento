"""Source-safe classification for historical examples and external references."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from validators.source_manifest import ContentType, SourceManifest


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SpecialKnowledgeKind(str, Enum):
    HISTORICAL_EXAMPLE = "historical-example"
    EXTERNAL_REFERENCE = "external-reference"


class SpecialSourceClassification(_StrictModel):
    unit_id: str = Field(min_length=3, max_length=192)
    kind: SpecialKnowledgeKind
    generalizable: bool
    knowledge_scope: str = Field(min_length=12, max_length=512)
    requires_additional_source: bool

    @model_validator(mode="after")
    def validate_scope(self) -> "SpecialSourceClassification":
        if self.kind is SpecialKnowledgeKind.HISTORICAL_EXAMPLE:
            if self.generalizable or self.requires_additional_source:
                raise ValueError("historical example must remain non-generalizable")
        elif not self.requires_additional_source:
            raise ValueError("external reference requires its primary source")
        return self


class SpecialSourceClassificationSet(_StrictModel):
    schema_version: int = Field(ge=1, le=1)
    source_id: str = Field(min_length=3, max_length=128)
    entries: list[SpecialSourceClassification] = Field(default_factory=list)


def validate_special_source_classifications(
    classifications: SpecialSourceClassificationSet, manifest: SourceManifest
) -> None:
    if classifications.source_id != manifest.source_id:
        raise ValueError("classification source differs from manifest")
    expected = {
        unit.unit_id: unit.content_type
        for unit in manifest.units
        if unit.content_type
        in {ContentType.HISTORICAL_EXAMPLE, ContentType.EXTERNAL_REFERENCE}
    }
    actual = {entry.unit_id: entry for entry in classifications.entries}
    if len(actual) != len(classifications.entries):
        raise ValueError("duplicate special-source classification")
    if set(actual) != set(expected):
        raise ValueError("special-source classification coverage mismatch")
    for unit_id, content_type in expected.items():
        expected_kind = (
            SpecialKnowledgeKind.HISTORICAL_EXAMPLE
            if content_type is ContentType.HISTORICAL_EXAMPLE
            else SpecialKnowledgeKind.EXTERNAL_REFERENCE
        )
        if actual[unit_id].kind is not expected_kind:
            raise ValueError("special-source classification kind mismatch")
