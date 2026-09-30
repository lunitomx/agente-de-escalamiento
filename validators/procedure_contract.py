"""Fail-closed internal procedure contracts for E65.

This module defines authored procedure metadata only.  It never reads source
corpora, executes a company action, or persists a completed company artifact.
Evidence is checked solely against the safe E64 canonical release.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import re
import tomllib
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.ontology_v2 import OriginKind, load_canonical_release


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
    """Allow concise authored labels, never locators, URLs, or source passages."""
    if (
        not value.strip()
        or value != value.strip()
        or len(value) > 96
        or len(value.split()) > 12
    ):
        raise ValueError(f"unsafe {label}")
    if (
        any(ord(char) < 32 or ord(char) == 127 for char in value)
        or ("/" in value and value != "Who/What/When")
        or "\\" in value
        or "://" in value
        or value.lower().startswith("www.")
        or re.search(
            r"\b(source[_ -]?id|source text|verbatim|copyright|all rights reserved|page \d+)\b",
            value,
            flags=re.IGNORECASE,
        )
    ):
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
    origin: OriginKind | None = None
    evidence_ids: list[str] = Field(default_factory=list, max_length=32)
    consent_receipt: str | None = Field(default=None, max_length=128)
    confirmed_by: str | None = Field(default=None, max_length=128)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str | None) -> str | None:
        return None if value is None else _text(value, "output value")

    @field_validator("evidence_ids")
    @classmethod
    def validate_evidence_ids(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate output evidence ID")
        return [_id(value, "output evidence ID") for value in values]

    @field_validator("consent_receipt")
    @classmethod
    def validate_consent_receipt(cls, value: str | None) -> str | None:
        return None if value is None else _id(value, "consent receipt")

    @field_validator("confirmed_by")
    @classmethod
    def validate_confirmed_by(cls, value: str | None) -> str | None:
        return None if value is None else _id(value, "human confirmer")

    @model_validator(mode="after")
    def validate_status_value(self) -> "OutputValue":
        if self.status == "known":
            if self.value is None:
                raise ValueError("known value requires a non-empty value")
            if self.origin not in {
                OriginKind.SOURCE_EXPLICIT,
                OriginKind.SOURCE_SYNTHESIS,
                OriginKind.COMPANY_LOCAL,
            }:
                raise ValueError("known value requires an allowed typed origin")
            if (
                not self.evidence_ids
                or self.consent_receipt is None
                or self.confirmed_by is None
            ):
                raise ValueError(
                    "known value requires evidence, consent, and human confirmation"
                )
        elif (
            self.value is not None
            or self.origin is not None
            or self.evidence_ids
            or self.consent_receipt is not None
            or self.confirmed_by is not None
        ):
            raise ValueError(
                "unknown or not-applicable value must not carry a value or evidence"
            )
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


class StateConfirmation(_StrictModel):
    record_id: str = Field(min_length=3, max_length=128)
    origin: Literal[OriginKind.COMPANY_LOCAL]
    consent_receipt: str = Field(min_length=3, max_length=128)
    confirmed_by: str = Field(min_length=3, max_length=128)

    @field_validator("record_id", "consent_receipt", "confirmed_by")
    @classmethod
    def validate_confirmation_id(cls, value: str) -> str:
        return _id(value, "state confirmation ID")


class StateUpdate(_StrictModel):
    id: str = Field(min_length=3, max_length=128)
    path: str = Field(min_length=8, max_length=256)
    mode: Literal["proposed", "confirmed"]
    confirmation: StateConfirmation | None = None

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

    @model_validator(mode="after")
    def validate_confirmation(self) -> "StateUpdate":
        if self.mode == "confirmed" and self.confirmation is None:
            raise ValueError("confirmed state update requires a human consent record")
        if self.mode == "proposed" and self.confirmation is not None:
            raise ValueError("proposed state update must not carry a confirmation")
        return self


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


class _TrustedRegistry(_StrictModel):
    """Allowlisted local IDs supplied by E49/E52/E55 adapters at validation time."""

    schema_version: Literal[1]
    evidence_ids: list[str] = Field(default_factory=list, max_length=256)
    consent_receipts: list[str] = Field(default_factory=list, max_length=256)
    human_ids: list[str] = Field(default_factory=list, max_length=256)
    confirmation_record_ids: list[str] = Field(default_factory=list, max_length=256)

    @field_validator(
        "evidence_ids", "consent_receipts", "human_ids", "confirmation_record_ids"
    )
    @classmethod
    def validate_registry_ids(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate trusted registry ID")
        return sorted(_id(value, "trusted registry ID") for value in values)


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


_TRUSTED_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _trusted_workspace_root() -> Path:
    """Return the canonical ScaleUp project root after identity verification."""
    root = _TRUSTED_PROJECT_ROOT
    version_path = root / ".scaleup" / "VERSION"
    manifest_path = root / ".raise" / "manifest.yaml"
    project_path = root / "pyproject.toml"
    if (
        not version_path.is_file()
        or not manifest_path.is_file()
        or not project_path.is_file()
    ):
        raise ValueError("trusted workspace identity is invalid")
    if not version_path.read_text(encoding="utf-8").strip():
        raise ValueError("trusted workspace identity is invalid")
    try:
        project = tomllib.loads(project_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError("trusted workspace identity is invalid") from exc
    if project.get("project", {}).get("name") != "escala-coaching":
        raise ValueError("trusted workspace identity is invalid")
    if not (root / "ontology" / "v2" / "releases" / "s64.1.json").is_file():
        raise ValueError("trusted workspace release is unavailable")
    return root


def _load_local_trust_registry() -> _TrustedRegistry | None:
    """Derive trust only from the canonical E49/E52/E55 project state.

    The public validator has no path, provider, handle, or registry parameter.
    Its only authority is the active workspace used by the runner. A missing or
    malformed authorized Welcome receipt fails closed. E52 currently provides
    no authoritative human/confirmation register, so confirmed updates remain
    blocked until that dedicated adapter exists.
    """
    from coaching.core import read_yaml
    from coaching.evidence.facts import load_facts

    base_path = _trusted_workspace_root()
    payload = read_yaml(
        base_path / ".escala" / "agent" / "memory" / "welcome-state.yaml"
    )
    authorized_at = payload.get("authorized_at") if isinstance(payload, dict) else None
    if not isinstance(authorized_at, str) or not authorized_at:
        return None
    consent_receipt = (
        "consent.local." + hashlib.sha256(authorized_at.encode("utf-8")).hexdigest()
    )
    return _TrustedRegistry(
        schema_version=1,
        evidence_ids=[
            "evidence.local." + hashlib.sha256(fact.fact_id.encode("utf-8")).hexdigest()
            for fact in load_facts(base_path)
        ],
        consent_receipts=[consent_receipt],
        human_ids=[],
        confirmation_record_ids=[],
    )


def validate_procedure_against_release(procedure: ProcedureContract) -> None:
    """Validate against the canonical E64 release and mandatory local trust.

    The release is deliberately loaded from the verified project root. Callers
    cannot supply a release object, digest list, or alternate path.
    """
    root = _trusted_workspace_root()
    release = load_canonical_release(
        root / "ontology" / "v2" / "releases" / "s64.1.json"
    )
    release_refs = {
        evidence_ref for node in release.nodes for evidence_ref in node.evidence_refs
    }
    unknown_refs = set(procedure.evidence_refs) - release_refs
    if unknown_refs:
        raise ValueError("procedure contract references unknown release evidence")
    _validate_procedure_against_trust(procedure, _load_local_trust_registry())


def _validate_procedure_against_trust(
    procedure: ProcedureContract, registry: _TrustedRegistry | None
) -> None:
    """Fail closed for known output or confirmed state without local trust records.

    The registry is an adapter boundary: E49/E52/E55 must create it from
    authorized local evidence and consent records. This contract never invents
    those records or treats syntactically valid IDs as trustworthy by itself.
    """
    known_values = [
        value
        for value in (
            procedure.output_contract.artifact,
            procedure.output_contract.owner,
            procedure.output_contract.kpi,
            procedure.output_contract.who_what_when,
            procedure.output_contract.review_cadence,
        )
        if value.status == "known"
    ]
    confirmations = [
        update.confirmation
        for update in procedure.state_updates
        if update.mode == "confirmed" and update.confirmation is not None
    ]
    if not known_values and not confirmations:
        return
    if registry is None:
        raise ValueError("known or confirmed procedure state requires trusted registry")

    trusted_evidence = set(registry.evidence_ids)
    trusted_consent = set(registry.consent_receipts)
    trusted_humans = set(registry.human_ids)
    trusted_confirmation = set(registry.confirmation_record_ids)
    for value in known_values:
        if not set(value.evidence_ids).issubset(trusted_evidence):
            raise ValueError("known value references untrusted evidence")
        if value.consent_receipt not in trusted_consent:
            raise ValueError("known value references untrusted consent")
        if value.confirmed_by not in trusted_humans:
            raise ValueError("known value references untrusted human")
    for confirmation in confirmations:
        if confirmation.record_id not in trusted_confirmation:
            raise ValueError("confirmed update references untrusted confirmation")
        if confirmation.consent_receipt not in trusted_consent:
            raise ValueError("confirmed update references untrusted consent")
        if confirmation.confirmed_by not in trusted_humans:
            raise ValueError("confirmed update references untrusted human")
