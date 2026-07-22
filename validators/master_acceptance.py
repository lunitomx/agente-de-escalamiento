"""Strict local acceptance contract for the ESCALA Local V2 master plan."""

from __future__ import annotations

from enum import Enum
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.governance_contract import (
    closure_disposition_policy_hash,
    epic_identity_policy_hash,
    load_closure_disposition_policy,
    load_epic_identity_policy,
)
from validators.public_export import (
    load_public_export_policy,
    public_export_policy_hash,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


_MISSION_ID = "escala-local-v2-plan-maestro-2607202112"
_EXPECTED_COUNTS = {
    "E37": 7,
    "E38": 7,
    "E39": 7,
    "E40": 8,
    "E41": 7,
    "E42": 6,
}
_EXPECTED_SLUGS = {
    "E37": "local-workspace-flexible-ingestion",
    "E38": "cash-and-financial-intelligence",
    "E39": "meeting-and-team-intelligence",
    "E40": "executive-cockpit-and-coaching",
    "E41": "local-installation-and-lifecycle",
    "E42": "product-qualification-and-functional-catalog",
}
_AUTHORITY_PATHS = {
    "closure_dispositions": "governance/closure-dispositions.yaml",
    "epic_identities": "governance/epic-identities.yaml",
    "public_export": "governance/public-export.yaml",
}
_EPIC_ID_PATTERN = re.compile(r"^E(?:3[7-9]|4[0-2])$")
_STORY_ID_PATTERN = re.compile(r"^S(3[7-9]|4[0-2])\.([1-9][0-9]*)$")
_REQUIREMENT_ID_PATTERN = re.compile(r"^REQ-(E(?:3[7-9]|4[0-2]))-([0-9]{3})$")
_SOURCE_ID_PATTERN = re.compile(r"^SRC-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_GATE_ID_PATTERN = re.compile(r"^gate-[a-z0-9]+(?:-[a-z0-9]+)*$")
_DISPOSITION_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*(?:/[a-z][a-z0-9-]*)?$")
_COMMAND_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")


class MasterAcceptanceError(ValueError):
    """Safe failure for incomplete or drifting acceptance authority."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AuthorityBinding(_StrictModel):
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    hash_kind: Literal["semantic"]

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _validate_relative_path(value)


class AuthorityBindings(_StrictModel):
    closure_dispositions: AuthorityBinding
    epic_identities: AuthorityBinding
    public_export: AuthorityBinding

    @model_validator(mode="after")
    def validate_unique_paths(self) -> AuthorityBindings:
        paths = [
            self.closure_dispositions.path,
            self.epic_identities.path,
            self.public_export.path,
        ]
        _reject_duplicates(paths, "authority paths")
        return self


class SourceRequirement(_StrictModel):
    id: str = Field(min_length=5, max_length=64)
    statement: str = Field(min_length=1, max_length=2048)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if _SOURCE_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe source requirement ID")
        return value

    @field_validator("statement")
    @classmethod
    def validate_statement(cls, value: str) -> str:
        return _validate_safe_text(value, "source requirement")


class PlannedStory(_StrictModel):
    id: str
    title: str = Field(min_length=1, max_length=160)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if _STORY_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe planned story ID")
        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _validate_safe_text(value, "planned story title")


class PlannedEpic(_StrictModel):
    id: str
    slug: str
    title: str = Field(min_length=1, max_length=160)
    stories: list[PlannedStory] = Field(min_length=1)
    requirement_count: int = Field(ge=1, le=1000)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_epic_id(value)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        if _SLUG_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe epic slug")
        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _validate_safe_text(value, "planned epic title")

    @field_validator("stories")
    @classmethod
    def validate_stories(cls, values: list[PlannedStory]) -> list[PlannedStory]:
        identifiers = [item.id for item in values]
        if identifiers != sorted(identifiers):
            raise ValueError("planned stories must be sorted")
        _reject_duplicates(identifiers, "planned story IDs")
        return values

    @model_validator(mode="after")
    def validate_story_ownership(self) -> PlannedEpic:
        if any(_story_epic(item.id) != self.id for item in self.stories):
            raise ValueError("planned story must belong to its epic")
        return self


class RequirementOwner(_StrictModel):
    epic: str
    story: str

    @field_validator("epic")
    @classmethod
    def validate_epic(cls, value: str) -> str:
        return _validate_epic_id(value)

    @field_validator("story")
    @classmethod
    def validate_story(cls, value: str) -> str:
        if _STORY_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe owner story ID")
        return value

    @model_validator(mode="after")
    def validate_alignment(self) -> RequirementOwner:
        if _story_epic(self.story) != self.epic:
            raise ValueError("owner story must belong to owner epic")
        return self


class EvidenceDeclaration(_StrictModel):
    artifact_path: str
    receipt_path: str
    verification_command: list[str] = Field(min_length=4, max_length=16)
    required_gates: list[str] = Field(min_length=1)

    @field_validator("artifact_path", "receipt_path")
    @classmethod
    def validate_evidence_path(cls, value: str) -> str:
        path = _validate_relative_path(value)
        if not path.endswith(".json"):
            raise ValueError("evidence paths must be JSON")
        return path

    @field_validator("verification_command")
    @classmethod
    def validate_command(cls, values: list[str]) -> list[str]:
        if values[0] not in {".venv/bin/rai", "python"}:
            raise ValueError("verification command executable is not allowed")
        for value in values:
            if (
                not value
                or value != value.strip()
                or len(value) > 128
                or _COMMAND_TOKEN_PATTERN.fullmatch(value) is None
                or "://" in value
                or value.startswith("/")
                or ".." in PurePosixPath(value).parts
            ):
                raise ValueError("unsafe verification command token")
        return values

    @field_validator("required_gates")
    @classmethod
    def validate_gates(cls, values: list[str]) -> list[str]:
        if values != sorted(values):
            raise ValueError("required gates must be sorted")
        _reject_duplicates(values, "required gates")
        if any(_GATE_ID_PATTERN.fullmatch(value) is None for value in values):
            raise ValueError("unsafe gate ID")
        return values

    @model_validator(mode="after")
    def validate_distinct_paths(self) -> EvidenceDeclaration:
        if self.artifact_path == self.receipt_path:
            raise ValueError("artifact and receipt paths must differ")
        return self


class Platform(str, Enum):
    MACOS = "macos"
    WINDOWS = "windows"


class ArchitectureClassification(_StrictModel):
    runtime_authority: Literal["installer_machine"]
    data_authority: Literal["installer_machine"]
    team_exchange: Literal["ordinary_filesystem_documents_only"]
    authoritative_sqlite_sync: Literal["forbidden"]


class EvidenceBlocker(str, Enum):
    MISSING = "evidence.missing"
    STALE = "evidence.stale"
    FAILED = "evidence.failed"


class UnprovedProof(_StrictModel):
    state: Literal["unproved"]
    blockers: list[EvidenceBlocker] = Field(min_length=1)

    @field_validator("blockers")
    @classmethod
    def validate_blockers(
        cls,
        values: list[EvidenceBlocker],
    ) -> list[EvidenceBlocker]:
        if values != sorted(values, key=lambda item: item.value):
            raise ValueError("evidence blockers must be sorted")
        _reject_duplicates([item.value for item in values], "evidence blockers")
        return values


class ProvedProof(_StrictModel):
    state: Literal["proved"]
    receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


Proof = Annotated[UnprovedProof | ProvedProof, Field(discriminator="state")]


class AcceptanceRequirement(_StrictModel):
    id: str
    owner: RequirementOwner
    source_ids: list[str] = Field(min_length=1)
    acceptance: str = Field(min_length=1, max_length=2048)
    evidence: EvidenceDeclaration
    platforms: list[Platform] = Field(min_length=1)
    architecture: ArchitectureClassification
    delivery_disposition: str
    proof: Proof

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if _REQUIREMENT_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe acceptance requirement ID")
        return value

    @field_validator("source_ids")
    @classmethod
    def validate_source_ids(cls, values: list[str]) -> list[str]:
        if values != sorted(values):
            raise ValueError("source IDs must be sorted")
        _reject_duplicates(values, "source IDs")
        if any(_SOURCE_ID_PATTERN.fullmatch(value) is None for value in values):
            raise ValueError("unsafe source requirement ID")
        return values

    @field_validator("acceptance")
    @classmethod
    def validate_acceptance(cls, value: str) -> str:
        return _validate_safe_text(value, "acceptance statement")

    @field_validator("platforms")
    @classmethod
    def validate_platforms(cls, values: list[Platform]) -> list[Platform]:
        if values != sorted(values, key=lambda item: item.value):
            raise ValueError("platforms must be sorted")
        _reject_duplicates([item.value for item in values], "platforms")
        return values

    @field_validator("delivery_disposition")
    @classmethod
    def validate_delivery_disposition(cls, value: str) -> str:
        if _DISPOSITION_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe closure disposition ID")
        return value

    @model_validator(mode="after")
    def validate_requirement_alignment(self) -> AcceptanceRequirement:
        requirement_epic, _ = _requirement_parts(self.id)
        if requirement_epic != self.owner.epic:
            raise ValueError("requirement ID must match owner epic")
        expected_gate = f"gate-{self.id.lower()}"
        if self.evidence.verification_command != [
            ".venv/bin/rai",
            "gate",
            "check",
            expected_gate,
        ]:
            raise ValueError("verification command must name the requirement gate")
        if expected_gate not in self.evidence.required_gates:
            raise ValueError("requirement gate is missing")
        if isinstance(self.proof, ProvedProof):
            if self.delivery_disposition != "complete":
                raise ValueError("proved requirement must be complete")
        elif self.delivery_disposition == "complete":
            raise ValueError("unproved requirement cannot be complete")
        return self


class AcceptanceLimits(_StrictModel):
    max_acceptance_chars: Literal[2048]
    max_command_tokens: Literal[16]
    max_receipt_bytes: Literal[65536]


class MasterAcceptanceLedger(_StrictModel):
    schema_version: Literal[1]
    mission_id: Literal["escala-local-v2-plan-maestro-2607202112"]
    authorities: AuthorityBindings
    source_requirements: list[SourceRequirement] = Field(min_length=1)
    epics: list[PlannedEpic] = Field(min_length=1)
    requirements: list[AcceptanceRequirement] = Field(min_length=1)
    limits: AcceptanceLimits

    @field_validator("source_requirements")
    @classmethod
    def validate_source_requirements(
        cls,
        values: list[SourceRequirement],
    ) -> list[SourceRequirement]:
        identifiers = [item.id for item in values]
        if identifiers != sorted(identifiers):
            raise ValueError("source requirements must be sorted")
        _reject_duplicates(identifiers, "source requirement IDs")
        return values

    @field_validator("epics")
    @classmethod
    def validate_epics(cls, values: list[PlannedEpic]) -> list[PlannedEpic]:
        identifiers = [item.id for item in values]
        if identifiers != list(_EXPECTED_COUNTS):
            raise ValueError("planned epic inventory must be exactly E37-E42")
        for item in values:
            if item.slug != _EXPECTED_SLUGS[item.id]:
                raise ValueError("planned epic slug mismatch")
            if item.requirement_count != _EXPECTED_COUNTS[item.id]:
                raise ValueError("planned epic requirement count mismatch")
        return values

    @field_validator("requirements")
    @classmethod
    def validate_requirement_order(
        cls,
        values: list[AcceptanceRequirement],
    ) -> list[AcceptanceRequirement]:
        identifiers = [item.id for item in values]
        expected = [
            f"REQ-{epic}-{index:03d}"
            for epic, count in _EXPECTED_COUNTS.items()
            for index in range(1, count + 1)
        ]
        if identifiers != expected:
            raise ValueError("requirement inventory must be exact and contiguous")
        return values

    @model_validator(mode="after")
    def validate_inventory_graph(self) -> MasterAcceptanceLedger:
        stories_by_epic = {
            item.id: {story.id for story in item.stories} for item in self.epics
        }
        sources = {item.id for item in self.source_requirements}
        used_sources: set[str] = set()
        counts = {epic: 0 for epic in _EXPECTED_COUNTS}
        for requirement in self.requirements:
            if requirement.owner.story not in stories_by_epic[requirement.owner.epic]:
                raise ValueError("requirement owner story is not planned")
            if not set(requirement.source_ids) <= sources:
                raise ValueError("requirement references an unknown source")
            used_sources.update(requirement.source_ids)
            counts[requirement.owner.epic] += 1
            expected_root = (
                f"work/epics/e{requirement.owner.epic[1:]}-"
                f"{_EXPECTED_SLUGS[requirement.owner.epic]}/evidence/"
            )
            if not requirement.evidence.artifact_path.startswith(expected_root):
                raise ValueError("artifact path must belong to the owner epic")
            if not requirement.evidence.receipt_path.startswith(expected_root):
                raise ValueError("receipt path must belong to the owner epic")
        if used_sources != sources:
            raise ValueError("every source requirement must be mapped")
        if counts != _EXPECTED_COUNTS:
            raise ValueError("requirement counts must match planned epics")
        return self


class AcceptanceAuthoritySnapshot(_StrictModel):
    closure_dispositions_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    epic_identities_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    public_export_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    runtime_authority: Literal["installer_machine"]
    data_authority: Literal["installer_machine"]
    team_exchange: Literal["ordinary_filesystem_documents_only"]
    authoritative_sqlite_sync: Literal["forbidden"]
    human_legal_review_status: Literal["required"]
    publication_authorized: Literal[False]


def load_master_acceptance_ledger(ledger_path: Path) -> MasterAcceptanceLedger:
    """Load one strict local master-acceptance ledger."""
    data: Any = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    return MasterAcceptanceLedger.model_validate(data)


def master_acceptance_ledger_hash(ledger: MasterAcceptanceLedger) -> str:
    """Return a stable SHA-256 for normalized ledger semantics."""
    payload = json.dumps(
        ledger.model_dump(mode="json"),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def render_master_acceptance_json(ledger: MasterAcceptanceLedger) -> str:
    """Render the canonical ledger as deterministic semantic JSON."""
    return (
        json.dumps(
            ledger.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def render_master_acceptance_markdown(ledger: MasterAcceptanceLedger) -> str:
    """Render the complete human acceptance view from typed ledger data."""
    proved_count = sum(
        isinstance(requirement.proof, ProvedProof)
        for requirement in ledger.requirements
    )
    unproved_count = len(ledger.requirements) - proved_count
    lines = [
        "# ESCALA Local V2 Master Acceptance Ledger",
        "",
        f"**Mission:** `{ledger.mission_id}`",
        "",
        (
            f"**Contract inventory:** {len(ledger.requirements)} requirements "
            f"across {len(ledger.epics)} epics."
        ),
        "",
        (
            f"**Initial proof posture:** {proved_count} proved, "
            f"{unproved_count} unproved."
        ),
        "",
        (
            "A valid ledger is not a completed product. Mission readiness requires "
            "fresh passing evidence for every requirement."
        ),
        "",
        "## Authority bindings",
        "",
        "| Authority | Path | Semantic SHA-256 |",
        "|---|---|---|",
    ]
    for authority_name, binding in (
        ("Closure dispositions", ledger.authorities.closure_dispositions),
        ("Epic identities", ledger.authorities.epic_identities),
        ("Public export", ledger.authorities.public_export),
    ):
        lines.append(f"| {authority_name} | `{binding.path}` | `{binding.sha256}` |")
    lines.extend(
        [
            "",
            "## Product-owner source requirements",
            "",
            "| Source ID | Binding statement |",
            "|---|---|",
        ]
    )
    lines.extend(
        f"| `{source.id}` | {_markdown_cell(source.statement)} |"
        for source in ledger.source_requirements
    )
    lines.extend(
        [
            "",
            "## Planned epic inventory",
            "",
            "| Epic | Slug | Stories | Requirements |",
            "|---|---|---|---:|",
        ]
    )
    for epic in ledger.epics:
        stories = ", ".join(f"`{story.id}`" for story in epic.stories)
        lines.append(
            f"| `{epic.id}` — {_markdown_cell(epic.title)} | `{epic.slug}` | "
            f"{stories} | {epic.requirement_count} |"
        )
    for epic in ledger.epics:
        lines.extend(
            [
                "",
                f"## {epic.id} — {epic.title}",
                "",
                (
                    "| Requirement | Owner | Acceptance | Evidence artifact | "
                    "Verification | Gates | Platforms | State |"
                ),
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for requirement in ledger.requirements:
            if requirement.owner.epic != epic.id:
                continue
            command = " ".join(requirement.evidence.verification_command)
            gates = ", ".join(
                f"`{gate_id}`" for gate_id in requirement.evidence.required_gates
            )
            platforms = ", ".join(
                f"`{platform.value}`" for platform in requirement.platforms
            )
            lines.append(
                f"| `{requirement.id}` | `{requirement.owner.story}` | "
                f"{_markdown_cell(requirement.acceptance)} | "
                f"`{requirement.evidence.artifact_path}` | `{command}` | "
                f"{gates} | {platforms} | `{requirement.proof.state}` |"
            )
    lines.extend(
        [
            "",
            "## Binding invariants",
            "",
            "- Runtime authority: `installer_machine`.",
            "- Authoritative data: `installer_machine`.",
            "- Team exchange: `ordinary_filesystem_documents_only`.",
            "- Authoritative SQLite synchronization: `forbidden`.",
            "- Hosted ESCALA service, cloud database, OAuth, Drive API, and "
            "OneDrive API remain forbidden by the bound public-export authority.",
            "- Human legal review remains required and publication authorization "
            "remains false.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_master_acceptance_authorities(
    repository_root: Path,
    ledger: MasterAcceptanceLedger,
) -> AcceptanceAuthoritySnapshot:
    """Cross-check the ledger against current typed governance authorities."""
    bindings = ledger.authorities
    for name, expected_path in _AUTHORITY_PATHS.items():
        binding = getattr(bindings, name)
        if binding.path != expected_path:
            raise MasterAcceptanceError("authority contract mismatch")
    try:
        closure_policy = load_closure_disposition_policy(
            repository_root / bindings.closure_dispositions.path
        )
        identity_policy = load_epic_identity_policy(
            repository_root / bindings.epic_identities.path
        )
        export_policy = load_public_export_policy(
            repository_root / bindings.public_export.path
        )
    except Exception as exc:
        raise MasterAcceptanceError("authority contract mismatch") from exc

    closure_hash = closure_disposition_policy_hash(closure_policy)
    identity_hash = epic_identity_policy_hash(identity_policy)
    export_hash = public_export_policy_hash(export_policy)
    if (
        closure_hash != bindings.closure_dispositions.sha256
        or identity_hash != bindings.epic_identities.sha256
        or export_hash != bindings.public_export.sha256
    ):
        raise MasterAcceptanceError("authority contract mismatch")

    dispositions = {item.id: item for item in closure_policy.dispositions}
    for requirement in ledger.requirements:
        disposition = dispositions.get(requirement.delivery_disposition)
        if disposition is None:
            raise MasterAcceptanceError("authority contract mismatch")
        if isinstance(requirement.proof, ProvedProof):
            if not disposition.completed:
                raise MasterAcceptanceError("authority contract mismatch")
        elif disposition.completed or not disposition.activation_eligible:
            raise MasterAcceptanceError("authority contract mismatch")

    local_only = export_policy.local_only
    license_posture = export_policy.license
    if (
        local_only.runtime_mode != "local_machine_only"
        or local_only.hosted_product_service != "forbidden"
        or local_only.cloud_database != "forbidden"
        or local_only.telemetry != "forbidden"
        or local_only.oauth_requirement != "forbidden"
        or local_only.drive_api_requirement != "forbidden"
        or local_only.onedrive_api_requirement != "forbidden"
        or local_only.authoritative_sqlite_in_sync_folder != "forbidden"
        or local_only.team_sharing != "ordinary_filesystem_documents_only"
        or license_posture.human_review_status != "required"
        or license_posture.publication_authorized is not False
    ):
        raise MasterAcceptanceError("authority contract mismatch")

    return AcceptanceAuthoritySnapshot(
        closure_dispositions_sha256=closure_hash,
        epic_identities_sha256=identity_hash,
        public_export_sha256=export_hash,
        runtime_authority="installer_machine",
        data_authority="installer_machine",
        team_exchange=local_only.team_sharing,
        authoritative_sqlite_sync=local_only.authoritative_sqlite_in_sync_folder,
        human_legal_review_status=license_posture.human_review_status,
        publication_authorized=license_posture.publication_authorized,
    )


def _validate_epic_id(value: str) -> str:
    if _EPIC_ID_PATTERN.fullmatch(value) is None:
        raise ValueError("unsafe planned epic ID")
    return value


def _story_epic(value: str) -> str:
    match = _STORY_ID_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError("unsafe planned story ID")
    return f"E{match.group(1)}"


def _requirement_parts(value: str) -> tuple[str, int]:
    match = _REQUIREMENT_ID_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError("unsafe acceptance requirement ID")
    return match.group(1), int(match.group(2))


def _validate_relative_path(value: str) -> str:
    if (
        not value
        or value != value.strip()
        or "\\" in value
        or "://" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
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


def _validate_safe_text(value: str, label: str) -> str:
    if (
        value != value.strip()
        or "://" in value
        or any(
            ord(character) < 32 and character not in {"\n", "\t"} for character in value
        )
    ):
        raise ValueError(f"unsafe {label}")
    return value


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _reject_duplicates(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label}")
