"""Locate named external methods inside a private corpus slice without text output."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from validators.domain_coverage import DomainInventory


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ExternalReferenceLocator(_StrictModel):
    unit_id: str = Field(min_length=3, max_length=192)
    references: list[str] = Field(min_length=1, max_length=32)


class ExternalReferenceLocatorReceipt(_StrictModel):
    schema_version: int = Field(ge=1, le=1)
    domain: str = Field(min_length=2, max_length=64)
    status: str = Field(min_length=3, max_length=96)
    rule: str = Field(min_length=24, max_length=1024)
    locators: list[ExternalReferenceLocator] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_units(self) -> "ExternalReferenceLocatorReceipt":
        unit_ids = [item.unit_id for item in self.locators]
        if len(unit_ids) != len(set(unit_ids)):
            raise ValueError("duplicate external reference locator unit")
        return self


def validate_external_reference_locators(
    receipt: ExternalReferenceLocatorReceipt,
    inventory: DomainInventory,
    observed: dict[str, set[str]],
) -> None:
    """Require an exact, source-scanned locator inventory for the given domain."""
    receipt = ExternalReferenceLocatorReceipt.model_validate(
        receipt.model_dump(mode="json")
    )
    if receipt.domain != inventory.domain:
        raise ValueError("external locator domain differs from inventory")
    inventory_ids = {unit.unit_id for unit in inventory.units}
    reported = {item.unit_id: set(item.references) for item in receipt.locators}
    if not set(reported).issubset(inventory_ids):
        raise ValueError("external locator references unknown inventory unit")
    if reported != observed:
        raise ValueError("external locator receipt differs from source scan")
