"""Exhaustive, evidence-bound coverage for a single source domain."""

from __future__ import annotations

from collections import Counter
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from validators.source_manifest import ContentType, SourceManifest, source_manifest_hash


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DomainCoverageDisposition(str, Enum):
    MAPPED = "foundation-mapped"
    SPECIAL_SOURCE = "special-source"
    HANDOFF = "handoff"
    EXCLUDED = "excluded"


_INVENTORY_STATUSES = {
    DomainCoverageDisposition.MAPPED: {
        "classified-pending-independent-review",
        "foundation-mapped",
    },
    DomainCoverageDisposition.SPECIAL_SOURCE: {"special-source"},
    DomainCoverageDisposition.HANDOFF: {"handoff"},
    DomainCoverageDisposition.EXCLUDED: {"excluded"},
}


class DomainRange(_StrictModel):
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_order(self) -> "DomainRange":
        if self.line_end < self.line_start:
            raise ValueError("domain range is invalid")
        return self


class DomainInventoryUnit(_StrictModel):
    source_id: str = Field(min_length=3, max_length=128)
    unit_id: str = Field(min_length=3, max_length=192)
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    content_type: ContentType
    sha256: str = Field(min_length=64, max_length=64)
    domain: str = Field(min_length=2, max_length=64)
    classification_status: str = Field(min_length=3, max_length=96)
    exclusion_reason: str | None = None


class DomainInventory(_StrictModel):
    schema_version: int = Field(ge=1, le=1)
    source_id: str = Field(min_length=3, max_length=128)
    domain: str = Field(min_length=2, max_length=64)
    range: DomainRange
    manifest_sha256: str = Field(min_length=64, max_length=64)
    unit_count: int = Field(ge=1)
    units: list[DomainInventoryUnit] = Field(min_length=1)
    classification_complete: bool | None = None
    classification_counts: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_unit_count(self) -> "DomainInventory":
        if self.unit_count != len(self.units):
            raise ValueError("domain inventory unit count differs from units")
        actual_counts = dict(Counter(unit.classification_status for unit in self.units))
        if self.classification_counts and self.classification_counts != actual_counts:
            raise ValueError("domain inventory classification counts differ from units")
        return self


class DomainCoverageRow(_StrictModel):
    unit_id: str = Field(min_length=3, max_length=192)
    disposition: DomainCoverageDisposition
    rationale: str = Field(min_length=12, max_length=512)
    node_ids: list[str] = Field(default_factory=list, max_length=32)
    handoff_epic: str | None = None

    @model_validator(mode="after")
    def validate_disposition_contract(self) -> "DomainCoverageRow":
        if self.disposition is DomainCoverageDisposition.MAPPED:
            if not self.node_ids or self.handoff_epic is not None:
                raise ValueError("mapped domain unit requires nodes and no handoff")
        elif self.disposition is DomainCoverageDisposition.HANDOFF:
            if not self.handoff_epic or self.node_ids:
                raise ValueError("handoff requires epic and no domain nodes")
        elif self.node_ids or self.handoff_epic is not None:
            raise ValueError("special/excluded row cannot declare nodes or handoff")
        return self


class DomainCoverageMatrix(_StrictModel):
    schema_version: int = Field(ge=1, le=1)
    source_id: str = Field(min_length=3, max_length=128)
    domain: str = Field(min_length=2, max_length=64)
    manifest_sha256: str = Field(min_length=64, max_length=64)
    rows: list[DomainCoverageRow] = Field(min_length=1)
    classification_counts: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_declared_counts(self) -> "DomainCoverageMatrix":
        actual = dict(Counter(row.disposition.value for row in self.rows))
        if self.classification_counts and self.classification_counts != actual:
            raise ValueError("domain coverage counts differ from rows")
        return self


def validate_domain_coverage(
    matrix: DomainCoverageMatrix,
    inventory: DomainInventory,
    manifest: SourceManifest,
    known_node_evidence: dict[str, set[str]],
) -> None:
    """Validate exhaustive coverage without turning candidates into canon."""
    manifest_hash = source_manifest_hash(manifest)
    if (
        matrix.source_id != manifest.source_id
        or inventory.source_id != manifest.source_id
    ):
        raise ValueError("domain coverage source differs from manifest")
    if matrix.domain != inventory.domain:
        raise ValueError("domain coverage differs from inventory domain")
    if inventory.unit_count != len(inventory.units):
        raise ValueError("domain inventory unit count differs from units")
    if (
        matrix.manifest_sha256 != manifest_hash
        or inventory.manifest_sha256 != manifest_hash
    ):
        raise ValueError("domain coverage manifest identity mismatch")

    manifest_by_id = {unit.unit_id: unit for unit in manifest.units}
    inventory_ids = {unit.unit_id for unit in inventory.units}
    if len(inventory_ids) != len(inventory.units):
        raise ValueError("duplicate domain inventory unit")
    if inventory.range.line_start != min(
        unit.line_start for unit in inventory.units
    ) or inventory.range.line_end != max(unit.line_end for unit in inventory.units):
        raise ValueError("domain range differs from its inventory units")
    for unit in inventory.units:
        source_unit = manifest_by_id.get(unit.unit_id)
        if source_unit is None:
            raise ValueError("domain inventory unit absent from manifest")
        if (
            source_unit.source_id != unit.source_id
            or source_unit.line_start != unit.line_start
            or source_unit.line_end != unit.line_end
            or source_unit.content_type is not unit.content_type
            or source_unit.sha256 != unit.sha256
            or source_unit.exclusion_reason != unit.exclusion_reason
            or unit.domain != inventory.domain
        ):
            raise ValueError("domain inventory differs from manifest")

    row_ids = [row.unit_id for row in matrix.rows]
    if len(row_ids) != len(set(row_ids)):
        raise ValueError("duplicate domain coverage unit")
    if set(row_ids) != inventory_ids:
        raise ValueError("domain coverage is not exhaustive")

    rows_by_unit = {row.unit_id: row for row in matrix.rows}
    special_ids = {
        unit.unit_id
        for unit in inventory.units
        if unit.content_type
        in {ContentType.HISTORICAL_EXAMPLE, ContentType.EXTERNAL_REFERENCE}
    }
    covered_special_ids = {
        row.unit_id
        for row in matrix.rows
        if row.disposition is DomainCoverageDisposition.SPECIAL_SOURCE
    }
    if covered_special_ids != special_ids:
        raise ValueError("domain special-source coverage mismatch")

    for unit in inventory.units:
        row = rows_by_unit[unit.unit_id]
        if unit.classification_status not in _INVENTORY_STATUSES[row.disposition]:
            raise ValueError("domain inventory status differs from coverage")
        if row.disposition is DomainCoverageDisposition.MAPPED:
            for node_id in row.node_ids:
                evidence_units = known_node_evidence.get(node_id)
                if evidence_units is None:
                    raise ValueError("coverage references unknown domain node")
                if row.unit_id not in evidence_units:
                    raise ValueError("domain mapping lacks node evidence")
