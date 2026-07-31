"""coaching.evidence.models — Pydantic models for evidence sources and packages.

Guarantees that every evidence source has a stable contract and that internal
locators never expose absolute paths or external URLs.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

VALID_STATUSES = ["available", "missing", "not_trustworthy"]
VALID_CONFIDENCES = ["high", "medium", "low"]
SAFE_LOCATOR_PREFIX = ".escala/"

EvidenceStatus = Literal["available", "missing", "not_trustworthy"]
EvidenceConfidence = Literal["high", "medium", "low"]


class DecisionRef(BaseModel):
    """Reference to the decision sheet produced by S43.1."""

    decision: str = Field(..., min_length=1)
    area: str = Field(..., min_length=1)
    horizon: str = Field(..., min_length=1)
    outcome: str = Field(..., min_length=1)


class EvidenceSource(BaseModel):
    """A single piece of evidence discovered for a decision."""

    source_id: str = Field(..., min_length=1)
    source_type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    status: EvidenceStatus
    period: str = Field(default="")
    confidence: EvidenceConfidence
    reason: str = Field(..., min_length=1)
    locator: str | None = Field(default=None)

    @field_validator("locator")
    @classmethod
    def _locator_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value.startswith(("http://", "https://", "file://")):
            raise ValueError("Locator must not be a URL.")
        if value.startswith(("/", "\\\\")) or ":" in value[:10]:
            raise ValueError("Locator must not be an absolute path.")
        if ".." in value or not value.startswith(SAFE_LOCATOR_PREFIX):
            raise ValueError(
                f"Locator must be relative and start with {SAFE_LOCATOR_PREFIX!r}."
            )
        return value


class EvidencePackage(BaseModel):
    """Collection of evidence sources classified for a single decision."""

    decision_ref: DecisionRef
    sources: list[EvidenceSource] = Field(default_factory=list)
    missing: list[EvidenceSource] = Field(default_factory=list)
    not_trustworthy: list[EvidenceSource] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
