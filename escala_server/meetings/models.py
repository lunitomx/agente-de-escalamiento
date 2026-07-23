"""Closed contracts for local meeting intelligence."""

from __future__ import annotations

from datetime import date
import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


MeetingType = Literal["daily", "weekly", "one_on_one", "planning", "review", "unknown"]
ContextStatus = Literal["ready", "unresolved"]
MeetingItemStatus = Literal["ready", "unresolved", "duplicate", "rejected"]
EvidenceOrigin = Literal["line", "filename"]
Confidence = Literal["high", "medium", "low"]
FactKind = Literal[
    "decision",
    "action",
    "owner",
    "due_date",
    "blocker",
    "risk",
    "commitment",
]
FactResultStatus = Literal["ready", "partial", "blocked"]
RhythmStatus = Literal["supported", "evidence_missing", "unresolved"]
SignalKind = Literal[
    "repeated_blocker",
    "repeated_commitment",
    "overdue_commitment",
    "unresolved_decision",
    "trend",
]
ReviewHealth = Literal["watch", "evidence_supported", "evidence_limited", "unresolved"]
ScheduleFrequency = Literal["daily", "weekly"]
ReportStatus = Literal["pass", "fail"]


class _StrictModel(BaseModel):
    """Immutable boundary model that rejects undocumented fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class MeetingProvenance(_StrictModel):
    """Path-redacted provenance for a transcript source."""

    source_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    relative_path: str = Field(min_length=1, max_length=512)
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    origin: EvidenceOrigin = "line"

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        if "\x00" in value or Path(value).is_absolute():
            raise ValueError("relative path required")
        normalized = value.replace("\\", "/")
        if normalized == ".." or normalized.startswith("../"):
            raise ValueError("relative path required")
        return normalized

    @model_validator(mode="after")
    def validate_line_order(self) -> MeetingProvenance:
        if self.line_end < self.line_start:
            raise ValueError("line range must be ordered")
        return self


class MeetingQuestion(_StrictModel):
    """Bounded clarification question for missing or ambiguous context."""

    code: str = Field(min_length=1, max_length=80)
    options: tuple[str, ...] = Field(min_length=2, max_length=5)


class MeetingContext(_StrictModel):
    """Meeting metadata that is ready or explicitly unresolved."""

    context_status: ContextStatus
    meeting_type: MeetingType
    meeting_date: date | None = None
    team: str | None = None
    participants: tuple[str, ...] = ()
    provenance: MeetingProvenance
    evidence: tuple[MeetingProvenance, ...] = ()
    confidence: Confidence


class MeetingLedgerEntry(_StrictModel):
    """One first-seen source and its non-content derived context."""

    source_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    relative_path: str = Field(min_length=1, max_length=512)
    status: Literal["ready", "unresolved"]
    context: MeetingContext

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        if "\x00" in value or Path(value).is_absolute():
            raise ValueError("relative path required")
        normalized = value.replace("\\", "/")
        if normalized == ".." or normalized.startswith("../"):
            raise ValueError("relative path required")
        return normalized


class MeetingLedger(_StrictModel):
    """Versioned deterministic ledger stored on the installer machine."""

    schema_version: Literal[1] = 1
    entries: tuple[MeetingLedgerEntry, ...] = ()

    def by_source_id(self) -> dict[str, MeetingLedgerEntry]:
        return {entry.source_id: entry for entry in self.entries}


class MeetingItemResult(_StrictModel):
    """Safe result for one exchange entry."""

    relative_path: str = Field(min_length=1, max_length=512)
    status: MeetingItemStatus
    code: str = Field(min_length=1, max_length=100)
    source_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    context: MeetingContext | None = None
    questions: tuple[MeetingQuestion, ...] = ()

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        if "\x00" in value or Path(value).is_absolute():
            raise ValueError("relative path required")
        normalized = value.replace("\\", "/")
        if normalized == ".." or normalized.startswith("../"):
            raise ValueError("relative path required")
        return normalized


class MeetingRunResult(_StrictModel):
    """Deterministic local intake result."""

    status: Literal["pass"] = "pass"
    run_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    items: tuple[MeetingItemResult, ...] = ()
    ledger: MeetingLedger = Field(default_factory=MeetingLedger)
    ledger_changed: bool = False


class MeetingFact(_StrictModel):
    """One explicitly labelled meeting fact with line provenance."""

    fact_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    kind: FactKind
    value: str = Field(min_length=1, max_length=1000)
    owner: str | None = None
    due_date: date | None = None
    evidence: MeetingProvenance
    confidence: Confidence


class MeetingFactResult(_StrictModel):
    """Extraction result that can be partial but never overconfident."""

    status: FactResultStatus
    source_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    facts: tuple[MeetingFact, ...] = ()
    questions: tuple[MeetingQuestion, ...] = ()
    findings: tuple[str, ...] = ()


class RhythmRule(_StrictModel):
    """Declared business expectation; it is not a performance score."""

    rule_id: str = Field(min_length=1, max_length=80)
    meeting_type: MeetingType
    cadence_days: int = Field(ge=1, le=31)


class RhythmAssessment(_StrictModel):
    """Observed versus missing evidence for one declared rhythm rule."""

    status: RhythmStatus
    rule_id: str
    meeting_type: MeetingType
    observed_dates: tuple[date, ...] = ()
    expected_dates: tuple[date, ...] = ()
    missing_dates: tuple[date, ...] = ()
    person_impact: Literal["not_assessed"] = "not_assessed"
    note_code: str = Field(min_length=1, max_length=80)


class MeetingRecord(_StrictModel):
    """One context plus its extracted facts for temporal analysis."""

    context: MeetingContext
    extraction: MeetingFactResult


class TeamSignal(_StrictModel):
    """A repeated or temporal signal grounded in one or more sources."""

    signal_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    kind: SignalKind
    value: str = Field(min_length=1, max_length=500)
    evidence_source_ids: tuple[str, ...] = ()
    evidence_count: int = Field(ge=1)
    confidence: Confidence


class TeamSignalAnalysis(_StrictModel):
    """Deterministic cross-meeting signal collection."""

    signals: tuple[TeamSignal, ...] = ()
    evidence_source_ids: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()


class ExecutiveReview(_StrictModel):
    """Daily executive view with explicit evidence limits."""

    review_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_date: date
    health: ReviewHealth
    material_changes: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()
    signals: tuple[TeamSignal, ...] = ()
    evidence_source_ids: tuple[str, ...] = ()


class LocalSchedule(_StrictModel):
    """Pull-based schedule manifest owned by the installer machine."""

    schedule_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    frequency: ScheduleFrequency
    run_date: date
    manifest_path: str = Field(min_length=1, max_length=200)


class MeetingReportArtifact(_StrictModel):
    """Relative local report artifacts for one executive review."""

    report_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    html_path: str = Field(min_length=1, max_length=240)
    markdown_path: str = Field(min_length=1, max_length=240)
    json_path: str = Field(min_length=1, max_length=240)
    source_ids: tuple[str, ...] = ()


class MeetingExchangeReceipt(_StrictModel):
    """Safe authority check for the ordinary filesystem exchange."""

    status: ReportStatus
    runtime_authority: Literal["installer_machine"] = "installer_machine"
    data_authority: Literal["installer_machine"] = "installer_machine"
    team_exchange: Literal["ordinary_filesystem_documents_only"] = (
        "ordinary_filesystem_documents_only"
    )
    authoritative_sqlite_sync: Literal["forbidden"] = "forbidden"
    findings: tuple[str, ...] = ()


def evidence_hash(text: str) -> str:
    """Hash an evidence line without persisting its content."""

    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
