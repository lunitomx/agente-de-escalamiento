"""Strict contracts for deterministic local ESCALA product exports."""

from __future__ import annotations

import ast
from enum import Enum
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Literal, NoReturn, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from validators.public_boundary import (
    BoundaryFindingCode,
    PublicBoundaryPolicy,
    PublicPathDisposition,
    classify_public_path,
    public_boundary_policy_hash,
    scan_public_content,
)
from validators.exposure_inventory import detect_secret_shapes

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


_SAFE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+_-]{0,63}$")
_IMPORT_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_UNSAFE_PATH_CHARACTERS = frozenset("*?[]")
_RUNTIME_EXTERNAL_PATTERN = re.compile(
    rb"(?i)(?:<(?:script|link)\b[^>]*(?:src|href)\s*=\s*|"
    rb"(?:fetch|websocket)\s*\(\s*)[\"']https?://"
    rb"(?!localhost(?::|/)|127\.0\.0\.1(?::|/)|\[::1\](?::|/))"
)
_CLOUD_API_PATTERN = re.compile(
    rb"(?i)\b(?:googleapiclient|oauth2client|msgraph|graph\.microsoft\.com|"
    rb"drive\.files|client_secret)\b"
)
_TELEMETRY_PATTERN = re.compile(
    rb"(?i)\b(?:sentry_sdk|segment\.io|mixpanel|telemetry_endpoint)\b"
)
_SYNC_MARKERS = ("onedrive", "google drive", "googledrive", "dropbox", "icloud")
_DATABASE_SUFFIXES = (".db", ".sqlite", ".sqlite3")
_BINARY_SUFFIXES = (
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".png",
    ".woff",
    ".woff2",
)
_VERIFICATION_CHECK_IDS = (
    "artifact_root",
    "credentials",
    "dependencies",
    "file_integrity",
    "license_posture",
    "local_only",
    "manifest_contract",
    "package_metadata",
    "path_set",
    "public_boundary",
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SelectionKind(str, Enum):
    FILE = "file"
    TREE = "tree"


class ArtifactRole(str, Enum):
    OPERATOR_DOCUMENTATION = "operator_documentation"
    INSTALLER_OR_UPDATER = "installer_or_updater"
    LOCAL_RUNTIME = "local_runtime"
    BUSINESS_KNOWLEDGE = "business_knowledge"
    AGENT_SKILL = "agent_skill"
    BUSINESS_TEMPLATE = "business_template"
    BUSINESS_VALIDATOR = "business_validator"


class DependencyRelationship(str, Enum):
    DIRECT = "direct"
    TRANSITIVE = "transitive"
    VENDORED = "vendored"
    SYSTEM_PREREQUISITE = "system_prerequisite"


class BundlingState(str, Enum):
    EXTERNAL_SYSTEM = "external_system"
    INSTALLED_BY_PACKAGE_MANAGER = "installed_by_package_manager"
    BUNDLED_SOURCE = "bundled_source"


class DependencyEvidenceKind(str, Enum):
    PROJECT_METADATA = "project_metadata"
    OPERATOR_CONTRACT = "operator_contract"
    SCRIPT_SHEBANG = "script_shebang"
    OBSERVED_LOCAL_METADATA = "observed_local_metadata"
    VENDORED_HEADER = "vendored_header"


class DependencyLicenseStatus(str, Enum):
    EXTERNAL_TERMS = "external_terms"
    DECLARED_METADATA = "declared_metadata"
    DECLARED_LICENSE_FILE = "declared_license_file"
    DECLARED_HEADER = "declared_header"


class NoticeStatus(str, Enum):
    INCLUDED = "included"
    NOT_APPLICABLE = "not_applicable"


class DependencyReviewState(str, Enum):
    TECHNICAL_INVENTORY_VERIFIED = "technical_inventory_verified"


class ExportBuildFailure(str, Enum):
    INVALID_REPOSITORY = "invalid_repository"
    INVALID_SOURCE_REF = "invalid_source_ref"
    SOURCE_OBJECT_MISSING = "source_object_missing"
    SOURCE_NOT_COMMIT = "source_not_commit"
    NON_CURRENT_COMMIT = "non_current_commit"
    POLICY_SOURCE_MISMATCH = "policy_source_mismatch"
    INVENTORY_SOURCE_MISMATCH = "inventory_source_mismatch"
    INVALID_GIT_TREE = "invalid_git_tree"
    UNSAFE_GIT_PATH = "unsafe_git_path"
    MISSING_SELECTION = "missing_selection"
    UNSUPPORTED_GIT_ENTRY = "unsupported_git_entry"
    CASE_COLLISION = "case_collision"
    GENERATED_PATH_COLLISION = "generated_path_collision"
    FILE_LIMIT_EXCEEDED = "file_limit_exceeded"
    DESTINATION_NOT_ABSOLUTE = "destination_not_absolute"
    DESTINATION_PARENT_INVALID = "destination_parent_invalid"
    DESTINATION_EXISTS = "destination_exists"
    DESTINATION_SYMLINK = "destination_symlink"
    DESTINATION_IN_REPOSITORY = "destination_in_repository"
    DESTINATION_SYNCHRONIZED = "destination_synchronized"
    DESTINATION_OUTSIDE_TEMP = "destination_outside_temp"
    MATERIALIZATION_FAILED = "materialization_failed"


class PublicExportBuildError(ValueError):
    """Safe, source-neutral build failure containing only a stable rule ID."""

    def __init__(self, failure: ExportBuildFailure) -> None:
        self.failure = failure
        super().__init__(failure.value)


class ProductIdentity(_StrictModel):
    id: Literal["escala"]
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")


class ExportSourceContract(_StrictModel):
    required_ref: Literal["explicit_full_head_commit"]
    allowed_git_modes: list[Literal["100644", "100755"]]

    @field_validator("allowed_git_modes")
    @classmethod
    def validate_modes(
        cls,
        values: list[Literal["100644", "100755"]],
    ) -> list[Literal["100644", "100755"]]:
        if values != ["100644", "100755"]:
            raise ValueError("regular and executable Git modes are required")
        return values


class PolicyBinding(_StrictModel):
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    hash_kind: Literal["semantic", "content"]

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _validate_relative_path(value)


class ExportPolicyBindings(_StrictModel):
    public_boundary: PolicyBinding
    exposure_baseline: PolicyBinding
    closure_dispositions: PolicyBinding
    epic_identities: PolicyBinding
    third_party: PolicyBinding

    @model_validator(mode="after")
    def validate_binding_kinds(self) -> ExportPolicyBindings:
        semantic = (
            self.public_boundary,
            self.closure_dispositions,
            self.epic_identities,
            self.third_party,
        )
        if any(binding.hash_kind != "semantic" for binding in semantic):
            raise ValueError("typed policy bindings require semantic hashes")
        if self.exposure_baseline.hash_kind != "content":
            raise ValueError("immutable baseline requires a content hash")
        paths = [
            binding.path.casefold() for binding in (*semantic, self.exposure_baseline)
        ]
        _reject_duplicates(paths, "binding paths")
        return self


class ExportSourceSelection(_StrictModel):
    path: str
    kind: SelectionKind
    role: ArtifactRole

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _validate_relative_path(value)


class GeneratedPaths(_StrictModel):
    package_metadata: str
    third_party_notices: str
    manifest: str

    @field_validator("package_metadata", "third_party_notices", "manifest")
    @classmethod
    def validate_generated_path(cls, value: str) -> str:
        safe = _validate_relative_path(value)
        if len(PurePosixPath(safe).parts) != 1:
            raise ValueError("generated files must be top-level")
        return safe

    @model_validator(mode="after")
    def validate_unique_paths(self) -> GeneratedPaths:
        values = [
            self.package_metadata.casefold(),
            self.third_party_notices.casefold(),
            self.manifest.casefold(),
        ]
        _reject_duplicates(values, "generated paths")
        return self


class LocalOnlyContract(_StrictModel):
    runtime_mode: Literal["local_machine_only"]
    hosted_product_service: Literal["forbidden"]
    cloud_database: Literal["forbidden"]
    telemetry: Literal["forbidden"]
    oauth_requirement: Literal["forbidden"]
    drive_api_requirement: Literal["forbidden"]
    onedrive_api_requirement: Literal["forbidden"]
    authoritative_sqlite_in_sync_folder: Literal["forbidden"]
    team_sharing: Literal["ordinary_filesystem_documents_only"]


class LicensePosture(_StrictModel):
    license_status: Literal["no_formal_distribution_license_selected"]
    interim_posture: Literal["proprietary_no_license_grant"]
    human_review_gate: Literal["human_legal_and_ip_release_review"]
    human_review_status: Literal["required"]
    approval_evidence_status: Literal["absent"]
    publication_authorized: Literal[False]
    allowed_artifact_use: Literal["internal_technical_validation_only"]


class ExportLimits(_StrictModel):
    max_text_bytes: int = Field(ge=1, le=104_857_600)
    max_receipt_bytes: int = Field(ge=1, le=1_048_576)
    max_file_count: int = Field(ge=1, le=100_000)


class PublicExportPolicy(_StrictModel):
    schema_version: Literal[1]
    product: ProductIdentity
    source: ExportSourceContract
    bindings: ExportPolicyBindings
    selections: list[ExportSourceSelection] = Field(min_length=1)
    generated_paths: GeneratedPaths
    local_only: LocalOnlyContract
    license: LicensePosture
    limits: ExportLimits

    @field_validator("selections")
    @classmethod
    def validate_selections(
        cls,
        values: list[ExportSourceSelection],
    ) -> list[ExportSourceSelection]:
        if values != sorted(values, key=lambda item: item.path):
            raise ValueError("selections must be sorted by path")
        folded = [selection.path.casefold() for selection in values]
        _reject_duplicates(folded, "case-insensitive selection paths")
        for index, first in enumerate(values):
            for second in values[index + 1 :]:
                if first.kind is SelectionKind.TREE and _is_under(
                    second.path,
                    first.path,
                ):
                    raise ValueError("selection roots must not overlap")
                if second.kind is SelectionKind.TREE and _is_under(
                    first.path,
                    second.path,
                ):
                    raise ValueError("selection roots must not overlap")
        return values

    @model_validator(mode="after")
    def validate_generated_collisions(self) -> PublicExportPolicy:
        generated = {
            self.generated_paths.package_metadata.casefold(),
            self.generated_paths.third_party_notices.casefold(),
            self.generated_paths.manifest.casefold(),
        }
        for selection in self.selections:
            if selection.path.casefold() in generated:
                raise ValueError("generated path collides with source selection")
            if selection.kind is SelectionKind.TREE and any(
                _is_under(path, selection.path) for path in generated
            ):
                raise ValueError("generated path falls within a selected tree")
        return self


class DependencyEvidence(_StrictModel):
    kind: DependencyEvidenceKind
    locator: str

    @field_validator("locator")
    @classmethod
    def validate_locator(cls, value: str) -> str:
        return _validate_relative_path(value)


class ThirdPartyEntry(_StrictModel):
    id: str = Field(min_length=2, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    relationship: DependencyRelationship
    purpose: str = Field(min_length=3, max_length=256)
    parents: list[str]
    version_constraint: str = Field(min_length=1, max_length=128)
    observed_version: str = Field(min_length=1, max_length=64)
    import_names: list[str]
    source_evidence: list[DependencyEvidence] = Field(min_length=1)
    bundling: BundlingState
    license_identifier: str = Field(min_length=2, max_length=64)
    license_status: DependencyLicenseStatus
    notice_required: bool
    notice_status: NoticeStatus
    review_state: DependencyReviewState

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if _SAFE_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe dependency ID")
        return value

    @field_validator("parents")
    @classmethod
    def validate_parents(cls, values: list[str]) -> list[str]:
        if values != sorted(values):
            raise ValueError("dependency parents must be sorted")
        for value in values:
            if _SAFE_ID_PATTERN.fullmatch(value) is None:
                raise ValueError("unsafe dependency parent")
        _reject_duplicates(values, "dependency parents")
        return values

    @field_validator("import_names")
    @classmethod
    def validate_import_names(cls, values: list[str]) -> list[str]:
        if values != sorted(values):
            raise ValueError("import names must be sorted")
        if any(_IMPORT_PATTERN.fullmatch(value) is None for value in values):
            raise ValueError("unsafe import name")
        _reject_duplicates(values, "import names")
        return values

    @field_validator("source_evidence")
    @classmethod
    def validate_source_evidence(
        cls,
        values: list[DependencyEvidence],
    ) -> list[DependencyEvidence]:
        expected = sorted(values, key=lambda item: (item.kind.value, item.locator))
        if values != expected:
            raise ValueError("dependency evidence must be sorted")
        _reject_duplicates(
            [(item.kind, item.locator) for item in values],
            "dependency evidence",
        )
        return values

    @model_validator(mode="after")
    def validate_dependency_boundary(self) -> ThirdPartyEntry:
        if self.relationship is DependencyRelationship.TRANSITIVE and not self.parents:
            raise ValueError("transitive dependencies require parents")
        if (
            self.relationship
            in {
                DependencyRelationship.DIRECT,
                DependencyRelationship.SYSTEM_PREREQUISITE,
            }
            and self.parents
        ):
            raise ValueError("direct and system dependencies cannot have parents")
        if self.bundling is BundlingState.BUNDLED_SOURCE:
            if (
                not self.notice_required
                or self.notice_status is not NoticeStatus.INCLUDED
            ):
                raise ValueError("bundled source requires an included notice")
        elif (
            self.notice_required
            or self.notice_status is not NoticeStatus.NOT_APPLICABLE
        ):
            raise ValueError("non-bundled dependencies use not-applicable notices")
        return self


class ThirdPartyInventory(_StrictModel):
    schema_version: Literal[1]
    human_legal_review_status: Literal["required"]
    publication_authorized: Literal[False]
    entries: list[ThirdPartyEntry] = Field(min_length=1)

    @field_validator("entries")
    @classmethod
    def validate_entries(cls, values: list[ThirdPartyEntry]) -> list[ThirdPartyEntry]:
        if values != sorted(values, key=lambda item: item.id):
            raise ValueError("dependency entries must be sorted by ID")
        identifiers = [entry.id for entry in values]
        _reject_duplicates(identifiers, "dependency IDs")
        entry_ids = set(identifiers)
        if any(parent not in entry_ids for entry in values for parent in entry.parents):
            raise ValueError("dependency parent is missing")
        import_names = [name for entry in values for name in entry.import_names]
        _reject_duplicates(import_names, "inventory import names")
        _validate_acyclic_dependencies(values)
        return values


class ArtifactEntry(_StrictModel):
    path: str
    mode: Literal["100644", "100755"]
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _validate_relative_path(value)


class ArtifactManifest(_StrictModel):
    schema_version: Literal[1]
    product_id: Literal["escala"]
    product_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    export_policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    public_boundary_policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    third_party_inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    entries: list[ArtifactEntry]

    @field_validator("entries")
    @classmethod
    def validate_entries(cls, values: list[ArtifactEntry]) -> list[ArtifactEntry]:
        if values != sorted(values, key=lambda item: item.path):
            raise ValueError("manifest entries must be sorted")
        folded = [entry.path.casefold() for entry in values]
        _reject_duplicates(folded, "manifest paths")
        if any(path == "escala-manifest.json" for path in folded):
            raise ValueError("manifest cannot hash itself")
        return values


class PackageMetadata(_StrictModel):
    schema_version: Literal[1] = 1
    product_id: Literal["escala"]
    product_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    technical_artifact_status: Literal["not_verified"]
    human_legal_review_status: Literal["required"]
    publication_authorized: Literal[False]
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    export_policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    public_boundary_policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    third_party_inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    dependency_count: int = Field(ge=1)
    local_only: LocalOnlyContract
    license: LicensePosture


class PublicExportBuildResult(_StrictModel):
    schema_version: Literal[1] = 1
    product_id: Literal["escala"]
    product_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    export_policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    third_party_inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_file_count: int = Field(ge=1)
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    technical_artifact_status: Literal["built_not_verified"]
    human_legal_review_status: Literal["required"]
    publication_authorized: Literal[False]


class VerificationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class ArtifactLocatorKind(str, Enum):
    RELATIVE_PATH = "relative_path"
    SHA256 = "sha256"


class ArtifactVerificationViolation(_StrictModel):
    check_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    rule_id: str = Field(pattern=r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
    locator_kind: ArtifactLocatorKind
    locator: str = Field(min_length=1, max_length=1024)

    @model_validator(mode="after")
    def validate_locator(self) -> ArtifactVerificationViolation:
        if self.locator_kind is ArtifactLocatorKind.RELATIVE_PATH:
            _validate_relative_path(self.locator)
        elif _SHA256_PATTERN.fullmatch(self.locator) is None:
            raise ValueError("invalid artifact locator hash")
        return self


class ArtifactVerificationCheck(_StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    status: VerificationStatus
    violation_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_count(self) -> ArtifactVerificationCheck:
        if (self.status is VerificationStatus.PASS) != (self.violation_count == 0):
            raise ValueError("check status must match its violation count")
        return self


class PublicExportVerificationResult(_StrictModel):
    schema_version: Literal[1] = 1
    product_id: Literal["escala"]
    product_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    source_commit: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    export_policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    third_party_inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    artifact_file_count: int = Field(ge=0)
    technical_artifact_status: VerificationStatus
    human_legal_review_status: Literal["required"]
    publication_authorized: Literal[False]
    checks: list[ArtifactVerificationCheck]
    violations: list[ArtifactVerificationViolation]

    @model_validator(mode="after")
    def validate_result(self) -> PublicExportVerificationResult:
        if self.checks != sorted(self.checks, key=lambda item: item.id):
            raise ValueError("verification checks must be sorted")
        expected_violations = sorted(
            self.violations,
            key=lambda item: (item.check_id, item.rule_id, item.locator),
        )
        if self.violations != expected_violations:
            raise ValueError("verification violations must be sorted")
        if (self.technical_artifact_status is VerificationStatus.PASS) != (
            not self.violations
        ):
            raise ValueError("technical status must match violations")
        return self


class _ArtifactFile(_StrictModel):
    path: str
    mode: int = Field(ge=0)
    content: bytes | None


class _GitTreeEntry(_StrictModel):
    mode: str = Field(pattern=r"^[0-9]{6}$")
    object_type: str = Field(min_length=1, max_length=16)
    object_id: str = Field(pattern=r"^[0-9a-f]{40}$")
    path: str = Field(min_length=1)


class _SelectedGitEntry(_StrictModel):
    mode: Literal["100644", "100755"]
    object_id: str = Field(pattern=r"^[0-9a-f]{40}$")
    path: str


class _MaterializedFile(_StrictModel):
    path: str
    mode: Literal["100644", "100755"]
    content: bytes


def load_public_export_policy(policy_path: Path) -> PublicExportPolicy:
    """Load one strict public-export policy from local YAML."""
    data: Any = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    return PublicExportPolicy.model_validate(data)


def load_third_party_inventory(inventory_path: Path) -> ThirdPartyInventory:
    """Load one strict third-party inventory from local YAML."""
    data: Any = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    return ThirdPartyInventory.model_validate(data)


def public_export_policy_hash(policy: PublicExportPolicy) -> str:
    """Hash normalized export-policy semantics."""
    return _semantic_hash(policy)


def third_party_inventory_hash(inventory: ThirdPartyInventory) -> str:
    """Hash normalized dependency-inventory semantics."""
    return _semantic_hash(inventory)


def validate_export_selections(
    policy: PublicExportPolicy,
    boundary_policy: PublicBoundaryPolicy,
) -> None:
    """Reject selected files or representative trees denied by the public policy."""
    if policy.bindings.public_boundary.sha256 != public_boundary_policy_hash(
        boundary_policy
    ):
        raise ValueError("public-boundary policy hash mismatch")
    for selection in policy.selections:
        candidate = (
            selection.path
            if selection.kind is SelectionKind.FILE
            else f"{selection.path}/__selection_probe__"
        )
        if (
            classify_public_path(boundary_policy, candidate)
            is PublicPathDisposition.DENIED
        ):
            raise ValueError("export selection intersects a denied public path")


def build_package_metadata(
    policy: PublicExportPolicy,
    inventory: ThirdPartyInventory,
    *,
    source_commit: str,
) -> PackageMetadata:
    """Create deterministic pre-verification package metadata."""
    if _COMMIT_PATTERN.fullmatch(source_commit) is None:
        raise ValueError("source commit must be a full SHA-1")
    inventory_sha256 = third_party_inventory_hash(inventory)
    if inventory_sha256 != policy.bindings.third_party.sha256:
        raise ValueError("third-party inventory hash mismatch")
    return PackageMetadata(
        product_id=policy.product.id,
        product_version=policy.product.version,
        technical_artifact_status="not_verified",
        human_legal_review_status=policy.license.human_review_status,
        publication_authorized=policy.license.publication_authorized,
        source_commit=source_commit,
        export_policy_sha256=public_export_policy_hash(policy),
        public_boundary_policy_sha256=policy.bindings.public_boundary.sha256,
        third_party_inventory_sha256=inventory_sha256,
        dependency_count=len(inventory.entries),
        local_only=policy.local_only,
        license=policy.license,
    )


def render_package_metadata(metadata: PackageMetadata) -> str:
    """Render deterministic JSON package metadata."""
    return (
        json.dumps(
            metadata.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def render_third_party_notices(inventory: ThirdPartyInventory) -> str:
    """Render a deterministic human inventory without external locators."""
    lines = [
        "# ESCALA Third-Party Notices",
        "",
        "Technical inventory status: verified.",
        "Human legal review status: required.",
        "Publication authorized: false.",
        "",
    ]
    for entry in inventory.entries:
        lines.extend(
            [
                f"## {entry.name}",
                "",
                f"- Relationship: `{entry.relationship.value}`",
                f"- Version constraint: `{entry.version_constraint}`",
                f"- Observed version: `{entry.observed_version}`",
                f"- Bundling: `{entry.bundling.value}`",
                f"- Declared license: `{entry.license_identifier}`",
                f"- License evidence: `{entry.license_status.value}`",
                f"- Notice status: `{entry.notice_status.value}`",
                f"- Review state: `{entry.review_state.value}`",
                "",
            ]
        )
    return "\n".join(lines)


def render_artifact_manifest(manifest: ArtifactManifest) -> bytes:
    """Render deterministic non-self-referential artifact metadata."""
    payload = (
        json.dumps(
            manifest.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return payload.encode("utf-8")


def render_public_export_build_json(
    result: PublicExportBuildResult,
    policy: PublicExportPolicy,
) -> str:
    """Render a bounded deterministic build receipt without machine paths."""
    content = (
        json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return _bounded_receipt(content, policy)


def render_public_export_build_markdown(
    result: PublicExportBuildResult,
    policy: PublicExportPolicy,
) -> str:
    """Render the three separate build, legal, and publication states."""
    content = "\n".join(
        [
            "# ESCALA Public Export Build Receipt",
            "",
            f"- Product: `{result.product_id}` `{result.product_version}`",
            f"- Source commit: `{result.source_commit}`",
            f"- Export policy SHA-256: `{result.export_policy_sha256}`",
            f"- Third-party inventory SHA-256: `{result.third_party_inventory_sha256}`",
            f"- Artifact file count: `{result.artifact_file_count}`",
            f"- Manifest SHA-256: `{result.manifest_sha256}`",
            f"- Technical artifact status: `{result.technical_artifact_status}`",
            f"- Human legal review status: `{result.human_legal_review_status}`",
            f"- Publication authorized: `{str(result.publication_authorized).lower()}`",
            "",
        ]
    )
    return _bounded_receipt(content, policy)


def render_public_export_verification_json(
    result: PublicExportVerificationResult,
    policy: PublicExportPolicy,
) -> str:
    """Render a bounded deterministic independent-verification receipt."""
    content = (
        json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return _bounded_receipt(content, policy)


def render_public_export_verification_markdown(
    result: PublicExportVerificationResult,
    policy: PublicExportPolicy,
) -> str:
    """Render bounded named checks and safe locators without content excerpts."""
    lines = [
        "# ESCALA Public Export Verification Receipt",
        "",
        f"- Product: `{result.product_id}` `{result.product_version}`",
        f"- Source commit: `{result.source_commit or 'unavailable'}`",
        f"- Export policy SHA-256: `{result.export_policy_sha256}`",
        f"- Third-party inventory SHA-256: `{result.third_party_inventory_sha256}`",
        f"- Manifest SHA-256: `{result.manifest_sha256 or 'unavailable'}`",
        f"- Artifact file count: `{result.artifact_file_count}`",
        f"- Technical artifact status: `{result.technical_artifact_status.value}`",
        f"- Human legal review status: `{result.human_legal_review_status}`",
        f"- Publication authorized: `{str(result.publication_authorized).lower()}`",
        "",
        "## Checks",
        "",
    ]
    lines.extend(
        f"- `{check.id}`: `{check.status.value}` (violations=`{check.violation_count}`)"
        for check in result.checks
    )
    lines.extend(["", "## Violations", ""])
    if result.violations:
        lines.extend(
            f"- `{item.check_id}` | `{item.rule_id}` | "
            f"`{item.locator_kind.value}` | `{item.locator}`"
            for item in result.violations
        )
    else:
        lines.append("- None")
    lines.append("")
    return _bounded_receipt("\n".join(lines), policy)


def write_public_export_build_receipts(
    result: PublicExportBuildResult,
    policy: PublicExportPolicy,
    *,
    json_output: Path | None = None,
    markdown_output: Path | None = None,
) -> None:
    """Write only explicitly requested successful build receipts."""
    _write_explicit_receipts(
        json_content=render_public_export_build_json(result, policy),
        markdown_content=render_public_export_build_markdown(result, policy),
        json_output=json_output,
        markdown_output=markdown_output,
    )


def write_public_export_verification_receipts(
    result: PublicExportVerificationResult,
    policy: PublicExportPolicy,
    *,
    json_output: Path | None = None,
    markdown_output: Path | None = None,
) -> None:
    """Write only explicitly requested technically passing receipts."""
    if result.technical_artifact_status is not VerificationStatus.PASS:
        raise ValueError("only a passing verification receipt may be written")
    _write_explicit_receipts(
        json_content=render_public_export_verification_json(result, policy),
        markdown_content=render_public_export_verification_markdown(result, policy),
        json_output=json_output,
        markdown_output=markdown_output,
    )


def build_public_export(
    *,
    repository: Path,
    destination: Path,
    source_commit: str,
    policy: PublicExportPolicy,
    inventory: ThirdPartyInventory,
) -> PublicExportBuildResult:
    """Build a local artifact exclusively from one immutable current commit."""
    repository_root = _validate_repository(repository)
    destination_root = _validate_build_destination(
        destination,
        repository=repository_root,
    )
    _validate_source_commit(repository_root, source_commit)
    _validate_committed_contracts(
        repository_root,
        source_commit=source_commit,
        policy=policy,
        inventory=inventory,
    )
    tree_entries = _read_git_tree(repository_root, source_commit)
    selected = _expand_git_selections(policy, tree_entries)
    files = [
        _MaterializedFile(
            path=entry.path,
            mode=entry.mode,
            content=_read_git_blob(repository_root, entry.object_id),
        )
        for entry in selected
    ]
    metadata = build_package_metadata(
        policy,
        inventory,
        source_commit=source_commit,
    )
    files.extend(
        [
            _MaterializedFile(
                path=policy.generated_paths.package_metadata,
                mode="100644",
                content=render_package_metadata(metadata).encode("utf-8"),
            ),
            _MaterializedFile(
                path=policy.generated_paths.third_party_notices,
                mode="100644",
                content=render_third_party_notices(inventory).encode("utf-8"),
            ),
        ]
    )
    files = sorted(files, key=lambda item: item.path)
    _validate_materialized_paths(policy, files)
    manifest = ArtifactManifest(
        schema_version=1,
        product_id=policy.product.id,
        product_version=policy.product.version,
        source_commit=source_commit,
        export_policy_sha256=public_export_policy_hash(policy),
        public_boundary_policy_sha256=policy.bindings.public_boundary.sha256,
        third_party_inventory_sha256=third_party_inventory_hash(inventory),
        entries=[
            ArtifactEntry(
                path=item.path,
                mode=item.mode,
                size_bytes=len(item.content),
                sha256=hashlib.sha256(item.content).hexdigest(),
            )
            for item in files
        ],
    )
    manifest_bytes = render_artifact_manifest(manifest)
    _materialize_export(
        destination_root,
        files=files,
        manifest_path=policy.generated_paths.manifest,
        manifest_bytes=manifest_bytes,
    )
    return PublicExportBuildResult(
        product_id=policy.product.id,
        product_version=policy.product.version,
        source_commit=source_commit,
        export_policy_sha256=public_export_policy_hash(policy),
        third_party_inventory_sha256=third_party_inventory_hash(inventory),
        artifact_file_count=len(files) + 1,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        technical_artifact_status="built_not_verified",
        human_legal_review_status=policy.license.human_review_status,
        publication_authorized=policy.license.publication_authorized,
    )


def verify_public_export(
    *,
    artifact: Path,
    policy: PublicExportPolicy,
    inventory: ThirdPartyInventory,
    boundary_policy: PublicBoundaryPolicy,
) -> PublicExportVerificationResult:
    """Independently verify staged bytes without calling or trusting the builder."""
    violations: list[ArtifactVerificationViolation] = []
    files = _enumerate_artifact_files(
        artifact,
        boundary_policy=boundary_policy,
        violations=violations,
    )
    manifest_path = policy.generated_paths.manifest
    manifest_file = files.get(manifest_path)
    manifest: ArtifactManifest | None = None
    manifest_sha256: str | None = None
    if manifest_file is None or manifest_file.content is None:
        _append_artifact_violation(
            violations,
            check_id="manifest_contract",
            rule_id="artifact.manifest_invalid",
            relative_path=manifest_path,
            boundary_policy=boundary_policy,
        )
    else:
        manifest_sha256 = hashlib.sha256(manifest_file.content).hexdigest()
        try:
            manifest = ArtifactManifest.model_validate_json(manifest_file.content)
        except (ValidationError, ValueError):
            _append_artifact_violation(
                violations,
                check_id="manifest_contract",
                rule_id="artifact.manifest_invalid",
                relative_path=manifest_path,
                boundary_policy=boundary_policy,
            )
        else:
            if render_artifact_manifest(manifest) != manifest_file.content:
                _append_artifact_violation(
                    violations,
                    check_id="manifest_contract",
                    rule_id="artifact.manifest_nondeterministic",
                    relative_path=manifest_path,
                    boundary_policy=boundary_policy,
                )
            _verify_manifest_contract(
                manifest,
                policy=policy,
                inventory=inventory,
                boundary_policy=boundary_policy,
                violations=violations,
            )
    if manifest is not None:
        _verify_exact_artifact_files(
            files,
            manifest=manifest,
            manifest_path=manifest_path,
            boundary_policy=boundary_policy,
            violations=violations,
        )
        _verify_generated_metadata(
            files,
            manifest=manifest,
            policy=policy,
            inventory=inventory,
            boundary_policy=boundary_policy,
            violations=violations,
        )
    _verify_payload_boundaries(
        artifact,
        files=files,
        policy=policy,
        inventory=inventory,
        boundary_policy=boundary_policy,
        violations=violations,
    )
    ordered_violations = _ordered_artifact_violations(violations)
    checks = [
        ArtifactVerificationCheck(
            id=check_id,
            status=(
                VerificationStatus.FAIL
                if any(item.check_id == check_id for item in ordered_violations)
                else VerificationStatus.PASS
            ),
            violation_count=sum(
                item.check_id == check_id for item in ordered_violations
            ),
        )
        for check_id in sorted(_VERIFICATION_CHECK_IDS)
    ]
    return PublicExportVerificationResult(
        product_id=policy.product.id,
        product_version=policy.product.version,
        source_commit=manifest.source_commit if manifest is not None else None,
        export_policy_sha256=public_export_policy_hash(policy),
        third_party_inventory_sha256=third_party_inventory_hash(inventory),
        manifest_sha256=manifest_sha256,
        artifact_file_count=len(files),
        technical_artifact_status=(
            VerificationStatus.FAIL if ordered_violations else VerificationStatus.PASS
        ),
        human_legal_review_status=policy.license.human_review_status,
        publication_authorized=policy.license.publication_authorized,
        checks=checks,
        violations=ordered_violations,
    )


def _enumerate_artifact_files(
    artifact: Path,
    *,
    boundary_policy: PublicBoundaryPolicy,
    violations: list[ArtifactVerificationViolation],
) -> dict[str, _ArtifactFile]:
    files: dict[str, _ArtifactFile] = {}
    if not artifact.is_absolute() or artifact.is_symlink() or not artifact.is_dir():
        _append_artifact_violation(
            violations,
            check_id="artifact_root",
            rule_id="artifact.invalid_root",
            relative_path="artifact-root",
            boundary_policy=boundary_policy,
            force_hash=True,
        )
        return files
    if _path_has_sync_marker(artifact):
        _append_artifact_violation(
            violations,
            check_id="local_only",
            rule_id="local.synchronized_artifact_root",
            relative_path="artifact-root",
            boundary_policy=boundary_policy,
            force_hash=True,
        )
    pending = [artifact]
    while pending:
        directory = pending.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name)
        except OSError:
            _append_artifact_violation(
                violations,
                check_id="artifact_root",
                rule_id="artifact.unreadable",
                relative_path="artifact-root",
                boundary_policy=boundary_policy,
                force_hash=True,
            )
            continue
        for entry in entries:
            entry_path = Path(entry.path)
            relative_path = entry_path.relative_to(artifact).as_posix()
            try:
                safe_path = _validate_relative_path(relative_path)
            except ValueError:
                _append_artifact_violation(
                    violations,
                    check_id="artifact_root",
                    rule_id="artifact.unsafe_path",
                    relative_path=relative_path,
                    boundary_policy=boundary_policy,
                    force_hash=True,
                )
                safe_path = relative_path
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError:
                _append_artifact_violation(
                    violations,
                    check_id="artifact_root",
                    rule_id="artifact.unreadable",
                    relative_path=safe_path,
                    boundary_policy=boundary_policy,
                    force_hash=safe_path != relative_path,
                )
                continue
            if stat.S_ISLNK(metadata.st_mode):
                _append_artifact_violation(
                    violations,
                    check_id="artifact_root",
                    rule_id="artifact.unsafe_entry",
                    relative_path=safe_path,
                    boundary_policy=boundary_policy,
                    force_hash=safe_path != relative_path,
                )
                files[safe_path] = _ArtifactFile(
                    path=safe_path,
                    mode=stat.S_IMODE(metadata.st_mode),
                    content=None,
                )
                continue
            if stat.S_ISDIR(metadata.st_mode):
                pending.append(entry_path)
                continue
            if not stat.S_ISREG(metadata.st_mode):
                _append_artifact_violation(
                    violations,
                    check_id="artifact_root",
                    rule_id="artifact.unsafe_entry",
                    relative_path=safe_path,
                    boundary_policy=boundary_policy,
                    force_hash=safe_path != relative_path,
                )
                continue
            try:
                content = entry_path.read_bytes()
            except OSError:
                content = None
                _append_artifact_violation(
                    violations,
                    check_id="artifact_root",
                    rule_id="artifact.unreadable",
                    relative_path=safe_path,
                    boundary_policy=boundary_policy,
                    force_hash=safe_path != relative_path,
                )
            files[safe_path] = _ArtifactFile(
                path=safe_path,
                mode=stat.S_IMODE(metadata.st_mode),
                content=content,
            )
    return files


def _verify_manifest_contract(
    manifest: ArtifactManifest,
    *,
    policy: PublicExportPolicy,
    inventory: ThirdPartyInventory,
    boundary_policy: PublicBoundaryPolicy,
    violations: list[ArtifactVerificationViolation],
) -> None:
    mismatched = (
        manifest.product_id != policy.product.id
        or manifest.product_version != policy.product.version
        or manifest.export_policy_sha256 != public_export_policy_hash(policy)
        or manifest.public_boundary_policy_sha256
        != public_boundary_policy_hash(boundary_policy)
        or manifest.public_boundary_policy_sha256
        != policy.bindings.public_boundary.sha256
        or manifest.third_party_inventory_sha256
        != third_party_inventory_hash(inventory)
        or manifest.third_party_inventory_sha256 != policy.bindings.third_party.sha256
    )
    if mismatched:
        _append_artifact_violation(
            violations,
            check_id="manifest_contract",
            rule_id="artifact.manifest_contract_mismatch",
            relative_path=policy.generated_paths.manifest,
            boundary_policy=boundary_policy,
        )


def _verify_exact_artifact_files(
    files: dict[str, _ArtifactFile],
    *,
    manifest: ArtifactManifest,
    manifest_path: str,
    boundary_policy: PublicBoundaryPolicy,
    violations: list[ArtifactVerificationViolation],
) -> None:
    expected = {entry.path: entry for entry in manifest.entries}
    expected_paths = set(expected) | {manifest_path}
    actual_paths = set(files)
    for path in sorted(expected_paths - actual_paths):
        _append_artifact_violation(
            violations,
            check_id="path_set",
            rule_id="artifact.missing_path",
            relative_path=path,
            boundary_policy=boundary_policy,
        )
    for path in sorted(actual_paths - expected_paths):
        _append_artifact_violation(
            violations,
            check_id="path_set",
            rule_id="artifact.unexpected_path",
            relative_path=path,
            boundary_policy=boundary_policy,
            force_hash=_path_is_unsafe(path, boundary_policy),
        )
    for path, expected_entry in expected.items():
        actual = files.get(path)
        if actual is None or actual.content is None:
            continue
        expected_mode = 0o755 if expected_entry.mode == "100755" else 0o644
        if actual.mode != expected_mode:
            _append_artifact_violation(
                violations,
                check_id="file_integrity",
                rule_id="artifact.mode_mismatch",
                relative_path=path,
                boundary_policy=boundary_policy,
            )
        if (
            len(actual.content) != expected_entry.size_bytes
            or hashlib.sha256(actual.content).hexdigest() != expected_entry.sha256
        ):
            _append_artifact_violation(
                violations,
                check_id="file_integrity",
                rule_id="artifact.hash_mismatch",
                relative_path=path,
                boundary_policy=boundary_policy,
            )
    manifest_file = files.get(manifest_path)
    if manifest_file is not None and manifest_file.mode != 0o644:
        _append_artifact_violation(
            violations,
            check_id="file_integrity",
            rule_id="artifact.mode_mismatch",
            relative_path=manifest_path,
            boundary_policy=boundary_policy,
        )


def _verify_generated_metadata(
    files: dict[str, _ArtifactFile],
    *,
    manifest: ArtifactManifest,
    policy: PublicExportPolicy,
    inventory: ThirdPartyInventory,
    boundary_policy: PublicBoundaryPolicy,
    violations: list[ArtifactVerificationViolation],
) -> None:
    expected_metadata = render_package_metadata(
        build_package_metadata(
            policy,
            inventory,
            source_commit=manifest.source_commit,
        )
    ).encode("utf-8")
    metadata_file = files.get(policy.generated_paths.package_metadata)
    if metadata_file is None or metadata_file.content != expected_metadata:
        _append_artifact_violation(
            violations,
            check_id="package_metadata",
            rule_id="artifact.metadata_mismatch",
            relative_path=policy.generated_paths.package_metadata,
            boundary_policy=boundary_policy,
        )
    notices_file = files.get(policy.generated_paths.third_party_notices)
    expected_notices = render_third_party_notices(inventory).encode("utf-8")
    if notices_file is None or notices_file.content != expected_notices:
        _append_artifact_violation(
            violations,
            check_id="package_metadata",
            rule_id="artifact.notices_mismatch",
            relative_path=policy.generated_paths.third_party_notices,
            boundary_policy=boundary_policy,
        )


def _verify_payload_boundaries(
    artifact: Path,
    *,
    files: dict[str, _ArtifactFile],
    policy: PublicExportPolicy,
    inventory: ThirdPartyInventory,
    boundary_policy: PublicBoundaryPolicy,
    violations: list[ArtifactVerificationViolation],
) -> None:
    vendored_locators = {
        evidence.locator
        for dependency in inventory.entries
        if dependency.bundling is BundlingState.BUNDLED_SOURCE
        for evidence in dependency.source_evidence
    }
    for path, artifact_file in sorted(files.items()):
        content = artifact_file.content
        try:
            safe_path = _validate_relative_path(path)
        except ValueError:
            continue
        if (
            classify_public_path(boundary_policy, safe_path)
            is PublicPathDisposition.DENIED
        ):
            _append_artifact_violation(
                violations,
                check_id="public_boundary",
                rule_id="artifact.denied_path",
                relative_path=safe_path,
                boundary_policy=boundary_policy,
                force_hash=True,
            )
        public_violations = scan_public_content(safe_path, content, boundary_policy)
        for public_violation in public_violations:
            if (
                safe_path in vendored_locators
                and public_violation.code is BoundaryFindingCode.PROHIBITED_TEXT
            ):
                continue
            if (
                public_violation.code is BoundaryFindingCode.UNSAFE_OR_UNREADABLE
                and safe_path.casefold().endswith(_BINARY_SUFFIXES)
            ):
                continue
            violations.append(
                ArtifactVerificationViolation(
                    check_id="public_boundary",
                    rule_id=public_violation.rule_id,
                    locator_kind=ArtifactLocatorKind(
                        public_violation.locator_kind.value
                    ),
                    locator=public_violation.locator,
                )
            )
        if safe_path.casefold().endswith(_DATABASE_SUFFIXES):
            _append_artifact_violation(
                violations,
                check_id="local_only",
                rule_id="local.database_payload",
                relative_path=safe_path,
                boundary_policy=boundary_policy,
                force_hash=True,
            )
        if content is None or not _is_text_content(
            content, policy.limits.max_text_bytes
        ):
            continue
        for shape in detect_secret_shapes(content):
            _append_artifact_violation(
                violations,
                check_id="credentials",
                rule_id=f"credential.{shape.value}",
                relative_path=safe_path,
                boundary_policy=boundary_policy,
            )
        if _RUNTIME_EXTERNAL_PATTERN.search(content):
            _append_artifact_violation(
                violations,
                check_id="local_only",
                rule_id="local.hosted_runtime_dependency",
                relative_path=safe_path,
                boundary_policy=boundary_policy,
            )
        if _CLOUD_API_PATTERN.search(content):
            _append_artifact_violation(
                violations,
                check_id="local_only",
                rule_id="local.cloud_api_requirement",
                relative_path=safe_path,
                boundary_policy=boundary_policy,
            )
        if _TELEMETRY_PATTERN.search(content):
            _append_artifact_violation(
                violations,
                check_id="local_only",
                rule_id="local.telemetry_dependency",
                relative_path=safe_path,
                boundary_policy=boundary_policy,
            )
    _verify_python_dependencies(
        files,
        inventory=inventory,
        boundary_policy=boundary_policy,
        violations=violations,
    )
    _verify_vendored_dependencies(
        files,
        inventory=inventory,
        boundary_policy=boundary_policy,
        violations=violations,
    )
    _verify_license_posture(
        files,
        boundary_policy=boundary_policy,
        violations=violations,
    )
    if _path_has_sync_marker(artifact):
        return


def _verify_python_dependencies(
    files: dict[str, _ArtifactFile],
    *,
    inventory: ThirdPartyInventory,
    boundary_policy: PublicBoundaryPolicy,
    violations: list[ArtifactVerificationViolation],
) -> None:
    known_external = {
        import_name for entry in inventory.entries for import_name in entry.import_names
    }
    internal = {
        PurePosixPath(path).parts[0].removesuffix(".py")
        for path in files
        if PurePosixPath(path).parts
    }
    for path, artifact_file in sorted(files.items()):
        if not path.endswith(".py") or artifact_file.content is None:
            continue
        try:
            tree = ast.parse(artifact_file.content, filename="artifact.py")
        except (SyntaxError, ValueError):
            _append_artifact_violation(
                violations,
                check_id="dependencies",
                rule_id="dependency.invalid_python",
                relative_path=path,
                boundary_policy=boundary_policy,
            )
            continue
        import_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                import_roots.update(
                    alias.name.split(".", maxsplit=1)[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                import_roots.add(node.module.split(".", maxsplit=1)[0])
        unknown = (
            import_roots - set(sys.stdlib_module_names) - known_external - internal
        )
        if unknown:
            _append_artifact_violation(
                violations,
                check_id="dependencies",
                rule_id="dependency.unmapped_import",
                relative_path=path,
                boundary_policy=boundary_policy,
            )


def _verify_vendored_dependencies(
    files: dict[str, _ArtifactFile],
    *,
    inventory: ThirdPartyInventory,
    boundary_policy: PublicBoundaryPolicy,
    violations: list[ArtifactVerificationViolation],
) -> None:
    for dependency in inventory.entries:
        if dependency.bundling is not BundlingState.BUNDLED_SOURCE:
            continue
        for evidence in dependency.source_evidence:
            artifact_file = files.get(evidence.locator)
            if artifact_file is None:
                continue
            content = artifact_file.content or b""
            required = (
                dependency.name.encode("utf-8"),
                dependency.observed_version.encode("utf-8"),
                dependency.license_identifier.encode("utf-8"),
            )
            if any(token not in content for token in required):
                _append_artifact_violation(
                    violations,
                    check_id="dependencies",
                    rule_id="dependency.vendored_evidence",
                    relative_path=evidence.locator,
                    boundary_policy=boundary_policy,
                )


def _verify_license_posture(
    files: dict[str, _ArtifactFile],
    *,
    boundary_policy: PublicBoundaryPolicy,
    violations: list[ArtifactVerificationViolation],
) -> None:
    license_file = files.get("LICENSE")
    if license_file is None:
        return
    content = (license_file.content or b"").decode("utf-8", errors="replace").casefold()
    required = (
        "todos los derechos reservados",
        "no se ha seleccionado una licencia formal",
        "no representa una aprobación legal",
        "ni una autorización para publicar",
    )
    forbidden = (
        "exclusivamente con fines educativos",
        "no está autorizado el uso comercial",
        "recurso educativo abierto",
    )
    if any(value not in content for value in required) or any(
        value in content for value in forbidden
    ):
        _append_artifact_violation(
            violations,
            check_id="license_posture",
            rule_id="license.posture_mismatch",
            relative_path="LICENSE",
            boundary_policy=boundary_policy,
        )


def _append_artifact_violation(
    violations: list[ArtifactVerificationViolation],
    *,
    check_id: str,
    rule_id: str,
    relative_path: str,
    boundary_policy: PublicBoundaryPolicy,
    force_hash: bool = False,
) -> None:
    locator_kind, locator = _safe_artifact_locator(
        relative_path,
        boundary_policy=boundary_policy,
        force_hash=force_hash,
    )
    violations.append(
        ArtifactVerificationViolation(
            check_id=check_id,
            rule_id=rule_id,
            locator_kind=locator_kind,
            locator=locator,
        )
    )


def _safe_artifact_locator(
    relative_path: str,
    *,
    boundary_policy: PublicBoundaryPolicy,
    force_hash: bool,
) -> tuple[ArtifactLocatorKind, str]:
    try:
        safe_path = _validate_relative_path(relative_path)
        denied = (
            classify_public_path(boundary_policy, safe_path)
            is PublicPathDisposition.DENIED
        )
    except ValueError:
        denied = True
        safe_path = relative_path
    if force_hash or denied:
        return (
            ArtifactLocatorKind.SHA256,
            hashlib.sha256(safe_path.encode("utf-8", errors="replace")).hexdigest(),
        )
    return ArtifactLocatorKind.RELATIVE_PATH, safe_path


def _path_is_unsafe(path: str, boundary_policy: PublicBoundaryPolicy) -> bool:
    try:
        safe_path = _validate_relative_path(path)
        return (
            classify_public_path(boundary_policy, safe_path)
            is PublicPathDisposition.DENIED
        )
    except ValueError:
        return True


def _path_has_sync_marker(path: Path) -> bool:
    return any(
        marker in part.casefold() for marker in _SYNC_MARKERS for part in path.parts
    )


def _is_text_content(content: bytes, max_bytes: int) -> bool:
    if len(content) > max_bytes or b"\0" in content:
        return False
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _ordered_artifact_violations(
    violations: list[ArtifactVerificationViolation],
) -> list[ArtifactVerificationViolation]:
    unique = {
        (item.check_id, item.rule_id, item.locator_kind, item.locator): item
        for item in violations
    }
    return sorted(
        unique.values(),
        key=lambda item: (item.check_id, item.rule_id, item.locator),
    )


def _bounded_receipt(content: str, policy: PublicExportPolicy) -> str:
    if len(content.encode("utf-8")) > policy.limits.max_receipt_bytes:
        raise ValueError("receipt_size_exceeded")
    return content


def _write_explicit_receipts(
    *,
    json_content: str,
    markdown_content: str,
    json_output: Path | None,
    markdown_output: Path | None,
) -> None:
    outputs = [path for path in (json_output, markdown_output) if path is not None]
    folded = [str(path.absolute()).casefold() for path in outputs]
    if len(folded) != len(set(folded)):
        raise ValueError("receipt outputs must be distinct")
    if any(path.exists() or path.is_symlink() for path in outputs):
        raise ValueError("receipt output already exists")
    for path in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
    for path, content in (
        (json_output, json_content),
        (markdown_output, markdown_content),
    ):
        if path is not None:
            with path.open("x", encoding="utf-8") as stream:
                stream.write(content)


def _validate_repository(repository: Path) -> Path:
    if not repository.is_absolute():
        _fail(ExportBuildFailure.INVALID_REPOSITORY)
    try:
        repository_root = repository.resolve(strict=True)
    except OSError:
        _fail(ExportBuildFailure.INVALID_REPOSITORY)
    if not repository_root.is_dir():
        _fail(ExportBuildFailure.INVALID_REPOSITORY)
    reported = _git_output(
        repository_root,
        "rev-parse",
        "--show-toplevel",
        failure=ExportBuildFailure.INVALID_REPOSITORY,
    )
    try:
        reported_root = Path(reported.decode("utf-8").strip()).resolve(strict=True)
    except (OSError, UnicodeDecodeError):
        _fail(ExportBuildFailure.INVALID_REPOSITORY)
    if reported_root != repository_root:
        _fail(ExportBuildFailure.INVALID_REPOSITORY)
    return repository_root


def _validate_build_destination(destination: Path, *, repository: Path) -> Path:
    if not destination.is_absolute():
        _fail(ExportBuildFailure.DESTINATION_NOT_ABSOLUTE)
    if destination.is_symlink():
        _fail(ExportBuildFailure.DESTINATION_SYMLINK)
    if destination.exists():
        _fail(ExportBuildFailure.DESTINATION_EXISTS)
    parent = destination.parent
    if not parent.exists() or not parent.is_dir() or parent.is_symlink():
        _fail(ExportBuildFailure.DESTINATION_PARENT_INVALID)
    try:
        resolved = parent.resolve(strict=True) / destination.name
        temporary_root = Path(tempfile.gettempdir()).resolve(strict=True)
    except OSError:
        _fail(ExportBuildFailure.DESTINATION_PARENT_INVALID)
    if resolved == repository or resolved.is_relative_to(repository):
        _fail(ExportBuildFailure.DESTINATION_IN_REPOSITORY)
    synchronized_markers = (
        "onedrive",
        "google drive",
        "googledrive",
        "dropbox",
        "icloud",
    )
    folded_parts = [part.casefold() for part in destination.parts]
    if any(marker in part for marker in synchronized_markers for part in folded_parts):
        _fail(ExportBuildFailure.DESTINATION_SYNCHRONIZED)
    if resolved != temporary_root and not resolved.is_relative_to(temporary_root):
        _fail(ExportBuildFailure.DESTINATION_OUTSIDE_TEMP)
    return resolved


def _validate_source_commit(repository: Path, source_commit: str) -> None:
    if _COMMIT_PATTERN.fullmatch(source_commit) is None:
        _fail(ExportBuildFailure.INVALID_SOURCE_REF)
    object_type = (
        _git_output(
            repository,
            "cat-file",
            "-t",
            source_commit,
            failure=ExportBuildFailure.SOURCE_OBJECT_MISSING,
        )
        .decode("ascii", errors="replace")
        .strip()
    )
    if object_type != "commit":
        _fail(ExportBuildFailure.SOURCE_NOT_COMMIT)
    head = (
        _git_output(
            repository,
            "rev-parse",
            "HEAD",
            failure=ExportBuildFailure.INVALID_REPOSITORY,
        )
        .decode("ascii", errors="replace")
        .strip()
    )
    if head != source_commit:
        _fail(ExportBuildFailure.NON_CURRENT_COMMIT)


def _validate_committed_contracts(
    repository: Path,
    *,
    source_commit: str,
    policy: PublicExportPolicy,
    inventory: ThirdPartyInventory,
) -> None:
    committed_policy = _load_committed_model(
        repository,
        source_commit=source_commit,
        relative_path="governance/public-export.yaml",
        model_type=PublicExportPolicy,
        failure=ExportBuildFailure.POLICY_SOURCE_MISMATCH,
    )
    if public_export_policy_hash(committed_policy) != public_export_policy_hash(policy):
        _fail(ExportBuildFailure.POLICY_SOURCE_MISMATCH)
    committed_inventory = _load_committed_model(
        repository,
        source_commit=source_commit,
        relative_path="governance/third-party.yaml",
        model_type=ThirdPartyInventory,
        failure=ExportBuildFailure.INVENTORY_SOURCE_MISMATCH,
    )
    inventory_hash = third_party_inventory_hash(inventory)
    if third_party_inventory_hash(committed_inventory) != inventory_hash:
        _fail(ExportBuildFailure.INVENTORY_SOURCE_MISMATCH)
    if policy.bindings.third_party.sha256 != inventory_hash:
        _fail(ExportBuildFailure.INVENTORY_SOURCE_MISMATCH)


_CommittedModelT = TypeVar(
    "_CommittedModelT",
    PublicExportPolicy,
    ThirdPartyInventory,
)


def _load_committed_model(
    repository: Path,
    *,
    source_commit: str,
    relative_path: str,
    model_type: type[_CommittedModelT],
    failure: ExportBuildFailure,
) -> _CommittedModelT:
    payload = _git_output(
        repository,
        "cat-file",
        "blob",
        f"{source_commit}:{relative_path}",
        failure=failure,
    )
    try:
        data: Any = yaml.safe_load(payload.decode("utf-8"))
        return model_type.model_validate(data)
    except (UnicodeDecodeError, yaml.YAMLError, ValidationError):
        _fail(failure)


def _read_git_tree(repository: Path, source_commit: str) -> list[_GitTreeEntry]:
    payload = _git_output(
        repository,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        source_commit,
        failure=ExportBuildFailure.INVALID_GIT_TREE,
    )
    entries: list[_GitTreeEntry] = []
    for record in payload.split(b"\0"):
        if not record:
            continue
        try:
            header, raw_path = record.split(b"\t", maxsplit=1)
            mode, object_type, object_id = header.decode("ascii").split(" ")
            path = raw_path.decode("utf-8")
            entries.append(
                _GitTreeEntry(
                    mode=mode,
                    object_type=object_type,
                    object_id=object_id,
                    path=path,
                )
            )
        except (ValueError, UnicodeDecodeError, ValidationError):
            _fail(ExportBuildFailure.INVALID_GIT_TREE)
    return entries


def _expand_git_selections(
    policy: PublicExportPolicy,
    tree_entries: list[_GitTreeEntry],
) -> list[_SelectedGitEntry]:
    selected: list[_GitTreeEntry] = []
    for selection in policy.selections:
        if selection.kind is SelectionKind.FILE:
            matches = [entry for entry in tree_entries if entry.path == selection.path]
        else:
            matches = [
                entry for entry in tree_entries if _is_under(entry.path, selection.path)
            ]
        if not matches:
            _fail(ExportBuildFailure.MISSING_SELECTION)
        selected.extend(matches)
    if len(selected) + 3 > policy.limits.max_file_count:
        _fail(ExportBuildFailure.FILE_LIMIT_EXCEEDED)
    folded: set[str] = set()
    result: list[_SelectedGitEntry] = []
    for entry in selected:
        try:
            safe_path = _validate_relative_path(entry.path)
        except ValueError:
            _fail(ExportBuildFailure.UNSAFE_GIT_PATH)
        normalized = safe_path.casefold()
        if normalized in folded:
            _fail(ExportBuildFailure.CASE_COLLISION)
        folded.add(normalized)
        if (
            entry.object_type != "blob"
            or entry.mode not in policy.source.allowed_git_modes
        ):
            _fail(ExportBuildFailure.UNSUPPORTED_GIT_ENTRY)
        mode: Literal["100644", "100755"] = (
            "100755" if entry.mode == "100755" else "100644"
        )
        result.append(
            _SelectedGitEntry(
                mode=mode,
                object_id=entry.object_id,
                path=safe_path,
            )
        )
    return sorted(result, key=lambda item: item.path)


def _read_git_blob(repository: Path, object_id: str) -> bytes:
    return _git_output(
        repository,
        "cat-file",
        "blob",
        object_id,
        failure=ExportBuildFailure.INVALID_GIT_TREE,
    )


def _validate_materialized_paths(
    policy: PublicExportPolicy,
    files: list[_MaterializedFile],
) -> None:
    all_paths = [item.path for item in files]
    all_paths.append(policy.generated_paths.manifest)
    folded = [path.casefold() for path in all_paths]
    if len(folded) != len(set(folded)):
        _fail(ExportBuildFailure.GENERATED_PATH_COLLISION)
    for index, first in enumerate(folded):
        for second in folded[index + 1 :]:
            if _is_under(first, second) or _is_under(second, first):
                _fail(ExportBuildFailure.GENERATED_PATH_COLLISION)


def _materialize_export(
    destination: Path,
    *,
    files: list[_MaterializedFile],
    manifest_path: str,
    manifest_bytes: bytes,
) -> None:
    created = False
    try:
        destination.mkdir(mode=0o700)
        created = True
        for item in files:
            target = destination.joinpath(*PurePosixPath(item.path).parts)
            target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(item.content)
            target.chmod(0o755 if item.mode == "100755" else 0o644)
        manifest_target = destination / manifest_path
        with manifest_target.open("xb") as stream:
            stream.write(manifest_bytes)
        manifest_target.chmod(0o644)
    except OSError:
        if created:
            shutil.rmtree(destination, ignore_errors=True)
        _fail(ExportBuildFailure.MATERIALIZATION_FAILED)


def _git_output(
    repository: Path,
    *arguments: str,
    failure: ExportBuildFailure,
) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=False,
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        _fail(failure)
    if completed.returncode != 0:
        _fail(failure)
    return completed.stdout


def _fail(failure: ExportBuildFailure) -> NoReturn:
    raise PublicExportBuildError(failure)


def _semantic_hash(model: BaseModel) -> str:
    payload = json.dumps(
        model.model_dump(mode="json"),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_relative_path(value: str) -> str:
    if not value or value != value.strip() or "\\" in value:
        raise ValueError("unsafe relative path")
    if any(character in value for character in _UNSAFE_PATH_CHARACTERS):
        raise ValueError("unsafe relative path")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError("unsafe relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value.startswith("./")
        or ".." in path.parts
        or path.as_posix() != value
        or value.endswith("/")
    ):
        raise ValueError("unsafe relative path")
    return value


def _is_under(path: str, root: str) -> bool:
    return path.casefold().startswith(f"{root.casefold()}/")


def _reject_duplicates(values: Iterable[object], label: str) -> None:
    materialized = list(values)
    if len(set(materialized)) != len(materialized):
        raise ValueError(f"duplicate {label}")


def _validate_acyclic_dependencies(entries: list[ThirdPartyEntry]) -> None:
    parents = {entry.id: tuple(entry.parents) for entry in entries}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visiting:
            raise ValueError("dependency graph contains a cycle")
        if identifier in visited:
            return
        visiting.add(identifier)
        for parent in parents[identifier]:
            visit(parent)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in sorted(parents):
        visit(identifier)
