"""Privacy-safe human attestation contract for the E68 quarterly pilot."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PilotAttestationError(ValueError):
    """A stable failure while validating the pilot completion record."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


_STAGES = ("diagnosis", "priority", "execution", "review")


class StageAttestation(_StrictModel):
    stage: Literal["diagnosis", "priority", "execution", "review"]
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    human_outcome: Literal["approved", "corrected"]
    reviewer_role: Literal[
        "company-leader", "functional-owner", "facilitator", "financial-reviewer"
    ]


class QuarterlyPilotAttestation(_StrictModel):
    """Stores proof of review, never business content or human identity."""

    schema_version: Literal[1]
    pilot_id: str = Field(pattern=r"^PILOT-[A-Z0-9-]+$")
    authorization_reference: str = Field(pattern=r"^authorization\.sha256\.[a-f0-9]{64}$")
    local_storage_consent: Literal[True]
    repository_content_free: Literal[True]
    stages: tuple[StageAttestation, ...] = Field(min_length=4, max_length=4)

    @field_validator("pilot_id")
    @classmethod
    def reject_identifiable_pilot_id(cls, value: str) -> str:
        if value != value.upper():
            raise ValueError("pilot_id_must_be_opaque")
        return value

    @model_validator(mode="after")
    def validate_complete_cycle(self) -> "QuarterlyPilotAttestation":
        stages = tuple(stage.stage for stage in self.stages)
        if stages != _STAGES:
            raise ValueError("pilot_stages_incomplete_or_reordered")
        return self


def validate_pilot_attestation(
    attestation: QuarterlyPilotAttestation,
) -> tuple[str, ...]:
    """Return explicit completion blockers, without interpreting company data."""

    errors: list[str] = []
    if not attestation.local_storage_consent:
        errors.append("local_storage_consent_required")
    if not attestation.repository_content_free:
        errors.append("repository_content_must_be_free")
    if len({stage.artifact_sha256 for stage in attestation.stages}) != len(
        attestation.stages
    ):
        errors.append("pilot_artifact_hashes_must_be_distinct")
    return tuple(errors)
