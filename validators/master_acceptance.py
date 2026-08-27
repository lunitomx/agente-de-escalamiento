"""Strict local acceptance contract for the ESCALA Local V2 master plan."""

from __future__ import annotations

from enum import Enum
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
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
_COMMIT_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


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
        if values[0] not in {".venv/bin/rai", ".venv/bin/python"}:
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
    blockers: list[EvidenceBlocker] = Field(min_length=1, max_length=1)

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
        expected_command = (
            [
                ".venv/bin/python",
                "scripts/qualify_epic.py",
                "--epic",
                requirement_epic,
            ]
            if requirement_epic in {"E37", "E38", "E39", "E40", "E41"}
            else [".venv/bin/rai", "gate", "check", expected_gate]
        )
        legacy_command = [".venv/bin/rai", "gate", "check", expected_gate]
        allowed_commands = (
            {tuple(expected_command), tuple(legacy_command)}
            if requirement_epic in {"E37", "E38", "E39", "E40", "E41"}
            else {tuple(expected_command)}
        )
        if tuple(self.evidence.verification_command) not in allowed_commands:
            raise ValueError(
                "verification command does not match the approved epic gate"
            )
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


class AcceptanceMode(str, Enum):
    BASELINE = "baseline"
    READINESS = "readiness"


class ContractStatus(str, Enum):
    PASS = "pass"


class MissionReadiness(str, Enum):
    PROVED = "proved"
    UNPROVED = "unproved"


class GateEvidenceReceipt(_StrictModel):
    id: str
    status: Literal["pass"]

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if _GATE_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe gate ID")
        return value


class RequirementEvidenceReceipt(_StrictModel):
    """Independent passing evidence for one exact acceptance declaration."""

    schema_version: Literal[1]
    requirement_id: str
    ledger_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    declaration_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_commit: str = Field(pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    command_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    gate_results: list[GateEvidenceReceipt] = Field(min_length=1)
    platforms: list[Platform] = Field(min_length=1)
    result: Literal["pass"]

    @field_validator("requirement_id")
    @classmethod
    def validate_requirement_id(cls, value: str) -> str:
        if _REQUIREMENT_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe acceptance requirement ID")
        return value

    @field_validator("gate_results")
    @classmethod
    def validate_gate_results(
        cls,
        values: list[GateEvidenceReceipt],
    ) -> list[GateEvidenceReceipt]:
        identifiers = [item.id for item in values]
        if identifiers != sorted(identifiers):
            raise ValueError("gate results must be sorted")
        _reject_duplicates(identifiers, "gate result IDs")
        return values

    @field_validator("platforms")
    @classmethod
    def validate_platforms(cls, values: list[Platform]) -> list[Platform]:
        if values != sorted(values, key=lambda item: item.value):
            raise ValueError("platforms must be sorted")
        _reject_duplicates([item.value for item in values], "platforms")
        return values


class AcceptanceFinding(_StrictModel):
    requirement_id: str
    rule_id: EvidenceBlocker

    @field_validator("requirement_id")
    @classmethod
    def validate_requirement_id(cls, value: str) -> str:
        if _REQUIREMENT_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe acceptance requirement ID")
        return value


class MasterAcceptanceReceipt(_StrictModel):
    """Bounded mission evidence with contract and readiness kept separate."""

    schema_version: Literal[1]
    contract_status: Literal[ContractStatus.PASS]
    mission_readiness: MissionReadiness
    mode: AcceptanceMode
    mission_id: Literal["escala-local-v2-plan-maestro-2607202112"]
    epic_filter: str | None
    verifier_source_commit: str = Field(pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
    ledger_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    ledger_markdown_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    authorities: AcceptanceAuthoritySnapshot
    epic_count: int = Field(ge=1, le=6)
    requirement_count: int = Field(ge=1, le=42)
    proved_count: int = Field(ge=0, le=42)
    unproved_count: int = Field(ge=0, le=42)
    proved_ids: list[str]
    blocking_requirements: list[AcceptanceFinding]

    @field_validator("epic_filter")
    @classmethod
    def validate_epic_filter(cls, value: str | None) -> str | None:
        if value is not None:
            _validate_epic_id(value)
        return value

    @field_validator("proved_ids")
    @classmethod
    def validate_proved_ids(cls, values: list[str]) -> list[str]:
        if values != sorted(values):
            raise ValueError("proved requirement IDs must be sorted")
        _reject_duplicates(values, "proved requirement IDs")
        if any(_REQUIREMENT_ID_PATTERN.fullmatch(value) is None for value in values):
            raise ValueError("unsafe acceptance requirement ID")
        return values

    @field_validator("blocking_requirements")
    @classmethod
    def validate_blocking_requirements(
        cls,
        values: list[AcceptanceFinding],
    ) -> list[AcceptanceFinding]:
        identifiers = [item.requirement_id for item in values]
        if identifiers != sorted(identifiers):
            raise ValueError("blocking requirements must be sorted")
        _reject_duplicates(identifiers, "blocking requirement IDs")
        return values

    @model_validator(mode="after")
    def validate_counts_and_readiness(self) -> MasterAcceptanceReceipt:
        if self.proved_count + self.unproved_count != self.requirement_count:
            raise ValueError("acceptance counts must reconcile")
        if self.proved_count != len(self.proved_ids):
            raise ValueError("proved count must match proved IDs")
        if self.unproved_count != len(self.blocking_requirements):
            raise ValueError("unproved count must match blockers")
        if self.mission_readiness is MissionReadiness.PROVED:
            if self.unproved_count != 0 or self.blocking_requirements:
                raise ValueError("proved readiness cannot contain blockers")
        elif self.unproved_count == 0:
            raise ValueError("unproved readiness requires a blocker")
        return self


def load_master_acceptance_ledger(ledger_path: Path) -> MasterAcceptanceLedger:
    """Load one strict local master-acceptance ledger."""
    data: Any = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    return MasterAcceptanceLedger.model_validate(data)


def master_acceptance_ledger_hash(ledger: MasterAcceptanceLedger) -> str:
    """Hash stable acceptance semantics without dynamic evidence pointers."""
    data = ledger.model_dump(mode="json")
    for requirement in data["requirements"]:
        requirement["delivery_disposition"] = "evidence_controlled"
        requirement["proof"] = {"state": "evidence_controlled"}
    payload = json.dumps(
        data,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def acceptance_requirement_declaration_hash(
    requirement: AcceptanceRequirement,
) -> str:
    """Hash the stable behavior and proof declaration for one requirement."""
    data = requirement.model_dump(mode="json")
    data.pop("delivery_disposition")
    data.pop("proof")
    return _json_semantic_hash(data)


def verification_command_hash(command: list[str]) -> str:
    """Hash one validated argv declaration without executing it."""
    return _json_semantic_hash(command)


def render_requirement_evidence_receipt_json(
    receipt: RequirementEvidenceReceipt,
) -> str:
    """Render one future requirement receipt deterministically."""
    return _render_json_model(receipt)


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
                    "| Requirement | Owner | Sources | Acceptance | "
                    "Evidence artifact | Evidence receipt | Verification | "
                    "Gates | Platforms | State | Blocker |"
                ),
                "|---|---|---|---|---|---|---|---|---|---|---|",
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
            sources = ", ".join(
                f"`{source_id}`" for source_id in requirement.source_ids
            )
            blocker = (
                requirement.proof.blockers[0].value
                if isinstance(requirement.proof, UnprovedProof)
                else "none"
            )
            lines.append(
                f"| `{requirement.id}` | `{requirement.owner.story}` | "
                f"{sources} | {_markdown_cell(requirement.acceptance)} | "
                f"`{requirement.evidence.artifact_path}` | "
                f"`{requirement.evidence.receipt_path}` | `{command}` | "
                f"{gates} | {platforms} | `{requirement.proof.state}` | "
                f"`{blocker}` |"
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


def build_master_acceptance_receipt(
    repository_root: Path,
    ledger: MasterAcceptanceLedger,
    *,
    mode: AcceptanceMode,
    epic_filter: str | None = None,
) -> MasterAcceptanceReceipt:
    """Evaluate exact local evidence without executing declared commands."""
    authorities = validate_master_acceptance_authorities(repository_root, ledger)
    if epic_filter is not None:
        _validate_epic_id(epic_filter)
    selected = [
        requirement
        for requirement in ledger.requirements
        if epic_filter is None or requirement.owner.epic == epic_filter
    ]
    if not selected:
        raise MasterAcceptanceError("acceptance filter has no requirements")

    ledger_sha256 = master_acceptance_ledger_hash(ledger)
    proved_ids: list[str] = []
    findings: list[AcceptanceFinding] = []
    for requirement in selected:
        finding = _evaluate_requirement_evidence(
            repository_root,
            ledger,
            ledger_sha256,
            requirement,
        )
        if finding is None:
            proved_ids.append(requirement.id)
        else:
            findings.append(finding)
    readiness = MissionReadiness.PROVED if not findings else MissionReadiness.UNPROVED
    receipt = MasterAcceptanceReceipt(
        schema_version=1,
        contract_status=ContractStatus.PASS,
        mission_readiness=readiness,
        mode=mode,
        mission_id=ledger.mission_id,
        epic_filter=epic_filter,
        verifier_source_commit=_read_git_head(repository_root),
        ledger_sha256=ledger_sha256,
        ledger_markdown_sha256=hashlib.sha256(
            render_master_acceptance_markdown(ledger).encode("utf-8")
        ).hexdigest(),
        authorities=authorities,
        epic_count=len({item.owner.epic for item in selected}),
        requirement_count=len(selected),
        proved_count=len(proved_ids),
        unproved_count=len(findings),
        proved_ids=proved_ids,
        blocking_requirements=findings,
    )
    _require_bounded_receipt(receipt, ledger.limits.max_receipt_bytes)
    return receipt


def render_master_acceptance_receipt_json(
    receipt: MasterAcceptanceReceipt,
) -> str:
    """Render deterministic bounded machine acceptance evidence."""
    return _render_json_model(receipt)


def render_master_acceptance_receipt_markdown(
    receipt: MasterAcceptanceReceipt,
) -> str:
    """Render deterministic bounded human acceptance evidence."""
    lines = [
        "# Master Acceptance Receipt",
        "",
        f"- Contract status: `{receipt.contract_status.value}`",
        f"- Mission readiness: `{receipt.mission_readiness.value}`",
        f"- Mode: `{receipt.mode.value}`",
        f"- Epic filter: `{receipt.epic_filter or 'all'}`",
        f"- Verifier source commit: `{receipt.verifier_source_commit}`",
        f"- Ledger SHA-256: `{receipt.ledger_sha256}`",
        f"- Ledger Markdown SHA-256: `{receipt.ledger_markdown_sha256}`",
        f"- Epics: `{receipt.epic_count}`",
        f"- Requirements: `{receipt.requirement_count}`",
        f"- Proved: `{receipt.proved_count}`",
        f"- Unproved: `{receipt.unproved_count}`",
        "",
        "## Authority bindings",
        "",
        (
            "- Closure dispositions SHA-256: "
            f"`{receipt.authorities.closure_dispositions_sha256}`"
        ),
        (f"- Epic identities SHA-256: `{receipt.authorities.epic_identities_sha256}`"),
        (f"- Public export SHA-256: `{receipt.authorities.public_export_sha256}`"),
        "- Runtime authority: `installer_machine`",
        "- Authoritative SQLite synchronization: `forbidden`",
        "- Human legal review: `required`",
        "- Publication authorized: `false`",
        "",
        "## Proved requirement IDs",
        "",
    ]
    lines.extend(f"- `{requirement_id}`" for requirement_id in receipt.proved_ids)
    if not receipt.proved_ids:
        lines.append("- None")
    lines.extend(["", "## Blocking requirement IDs", ""])
    lines.extend(
        f"- `{finding.requirement_id}`: `{finding.rule_id.value}`"
        for finding in receipt.blocking_requirements
    )
    if not receipt.blocking_requirements:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def write_master_acceptance_receipts(
    receipt: MasterAcceptanceReceipt,
    *,
    max_receipt_bytes: int,
    json_output: Path | None = None,
    markdown_output: Path | None = None,
) -> None:
    """Write only explicitly requested, bounded, non-existing receipt files."""
    json_content = render_master_acceptance_receipt_json(receipt)
    markdown_content = render_master_acceptance_receipt_markdown(receipt)
    if (
        len(json_content.encode("utf-8")) > max_receipt_bytes
        or len(markdown_content.encode("utf-8")) > max_receipt_bytes
    ):
        raise ValueError("acceptance receipt exceeds configured limit")
    requested = [path for path in (json_output, markdown_output) if path is not None]
    if len(requested) != len(set(requested)):
        raise ValueError("receipt output paths must be unique")
    if any(path.exists() or path.is_symlink() for path in requested):
        raise FileExistsError("acceptance receipt output already exists")
    for path, content in (
        (json_output, json_content),
        (markdown_output, markdown_content),
    ):
        if path is None:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


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
        elif disposition.completed or not disposition.reviewable:
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


def _evaluate_requirement_evidence(
    repository_root: Path,
    ledger: MasterAcceptanceLedger,
    ledger_sha256: str,
    requirement: AcceptanceRequirement,
) -> AcceptanceFinding | None:
    if isinstance(requirement.proof, UnprovedProof):
        return AcceptanceFinding(
            requirement_id=requirement.id,
            rule_id=requirement.proof.blockers[0],
        )

    receipt_path = repository_root / requirement.evidence.receipt_path
    if receipt_path.is_symlink() or not receipt_path.is_file():
        return AcceptanceFinding(
            requirement_id=requirement.id,
            rule_id=EvidenceBlocker.MISSING,
        )
    try:
        receipt_bytes = receipt_path.read_bytes()
    except OSError:
        return AcceptanceFinding(
            requirement_id=requirement.id,
            rule_id=EvidenceBlocker.FAILED,
        )
    if len(receipt_bytes) > ledger.limits.max_receipt_bytes:
        return AcceptanceFinding(
            requirement_id=requirement.id,
            rule_id=EvidenceBlocker.FAILED,
        )
    if hashlib.sha256(receipt_bytes).hexdigest() != requirement.proof.receipt_sha256:
        return AcceptanceFinding(
            requirement_id=requirement.id,
            rule_id=EvidenceBlocker.STALE,
        )
    try:
        data: Any = json.loads(receipt_bytes)
        evidence = RequirementEvidenceReceipt.model_validate(data)
    except Exception:
        return AcceptanceFinding(
            requirement_id=requirement.id,
            rule_id=EvidenceBlocker.STALE,
        )
    if (
        evidence.requirement_id != requirement.id
        or evidence.ledger_sha256 != ledger_sha256
        or evidence.declaration_sha256
        != acceptance_requirement_declaration_hash(requirement)
        or evidence.command_sha256
        != verification_command_hash(requirement.evidence.verification_command)
        or [item.id for item in evidence.gate_results]
        != requirement.evidence.required_gates
        or evidence.platforms != requirement.platforms
        or not _git_commit_exists(repository_root, evidence.source_commit)
    ):
        return AcceptanceFinding(
            requirement_id=requirement.id,
            rule_id=EvidenceBlocker.STALE,
        )

    artifact_path = repository_root / requirement.evidence.artifact_path
    if artifact_path.is_symlink() or not artifact_path.is_file():
        return AcceptanceFinding(
            requirement_id=requirement.id,
            rule_id=EvidenceBlocker.FAILED,
        )
    try:
        artifact_sha256 = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    except OSError:
        return AcceptanceFinding(
            requirement_id=requirement.id,
            rule_id=EvidenceBlocker.FAILED,
        )
    if artifact_sha256 != evidence.artifact_sha256:
        return AcceptanceFinding(
            requirement_id=requirement.id,
            rule_id=EvidenceBlocker.FAILED,
        )
    return None


def _render_json_model(model: BaseModel) -> str:
    return (
        json.dumps(
            model.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _json_semantic_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_git_head(repository_root: Path) -> str:
    environment = _sanitized_git_environment()
    completed = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
    )
    commit = completed.stdout.strip()
    if completed.returncode != 0 or _COMMIT_PATTERN.fullmatch(commit) is None:
        raise MasterAcceptanceError("unable to resolve verifier source commit")
    return commit


def _git_commit_exists(repository_root: Path, commit: str) -> bool:
    if _COMMIT_PATTERN.fullmatch(commit) is None:
        return False
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "cat-file",
            "-e",
            f"{commit}^{{commit}}",
        ],
        check=False,
        capture_output=True,
        env=_sanitized_git_environment(),
        text=True,
    )
    return completed.returncode == 0


def _sanitized_git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in tuple(environment):
        if key in {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"} or key.startswith(
            "GIT_CONFIG_"
        ):
            environment.pop(key, None)
    return environment


def _require_bounded_receipt(
    receipt: MasterAcceptanceReceipt,
    max_receipt_bytes: int,
) -> None:
    if (
        len(render_master_acceptance_receipt_json(receipt).encode("utf-8"))
        > max_receipt_bytes
        or len(render_master_acceptance_receipt_markdown(receipt).encode("utf-8"))
        > max_receipt_bytes
    ):
        raise MasterAcceptanceError("acceptance receipt exceeds configured limit")


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
