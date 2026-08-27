"""Private, privacy-bounded evidence contract for the external E42 release gate."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_OPAQUE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
STEPS = (
    "install",
    "workspace",
    "document-ingestion",
    "meeting-review",
    "cash",
    "strategy",
    "cockpit",
    "action-followup",
)
REQUIREMENTS = frozenset(
    {
        "REQ-E42-001",
        "REQ-E42-002",
        "REQ-E42-003",
        "REQ-E42-004",
        "REQ-E42-005",
        "REQ-E42-006",
    }
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PlatformRun(_StrictModel):
    run_ref: str = Field(min_length=3, max_length=64)
    platform: Literal["macos", "windows"]
    environment: Literal["physical", "dedicated-vm"]
    clean_environment: Literal[True]
    source_commit: str
    export_manifest_sha256: str
    public_entrypoint: Literal["escala"]
    journey_steps: tuple[
        Literal[
            "install",
            "workspace",
            "document-ingestion",
            "meeting-review",
            "cash",
            "strategy",
            "cockpit",
            "action-followup",
        ],
        ...,
    ]
    result: Literal["pass"]

    @model_validator(mode="after")
    def validate_run(self) -> "PlatformRun":
        if not _OPAQUE.fullmatch(self.run_ref):
            raise ValueError("run_ref must be an opaque, non-personal identifier")
        if not _COMMIT.fullmatch(self.source_commit):
            raise ValueError("source_commit must be a full lowercase commit hash")
        if not _SHA256.fullmatch(self.export_manifest_sha256):
            raise ValueError("export_manifest_sha256 must be a lowercase SHA-256 hash")
        if self.journey_steps != STEPS:
            raise ValueError(
                "platform run must cover the E42 journey in its exact order"
            )
        return self


class CatalogReview(_StrictModel):
    matches_public_inventory: Literal[True]
    limitations_are_clear: Literal[True]
    excludes_private_or_prohibited_sources: Literal[True]


class RequirementAcceptance(_StrictModel):
    requirement_id: Literal[
        "REQ-E42-001",
        "REQ-E42-002",
        "REQ-E42-003",
        "REQ-E42-004",
        "REQ-E42-005",
        "REQ-E42-006",
    ]
    accepted: bool


class E42ReleaseAcceptanceReceipt(_StrictModel):
    """Private local receipt; it cannot itself close E42."""

    schema_version: Literal[1]
    receipt_kind: Literal["e42-clean-hardware-and-human-acceptance"]
    storage: Literal["private-local-only"]
    participant_ref: str = Field(min_length=3, max_length=64)
    platform_runs: tuple[PlatformRun, PlatformRun]
    catalog_review: CatalogReview
    requirement_acceptance: tuple[
        RequirementAcceptance,
        RequirementAcceptance,
        RequirementAcceptance,
        RequirementAcceptance,
        RequirementAcceptance,
        RequirementAcceptance,
    ]
    release_decision: Literal["accepted", "reservations-open"]

    @model_validator(mode="after")
    def validate_receipt(self) -> "E42ReleaseAcceptanceReceipt":
        if not _OPAQUE.fullmatch(self.participant_ref):
            raise ValueError(
                "participant_ref must be an opaque, non-personal identifier"
            )
        if {run.platform for run in self.platform_runs} != {"macos", "windows"}:
            raise ValueError("receipt requires exactly one macOS and one Windows run")
        requirements = {
            item.requirement_id: item.accepted for item in self.requirement_acceptance
        }
        if set(requirements) != REQUIREMENTS or len(requirements) != 6:
            raise ValueError("receipt must address every E42 requirement exactly once")
        if all(requirements.values()) != (self.release_decision == "accepted"):
            raise ValueError("release decision must match the requirement acceptance")
        return self


def validation_errors(receipt: E42ReleaseAcceptanceReceipt) -> tuple[str, ...]:
    if receipt.release_decision != "accepted":
        pending = sorted(
            item.requirement_id
            for item in receipt.requirement_acceptance
            if not item.accepted
        )
        return ("owner acceptance remains open: " + ", ".join(pending),)
    return ()


def validate_release_acceptance(receipt: E42ReleaseAcceptanceReceipt) -> None:
    E42ReleaseAcceptanceReceipt.model_validate(receipt.model_dump(mode="json"))
