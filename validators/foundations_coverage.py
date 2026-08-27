"""Exhaustive, source-safe coverage accounting for E59 foundations."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from validators.source_manifest import SourceManifest, source_manifest_hash


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FoundationCoverageDisposition(str, Enum):
    FOUNDATION_MAPPED = "foundation-mapped"
    SPECIAL_SOURCE = "special-source"
    HANDOFF = "handoff"
    EXCLUDED = "excluded"


class FoundationCoverageRow(_StrictModel):
    unit_id: str = Field(min_length=3, max_length=192)
    disposition: FoundationCoverageDisposition
    rationale: str = Field(min_length=12, max_length=512)
    node_ids: list[str] = Field(default_factory=list, max_length=32)
    handoff_epic: str | None = None

    @model_validator(mode="after")
    def validate_disposition_contract(self) -> "FoundationCoverageRow":
        if self.disposition is FoundationCoverageDisposition.FOUNDATION_MAPPED:
            if not self.node_ids or self.handoff_epic is not None:
                raise ValueError("mapped foundation requires nodes and no handoff")
        elif self.disposition is FoundationCoverageDisposition.HANDOFF:
            if not self.handoff_epic or self.node_ids:
                raise ValueError("handoff requires epic and no foundation nodes")
        elif self.node_ids or self.handoff_epic is not None:
            raise ValueError("special/excluded row cannot declare nodes or handoff")
        return self


class FoundationCoverageMatrix(_StrictModel):
    schema_version: int = Field(ge=1, le=1)
    source_id: str = Field(min_length=3, max_length=128)
    manifest_sha256: str = Field(min_length=64, max_length=64)
    rows: list[FoundationCoverageRow] = Field(min_length=1)


def validate_foundation_coverage(
    matrix: FoundationCoverageMatrix,
    manifest: SourceManifest,
    known_node_ids: set[str],
) -> None:
    if matrix.source_id != manifest.source_id:
        raise ValueError("coverage source differs from manifest")
    if matrix.manifest_sha256 != source_manifest_hash(manifest):
        raise ValueError("coverage manifest identity mismatch")
    row_ids = [row.unit_id for row in matrix.rows]
    if len(row_ids) != len(set(row_ids)):
        raise ValueError("duplicate coverage unit")
    manifest_ids = {unit.unit_id for unit in manifest.units}
    if set(row_ids) != manifest_ids:
        raise ValueError("foundation coverage is not exhaustive")
    special_manifest_ids = {
        unit.unit_id
        for unit in manifest.units
        if unit.content_type.value in {"historical_example", "external_reference"}
    }
    special_row_ids = {
        row.unit_id
        for row in matrix.rows
        if row.disposition is FoundationCoverageDisposition.SPECIAL_SOURCE
    }
    if special_row_ids != special_manifest_ids:
        raise ValueError("special-source coverage mismatch")
    mapped_ids = {
        node_id
        for row in matrix.rows
        if row.disposition is FoundationCoverageDisposition.FOUNDATION_MAPPED
        for node_id in row.node_ids
    }
    if not mapped_ids.issubset(known_node_ids):
        raise ValueError("coverage references unknown foundation node")
