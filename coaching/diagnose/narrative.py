"""Narrative-first diagnostic contract for the public ESCALA intake.

The model deliberately keeps observations separate from numeric scoring. A
number can be attached later as an optional, evidence-backed view; it is never
required to understand a company or to choose a topic for confirmation.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .models import Confidence, DiagnosticIntake

Decision = Literal["people", "strategy", "execution", "cash"]
FindingStatus = Literal["observed", "hypothesis", "unknown", "not_applicable"]
ConfirmationStatus = Literal["pending", "confirmed", "corrected"]
CompanyField = Literal[
    "industry",
    "offering",
    "target_customer",
    "business_model",
    "primary_challenge",
]


class CompanyUnderstanding(BaseModel):
    """Confirmed company context, with gaps marked instead of silently omitted."""

    industry: str | None = Field(default=None, max_length=1_000)
    offering: str | None = Field(default=None, max_length=1_000)
    target_customer: str | None = Field(default=None, max_length=1_000)
    business_model: str | None = Field(default=None, max_length=1_000)
    primary_challenge: str | None = Field(default=None, max_length=1_000)
    unknown_fields: list[CompanyField] = Field(default_factory=list)

    @field_validator("unknown_fields")
    @classmethod
    def unknown_fields_are_unique(cls, value: list[CompanyField]) -> list[CompanyField]:
        if len(value) != len(set(value)):
            raise ValueError("company unknown_fields must be unique")
        return value

    @model_validator(mode="after")
    def each_company_field_is_known_or_explicitly_unknown(
        self,
    ) -> "CompanyUnderstanding":
        fields: tuple[CompanyField, ...] = (
            "industry",
            "offering",
            "target_customer",
            "business_model",
            "primary_challenge",
        )
        unknown = set(self.unknown_fields)
        for field in fields:
            value = getattr(self, field)
            if value is None and field not in unknown:
                raise ValueError(
                    "company understanding must mark missing fields unknown"
                )
            if value is not None and field in unknown:
                raise ValueError(
                    "company understanding cannot mark a known field unknown"
                )
        return self


class NarrativeFinding(BaseModel):
    """One explainable conclusion drawn from an entrepreneur's detailed answer."""

    decision: Decision
    statement: str = Field(min_length=3, max_length=1_000)
    evidence_ids: list[str] = Field(min_length=1, max_length=12)
    status: FindingStatus = "observed"
    confidence: Confidence = "medium"
    implication: str = Field(min_length=3, max_length=1_000)

    @field_validator("evidence_ids")
    @classmethod
    def evidence_ids_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("finding evidence_ids must be unique")
        return value


class FocusProposal(BaseModel):
    """A bounded next topic, proposed for the entrepreneur to confirm or reject."""

    decision: Decision
    rationale: str = Field(min_length=3, max_length=1_000)
    evidence_ids: list[str] = Field(min_length=1, max_length=12)

    @field_validator("evidence_ids")
    @classmethod
    def evidence_ids_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("focus evidence_ids must be unique")
        return value


_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_SENTENCE_END = re.compile(r"[.!?]\s+\S")
WEEK_DAYS = 7


class WeeklyAction(BaseModel):
    """S86.5: the one action for this week that closes the diagnosis.

    ``due`` stays ISO in the data; the owner reads it in plain Spanish.
    """

    decision: Decision
    constraint: str = Field(min_length=3, max_length=300)
    action: str = Field(min_length=3, max_length=300)
    responsible: str = Field(default="tú", min_length=1, max_length=120)
    due: date
    evidence_ids: list[str] = Field(min_length=1, max_length=12)

    @field_validator("constraint")
    @classmethod
    def constraint_is_one_sentence(cls, value: str) -> str:
        if _SENTENCE_END.search(value.strip()):
            raise ValueError("the main constraint must be one sentence")
        return value.strip()

    @field_validator("action", "responsible")
    @classmethod
    def strip_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("weekly action text must not be blank")
        return value.strip()

    @field_validator("evidence_ids")
    @classmethod
    def evidence_ids_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("weekly action evidence_ids must be unique")
        return value


def _numbers(text: str) -> set[str]:
    return {match.replace(",", ".") for match in _NUMBER.findall(text)}


def check_weekly_action(action: WeeklyAction, evidence_text: str, today: date) -> None:
    """Honesty rules: no invented number, and a date within this week."""
    invented = _numbers(f"{action.constraint} {action.action}") - _numbers(
        evidence_text
    )
    if invented:
        raise ValueError(
            "la acción usa un número que no está en la evidencia: "
            f"{', '.join(sorted(invented))}; pide el dato o propón juntarlo"
        )
    if not today <= action.due <= today + timedelta(days=WEEK_DAYS):
        raise ValueError("la fecha de la acción debe caer esta semana")


class NarrativeAssessment(BaseModel):
    """A confirmable diagnosis that makes uncertainty visible before any score."""

    company_summary: str = Field(min_length=3, max_length=2_000)
    company_understanding: CompanyUnderstanding
    findings: list[NarrativeFinding] = Field(min_length=1, max_length=20)
    proposed_focuses: list[FocusProposal] = Field(default_factory=list, max_length=2)
    open_questions: list[str] = Field(default_factory=list, max_length=12)
    confirmation_status: ConfirmationStatus = "pending"
    confirmation_question: str = Field(
        default=(
            "Esto es lo que entendí hasta ahora. ¿Lo ves igual, qué corregirías "
            "y cuál de estos temas te gustaría profundizar primero?"
        ),
        min_length=3,
        max_length=1_000,
    )
    weekly_action: WeeklyAction | None = None

    @model_validator(mode="after")
    def unknown_only_decisions_cannot_be_focuses(self) -> "NarrativeAssessment":
        supported_decisions = {
            finding.decision
            for finding in self.findings
            if finding.status in {"observed", "hypothesis"}
        }
        for focus in self.proposed_focuses:
            if focus.decision not in supported_decisions:
                raise ValueError("an unknown-only decision cannot be proposed as focus")
        action = self.weekly_action
        if action is not None:
            if self.confirmation_status == "pending":
                raise ValueError(
                    "the weekly action comes after the owner confirms the reading"
                )
            if action.decision not in supported_decisions:
                raise ValueError("the weekly action needs a finding in its area")
        return self


def build_narrative_assessment(
    intake: DiagnosticIntake,
    *,
    company_summary: str,
    company_understanding: CompanyUnderstanding | Mapping[str, object],
    findings: Sequence[NarrativeFinding | Mapping[str, object]],
    proposed_focuses: Sequence[FocusProposal | Mapping[str, object]] = (),
    open_questions: Sequence[str] = (),
    confirmation_status: ConfirmationStatus = "pending",
    weekly_action: WeeklyAction | Mapping[str, object] | None = None,
    today: date | None = None,
) -> NarrativeAssessment:
    """Validate a narrative assessment against its local evidence pack."""
    evidence_by_id = {item.evidence_id: item for item in intake.evidence}
    normalized_findings = [
        item
        if isinstance(item, NarrativeFinding)
        else NarrativeFinding.model_validate(item)
        for item in findings
    ]
    normalized_focuses = [
        item if isinstance(item, FocusProposal) else FocusProposal.model_validate(item)
        for item in proposed_focuses
    ]
    action = (
        None
        if weekly_action is None
        else weekly_action
        if isinstance(weekly_action, WeeklyAction)
        else WeeklyAction.model_validate(weekly_action)
    )
    traced: list[NarrativeFinding | FocusProposal | WeeklyAction] = [
        *normalized_findings,
        *normalized_focuses,
        *([action] if action is not None else []),
    ]
    for item in traced:
        if set(item.evidence_ids) - set(evidence_by_id):
            raise ValueError("narrative assessment references unknown evidence")
        if any(
            evidence_by_id[evidence_id].decision not in (None, item.decision)
            for evidence_id in item.evidence_ids
        ):
            raise ValueError("narrative assessment crosses decision evidence")
    if action is not None:
        cited = " ".join(
            str(evidence_by_id[evidence_id].value)
            for evidence_id in action.evidence_ids
        )
        check_weekly_action(action, cited, today or date.today())
    return NarrativeAssessment(
        company_summary=company_summary,
        company_understanding=(
            company_understanding
            if isinstance(company_understanding, CompanyUnderstanding)
            else CompanyUnderstanding.model_validate(company_understanding)
        ),
        findings=normalized_findings,
        proposed_focuses=normalized_focuses,
        open_questions=list(open_questions),
        confirmation_status=confirmation_status,
        weekly_action=action,
    )


def render_narrative_assessment(assessment: NarrativeAssessment) -> str:
    """Render a compact entrepreneur-facing assessment without a score table."""
    lines = ["## Esto es lo que entendí", "", assessment.company_summary, ""]
    lines.extend(["### Empresa que entendí", ""])
    labels = {
        "industry": "Industria",
        "offering": "Oferta",
        "target_customer": "Cliente objetivo",
        "business_model": "Modelo de negocio",
        "primary_challenge": "Reto actual",
    }
    for field, label in labels.items():
        value = getattr(assessment.company_understanding, field)
        if value is not None:
            lines.append(f"- **{label}:** {value}")
        else:
            lines.append(f"- **{label}:** todavía no lo sé")
    lines.extend(["", "### Señales que veo", ""])
    for finding in assessment.findings:
        qualifier = {
            "observed": "observé",
            "hypothesis": "parece",
            "unknown": "todavía no sé",
            "not_applicable": "no aplica",
        }[finding.status]
        lines.append(
            f"- **{finding.decision.title()}** — {qualifier}: "
            f"{finding.statement}. Implicación: {finding.implication}"
        )
    if assessment.open_questions:
        lines.extend(["", "### Lo que todavía necesito entender", ""])
        lines.extend(f"- {question}" for question in assessment.open_questions)
    if assessment.proposed_focuses:
        lines.extend(["", "### Dónde podríamos profundizar", ""])
        for focus in assessment.proposed_focuses:
            lines.append(f"- **{focus.decision.title()}** — {focus.rationale}")
    lines.extend(["", assessment.confirmation_question])
    return "\n".join(lines)


def assessment_to_artifact(assessment: NarrativeAssessment) -> dict[str, object]:
    """Return a stable JSON-safe representation for a local approved artifact."""
    return assessment.model_dump(mode="json")
