"""Private, deterministic source-custody contracts for ESCALA knowledge work."""

from __future__ import annotations

from datetime import date
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


_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class SourceAuthorityError(ValueError):
    """Raised without reproducing private source content."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RightsStatus(str, Enum):
    DOCUMENTED = "documented"
    UNKNOWN = "unknown"
    REVIEW_REQUIRED = "review_required"


class DistributionState(str, Enum):
    PRIVATE_ONLY = "private_only"


class ArtifactRole(str, Enum):
    PRIMARY = "primary"
    COMPANION = "companion"


class RightsEvidence(_StrictModel):
    kind: str = Field(min_length=3, max_length=80)
    locator: str = Field(min_length=1, max_length=512)

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe rights evidence kind")
        return value

    @field_validator("locator")
    @classmethod
    def validate_locator(cls, value: str) -> str:
        if "\x00" in value or "\n" in value or "\r" in value:
            raise ValueError("unsafe rights evidence locator")
        return value


class SourceArtifact(_StrictModel):
    role: ArtifactRole
    path: str = Field(min_length=1, max_length=512)
    sha256: str = Field(pattern=_SHA256_PATTERN.pattern)
    line_count: int = Field(ge=1)

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _validate_relative_path(value)


class SourceEntry(_StrictModel):
    source_id: str = Field(min_length=3, max_length=128)
    source_kind: Literal["third_party_methodology"]
    edition: str = Field(min_length=1, max_length=128)
    acquired_via: Literal["locally_provided"]
    rights_status: RightsStatus
    rights_evidence: list[RightsEvidence] = Field(default_factory=list)
    distribution_state: Literal[DistributionState.PRIVATE_ONLY]
    last_reviewed: date
    artifacts: list[SourceArtifact] = Field(min_length=1)

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe source ID")
        return value

    @field_validator("rights_evidence")
    @classmethod
    def sort_evidence(cls, values: list[RightsEvidence]) -> list[RightsEvidence]:
        identities = [(item.kind, item.locator) for item in values]
        if len(identities) != len(set(identities)):
            raise ValueError("duplicate rights evidence")
        return sorted(values, key=lambda item: (item.kind, item.locator))

    @field_validator("artifacts")
    @classmethod
    def validate_artifacts(cls, values: list[SourceArtifact]) -> list[SourceArtifact]:
        paths = [item.path for item in values]
        roles = [item.role for item in values]
        if len(paths) != len(set(paths)):
            raise ValueError("duplicate source artifact path")
        if roles.count(ArtifactRole.PRIMARY) != 1:
            raise ValueError("source requires exactly one primary artifact")
        return sorted(values, key=lambda item: (item.role.value, item.path))

    @model_validator(mode="after")
    def validate_rights_posture(self) -> SourceEntry:
        if self.rights_status is RightsStatus.DOCUMENTED and not self.rights_evidence:
            raise ValueError("documented rights require evidence")
        if self.rights_status is not RightsStatus.DOCUMENTED and self.rights_evidence:
            raise ValueError("unresolved rights cannot claim permission evidence")
        return self


class SourceRegistry(_StrictModel):
    schema_version: Literal[1]
    sources: list[SourceEntry] = Field(min_length=1)

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, values: list[SourceEntry]) -> list[SourceEntry]:
        ids = [item.source_id for item in values]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate source ID")
        return sorted(values, key=lambda item: item.source_id)


class SourceAuthorityReceipt(_StrictModel):
    schema_version: Literal[1]
    status: Literal["pass"]
    registry_sha256: str = Field(pattern=_SHA256_PATTERN.pattern)
    source_ids: list[str] = Field(min_length=1)
    source_count: int = Field(ge=1)
    artifact_count: int = Field(ge=1)
    all_private_only: Literal[True]
    all_rights_unresolved: Literal[True]

    @model_validator(mode="after")
    def validate_counts(self) -> SourceAuthorityReceipt:
        if self.source_ids != sorted(set(self.source_ids)):
            raise ValueError("receipt source IDs must be unique and sorted")
        if self.source_count != len(self.source_ids):
            raise ValueError("receipt source count mismatch")
        return self


def _validate_relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or chr(92) in value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError("unsafe source artifact path")
    return path.as_posix()


def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise SourceAuthorityError("registry unreadable") from exc


def load_source_registry(path: Path) -> SourceRegistry:
    try:
        return SourceRegistry.model_validate(_load_yaml(path))
    except Exception as exc:
        if isinstance(exc, SourceAuthorityError):
            raise
        raise SourceAuthorityError("registry contract invalid") from exc


def source_registry_hash(registry: SourceRegistry) -> str:
    payload = json.dumps(
        registry.model_dump(mode="json"),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _resolve_private_artifact(repository: Path, relative_path: str) -> Path:
    candidate = (repository / relative_path).resolve()
    try:
        candidate.relative_to(repository)
    except ValueError as exc:
        raise SourceAuthorityError("source artifact escapes repository") from exc
    if not candidate.is_file():
        raise SourceAuthorityError("source artifact missing")
    return candidate


def _artifact_line_count(path: Path) -> int:
    try:
        return path.read_bytes().count(b"\n")
    except OSError as exc:
        raise SourceAuthorityError("source artifact unreadable") from exc


def _artifact_hash(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise SourceAuthorityError("source artifact unreadable") from exc


def validate_source_authority(repository: Path, registry: SourceRegistry) -> None:
    repository = repository.resolve()
    if not repository.is_dir():
        raise SourceAuthorityError("repository missing")

    for source in registry.sources:
        for artifact in source.artifacts:
            path = _resolve_private_artifact(repository, artifact.path)
            if _artifact_hash(path) != artifact.sha256:
                raise SourceAuthorityError("source artifact hash mismatch")
            if _artifact_line_count(path) != artifact.line_count:
                raise SourceAuthorityError("source artifact line count mismatch")


def build_source_authority_receipt(
    repository: Path, registry_path: Path
) -> SourceAuthorityReceipt:
    registry = load_source_registry(registry_path)
    validate_source_authority(repository, registry)
    source_ids = [item.source_id for item in registry.sources]
    return SourceAuthorityReceipt(
        schema_version=1,
        status="pass",
        registry_sha256=source_registry_hash(registry),
        source_ids=source_ids,
        source_count=len(source_ids),
        artifact_count=sum(len(item.artifacts) for item in registry.sources),
        all_private_only=True,
        all_rights_unresolved=True,
    )


def render_source_authority_json(receipt: SourceAuthorityReceipt) -> str:
    return (
        json.dumps(
            receipt.model_dump(mode="json"), ensure_ascii=True, indent=2, sort_keys=True
        )
        + "\n"
    )


def render_source_authority_markdown(receipt: SourceAuthorityReceipt) -> str:
    return "\n".join(
        [
            "# ESCALA Source Authority Receipt",
            "",
            "- Status: `pass`",
            f"- Registry SHA-256: `{receipt.registry_sha256}`",
            f"- Sources verified: {receipt.source_count}",
            f"- Artifacts verified: {receipt.artifact_count}",
            "- Distribution: private only",
            "- Rights posture: unresolved; distribution remains blocked",
            "",
        ]
    )


def write_source_authority_receipts(
    receipt: SourceAuthorityReceipt,
    *,
    json_output: Path | None = None,
    markdown_output: Path | None = None,
) -> None:
    for output, content in (
        (json_output, render_source_authority_json(receipt)),
        (markdown_output, render_source_authority_markdown(receipt)),
    ):
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content, encoding="utf-8")
