"""Closed, path-redacted contracts for the E40 onboarding seam."""

from __future__ import annotations

from typing import Literal
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


Decision = Literal["people", "strategy", "execution", "cash"]
DECISIONS: tuple[Decision, ...] = ("people", "strategy", "execution", "cash")
FieldStatus = Literal["fact", "inference", "unknown"]
EvidenceStatus = Literal["supported", "evidence_limited", "unresolved"]
Freshness = Literal["fresh", "stale", "unknown"]

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SAFE_KEY = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _validate_safe_id(value: str, label: str) -> str:
    if _SAFE_ID.fullmatch(value) is None or "/" in value or "\\" in value:
        raise ValueError(f"{label} must be a stable non-path identifier")
    return value


def _validate_locator(value: str) -> str:
    normalized = value.replace("\\", "/")
    if (
        not normalized.strip()
        or normalized.startswith("/")
        or normalized.startswith("~")
        or re.match(r"^[A-Za-z]:", normalized)
        or "http://" in normalized.casefold()
        or "https://" in normalized.casefold()
        or ".." in normalized.split("/")
    ):
        raise ValueError("locator must be relative and local-safe")
    return normalized


class ProfileAnswer(_StrictModel):
    """One owner-provided answer used to build a company profile."""

    key: str = Field(min_length=2, max_length=64)
    value: str | int | float | bool | None
    status: FieldStatus
    question: str | None = Field(default=None, max_length=240)

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        if _SAFE_KEY.fullmatch(value) is None:
            raise ValueError("profile key must be a safe snake_case field")
        return value


class ProfileField(_StrictModel):
    """Validated profile field, including explicit unknown state."""

    key: str = Field(min_length=2, max_length=64)
    value: str | int | float | bool | None
    status: FieldStatus
    source_ids: tuple[str, ...] = ()
    question: str | None = Field(default=None, max_length=240)

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        if _SAFE_KEY.fullmatch(value) is None:
            raise ValueError("profile key must be a safe snake_case field")
        return value

    @field_validator("source_ids")
    @classmethod
    def validate_source_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_validate_safe_id(item, "source_id") for item in value)


class CompanyProfile(_StrictModel):
    """Stable ordered company profile assembled from owner answers."""

    schema_version: Literal[1] = 1
    fields: tuple[ProfileField, ...]

    def field(self, key: str) -> ProfileField:
        """Return a field by key; callers only use keys emitted by the builder."""

        for item in self.fields:
            if item.key == key:
                return item
        raise KeyError(key)


class OnboardingQuestion(_StrictModel):
    """One bounded question for a material missing profile field."""

    field: str = Field(min_length=2, max_length=64)
    prompt: str = Field(min_length=1, max_length=240)
    reason: Literal["missing", "uncertain"]


class OnboardingResult(_StrictModel):
    """Profile result with explicit completion state and unresolved fields."""

    profile: CompanyProfile
    status: Literal["ready", "needs_clarification"]
    unresolved_fields: tuple[str, ...] = ()
    questions: tuple[OnboardingQuestion, ...] = ()


class EvidenceItem(_StrictModel):
    """Redacted evidence pointer imported from a local source or owner."""

    source_id: str = Field(min_length=1, max_length=128)
    locator: str = Field(default="owner_input", min_length=1, max_length=240)
    freshness: Freshness = "unknown"
    confidence: int = Field(default=100, ge=0, le=100)

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, value: str) -> str:
        return _validate_safe_id(value, "source_id")

    @field_validator("locator")
    @classmethod
    def validate_locator(cls, value: str) -> str:
        return _validate_locator(value)


class DiagnosticAnswer(_StrictModel):
    """One bounded 0–100 owner/evidence answer for a decision."""

    decision: Decision
    score: int = Field(ge=0, le=100)
    source_ids: tuple[str, ...] = ()
    attribution: Literal["owner_input"] | None = None
    freshness: Freshness = "unknown"
    blocker: str | None = Field(default=None, max_length=160)

    @field_validator("source_ids")
    @classmethod
    def validate_source_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_validate_safe_id(item, "source_id") for item in value)


class DecisionAssessment(_StrictModel):
    """Aggregated decision score and safe drill-down metadata."""

    decision: Decision
    score: int | None = Field(default=None, ge=0, le=100)
    evidence_status: EvidenceStatus
    evidence_count: int = Field(ge=0)
    source_ids: tuple[str, ...] = ()
    attribution: tuple[str, ...] = ()
    freshness: Freshness = "unknown"
    blockers: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()


class ExecutiveDiagnostic(_StrictModel):
    """Four-decision diagnostic, explicit when the evidence is incomplete."""

    schema_version: Literal[1] = 1
    assessments: tuple[DecisionAssessment, ...]
    overall_score: int | None = Field(default=None, ge=0, le=100)
    status: Literal["supported", "evidence_limited", "unresolved"]

    def assessment_for(self, decision: Decision) -> DecisionAssessment:
        """Return the assessment for a known decision."""

        for item in self.assessments:
            if item.decision == decision:
                return item
        raise KeyError(decision)
