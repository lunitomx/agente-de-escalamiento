"""Strict contracts for deterministic local ESCALA product exports."""

from __future__ import annotations

from enum import Enum
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.public_boundary import (
    PublicBoundaryPolicy,
    PublicPathDisposition,
    classify_public_path,
    public_boundary_policy_hash,
)

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
