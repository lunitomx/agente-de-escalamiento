"""Narrative-only internal artifacts for the E65 OPPP and Vision MVP.

This module builds in-memory drafts. It never reads private sources, resolves a
person, or writes company state. A separate trusted adapter must perform any
actual persistence after an explicit confirmation bound to this exact draft.
"""

from __future__ import annotations

import hashlib
import json
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.procedure_compiler import compile_mvp_procedures


_DETAIL_MINIMUM = 20
_NARRATIVE_STATUS = Literal["known", "unknown", "not-applicable"]
_NARRATIVE_ORIGIN = Literal["personal-statement", "company-local", "model-hypothesis"]
_CONTEXT = Literal["personal", "company"]
_COMMITMENT_FIELDS = ("owner", "kpi", "who_what_when", "review_cadence")
_ACCEPTANCE_CRITERIA = (
    "detailed narrative or explicit unknown",
    "owner KPI Who What When and cadence visible",
    "human confirmation before state persistence",
)
_ARTIFACT_SPECS: dict[str, tuple[_CONTEXT, tuple[str, ...], str]] = {
    "procedure.build-leader-oppp": (
        "personal",
        ("relationships", "achievements", "rituals", "wealth"),
        "state/leader/oppp.yaml",
    ),
    "procedure.build-vision-summary": (
        "company",
        ("purpose", "customer", "differentiator", "future_direction"),
        "state/company/strategy.yaml",
    ),
}


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class NarrativeAnswer(_StrictModel):
    """A response that preserves narrative detail or declares its absence."""

    status: _NARRATIVE_STATUS
    text: str | None = Field(default=None, max_length=500)
    origin: _NARRATIVE_ORIGIN | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_hidden_unknown_values(cls, value: object) -> object:
        if (
            isinstance(value, dict)
            and value.get("status") in {"unknown", "not-applicable"}
            and (value.get("text") is not None or value.get("origin") is not None)
        ):
            raise ValueError("unknown answer cannot carry text or origin")
        return value

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value in {"1", "2", "3", "4", "5"}:
            raise ValueError("narrative answer cannot be a Likert score")
        if value != value.strip() or len(value) < _DETAIL_MINIMUM:
            raise ValueError("narrative answer requires detailed text")
        return value

    @model_validator(mode="after")
    def validate_answer(self) -> "NarrativeAnswer":
        if self.status == "known":
            if self.text is None or self.origin is None:
                raise ValueError("known answer requires text and origin")
        elif self.text is not None or self.origin is not None:
            raise ValueError("unknown answer cannot carry text or origin")
        return self


class ArtifactConfirmation(_StrictModel):
    confirmation_id: str = Field(pattern=r"^[a-z][a-z0-9._-]{2,127}$")
    consent_receipt: str = Field(pattern=r"^[a-z][a-z0-9._-]{2,127}$")
    confirmed_by: str = Field(pattern=r"^[a-z][a-z0-9._-]{2,127}$")
    artifact_id: str = Field(pattern=r"^artifact\.sha256\.[a-f0-9]{64}$")
    artifact_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class ProposedPersistence(_StrictModel):
    mode: Literal["proposed", "confirmed"]
    path: str = Field(pattern=r"^state/[a-z0-9][a-z0-9._/-]*\.yaml$")
    confirmation: ArtifactConfirmation | None = None
    writes_state: Literal[False] = False

    @model_validator(mode="after")
    def validate_confirmation(self) -> "ProposedPersistence":
        if self.mode == "confirmed" and self.confirmation is None:
            raise ValueError("confirmed persistence requires a confirmation")
        if self.mode == "proposed" and self.confirmation is not None:
            raise ValueError("proposed persistence must not carry confirmation")
        return self


def _canonical_payload(
    procedure_id: str,
    context: _CONTEXT,
    fields: Mapping[str, NarrativeAnswer],
    commitments: Mapping[str, NarrativeAnswer],
    assumptions: list[str],
    open_questions: list[str],
    acceptance_criteria: tuple[str, ...],
    path: str,
) -> bytes:
    payload = {
        "acceptance_criteria": acceptance_criteria,
        "assumptions": assumptions,
        "commitments": {
            name: answer.model_dump(mode="json")
            for name, answer in sorted(commitments.items())
        },
        "context": context,
        "fields": {
            name: answer.model_dump(mode="json")
            for name, answer in sorted(fields.items())
        },
        "open_questions": open_questions,
        "path": path,
        "procedure_id": procedure_id,
    }
    return json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode()


def _artifact_digest(
    procedure_id: str,
    context: _CONTEXT,
    fields: Mapping[str, NarrativeAnswer],
    commitments: Mapping[str, NarrativeAnswer],
    assumptions: list[str],
    open_questions: list[str],
    acceptance_criteria: tuple[str, ...],
    path: str,
) -> str:
    return hashlib.sha256(
        _canonical_payload(
            procedure_id,
            context,
            fields,
            commitments,
            assumptions,
            open_questions,
            acceptance_criteria,
            path,
        )
    ).hexdigest()


class NarrativeArtifact(_StrictModel):
    procedure_id: Literal[
        "procedure.build-leader-oppp", "procedure.build-vision-summary"
    ]
    context: _CONTEXT
    fields: dict[str, NarrativeAnswer]
    commitments: dict[str, NarrativeAnswer]
    assumptions: list[str]
    open_questions: list[str]
    acceptance_criteria: tuple[str, ...]
    persistence: ProposedPersistence
    artifact_id: str = Field(pattern=r"^artifact\.sha256\.[a-f0-9]{64}$")
    artifact_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="before")
    @classmethod
    def normalize_mapping_order(cls, value: object) -> object:
        """Accept mapping order from callers, then store canonical field order."""
        if not isinstance(value, Mapping):
            return value
        payload = dict(value)
        procedure_id = payload.get("procedure_id")
        if not isinstance(procedure_id, str):
            return payload
        specification = _ARTIFACT_SPECS.get(procedure_id)
        if specification is None:
            return payload
        _, field_names, _ = specification
        for name, expected in (
            ("fields", field_names),
            ("commitments", _COMMITMENT_FIELDS),
        ):
            mapping = payload.get(name)
            if isinstance(mapping, Mapping) and set(mapping) == set(expected):
                payload[name] = {key: mapping[key] for key in expected}
        return payload

    @model_validator(mode="after")
    def validate_public_surface(self) -> "NarrativeArtifact":
        context, field_names, state_path = _ARTIFACT_SPECS[self.procedure_id]
        if self.context != context:
            raise ValueError("context does not match procedure surface")
        if tuple(self.fields) != field_names:
            raise ValueError("artifact fields do not match the procedure surface")
        if tuple(self.commitments) != _COMMITMENT_FIELDS:
            raise ValueError("commitments do not match the procedure surface")
        if self.persistence.path != state_path:
            raise ValueError("persistence path does not match procedure surface")
        if (
            self.persistence.mode != "proposed"
            or self.persistence.confirmation is not None
        ):
            raise ValueError("narrative artifact must retain proposed persistence")
        all_answers = {**self.fields, **self.commitments}
        expected_assumptions = [
            name
            for name, answer in all_answers.items()
            if answer.origin == "model-hypothesis"
        ]
        if self.assumptions != expected_assumptions:
            raise ValueError("assumptions must list every model hypothesis")
        expected_questions = [
            name for name, answer in all_answers.items() if answer.status == "unknown"
        ]
        if self.open_questions != expected_questions:
            raise ValueError("open questions must list every unknown answer")
        if self.acceptance_criteria != _ACCEPTANCE_CRITERIA:
            raise ValueError(
                "acceptance criteria do not match narrative artifact policy"
            )
        expected_digest = _artifact_digest(
            self.procedure_id,
            self.context,
            self.fields,
            self.commitments,
            self.assumptions,
            self.open_questions,
            self.acceptance_criteria,
            self.persistence.path,
        )
        if self.artifact_digest != expected_digest:
            raise ValueError("artifact digest does not match canonical payload")
        if self.artifact_id != f"artifact.sha256.{expected_digest}":
            raise ValueError("artifact ID does not match canonical payload")
        return self


def _compiled_contract_ids() -> set[str]:
    return {contract.id for contract in compile_mvp_procedures().contracts}


def _answers(
    values: Mapping[str, NarrativeAnswer | Mapping[str, object]],
    expected: tuple[str, ...],
) -> dict[str, NarrativeAnswer]:
    if set(values) != set(expected):
        raise ValueError("artifact fields do not match the procedure surface")
    return {field: NarrativeAnswer.model_validate(values[field]) for field in expected}


def _validate_origins(
    context: _CONTEXT, answers: Mapping[str, NarrativeAnswer], *, require_known: bool
) -> None:
    known = [answer for answer in answers.values() if answer.status == "known"]
    if require_known and not known:
        raise ValueError("narrative artifact requires at least one detailed answer")
    if context == "personal" and any(
        answer.origin != "personal-statement" for answer in known
    ):
        raise ValueError("personal artifact accepts only personal statements")
    if context == "company" and any(
        answer.origin == "personal-statement" for answer in known
    ):
        raise ValueError(
            "company artifact cannot present personal statement as company fact"
        )


def build_narrative_artifact(
    procedure_id: Literal[
        "procedure.build-leader-oppp", "procedure.build-vision-summary"
    ],
    fields: Mapping[str, NarrativeAnswer | Mapping[str, object]],
    *,
    commitments: Mapping[str, NarrativeAnswer | Mapping[str, object]],
) -> NarrativeArtifact:
    """Build a proposed draft from a compiled procedure and interview inputs."""
    if procedure_id not in _compiled_contract_ids():
        raise ValueError("OPPP or Vision procedure is not in the compiled MVP")
    context, field_names, state_path = _ARTIFACT_SPECS[procedure_id]
    resolved_fields = _answers(fields, field_names)
    resolved_commitments = _answers(commitments, _COMMITMENT_FIELDS)
    _validate_origins(context, resolved_fields, require_known=True)
    _validate_origins(context, resolved_commitments, require_known=False)
    all_answers = {**resolved_fields, **resolved_commitments}
    assumptions = [
        name
        for name, answer in all_answers.items()
        if answer.origin == "model-hypothesis"
    ]
    open_questions = [
        name for name, answer in all_answers.items() if answer.status == "unknown"
    ]
    digest = _artifact_digest(
        procedure_id,
        context,
        resolved_fields,
        resolved_commitments,
        assumptions,
        open_questions,
        _ACCEPTANCE_CRITERIA,
        state_path,
    )
    return NarrativeArtifact(
        procedure_id=procedure_id,
        context=context,
        fields=resolved_fields,
        commitments=resolved_commitments,
        assumptions=assumptions,
        open_questions=open_questions,
        acceptance_criteria=_ACCEPTANCE_CRITERIA,
        persistence=ProposedPersistence(mode="proposed", path=state_path),
        artifact_id=f"artifact.sha256.{digest}",
        artifact_digest=digest,
    )


def request_confirmed_persistence(
    artifact: NarrativeArtifact, confirmation: ArtifactConfirmation | None
) -> ProposedPersistence:
    """Bind consent to exactly one valid draft; never write state from this runtime."""
    validated = NarrativeArtifact.model_validate(artifact.model_dump(mode="json"))
    if confirmation is None:
        raise ValueError("explicit human confirmation is required")
    if (
        confirmation.artifact_id != validated.artifact_id
        or confirmation.artifact_digest != validated.artifact_digest
    ):
        raise ValueError("confirmation does not match narrative artifact")
    return ProposedPersistence(
        mode="confirmed",
        path=validated.persistence.path,
        confirmation=confirmation,
    )
