"""Typed contracts for the E49 diagnostic evidence path.

The models are intentionally small: they describe evidence and its trust
boundary, not a generic survey or persistence framework.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

Applicability = Literal["applicable", "not_applicable", "unknown"]
AnswerStatus = Literal["fact", "estimate", "inference", "unanswered"]
Freshness = Literal["current", "stale", "unknown"]
Confidence = Literal["high", "medium", "low"]
SourceKind = Literal[
    "conversation",
    "user_file",
    "crm_export",
    "profile",
    "opsp",
    "estimate",
]


class DiagnosticEvidence(BaseModel):
    """One answer or fact that may support a diagnostic score."""

    evidence_id: str = Field(..., min_length=1, pattern=r"^[a-z0-9][a-z0-9_.-]*$")
    question_id: str = Field(..., min_length=1)
    value: Any = None
    applicability: Applicability = "applicable"
    answer_status: AnswerStatus = "fact"
    source_kind: SourceKind
    source_ref: str = Field(..., min_length=1)
    captured_at: date | datetime | None = None
    freshness: Freshness = "unknown"
    confidence: Confidence = "medium"
    rationale: str = Field(..., min_length=1)

    @field_validator("source_ref")
    @classmethod
    def _source_ref_must_not_escape_local_boundary(cls, value: str) -> str:
        """Reject URLs, absolute paths, and parent traversal in evidence refs."""
        if value.startswith(("http://", "https://", "file://")):
            raise ValueError("source_ref must not be a URL")
        if value.startswith(("/", "\\\\")) or ":\\" in value[:10]:
            raise ValueError("source_ref must not be an absolute path")
        if ".." in value:
            raise ValueError("source_ref must not contain parent traversal")
        return value

    @property
    def included_in_score(self) -> bool:
        """Whether this item can contribute to a decision denominator."""
        return self.applicability == "applicable" and self.answer_status != "unanswered"


class FunnelMetrics(BaseModel):
    """Optional commercial funnel counts; absent fields stay absent."""

    prospects: int | None = Field(default=None, ge=0)
    conversations: int | None = Field(default=None, ge=0)
    proposals: int | None = Field(default=None, ge=0)
    wins: int | None = Field(default=None, ge=0)
    average_sale: float | None = Field(default=None, ge=0)

    @property
    def total_prospects(self) -> int:
        """Return the known total for compatibility with funnel consumers."""
        return self.prospects or 0

    def __getitem__(self, key: str) -> int | float | None:
        """Allow existing dictionary-style consumers during migration."""
        return getattr(self, key)


class DiagnosticIntake(BaseModel):
    """Evidence-backed intake shared by scoring and result consumers."""

    company: dict[str, Any] = Field(default_factory=dict)
    evidence: list[DiagnosticEvidence] = Field(default_factory=list)
    funnel: FunnelMetrics | None = None
    open_context: dict[str, str] = Field(default_factory=dict)
    owner_context: dict[str, str] = Field(default_factory=dict)
