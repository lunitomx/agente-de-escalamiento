"""Fail-closed internal capability map for the six E65 MVP procedures.

This module is intentionally below ESCALA's one public conversational door.
It accepts a normalized internal intent plus authorized evidence receipts and
returns the one procedure contract that may run.  It does not parse a user's
natural-language request, read private source material, or expose a command
catalog.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from escala_server.specialist_team import SPECIALIST_CONTRACTS
from validators.procedure_compiler import (
    MVP_PROCEDURE_IDS,
    CompiledMvpProcedures,
    compile_mvp_procedures,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CAPABILITY_MAP_PATH = REPOSITORY_ROOT / "capabilities" / "mvp" / "catalog.json"
_ID = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")
_RECEIPT = re.compile(r"^receipt\.[a-z0-9][a-z0-9.-]{2,127}$")
_LIFECYCLE = (
    "route",
    "collect-authorized-evidence",
    "run-procedure",
    "validate-artifact",
    "propose-state",
    "handoff",
)
_AREAS = {"cash", "execution", "people", "strategy"}


class CapabilityMapError(ValueError):
    """Raised when a map or its routing request does not meet its contract."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SpecialistProfile(_StrictModel):
    id: str
    area: Literal["cash", "execution", "people", "strategy"]
    kind: Literal["role-definition"]
    contract_ref: str

    @field_validator("id", "contract_ref")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        if not _ID.fullmatch(value):
            raise ValueError("specialist profile identifier is invalid")
        return value

    @model_validator(mode="after")
    def validate_common_contract_reference(self) -> "SpecialistProfile":
        if self.contract_ref != f"e45.specialist.{self.area}.v1":
            raise ValueError("specialist profile must use its E45 common contract")
        return self


class CapabilityBinding(_StrictModel):
    id: str
    procedure_id: str
    intents: tuple[str, ...] = Field(min_length=1, max_length=1)
    aliases: tuple[str, ...] = Field(min_length=1, max_length=8)
    evidence_kinds: tuple[str, ...] = Field(min_length=1, max_length=8)
    specialist_profiles: tuple[str, ...] = Field(min_length=1, max_length=4)

    @field_validator("id", "procedure_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        if not _ID.fullmatch(value):
            raise ValueError("capability identifier is invalid")
        return value

    @field_validator("intents", "aliases", "evidence_kinds", "specialist_profiles")
    @classmethod
    def validate_unique_identifiers(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)) or any(
            not _ID.fullmatch(value) for value in values
        ):
            raise ValueError("capability binding identifiers must be unique and safe")
        return values

    @model_validator(mode="after")
    def validate_capability_name(self) -> "CapabilityBinding":
        expected = f"capability.{self.procedure_id.removeprefix('procedure.')}"
        if self.id != expected:
            raise ValueError("capability id must be derived from its procedure")
        return self


class CapabilityMap(_StrictModel):
    schema_version: Literal[1]
    catalog_id: Literal["escala.mvp-capability-map.v1"]
    lifecycle: tuple[str, ...]
    specialist_profiles: tuple[SpecialistProfile, ...] = Field(
        min_length=4, max_length=4
    )
    capabilities: tuple[CapabilityBinding, ...] = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def validate_closed_surface(self) -> "CapabilityMap":
        if self.lifecycle != _LIFECYCLE:
            raise ValueError("capability lifecycle is incomplete or reordered")
        profile_ids = [profile.id for profile in self.specialist_profiles]
        areas = [profile.area for profile in self.specialist_profiles]
        if len(profile_ids) != len(set(profile_ids)) or set(areas) != _AREAS:
            raise ValueError(
                "specialist profiles must cover each E45 area exactly once"
            )
        procedure_ids = [binding.procedure_id for binding in self.capabilities]
        if len(procedure_ids) != len(set(procedure_ids)) or set(procedure_ids) != set(
            MVP_PROCEDURE_IDS
        ):
            raise ValueError("capability map must cover exactly the six MVP procedures")
        all_intents = [
            intent for binding in self.capabilities for intent in binding.intents
        ]
        all_aliases = [
            alias for binding in self.capabilities for alias in binding.aliases
        ]
        if len(all_intents) != len(set(all_intents)) or len(all_aliases) != len(
            set(all_aliases)
        ):
            raise ValueError("intent and alias resolution must be unambiguous")
        if set(all_intents).intersection(all_aliases):
            raise ValueError("an alias cannot act as another capability intent")
        known_profiles = set(profile_ids)
        for binding in self.capabilities:
            if not set(binding.specialist_profiles).issubset(known_profiles):
                raise ValueError("capability references an unknown specialist profile")
            if len(binding.specialist_profiles) != len(
                set(binding.specialist_profiles)
            ):
                raise ValueError("capability cannot overlap one specialist profile")
        return self


class AuthorizedEvidence(_StrictModel):
    kind: str
    receipt: str
    status: Literal["known", "confirmed"]

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, value: str) -> str:
        if not _ID.fullmatch(value):
            raise ValueError("evidence kind is invalid")
        return value

    @field_validator("receipt")
    @classmethod
    def validate_receipt(cls, value: str) -> str:
        if not _RECEIPT.fullmatch(value):
            raise ValueError("evidence receipt is invalid")
        return value


@dataclass(frozen=True)
class CapabilityRoute:
    """An explainable internal handoff, never a public command description."""

    capability_id: str
    procedure_id: str
    lifecycle: tuple[str, ...]
    specialist_profile_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    reason: str
    resolved_from_alias: str | None = None


def load_capability_map(path: Path = DEFAULT_CAPABILITY_MAP_PATH) -> CapabilityMap:
    """Load only the checked-in, source-safe E67 map."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CapabilityMapError("capability_map_unavailable") from exc
    try:
        return CapabilityMap.model_validate(raw)
    except ValueError as exc:
        raise CapabilityMapError(f"capability_map_invalid:{exc}") from exc


def validate_capability_map(
    capability_map: CapabilityMap,
    compiled: CompiledMvpProcedures | None = None,
) -> tuple[str, ...]:
    """Return deterministic drift errors without opening any source corpus."""
    active_compiled = compiled or compile_mvp_procedures()
    errors: list[str] = []
    contracts = {contract.id: contract for contract in active_compiled.contracts}
    traces = {trace.procedure_id: trace for trace in active_compiled.release.procedures}
    if set(contracts) != set(MVP_PROCEDURE_IDS) or set(traces) != set(
        MVP_PROCEDURE_IDS
    ):
        errors.append("mvp_procedure_release_incomplete")
    for binding in capability_map.capabilities:
        contract = contracts.get(binding.procedure_id)
        trace = traces.get(binding.procedure_id)
        if contract is None or trace is None:
            errors.append(f"missing_procedure:{binding.procedure_id}")
            continue
        required_kinds = {
            input_.id.removeprefix("input.") for input_ in contract.required_inputs
        }
        if set(binding.evidence_kinds) != required_kinds:
            errors.append(f"evidence_kind_mismatch:{binding.procedure_id}")
        if not trace.evidence_refs:
            errors.append(f"procedure_has_no_evidence:{binding.procedure_id}")
    expected_areas = set(SPECIALIST_CONTRACTS)
    map_areas = {profile.area for profile in capability_map.specialist_profiles}
    if map_areas != expected_areas:
        errors.append("specialist_contract_coverage_mismatch")
    return tuple(sorted(errors))


def route_capability(
    intent: str,
    evidence: tuple[AuthorizedEvidence, ...] | list[AuthorizedEvidence],
    capability_map: CapabilityMap | None = None,
    compiled: CompiledMvpProcedures | None = None,
) -> CapabilityRoute:
    """Resolve one declared intent after its required evidence is authorized.

    Unknown or missing evidence is a boundary, not a heuristic: callers must
    ask their next business question before selecting a procedure.
    """
    active_map = capability_map or load_capability_map()
    errors = validate_capability_map(active_map, compiled)
    if errors:
        raise CapabilityMapError(f"capability_map_drift:{','.join(errors)}")
    if not _ID.fullmatch(intent):
        raise CapabilityMapError("unknown_intent")
    aliases = {
        alias: binding
        for binding in active_map.capabilities
        for alias in binding.aliases
    }
    binding = next(
        (item for item in active_map.capabilities if intent in item.intents),
        aliases.get(intent),
    )
    if binding is None:
        raise CapabilityMapError("unknown_intent")
    safe_evidence = tuple(evidence)
    if not safe_evidence:
        raise CapabilityMapError("evidence_required")
    if not all(isinstance(item, AuthorizedEvidence) for item in safe_evidence):
        raise CapabilityMapError("evidence_invalid")
    present_kinds = {item.kind for item in safe_evidence}
    missing = set(binding.evidence_kinds) - present_kinds
    if missing:
        raise CapabilityMapError(f"evidence_missing:{','.join(sorted(missing))}")
    active_compiled = compiled or compile_mvp_procedures()
    trace = next(
        (
            item
            for item in active_compiled.release.procedures
            if item.procedure_id == binding.procedure_id
        ),
        None,
    )
    if trace is None or not trace.evidence_refs:
        raise CapabilityMapError("procedure_evidence_unavailable")
    resolved_from_alias = intent if intent in aliases else None
    return CapabilityRoute(
        capability_id=binding.id,
        procedure_id=binding.procedure_id,
        lifecycle=active_map.lifecycle,
        specialist_profile_ids=binding.specialist_profiles,
        evidence_refs=tuple(trace.evidence_refs),
        reason=(f"alias:{intent}" if resolved_from_alias else f"intent:{intent}"),
        resolved_from_alias=resolved_from_alias,
    )
