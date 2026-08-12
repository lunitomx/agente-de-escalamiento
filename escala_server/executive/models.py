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


class CockpitCard(_StrictModel):
    """One visual decision card projected from a diagnostic assessment."""

    decision: Decision
    score: int | None = Field(default=None, ge=0, le=100)
    status: EvidenceStatus
    freshness: Freshness = "unknown"
    evidence_count: int = Field(ge=0)
    blockers: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()
    recommended_action: str = Field(min_length=1, max_length=240)


class PainDrillDown(_StrictModel):
    """Evidence-first explanation of the selected pain/focus."""

    decision: Decision | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    source_ids: tuple[str, ...] = ()
    freshness: Freshness = "unknown"
    blockers: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()
    next_action: str = Field(min_length=1, max_length=240)


class ExecutiveCockpit(_StrictModel):
    """Local visual cockpit projection with an honest focus state."""

    schema_version: Literal[1] = 1
    cards: tuple[CockpitCard, ...]
    focus_decision: Decision | None = None
    drill_down: PainDrillDown
    status: Literal["supported", "evidence_limited", "unresolved"]

    def card_for(self, decision: Decision) -> CockpitCard:
        """Return a card for a known decision."""

        for card in self.cards:
            if card.decision == decision:
                return card
        raise KeyError(decision)


class CockpitArtifact(_StrictModel):
    """Safe relative paths and content hash for a local cockpit export."""

    schema_version: Literal[1] = 1
    html_path: str = Field(pattern=r"^\.escala-executive/cockpit\.html$")
    json_path: str = Field(pattern=r"^\.escala-executive/cockpit\.json$")
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class StrategyAnswer(_StrictModel):
    """One owner answer for an OPSP/vision section."""

    key: str = Field(min_length=2, max_length=64)
    value: str | int | float | bool | None
    status: FieldStatus
    source_ids: tuple[str, ...] = ()
    question: str | None = Field(default=None, max_length=240)
    owner: str | None = Field(default=None, min_length=1, max_length=120)

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        if _SAFE_KEY.fullmatch(value) is None:
            raise ValueError("strategy key must be a safe snake_case field")
        return value

    @field_validator("source_ids")
    @classmethod
    def validate_source_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_validate_safe_id(item, "source_id") for item in value)


class StrategyPlan(_StrictModel):
    """Partial or ready OPSP-style strategy plan from explicit answers."""

    schema_version: Literal[1] = 1
    vision: str | None = None
    purpose: str | None = None
    bhag: str | None = None
    sandbox: str | None = None
    brand_promise: str | None = None
    profit_per_x: str | None = None
    annual_goal: str | None = None
    critical_number: str | None = None
    columns: tuple["OPSPColumn", ...] = ()
    rows: tuple["OPSPRow", ...] = ()
    key_capabilities: tuple["KeyCapability", ...] = ()
    source_ids: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()
    status: Literal["ready", "needs_clarification"]


class OPSPColumn(_StrictModel):
    """One of the seven fixed columns in a One-Page Strategic Plan."""

    number: int = Field(ge=1, le=7)
    title: str = Field(min_length=1, max_length=120)
    execution: bool


class OPSPAccountability(_StrictModel):
    """A person's explicit accountability for one OPSP cell."""

    person: str = Field(min_length=1, max_length=120)
    responsibility: str = Field(min_length=1, max_length=240)


class OPSPCell(_StrictModel):
    """A structured cell in the Actions, Goals, or Targets row."""

    key: str = Field(min_length=2, max_length=64)
    column: int = Field(ge=1, le=7)
    value: str | None = None
    status: FieldStatus
    question: str | None = Field(default=None, max_length=240)
    accountability: OPSPAccountability | None = None

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        if _SAFE_KEY.fullmatch(value) is None:
            raise ValueError("OPSP cell key must be a safe snake_case field")
        return value


class OPSPRow(_StrictModel):
    """One complete Actions, Goals, or Targets row across seven columns."""

    name: Literal["actions", "goals", "targets"]
    cells: tuple[OPSPCell, ...]

    @field_validator("cells")
    @classmethod
    def validate_cells(cls, value: tuple[OPSPCell, ...]) -> tuple[OPSPCell, ...]:
        if len(value) != 7 or tuple(cell.column for cell in value) != tuple(
            range(1, 8)
        ):
            raise ValueError(
                "an OPSP row must contain columns 1 through 7 exactly once"
            )
        return value


class KeyCapability(_StrictModel):
    """A capability required within the OPSP's three-to-five-year horizon."""

    description: str = Field(min_length=1, max_length=240)
    horizon: Literal["3-5 years"] = "3-5 years"


class CoachingRequest(_StrictModel):
    """Owner request for an explicit or diagnostic-derived decision route."""

    decision: Decision | None = None
    question: str = Field(default="", max_length=240)


class CoachingRoute(_StrictModel):
    """Safe route to an existing four-decision skill."""

    decision: Decision
    skill: str = Field(pattern=r"^/escala-(people|strategy|execution|cash)$")
    supported: bool
    evidence_status: EvidenceStatus
    rationale: str = Field(min_length=1, max_length=240)
    questions: tuple[str, ...] = ()


class Goal(_StrictModel):
    """One persisted company goal."""

    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    owner: str = Field(min_length=1, max_length=120)
    due_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    progress: int = Field(default=0, ge=0, le=100)
    status: Literal["pending", "in_progress", "done"] = "pending"

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_safe_id(value, "goal id")


class Priority(_StrictModel):
    """One persisted quarterly/annual priority."""

    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    owner: str = Field(min_length=1, max_length=120)
    due_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    progress: int = Field(default=0, ge=0, le=100)
    status: Literal["pending", "in_progress", "done"] = "pending"

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_safe_id(value, "priority id")


class ExecutionTask(_StrictModel):
    """One persisted task linked to a priority."""

    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    owner: str = Field(min_length=1, max_length=120)
    due_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    priority_id: str | None = None
    progress: int = Field(default=0, ge=0, le=100)
    status: Literal["pending", "in_progress", "done"] = "pending"

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_safe_id(value, "task id")

    @field_validator("priority_id")
    @classmethod
    def validate_priority_id(cls, value: str | None) -> str | None:
        return _validate_safe_id(value, "priority id") if value is not None else None


class SessionContinuity(_StrictModel):
    """Explicit next-session handoff without a machine timestamp/path."""

    session_id: str = Field(default="unspecified", min_length=1, max_length=80)
    next_prompt: str = Field(default="", max_length=240)
    pending_questions: tuple[str, ...] = ()

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, value: str) -> str:
        return _validate_safe_id(value, "session id")


class ExecutionState(_StrictModel):
    """Locally persisted execution and session continuity snapshot."""

    schema_version: Literal[1] = 1
    goals: tuple[Goal, ...] = ()
    priorities: tuple[Priority, ...] = ()
    tasks: tuple[ExecutionTask, ...] = ()
    continuity: SessionContinuity = Field(default_factory=SessionContinuity)


class StateReceipt(_StrictModel):
    """Redacted local state receipt with a stable relative path."""

    schema_version: Literal[1] = 1
    path: str = Field(pattern=r"^\.escala-executive/execution\.json$")
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class GuidanceRequest(_StrictModel):
    """Explicit context supplied to the honest guidance seam."""

    topic: str = Field(min_length=1, max_length=120)
    facts: tuple[str, ...] = ()
    inferences: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    question: str = Field(default="", max_length=240)


class HonestGuidance(_StrictModel):
    """Guidance that keeps facts, inferences and unknowns separate."""

    status: Literal["supported", "evidence_limited"]
    facts: tuple[str, ...] = ()
    inferences: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()
    next_action: str = Field(min_length=1, max_length=240)
