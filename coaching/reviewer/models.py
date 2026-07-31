"""coaching.reviewer.models — Pydantic models for pre-response review reports.

Guarantees that every review has a stable contract and traceable findings,
including the blocked/clarify actions when the response would be unsafe.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ReviewAction = Literal["reviewed", "clarify", "blocked"]
FindingKind = Literal[
    "fact", "inference", "unknown", "contradiction", "alignment", "missing"
]
Severity = Literal["info", "warning", "critical"]


class ReviewFinding(BaseModel):
    """A single observation produced by the review."""

    kind: FindingKind
    severity: Severity
    source_ids: list[str] = Field(default_factory=list)
    message: str = Field(..., min_length=1)
    recommendation: str = Field(default="")


class ReviewReport(BaseModel):
    """Structured record of the review outcome."""

    decision: str = Field(..., min_length=1)
    area: str = Field(..., min_length=1)
    tool: str | None = Field(default=None)
    findings: list[ReviewFinding] = Field(default_factory=list)
    critical_questions: list[str] = Field(default_factory=list)
    action_aligned: bool = Field(default=True)
    can_proceed: bool = Field(default=True)


class ReviewResult(BaseModel):
    """Structured result returned by the review engine."""

    action: ReviewAction
    report: ReviewReport
    output: str = Field(..., min_length=1)
    questions: list[str] = Field(default_factory=list)
