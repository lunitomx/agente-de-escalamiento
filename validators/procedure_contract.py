"""Fail-closed internal procedure contracts for E65.

This module defines authored procedure metadata only.  It never reads source
corpora, executes a company action, or persists a completed company artifact.
Evidence is checked solely against the safe E64 canonical release.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.ontology_v2 import CanonicalRelease, OriginKind


_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_OPAQUE = re.compile(r"^digest\.sha256\.[a-f0-9]{64}$")
_STATE_PATH = re.compile(r"^state/[a-z0-9][a-z0-9._/-]*\.(?:yaml|jsonl)$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _id(value: str, label: str) -> str:
    if _ID.fullmatch(value) is None:
        raise ValueError(f"unsafe {label}")
    return value


def _text(value: str, label: str) -> str:
    if not value.strip() or value != value.strip() or len(value) > 500:
        raise ValueError(f"unsafe {label}")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError(f"unsafe {label}")
    return value


class ProcedureInput(_StrictModel):
    id: str = Field(min_length=3, max_length=128)
    description: str = Field(min_length=1, max_length=500)
    required: bool
    accepted_statuses: list[Literal["known", "unknown", "not-applicable"]] = Field(
        min_length=1, max_length=3
    )

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _id(value, "input ID")

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        return _text(value, "input description")

    @field_validator("accepted_statuses")
    @classmethod
    def validate_statuses(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate input status")
        return values


class InterviewQuestion(_StrictModel):
    id: str = Field(min_length=3, max_length=128)
    prompt: str = Field(min_length=1, max_length=500)
    required: bool

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _id(value, "question ID")

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        return _text(value, "question prompt")


class ProcedureStep(_StrictModel):
    id: str = Field(min_length=3, max_length=128)
    action: str = Field(min_length=1, max_length=500)
    produces: list[str] = Field(min_length=1, max_length=16)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _id(value, "step ID")

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        return _text(value, "step action")

    @field_validator("produces")
    @classmethod
    def validate_produces(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate step output")
        return [_id(value, "step output ID") for value in values]


class Rule(_StrictModel):
    id: str = Field(min_length=3, max_length=128)
    statement: str = Field(min_length=1, max_length=500)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _id(value, "rule ID")

    @field_validator("statement")
    @classmethod
    def validate_statement(cls, value: str) -> str:
        return _text(value, "rule statement")


class OutputValue(_StrictModel):
    """A bounded result slot; unknown is first-class and cannot be silent."""

    status: Literal["known", "unknown", "not-applicable"]
    value: str | None = Field(default=None, max_length=500)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str | None) -> str | None:
        return None if value is None else _text(value, "output value")

    @model_validator(mode="after")
    def validate_status_value(self) -> "OutputValue":
        if self.status == "known" and self.value is None:
            raise ValueError("known value requires a non-empty value")
        if self.status != "known" and self.value is not None:
            raise ValueError("unknown or not-applicable value must be null")
        return self


class ProcedureOutputContract(_StrictModel):
    artifact: OutputValue
    assumptions: list[str] = Field(default_factory=list, max_length=32)
    open_questions: list[str] = Field(default_factory=list, max_length=32)
    owner: OutputValue
    kpi: OutputValue
    who_what_when: OutputValue
    review_cadence: OutputValue

    @field_validator("assumptions", "open_questions")
    @classmethod
    def validate_text_list(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate output text")
        return [_text(value, "output text") for value in values]

    @model_validator(mode="after")
    def require_questions_for_unknowns(self) -> "ProcedureOutputContract":
        values = (
            self.artifact,
            self.owner,
            self.kpi,
            self.who_what_when,
            self.review_cadence,
        )
        if (
            any(value.status == "unknown" for value in values)
            and not self.open_questions
        ):
            raise ValueError("unknown output values require open questions")
        return self


class StateUpdate(_StrictModel):
    id: str = Field(min_length=3, max_length=128)
    path: str = Field(min_length=8, max_length=256)
    mode: Literal["proposed", "confirmed"]

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _id(value, "state update ID")

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        if _STATE_PATH.fullmatch(value) is None or ".." in value:
            raise ValueError("unsafe state update path")
        return value


class ProcedureHandoff(_StrictModel):
    next_procedure_id: str = Field(min_length=3, max_length=128)
    condition: str = Field(min_length=1, max_length=500)

    @field_validator("next_procedure_id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _id(value, "handoff procedure ID")

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, value: str) -> str:
        return _text(value, "handoff condition")


class ProcedureContract(_StrictModel):
    """An authored, non-executing internal procedure contract."""

    id: str = Field(min_length=3, max_length=128)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$", max_length=32)
    provenance: OriginKind
    trigger: list[str] = Field(min_length=1, max_length=16)
    non_trigger: list[str] = Field(min_length=1, max_length=16)
    objective: str = Field(min_length=1, max_length=500)
    required_inputs: list[ProcedureInput] = Field(min_length=1, max_length=32)
    optional_inputs: list[ProcedureInput] = Field(default_factory=list, max_length=32)
    interview_questions: list[InterviewQuestion] = Field(min_length=1, max_length=64)
    steps: list[ProcedureStep] = Field(min_length=1, max_length=64)
    decision_rules: list[Rule] = Field(min_length=1, max_length=64)
    warnings: list[Rule] = Field(min_length=1, max_length=64)
    output_contract: ProcedureOutputContract
    acceptance_criteria: list[Rule] = Field(min_length=1, max_length=64)
    state_updates: list[StateUpdate] = Field(min_length=1, max_length=16)
    handoff: ProcedureHandoff
    evidence_refs: list[str] = Field(min_length=1, max_length=64)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _id(value, "procedure ID")

    @field_validator("trigger", "non_trigger")
    @classmethod
    def validate_texts(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate procedure condition")
        return [_text(value, "procedure condition") for value in values]

    @field_validator("objective")
    @classmethod
    def validate_objective(cls, value: str) -> str:
        return _text(value, "procedure objective")

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate evidence reference")
        for value in values:
            if _OPAQUE.fullmatch(value) is None:
                raise ValueError("unsafe opaque reference")
        return sorted(values)

    @model_validator(mode="after")
    def validate_unique_contract_members(self) -> "ProcedureContract":
        inputs = self.required_inputs + self.optional_inputs
        input_ids = [item.id for item in inputs]
        if len(input_ids) != len(set(input_ids)):
            raise ValueError("duplicate procedure input ID")
        if any(not item.required for item in self.required_inputs):
            raise ValueError("required inputs must be marked required")
        if any(item.required for item in self.optional_inputs):
            raise ValueError("optional inputs must not be marked required")
        for label, members in (
            ("question", self.interview_questions),
            ("step", self.steps),
            ("decision rule", self.decision_rules),
            ("warning", self.warnings),
            ("acceptance criterion", self.acceptance_criteria),
            ("state update", self.state_updates),
        ):
            ids = [item.id for item in members]
            if len(ids) != len(set(ids)):
                raise ValueError(f"duplicate {label} ID")
        return self


def load_procedure_contract(path: Path) -> ProcedureContract:
    """Load authored YAML without permitting arbitrary source documents."""
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
        return ProcedureContract.model_validate(parsed)
    except Exception as exc:
        raise ValueError("procedure contract invalid") from exc


def validate_procedure_against_release(
    procedure: ProcedureContract, release: CanonicalRelease
) -> None:
    """Fail closed unless every opaque reference belongs to approved E64 evidence."""
    release_refs = {
        evidence_ref for node in release.nodes for evidence_ref in node.evidence_refs
    }
    unknown_refs = set(procedure.evidence_refs) - release_refs
    if unknown_refs:
        raise ValueError("procedure contract references unknown release evidence")
