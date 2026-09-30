"""Typed contracts for the E49 diagnostic evidence path.

The models are intentionally small: they describe evidence and its trust
boundary, not a generic survey or persistence framework.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from coaching.core import require_local_ref

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
    decision: str | None = None
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
        return require_local_ref(value, "source_ref")

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


class DecisionScore(BaseModel):
    """One explainable decision score and its evidence coverage."""

    decision: str
    score: float | None = None
    answered: int = 0
    applicable: int = 0
    excluded: int = 0
    coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: Confidence = "low"
    evidence_ids: list[str] = Field(default_factory=list)
    excluded_evidence_ids: list[str] = Field(default_factory=list)


class ExplainableDiagnosis(BaseModel):
    """Scorecard with a traceable focus selection."""

    scores: dict[str, DecisionScore] = Field(default_factory=dict)
    focus: str | None = None
    focus_evidence_ids: list[str] = Field(default_factory=list)
    selection_rule: str = "lowest_score_then_decision_order"


class PrefillResult(BaseModel):
    """Proposed profile/OPSP facts awaiting explicit confirmation."""

    evidence: list[DiagnosticEvidence] = Field(default_factory=list)
    confirmation_ids: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)


class RouteAction(BaseModel):
    """One bounded action in the first 90-day route."""

    quarter: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    owner: str | None = None
    metric: str | None = None
    rationale: str | None = None


class DiagnosticResult(BaseModel):
    """Stable local result consumed by Markdown and machine-readable exports."""

    diagnosis: ExplainableDiagnosis
    funnel: FunnelMetrics | None = None
    route: list[RouteAction] = Field(default_factory=list, max_length=2)
    company: dict[str, Any] = Field(default_factory=dict)
    open_context: dict[str, str] = Field(default_factory=dict)
    owner_context: dict[str, str] = Field(default_factory=dict)
    generated_at: date | datetime
    provenance: dict[str, Any] = Field(default_factory=dict)
