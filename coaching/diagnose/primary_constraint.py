"""Narrative-first S65.3 primary-constraint diagnosis.

This runtime consumes only the compiled E65 MVP contract and local typed
evidence. It neither scores a company nor writes company state before E52.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from coaching.diagnose.models import DiagnosticEvidence
from coaching.diagnose.narrative import CompanyUnderstanding
from validators.procedure_compiler import compile_mvp_procedures
from validators.procedure_contract import (
    ProcedureContract,
    ProcedureOutputContract,
    StateUpdate,
)


Decision = Literal["people", "strategy", "execution", "cash"]
FindingStatus = Literal["known", "hypothesis", "unknown"]
PERSISTENCE_REASON = "E52 no ha entregado un adaptador confiable de consentimiento y persistencia; la propuesta no se guardó."
_DECISIONS: tuple[Decision, ...] = ("people", "strategy", "execution", "cash")
_PROCEDURE_ID = "procedure.diagnose-primary-constraint"
_NARRATIVE_SOURCE_KINDS = {"conversation", "user_file", "crm_export", "profile", "opsp"}


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DecisionAssessment(_StrictModel):
    """Detailed evidence-based view of exactly one decision area."""

    decision: Decision
    status: FindingStatus
    rationale: str = Field(min_length=3, max_length=1_000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("evidence_ids")
    @classmethod
    def evidence_ids_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("assessment evidence IDs must be unique")
        return value

    @model_validator(mode="after")
    def certainty_matches_evidence(self) -> "DecisionAssessment":
        if self.status in {"known", "hypothesis"} and not self.evidence_ids:
            raise ValueError("known or hypothesis assessment requires evidence")
        if self.status == "unknown" and self.evidence_ids:
            raise ValueError("unknown assessment must not imply supporting evidence")
        return self


class PrimaryConstraintRequest(_StrictModel):
    """Input for a one-focus diagnosis, never a rating questionnaire."""

    company_summary: str = Field(min_length=3, max_length=2_000)
    company_understanding: CompanyUnderstanding
    evidence: list[DiagnosticEvidence] = Field(min_length=1, max_length=64)
    decision_assessments: list[DecisionAssessment] = Field(min_length=4, max_length=8)
    requested_primary_decision: Decision | None = None
    assumptions: list[str] = Field(default_factory=list, max_length=20)
    open_questions: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("assumptions", "open_questions")
    @classmethod
    def distinct_detailed_text(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("duplicate diagnostic text")
        if any(not item.strip() for item in value):
            raise ValueError("diagnostic text must not be blank")
        return value

    @model_validator(mode="after")
    def assessments_are_complete_and_locally_traced(self) -> "PrimaryConstraintRequest":
        decisions = [item.decision for item in self.decision_assessments]
        if set(decisions) != set(_DECISIONS) or len(decisions) != len(set(decisions)):
            raise ValueError("each decision must appear exactly once")
        evidence_by_id = {item.evidence_id: item for item in self.evidence}
        if len(evidence_by_id) != len(self.evidence):
            raise ValueError("diagnostic evidence IDs must be unique")
        for assessment in self.decision_assessments:
            unknown = set(assessment.evidence_ids) - set(evidence_by_id)
            if unknown:
                raise ValueError("assessment references unknown evidence")
            for evidence_id in assessment.evidence_ids:
                evidence = evidence_by_id[evidence_id]
                if evidence.decision != assessment.decision:
                    raise ValueError("assessment crosses decision evidence")
                if evidence.source_kind not in _NARRATIVE_SOURCE_KINDS:
                    raise ValueError("assessment uses unsupported evidence source")
                if evidence.answer_status != "fact":
                    raise ValueError("assessment requires factual narrative evidence")
                if not _is_detailed_narrative(evidence.value):
                    raise ValueError("assessment requires detailed narrative evidence")
        return self


class DecisionExplanation(_StrictModel):
    decision: Decision
    status: FindingStatus
    priority_reason: str = Field(min_length=3, max_length=1_000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=12)


class PrimaryConstraint(_StrictModel):
    decision: Decision
    status: Literal["known", "hypothesis"]
    rationale: str = Field(min_length=3, max_length=1_000)
    evidence_ids: list[str] = Field(min_length=1, max_length=12)


class PrimaryConstraintDiagnosis(_StrictModel):
    procedure_id: Literal["procedure.diagnose-primary-constraint"]
    company_summary: str
    company_understanding: CompanyUnderstanding
    decision_explanations: list[DecisionExplanation] = Field(min_length=4, max_length=4)
    primary_constraint: PrimaryConstraint | None
    missing_evidence: list[Decision]
    output_contract: ProcedureOutputContract
    proposed_state_updates: list[StateUpdate] = Field(min_length=1)
    persistence_status: Literal["proposed_not_persisted"]
    persistence_reason: str
    confirmation_prompt: str

    @model_validator(mode="after")
    def choose_one_constraint_or_visible_gap(self) -> "PrimaryConstraintDiagnosis":
        if self.primary_constraint is None and not self.missing_evidence:
            raise ValueError("diagnosis needs one primary constraint or evidence gap")
        if self.primary_constraint is not None and self.missing_evidence:
            raise ValueError("diagnosis cannot select a constraint and evidence gap")
        return self


def _diagnosis_contract() -> ProcedureContract:
    """Read only the approved compiled MVP procedure, never raw sources."""
    return next(
        contract
        for contract in compile_mvp_procedures().contracts
        if contract.id == _PROCEDURE_ID
    )


def _output_contract(
    contract: ProcedureContract, request: PrimaryConstraintRequest
) -> ProcedureOutputContract:
    questions = list(
        dict.fromkeys(
            [*request.open_questions, *contract.output_contract.open_questions]
        )
    )
    payload = contract.output_contract.model_dump(mode="python")
    payload["assumptions"] = list(request.assumptions)
    payload["open_questions"] = questions
    return ProcedureOutputContract.model_validate(payload)


def _is_detailed_narrative(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip()
    return (
        len(normalized) >= 20
        and len(normalized.split()) >= 4
        and normalized.lower() not in {"n/a", "none", "unknown", "generic", "general"}
    )


def _explain(assessment: DecisionAssessment, selected: bool) -> DecisionExplanation:
    if selected:
        reason = (
            "Se prioriza porque la dirección pidió profundizar y hay evidencia local."
        )
    elif assessment.status == "unknown":
        reason = "No se prioriza: falta una respuesta detallada y evidencia local."
    else:
        reason = (
            "No se prioriza ahora: se conserva la señal para una siguiente iteración."
        )
    return DecisionExplanation(
        decision=assessment.decision,
        status=assessment.status,
        priority_reason=reason,
        evidence_ids=assessment.evidence_ids,
    )


def diagnose_primary_constraint(
    request: PrimaryConstraintRequest,
    *,
    persistence_requested: bool = False,
    state_root: Path | None = None,
) -> PrimaryConstraintDiagnosis:
    """Propose one requested, evidence-backed focus or state what is missing.

    Attempted persistence is observable but intentionally non-mutating until E52.
    """
    del persistence_requested, state_root
    contract = _diagnosis_contract()
    by_decision = {item.decision: item for item in request.decision_assessments}
    requested = request.requested_primary_decision
    missing: list[Decision] = [
        assessment.decision
        for assessment in request.decision_assessments
        if assessment.status == "unknown"
    ]
    selected = (
        by_decision[requested]
        if requested is not None
        and not missing
        and by_decision[requested].status in {"known", "hypothesis"}
        else None
    )
    primary = (
        PrimaryConstraint(
            decision=selected.decision,
            status=cast(Literal["known", "hypothesis"], selected.status),
            rationale=selected.rationale,
            evidence_ids=selected.evidence_ids,
        )
        if selected is not None
        else None
    )
    if primary is None and not missing:
        missing = list(_DECISIONS)
    explanations = [
        _explain(by_decision[decision], decision == requested and primary is not None)
        for decision in _DECISIONS
    ]
    target = requested.title() if requested is not None else "cada decisión"
    return PrimaryConstraintDiagnosis(
        procedure_id=_PROCEDURE_ID,
        company_summary=request.company_summary,
        company_understanding=request.company_understanding,
        decision_explanations=explanations,
        primary_constraint=primary,
        missing_evidence=missing,
        output_contract=_output_contract(contract, request),
        proposed_state_updates=list(contract.state_updates),
        persistence_status="proposed_not_persisted",
        persistence_reason=PERSISTENCE_REASON,
        confirmation_prompt=f"Esto es lo que entendí. ¿Confirmas o corriges el enfoque en {target} antes de proponer un siguiente paso?",
    )


def explain_primary_constraint(
    request: PrimaryConstraintRequest,
    *,
    persistence_requested: bool = False,
    state_root: Path | None = None,
) -> PrimaryConstraintDiagnosis:
    """Named alias for callers that need an explicit non-mutating operation."""
    return diagnose_primary_constraint(
        request, persistence_requested=persistence_requested, state_root=state_root
    )
