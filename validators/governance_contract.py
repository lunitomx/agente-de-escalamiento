"""Strict typed contracts for local governance identity and closure truth."""

from __future__ import annotations

from collections import Counter, defaultdict
from enum import Enum
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


_DISPOSITION_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*(?:/[a-z][a-z0-9-]*)?$")
_EPIC_ID_PATTERN = re.compile(r"^E[1-9][0-9]*$")
_EPIC_FOLDER_PATTERN = re.compile(
    r"^work/epics/e([1-9][0-9]*)-[a-z0-9]+(?:-[a-z0-9]+)*$"
)
_IDENTITY_REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9._/\\-]+$")


class GovernanceContractError(ValueError):
    """Safe failure raised when repository identity truth is incomplete."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ClosureDisposition(_StrictModel):
    """One data-owned closure posture and its executable semantics."""

    id: str = Field(min_length=3, max_length=128)
    terminal: bool
    completed: bool
    reviewable: bool
    activation_eligible: bool

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if _DISPOSITION_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe closure disposition ID")
        return value

    @model_validator(mode="after")
    def validate_semantics(self) -> ClosureDisposition:
        if self.completed and not self.terminal:
            raise ValueError("completed dispositions must be terminal")
        if self.completed and not self.reviewable:
            raise ValueError("completed dispositions must be reviewable")
        if self.completed and self.activation_eligible:
            raise ValueError("completed dispositions cannot be activation eligible")
        if self.activation_eligible and self.terminal:
            raise ValueError("activation-eligible dispositions cannot be terminal")
        if self.activation_eligible and not self.reviewable:
            raise ValueError("activation-eligible dispositions must be reviewable")
        return self


class ClosureDispositionPolicy(_StrictModel):
    """Versioned source of truth for accepted closure dispositions."""

    schema_version: Literal[1]
    dispositions: list[ClosureDisposition] = Field(min_length=1)

    @field_validator("dispositions")
    @classmethod
    def validate_dispositions(
        cls,
        values: list[ClosureDisposition],
    ) -> list[ClosureDisposition]:
        identifiers = [item.id for item in values]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("duplicate closure disposition IDs")
        return sorted(values, key=lambda item: item.id)


class EpicIdentity(_StrictModel):
    """One unique canonical epic and its folder-qualified legacy aliases."""

    canonical_id: str = Field(min_length=2, max_length=32)
    folder: str = Field(min_length=1, max_length=256)
    closure_disposition: str = Field(min_length=3, max_length=128)
    legacy_folder_aliases: list[str] = Field(min_length=1)

    @field_validator("canonical_id")
    @classmethod
    def validate_canonical_id(cls, value: str) -> str:
        return _validate_epic_id(value)

    @field_validator("folder")
    @classmethod
    def validate_folder(cls, value: str) -> str:
        return _validate_epic_folder(value)

    @field_validator("closure_disposition")
    @classmethod
    def validate_closure_disposition(cls, value: str) -> str:
        if _DISPOSITION_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe closure disposition ID")
        return value

    @field_validator("legacy_folder_aliases")
    @classmethod
    def validate_legacy_folder_aliases(cls, values: list[str]) -> list[str]:
        validated = [_validate_epic_folder(value) for value in values]
        _reject_duplicates(validated, "legacy epic folder aliases")
        return sorted(validated)

    @model_validator(mode="after")
    def validate_folder_identity(self) -> EpicIdentity:
        folder_id = _folder_epic_id(self.folder)
        if folder_id != self.canonical_id:
            raise ValueError("canonical epic ID must match the folder prefix")
        if self.folder in self.legacy_folder_aliases:
            raise ValueError("canonical folder cannot also be a legacy alias")
        return self


class AmbiguousEpicAlias(_StrictModel):
    """One legacy bare ID whose candidates must remain explicit."""

    alias: str = Field(min_length=2, max_length=32)
    canonical_ids: list[str] = Field(min_length=2)

    @field_validator("alias")
    @classmethod
    def validate_alias(cls, value: str) -> str:
        return _validate_epic_id(value)

    @field_validator("canonical_ids")
    @classmethod
    def validate_canonical_ids(cls, values: list[str]) -> list[str]:
        validated = [_validate_epic_id(value) for value in values]
        _reject_duplicates(validated, "ambiguous alias candidates")
        return sorted(validated)


class EpicIdentityPolicy(_StrictModel):
    """Versioned canonical identities plus declared ambiguous legacy IDs."""

    schema_version: Literal[1]
    identities: list[EpicIdentity] = Field(min_length=1)
    ambiguous_aliases: list[AmbiguousEpicAlias]

    @field_validator("identities")
    @classmethod
    def validate_identities(cls, values: list[EpicIdentity]) -> list[EpicIdentity]:
        _reject_duplicates(
            [item.canonical_id for item in values],
            "canonical epic IDs",
        )
        _reject_duplicates([item.folder for item in values], "canonical epic folders")
        legacy_aliases = [
            alias for item in values for alias in item.legacy_folder_aliases
        ]
        _reject_duplicates(legacy_aliases, "legacy epic folder aliases")
        canonical_folders = {item.folder for item in values}
        if canonical_folders.intersection(legacy_aliases):
            raise ValueError("canonical and legacy epic folders must be disjoint")
        return sorted(values, key=lambda item: item.canonical_id)

    @field_validator("ambiguous_aliases")
    @classmethod
    def validate_ambiguous_aliases(
        cls,
        values: list[AmbiguousEpicAlias],
    ) -> list[AmbiguousEpicAlias]:
        _reject_duplicates([item.alias for item in values], "ambiguous epic aliases")
        return sorted(values, key=lambda item: item.alias)

    @model_validator(mode="after")
    def validate_alias_graph(self) -> EpicIdentityPolicy:
        canonical_ids = {item.canonical_id for item in self.identities}
        declared = {
            item.alias: set(item.canonical_ids) for item in self.ambiguous_aliases
        }
        if any(not candidates <= canonical_ids for candidates in declared.values()):
            raise ValueError("ambiguous alias points to an unknown canonical epic")

        derived: dict[str, set[str]] = defaultdict(set)
        for item in self.identities:
            for legacy_alias in item.legacy_folder_aliases:
                derived[_folder_epic_id(legacy_alias)].add(item.canonical_id)
        expected = {
            alias: candidates
            for alias, candidates in derived.items()
            if len(candidates) > 1
        }
        if declared != expected:
            raise ValueError("ambiguous aliases must exactly match legacy collisions")
        return self


class GovernanceContract(_StrictModel):
    """Cross-validated closure and identity policies."""

    closure_policy: ClosureDispositionPolicy
    identity_policy: EpicIdentityPolicy

    @model_validator(mode="after")
    def validate_cross_policy_dispositions(self) -> GovernanceContract:
        dispositions = {item.id for item in self.closure_policy.dispositions}
        if any(
            item.closure_disposition not in dispositions
            for item in self.identity_policy.identities
        ):
            raise ValueError("epic identity references an unknown closure disposition")
        return self


class EpicIdentityResolutionCode(str, Enum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


class EpicIdentityResolution(_StrictModel):
    code: EpicIdentityResolutionCode
    canonical_id: str | None = None
    candidates: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result_shape(self) -> EpicIdentityResolution:
        if self.code is EpicIdentityResolutionCode.RESOLVED:
            if self.canonical_id is None or self.candidates:
                raise ValueError("resolved identity requires one canonical ID")
        elif self.code is EpicIdentityResolutionCode.AMBIGUOUS:
            if self.canonical_id is not None or len(self.candidates) < 2:
                raise ValueError("ambiguous identity requires candidate IDs only")
        elif self.canonical_id is not None or self.candidates:
            raise ValueError("unknown identity cannot carry a candidate")
        return self


class EpicIdentityInventory(_StrictModel):
    canonical_ids: list[str]
    canonical_scope_paths: list[str]
    legacy_scope_paths_present: list[str]
    duplicate_graph_ids: list[str]


ClosureDisposition.model_rebuild()
ClosureDispositionPolicy.model_rebuild()
EpicIdentity.model_rebuild()
AmbiguousEpicAlias.model_rebuild()
EpicIdentityPolicy.model_rebuild()
GovernanceContract.model_rebuild()
EpicIdentityResolution.model_rebuild()
EpicIdentityInventory.model_rebuild()


def load_closure_disposition_policy(policy_path: Path) -> ClosureDispositionPolicy:
    """Load and strictly validate a local closure-disposition policy."""
    data: Any = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    return ClosureDispositionPolicy.model_validate(data)


def closure_disposition_policy_hash(policy: ClosureDispositionPolicy) -> str:
    """Return a stable SHA-256 for normalized closure-policy semantics."""
    payload = json.dumps(
        policy.model_dump(mode="json"),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_epic_identity_policy(policy_path: Path) -> EpicIdentityPolicy:
    """Load and strictly validate a local epic-identity policy."""
    data: Any = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    return EpicIdentityPolicy.model_validate(data)


def epic_identity_policy_hash(policy: EpicIdentityPolicy) -> str:
    """Return a stable SHA-256 for normalized identity-policy semantics."""
    return _semantic_hash(policy)


def load_governance_contract(
    closure_policy_path: Path,
    identity_policy_path: Path,
) -> GovernanceContract:
    """Load both governance policies and validate their cross-record truth."""
    return GovernanceContract(
        closure_policy=load_closure_disposition_policy(closure_policy_path),
        identity_policy=load_epic_identity_policy(identity_policy_path),
    )


def resolve_epic_identity(
    contract: GovernanceContract,
    reference: str,
) -> EpicIdentityResolution:
    """Resolve one safe exact reference without first-match behavior."""
    normalized = _normalize_identity_reference(reference)
    ambiguities = {
        item.alias.casefold(): item.canonical_ids
        for item in contract.identity_policy.ambiguous_aliases
    }
    if normalized in ambiguities:
        return EpicIdentityResolution(
            code=EpicIdentityResolutionCode.AMBIGUOUS,
            candidates=ambiguities[normalized],
        )

    unique: dict[str, EpicIdentity] = {}
    for item in contract.identity_policy.identities:
        for candidate in (
            item.canonical_id,
            item.folder,
            *item.legacy_folder_aliases,
        ):
            unique[candidate.casefold()] = item
    identity = unique.get(normalized)
    if identity is None:
        return EpicIdentityResolution(code=EpicIdentityResolutionCode.UNKNOWN)
    return EpicIdentityResolution(
        code=EpicIdentityResolutionCode.RESOLVED,
        canonical_id=identity.canonical_id,
    )


def validate_epic_identity_inventory(
    repository_root: Path,
    contract: GovernanceContract,
) -> EpicIdentityInventory:
    """Require every canonical scope and reject every occupied legacy alias."""
    identities = contract.identity_policy.identities
    canonical_scope_paths = sorted(f"{item.folder}/scope.md" for item in identities)
    missing = [
        path for path in canonical_scope_paths if not (repository_root / path).is_file()
    ]
    legacy_scope_paths = sorted(
        f"{alias}/scope.md"
        for item in identities
        for alias in item.legacy_folder_aliases
    )
    legacy_present = [
        path for path in legacy_scope_paths if (repository_root / path).exists()
    ]
    graph_ids = [_folder_epic_id(item.folder) for item in identities]
    duplicate_graph_ids = sorted(
        identifier for identifier, count in Counter(graph_ids).items() if count > 1
    )
    if missing or legacy_present or duplicate_graph_ids:
        raise GovernanceContractError(
            "epic identity inventory is incomplete or colliding"
        )
    return EpicIdentityInventory(
        canonical_ids=sorted(item.canonical_id for item in identities),
        canonical_scope_paths=canonical_scope_paths,
        legacy_scope_paths_present=legacy_present,
        duplicate_graph_ids=duplicate_graph_ids,
    )


def _semantic_hash(model: BaseModel) -> str:
    payload = json.dumps(
        model.model_dump(mode="json"),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_epic_id(value: str) -> str:
    if _EPIC_ID_PATTERN.fullmatch(value) is None:
        raise ValueError("unsafe epic ID")
    return value


def _validate_epic_folder(value: str) -> str:
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or str(path) != value
        or _EPIC_FOLDER_PATTERN.fullmatch(value) is None
    ):
        raise ValueError("unsafe epic folder")
    return value


def _folder_epic_id(folder: str) -> str:
    match = _EPIC_FOLDER_PATTERN.fullmatch(folder)
    if match is None:
        raise ValueError("unsafe epic folder")
    return f"E{match.group(1)}"


def _normalize_identity_reference(reference: str) -> str:
    clean = reference.strip().replace("\\", "/")
    if (
        not clean
        or clean.startswith("/")
        or _IDENTITY_REFERENCE_PATTERN.fullmatch(clean) is None
        or ".." in PurePosixPath(clean).parts
        or "://" in clean
    ):
        raise ValueError("unsafe epic identity reference")
    return clean.casefold()


def _reject_duplicates(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label}")
