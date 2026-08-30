"""Narrative-only internal artifacts for the E65 OPPP and Vision MVP.

This module builds in-memory drafts.  It intentionally does not read private
sources, resolve a person, or write company state.  A separate trusted adapter
must perform any actual persistence after explicit human confirmation.
"""

from __future__ import annotations

from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.procedure_compiler import compile_mvp_procedures


_DETAIL_MINIMUM = 20
_NARRATIVE_STATUS = Literal["known", "unknown", "not-applicable"]
_NARRATIVE_ORIGIN = Literal["personal-statement", "company-local", "model-hypothesis"]
_CONTEXT = Literal["personal", "company"]


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
_COMMITMENT_FIELDS = ("owner", "kpi", "who_what_when", "review_cadence")


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
    """Build a proposed draft from both compiled-contract and interview inputs."""
    if procedure_id not in _compiled_contract_ids():
        raise ValueError("OPPP or Vision procedure is not in the compiled MVP")
    context, field_names, state_path = _ARTIFACT_SPECS[procedure_id]
    resolved_fields = _answers(fields, field_names)
    resolved_commitments = _answers(commitments, _COMMITMENT_FIELDS)
    _validate_origins(context, resolved_fields, require_known=True)
    _validate_origins(context, resolved_commitments, require_known=False)

    all_answers = {**resolved_fields, **resolved_commitments}
    unknowns = [
        name for name, answer in all_answers.items() if answer.status == "unknown"
    ]
    hypotheses = [
        name
        for name, answer in resolved_fields.items()
        if answer.origin == "model-hypothesis"
    ]
    return NarrativeArtifact(
        procedure_id=procedure_id,
        context=context,
        fields=resolved_fields,
        commitments=resolved_commitments,
        assumptions=hypotheses,
        open_questions=unknowns,
        acceptance_criteria=(
            "detailed narrative or explicit unknown",
            "owner KPI Who What When and cadence visible",
            "human confirmation before state persistence",
        ),
        persistence=ProposedPersistence(mode="proposed", path=state_path),
    )


def request_confirmed_persistence(
    artifact: NarrativeArtifact, confirmation: ArtifactConfirmation | None
) -> ProposedPersistence:
    """Return a confirmation receipt; never write state from this runtime."""
    if confirmation is None:
        raise ValueError("explicit human confirmation is required")
    return ProposedPersistence(
        mode="confirmed",
        path=artifact.persistence.path,
        confirmation=confirmation,
    )
