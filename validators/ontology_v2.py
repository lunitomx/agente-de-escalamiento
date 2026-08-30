"""Typed, source-safe ontology v2 contracts; no corpus extraction occurs here."""

from __future__ import annotations

from enum import Enum
import hashlib
import json
from pathlib import Path
import re
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
ExclusionDisposition: TypeAlias = Literal["excluded", "review-required"]
ExclusionReason: TypeAlias = Literal[
    "needs-revision",
    "reject-candidate",
    "missing-or-invalid-receipt",
    "generic-candidate",
    "blocked-source",
    "external-content-source-bounded",
    "review-not-independent",
]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class NodeKind(str, Enum):
    DECISION_AREA = "decision-area"
    FRAMEWORK = "framework"
    PRINCIPLE = "principle"
    DIAGNOSTIC_QUESTION = "diagnostic-question"
    RESULT = "result"
    TOOL = "tool"
    ARTIFACT = "artifact"
    PROCEDURE = "procedure"
    STEP = "step"
    RULE = "rule"
    WARNING = "warning"
    METRIC = "metric"
    ROLE = "role"
    ROUTINE = "routine"
    TIME_HORIZON = "time-horizon"
    EXAMPLE = "example"
    EXTERNAL_REFERENCE = "external-reference"
    PERSONAL_DIMENSION = "personal-dimension"


class OriginKind(str, Enum):
    SOURCE_EXPLICIT = "source-explicit"
    SOURCE_SYNTHESIS = "source-synthesis"
    HISTORICAL_EXAMPLE = "historical-example"
    EXTERNAL_REFERENCE = "external-reference"
    COMPANY_LOCAL = "company-local"
    MODEL_HYPOTHESIS = "model-hypothesis"


class ReviewState(str, Enum):
    CANDIDATE = "candidate"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs-review"


class CandidateReviewOutcome(str, Enum):
    """A reviewer outcome for a candidate, without promoting it to ontology."""

    APPROVE_CANDIDATE = "approve-candidate"
    NEEDS_REVISION = "needs-revision"
    REJECT_CANDIDATE = "reject-candidate"


_OPAQUE_REFERENCE_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


def _validate_safe_identifier(value: str, label: str) -> str:
    if _ID_PATTERN.fullmatch(value) is None:
        raise ValueError(f"unsafe {label}")
    return value


def _validate_opaque_reference(value: str) -> str:
    if _OPAQUE_REFERENCE_PATTERN.fullmatch(value) is None:
        raise ValueError("unsafe opaque reference")
    if any(token in value for token in ("url", "path", "file", "locator")):
        raise ValueError("unsafe opaque reference")
    return value


def _validate_safe_label(value: str) -> str:
    """Permit concise public labels, never source prose, URLs, or paths."""
    if value.lower().startswith(("e6.", "e6-", "e56.", "e56-", "legacy.")):
        raise ValueError("legacy safe label is not authorized")
    if (
        not value.strip()
        or value != value.strip()
        or len(value) > 96
        or len(value.split()) > 12
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
        or "/" in value
        or "\\" in value
        or "://" in value
        or value.lower().startswith("www.")
    ):
        raise ValueError("unsafe safe label")
    return value


def _validate_nonlegacy_identifier(value: str, label: str) -> str:
    value = _validate_safe_identifier(value, label)
    legacy_prefixes = ("e6.", "e6-", "e56.", "e56-", "legacy.", "legacy-")
    if value.startswith(legacy_prefixes) or (
        label != "source ID"
        and value.startswith(
            ("concept-", "metric-", "tool-", "worksheet-", "decision-")
        )
    ):
        raise ValueError(f"legacy {label} is not authorized")
    return value


class AuthorizedProjectionCandidate(_StrictModel):
    """Safe, one-way metadata projection from an authorized private review."""

    candidate_id: str = Field(min_length=3, max_length=192)
    canonical_id: str = Field(min_length=3, max_length=192)
    kind: NodeKind
    canonical_name: str = Field(min_length=1, max_length=256)
    origin: OriginKind
    aliases: list[str] = Field(default_factory=list, max_length=64)
    source_ids: list[str] = Field(min_length=1, max_length=64)
    evidence_refs: list[str] = Field(min_length=1, max_length=64)
    candidate_receipt: str = Field(min_length=3, max_length=192)
    review_receipt: str = Field(min_length=3, max_length=192)
    review_outcome: CandidateReviewOutcome
    reviewer_independent: bool
    receipts_valid: bool
    source_bounded: bool
    external_content: bool = False
    blocked: bool
    generic: bool

    @field_validator("candidate_id", "canonical_id")
    @classmethod
    def validate_projection_id(cls, value: str) -> str:
        return _validate_nonlegacy_identifier(value, "projection ID")

    @field_validator("canonical_name")
    @classmethod
    def validate_projection_name(cls, value: str) -> str:
        return _validate_safe_label(value)

    @field_validator("source_ids")
    @classmethod
    def validate_projection_source_ids(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate source ID")
        return sorted(
            _validate_nonlegacy_identifier(value, "source ID") for value in values
        )

    @field_validator("evidence_refs")
    @classmethod
    def validate_projection_evidence_refs(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate evidence reference")
        return sorted(_validate_opaque_reference(value) for value in values)

    @field_validator("candidate_receipt", "review_receipt")
    @classmethod
    def validate_projection_receipts(cls, value: str) -> str:
        return _validate_opaque_reference(value)

    @field_validator("aliases")
    @classmethod
    def validate_projection_aliases(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate or empty alias")
        return sorted(_validate_safe_label(value) for value in values)


class AuthorizedCandidateProjection(_StrictModel):
    """Strictly allowlisted input; deliberately separate from ``ReviewQueue``."""

    schema_version: Literal[1]
    authorization_scope: Literal["e59-e63-reviewed"]
    candidates: list[AuthorizedProjectionCandidate] = Field(
        min_length=1, max_length=256
    )

    @model_validator(mode="after")
    def validate_projection_candidates(self) -> AuthorizedCandidateProjection:
        candidate_ids = [candidate.candidate_id for candidate in self.candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("duplicate projection candidate ID")
        return self


class CanonicalReleaseNode(_StrictModel):
    canonical_id: str = Field(min_length=3, max_length=192)
    candidate_id: str = Field(min_length=3, max_length=192)
    kind: NodeKind
    canonical_name: str = Field(min_length=1, max_length=256)
    origin: OriginKind
    aliases: list[str] = Field(default_factory=list, max_length=64)
    source_ids: list[str] = Field(min_length=1, max_length=64)
    evidence_refs: list[str] = Field(min_length=1, max_length=64)
    candidate_receipt: str = Field(min_length=3, max_length=192)
    review_receipt: str = Field(min_length=3, max_length=192)
    review_outcome: Literal[CandidateReviewOutcome.APPROVE_CANDIDATE]

    @field_validator("canonical_id", "candidate_id")
    @classmethod
    def validate_release_id(cls, value: str) -> str:
        return _validate_nonlegacy_identifier(value, "release ID")

    @field_validator("canonical_name")
    @classmethod
    def validate_release_name(cls, value: str) -> str:
        return _validate_safe_label(value)

    @field_validator("source_ids")
    @classmethod
    def validate_release_source_ids(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate source ID")
        return sorted(
            _validate_nonlegacy_identifier(value, "source ID") for value in values
        )

    @field_validator("evidence_refs")
    @classmethod
    def validate_release_evidence_refs(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate evidence reference")
        return sorted(_validate_opaque_reference(value) for value in values)

    @field_validator("candidate_receipt", "review_receipt")
    @classmethod
    def validate_release_receipts(cls, value: str) -> str:
        return _validate_opaque_reference(value)

    @field_validator("aliases")
    @classmethod
    def validate_release_aliases(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate or empty alias")
        return sorted(_validate_safe_label(value) for value in values)


class CanonicalReleaseExclusion(_StrictModel):
    candidate_id: str = Field(min_length=3, max_length=192)
    disposition: ExclusionDisposition
    reason_code: ExclusionReason
    candidate_receipt: str = Field(min_length=3, max_length=192)
    review_receipt: str = Field(min_length=3, max_length=192)
    source_ids: list[str] = Field(min_length=1, max_length=64)
    evidence_refs: list[str] = Field(min_length=1, max_length=64)

    @field_validator("candidate_id")
    @classmethod
    def validate_exclusion_id(cls, value: str) -> str:
        return _validate_nonlegacy_identifier(value, "candidate ID")

    @field_validator("candidate_receipt", "review_receipt")
    @classmethod
    def validate_exclusion_receipts(cls, value: str) -> str:
        return _validate_opaque_reference(value)

    @field_validator("source_ids")
    @classmethod
    def validate_exclusion_source_ids(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate source ID")
        return sorted(
            _validate_nonlegacy_identifier(value, "source ID") for value in values
        )

    @field_validator("evidence_refs")
    @classmethod
    def validate_exclusion_evidence_refs(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate evidence reference")
        return sorted(_validate_opaque_reference(value) for value in values)


class CanonicalRelease(_StrictModel):
    """Versioned, public-safe promotion result; not an ``OntologyDocument``."""

    schema_version: Literal[1]
    release_id: Literal["s64.1"]
    nodes: list[CanonicalReleaseNode] = Field(default_factory=list)
    exclusions: list[CanonicalReleaseExclusion] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_release_partition(self) -> CanonicalRelease:
        candidate_ids = [item.candidate_id for item in self.nodes] + [
            item.candidate_id for item in self.exclusions
        ]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("every candidate must appear exactly once")
        canonical_ids = [item.canonical_id for item in self.nodes]
        if len(canonical_ids) != len(set(canonical_ids)):
            raise ValueError("duplicate canonical ID")
        aliases = [alias for item in self.nodes for alias in item.aliases]
        if len(aliases) != len(set(aliases)):
            raise ValueError("duplicate release alias")
        return self


def _exclusion_reason(
    candidate: AuthorizedProjectionCandidate,
) -> tuple[ExclusionDisposition, ExclusionReason] | None:
    if not candidate.reviewer_independent:
        return "review-required", "review-not-independent"
    if candidate.external_content:
        return "review-required", "external-content-source-bounded"
    if not candidate.source_bounded:
        return "review-required", "blocked-source"
    if candidate.blocked:
        return "review-required", "blocked-source"
    if candidate.generic:
        return "excluded", "generic-candidate"
    if not candidate.receipts_valid:
        return "review-required", "missing-or-invalid-receipt"
    if candidate.review_outcome is CandidateReviewOutcome.NEEDS_REVISION:
        return "review-required", "needs-revision"
    if candidate.review_outcome is CandidateReviewOutcome.REJECT_CANDIDATE:
        return "excluded", "reject-candidate"
    return None


def build_canonical_release(
    projection: AuthorizedCandidateProjection | None,
) -> CanonicalRelease:
    """Partition each already-sanitised candidate once without source inspection."""
    if projection is None or not projection.candidates:
        raise ValueError("authorized projection is required")
    nodes: list[CanonicalReleaseNode] = []
    exclusions: list[CanonicalReleaseExclusion] = []
    for candidate in projection.candidates:
        exclusion = _exclusion_reason(candidate)
        if exclusion is None:
            nodes.append(
                CanonicalReleaseNode(
                    canonical_id=candidate.canonical_id,
                    candidate_id=candidate.candidate_id,
                    kind=candidate.kind,
                    canonical_name=candidate.canonical_name,
                    origin=candidate.origin,
                    aliases=candidate.aliases,
                    source_ids=candidate.source_ids,
                    evidence_refs=candidate.evidence_refs,
                    candidate_receipt=candidate.candidate_receipt,
                    review_receipt=candidate.review_receipt,
                    review_outcome=CandidateReviewOutcome.APPROVE_CANDIDATE,
                )
            )
        else:
            disposition, reason_code = exclusion
            exclusions.append(
                CanonicalReleaseExclusion(
                    candidate_id=candidate.candidate_id,
                    disposition=disposition,
                    reason_code=reason_code,
                    candidate_receipt=candidate.candidate_receipt,
                    review_receipt=candidate.review_receipt,
                    source_ids=candidate.source_ids,
                    evidence_refs=candidate.evidence_refs,
                )
            )
    return CanonicalRelease(
        schema_version=1,
        release_id="s64.1",
        nodes=sorted(nodes, key=lambda item: item.canonical_id),
        exclusions=sorted(exclusions, key=lambda item: item.candidate_id),
    )


def render_canonical_release(release: CanonicalRelease) -> str:
    return (
        json.dumps(
            release.model_dump(mode="json"), ensure_ascii=True, indent=2, sort_keys=True
        )
        + "\n"
    )


def load_canonical_release(path: Path) -> CanonicalRelease:
    try:
        return CanonicalRelease.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("canonical release contract invalid") from exc


class CanonicalReleaseRelation(_StrictModel):
    """A public-safe typed relation declared for a canonical release."""

    source_id: str = Field(min_length=3, max_length=192)
    target_id: str = Field(min_length=3, max_length=192)
    relation_type: str = Field(min_length=3, max_length=96)

    @field_validator("source_id", "target_id", "relation_type")
    @classmethod
    def validate_relation_identifier(cls, value: str) -> str:
        return _validate_nonlegacy_identifier(value, "release relation identifier")


class CanonicalNodeIntegrityContract(_StrictModel):
    """Explicit, safe metadata required to qualify a release node by kind."""

    canonical_id: str = Field(min_length=3, max_length=192)
    decision_ids: list[str] = Field(default_factory=list, max_length=16)
    evidence_refs: list[str] = Field(default_factory=list, max_length=64)
    definition_ref: str | None = Field(default=None, max_length=192)
    unit: str | None = Field(default=None, max_length=96)

    @field_validator("canonical_id")
    @classmethod
    def validate_contract_id(cls, value: str) -> str:
        return _validate_nonlegacy_identifier(value, "integrity contract ID")

    @field_validator("decision_ids")
    @classmethod
    def validate_contract_decision_ids(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate decision ID")
        return sorted(
            _validate_nonlegacy_identifier(value, "integrity decision ID")
            for value in values
        )

    @field_validator("evidence_refs")
    @classmethod
    def validate_contract_evidence_refs(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate integrity evidence reference")
        return sorted(_validate_opaque_reference(value) for value in values)

    @field_validator("definition_ref")
    @classmethod
    def validate_contract_definition_ref(cls, value: str | None) -> str | None:
        return None if value is None else _validate_opaque_reference(value)

    @field_validator("unit")
    @classmethod
    def validate_contract_unit(cls, value: str | None) -> str | None:
        return None if value is None else _validate_safe_label(value)


class CanonicalReleaseIntegrityManifest(_StrictModel):
    """Optional publication of relations and node qualification metadata."""

    schema_version: Literal[1]
    release_id: Literal["s64.1"]
    relations: list[CanonicalReleaseRelation] = Field(default_factory=list)
    node_contracts: list[CanonicalNodeIntegrityContract] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest_uniqueness(self) -> CanonicalReleaseIntegrityManifest:
        relations = [
            (item.source_id, item.target_id, item.relation_type)
            for item in self.relations
        ]
        if len(relations) != len(set(relations)):
            raise ValueError("duplicate release relation")
        contract_ids = [item.canonical_id for item in self.node_contracts]
        if len(contract_ids) != len(set(contract_ids)):
            raise ValueError("duplicate node integrity contract")
        return self


class CanonicalReleaseIntegrityReceipt(_StrictModel):
    """Bounded verification result; it never contains source labels or prose."""

    schema_version: Literal[1]
    status: Literal["pass", "not-assessed"]
    release_id: Literal["s64.1"]
    node_count: int = Field(ge=0)
    exclusion_count: int = Field(ge=0)
    relation_count: int = Field(ge=0)
    qualified_tool_count: int = Field(ge=0)
    qualified_rule_count: int = Field(ge=0)
    qualified_metric_count: int = Field(ge=0)
    relations_state: Literal["no-relations-published", "relations-validated"]


def _release_integrity_error(reason: str) -> ValueError:
    """Keep failures safe: callers receive a stable rule, never private content."""
    return ValueError(f"canonical release integrity failed: {reason}")


def validate_canonical_release_integrity(
    release: CanonicalRelease,
    manifest: CanonicalReleaseIntegrityManifest | None = None,
) -> CanonicalReleaseIntegrityReceipt:
    """Validate public topology without reading or inferring source material."""
    if manifest is None:
        return CanonicalReleaseIntegrityReceipt(
            schema_version=1,
            status="not-assessed",
            release_id=release.release_id,
            node_count=len(release.nodes),
            exclusion_count=len(release.exclusions),
            relation_count=0,
            qualified_tool_count=0,
            qualified_rule_count=0,
            qualified_metric_count=0,
            relations_state="no-relations-published",
        )
    if manifest.release_id != release.release_id:
        raise _release_integrity_error("manifest-release-mismatch")

    nodes_by_id = {node.canonical_id: node for node in release.nodes}
    for relation in manifest.relations:
        if (
            relation.source_id not in nodes_by_id
            or relation.target_id not in nodes_by_id
        ):
            raise _release_integrity_error("relation-references-unknown-node")

    contracts_by_id = {
        contract.canonical_id: contract for contract in manifest.node_contracts
    }
    if any(contract_id not in nodes_by_id for contract_id in contracts_by_id):
        raise _release_integrity_error("contract-references-unknown-node")

    relevant_kinds = {NodeKind.TOOL, NodeKind.RULE, NodeKind.METRIC}
    relevant_nodes = [node for node in release.nodes if node.kind in relevant_kinds]
    if any(node.canonical_id not in contracts_by_id for node in relevant_nodes):
        raise _release_integrity_error("published-node-missing-integrity-contract")

    tool_count = rule_count = metric_count = 0
    for node in relevant_nodes:
        contract = contracts_by_id[node.canonical_id]
        if node.kind is NodeKind.TOOL:
            if contract.evidence_refs or contract.definition_ref or contract.unit:
                raise _release_integrity_error("tool-has-inapplicable-field")
            if not contract.decision_ids:
                raise _release_integrity_error("tool-missing-decision")
            if any(
                decision_id not in nodes_by_id
                or nodes_by_id[decision_id].kind is not NodeKind.DECISION_AREA
                for decision_id in contract.decision_ids
            ):
                raise _release_integrity_error("tool-references-invalid-decision")
            expected_relations = {
                (node.canonical_id, decision_id, "belongs-to-decision")
                for decision_id in contract.decision_ids
            }
            published_relations = {
                (relation.source_id, relation.target_id, relation.relation_type)
                for relation in manifest.relations
            }
            if not expected_relations.issubset(published_relations):
                raise _release_integrity_error("tool-missing-decision-relation")
            tool_count += 1
        elif node.kind is NodeKind.RULE:
            if contract.decision_ids or contract.definition_ref or contract.unit:
                raise _release_integrity_error("rule-has-inapplicable-field")
            if not contract.evidence_refs:
                raise _release_integrity_error("rule-missing-evidence")
            if not set(contract.evidence_refs).issubset(node.evidence_refs):
                raise _release_integrity_error("rule-references-unknown-evidence")
            rule_count += 1
        elif node.kind is NodeKind.METRIC:
            if contract.decision_ids or contract.evidence_refs:
                raise _release_integrity_error("metric-has-inapplicable-field")
            if contract.definition_ref is None:
                raise _release_integrity_error("metric-missing-definition")
            if contract.unit is None:
                raise _release_integrity_error("metric-missing-unit")
            if contract.definition_ref not in node.evidence_refs:
                raise _release_integrity_error("metric-references-unknown-definition")
            metric_count += 1

    return CanonicalReleaseIntegrityReceipt(
        schema_version=1,
        status="pass",
        release_id=release.release_id,
        node_count=len(release.nodes),
        exclusion_count=len(release.exclusions),
        relation_count=len(manifest.relations),
        qualified_tool_count=tool_count,
        qualified_rule_count=rule_count,
        qualified_metric_count=metric_count,
        relations_state="relations-validated",
    )


def load_canonical_release_integrity_manifest(
    path: Path,
) -> CanonicalReleaseIntegrityManifest:
    try:
        return CanonicalReleaseIntegrityManifest.model_validate_json(
            path.read_text(encoding="utf-8")
        )
    except Exception as exc:
        raise ValueError("canonical release integrity manifest invalid") from exc


def render_canonical_release_integrity_receipt(
    receipt: CanonicalReleaseIntegrityReceipt,
) -> str:
    return (
        json.dumps(
            receipt.model_dump(mode="json"), ensure_ascii=True, indent=2, sort_keys=True
        )
        + "\n"
    )


class EvidenceRef(_StrictModel):
    source_id: str = Field(min_length=3, max_length=128)
    unit_ids: list[str] = Field(min_length=1, max_length=64)

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe source ID")
        return value

    @field_validator("unit_ids")
    @classmethod
    def validate_unit_ids(cls, values: list[str]) -> list[str]:
        if any(_ID_PATTERN.fullmatch(value) is None for value in values):
            raise ValueError("unsafe evidence unit ID")
        if len(values) != len(set(values)):
            raise ValueError("duplicate evidence unit ID")
        return sorted(values)


class OntologyNode(_StrictModel):
    id: str = Field(min_length=3, max_length=192)
    kind: NodeKind
    canonical_name: str = Field(min_length=1, max_length=256)
    origin: OriginKind
    review_state: ReviewState
    evidence: list[EvidenceRef] = Field(default_factory=list, max_length=64)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe ontology ID")
        return value

    @model_validator(mode="after")
    def validate_source_evidence(self) -> OntologyNode:
        if (
            self.origin
            in {
                OriginKind.SOURCE_EXPLICIT,
                OriginKind.SOURCE_SYNTHESIS,
                OriginKind.HISTORICAL_EXAMPLE,
            }
            and not self.evidence
        ):
            raise ValueError("source-derived nodes require evidence")
        if (
            self.review_state is ReviewState.APPROVED
            and self.origin is OriginKind.SOURCE_SYNTHESIS
            and len(self.evidence) < 2
        ):
            raise ValueError("approved synthesis requires independent evidence")
        return self


class OntologyRelation(_StrictModel):
    source_id: str = Field(min_length=3, max_length=192)
    target_id: str = Field(min_length=3, max_length=192)
    relation_type: str = Field(min_length=3, max_length=96)

    @field_validator("source_id", "target_id", "relation_type")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe relation identifier")
        return value


class OntologyAlias(_StrictModel):
    alias: str = Field(min_length=1, max_length=192)
    canonical_id: str = Field(min_length=3, max_length=192)

    @field_validator("canonical_id")
    @classmethod
    def validate_canonical_id(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe canonical ID")
        return value


class CandidateNode(_StrictModel):
    candidate_id: str = Field(min_length=3, max_length=192)
    proposed_node: OntologyNode
    extractor_id: str = Field(min_length=3, max_length=192)
    extraction_run_id: str = Field(min_length=3, max_length=192)
    confidence: float = Field(ge=0, le=1)
    unresolved_questions: list[str] = Field(default_factory=list, max_length=32)
    working_text: str = Field(min_length=24, max_length=2048)
    locators: list[str] = Field(min_length=1, max_length=64)

    @field_validator("candidate_id", "extractor_id", "extraction_run_id")
    @classmethod
    def validate_candidate_id(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe candidate ID")
        return value

    @model_validator(mode="after")
    def validate_candidate_state(self) -> CandidateNode:
        if self.proposed_node.review_state not in {
            ReviewState.CANDIDATE,
            ReviewState.NEEDS_REVIEW,
        }:
            raise ValueError("candidate cannot carry a terminal review state")
        evidence_units = {
            unit_id
            for evidence in self.proposed_node.evidence
            for unit_id in evidence.unit_ids
        }
        if set(self.locators) != evidence_units:
            raise ValueError("candidate locators must match proposed-node evidence")
        return self


class ReviewDecision(_StrictModel):
    candidate_id: str = Field(min_length=3, max_length=192)
    state: ReviewState
    outcome: CandidateReviewOutcome
    reviewer_id: str = Field(min_length=3, max_length=192)
    review_run_id: str = Field(min_length=3, max_length=192)
    rationale: str = Field(min_length=1, max_length=1024)
    evidence: list[EvidenceRef] = Field(default_factory=list, max_length=64)

    @field_validator("candidate_id", "reviewer_id", "review_run_id")
    @classmethod
    def validate_candidate_id(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe candidate ID")
        return value

    @model_validator(mode="after")
    def validate_decision(self) -> ReviewDecision:
        if self.state is ReviewState.CANDIDATE:
            raise ValueError("review decision cannot retain candidate state")
        if self.state is ReviewState.APPROVED:
            raise ValueError("review queue cannot promote candidate knowledge")
        if not self.evidence:
            raise ValueError("review decision requires evidence")
        expected_state = {
            CandidateReviewOutcome.APPROVE_CANDIDATE: ReviewState.NEEDS_REVIEW,
            CandidateReviewOutcome.NEEDS_REVISION: ReviewState.NEEDS_REVIEW,
            CandidateReviewOutcome.REJECT_CANDIDATE: ReviewState.REJECTED,
        }[self.outcome]
        if self.state is not expected_state:
            raise ValueError("review decision state conflicts with its outcome")
        return self


class ReviewQueue(_StrictModel):
    schema_version: Literal[2]
    candidates: list[CandidateNode] = Field(default_factory=list)
    decisions: list[ReviewDecision] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> ReviewQueue:
        candidate_ids = [item.candidate_id for item in self.candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("duplicate candidate ID")
        if any(item.candidate_id not in set(candidate_ids) for item in self.decisions):
            raise ValueError("review decision references unknown candidate")
        if len({item.candidate_id for item in self.decisions}) != len(self.decisions):
            raise ValueError("candidate has multiple review decisions")
        if set(candidate_ids) != {item.candidate_id for item in self.decisions}:
            raise ValueError("every candidate requires exactly one review decision")
        candidates_by_id = {item.candidate_id: item for item in self.candidates}
        for decision in self.decisions:
            candidate = candidates_by_id[decision.candidate_id]
            if candidate.extractor_id == decision.reviewer_id:
                raise ValueError("extractor and reviewer must be independent")
        return self


def render_review_queue(queue: ReviewQueue) -> str:
    return (
        json.dumps(
            queue.model_dump(mode="json"), ensure_ascii=True, indent=2, sort_keys=True
        )
        + "\n"
    )


def load_review_queue(path: Path) -> ReviewQueue:
    try:
        return ReviewQueue.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("review queue contract invalid") from exc


class OntologyDocument(_StrictModel):
    schema_version: Literal[2]
    nodes: list[OntologyNode] = Field(default_factory=list)
    relations: list[OntologyRelation] = Field(default_factory=list)
    aliases: list[OntologyAlias] = Field(default_factory=list)
    review_queue: list[ReviewDecision] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_graph_integrity(self) -> OntologyDocument:
        node_ids = [node.id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("duplicate ontology node ID")
        known = set(node_ids)
        if any(alias.canonical_id not in known for alias in self.aliases):
            raise ValueError("alias references unknown canonical node")
        if len([alias.alias for alias in self.aliases]) != len(
            {alias.alias for alias in self.aliases}
        ):
            raise ValueError("duplicate ontology alias")
        if any(
            relation.source_id not in known or relation.target_id not in known
            for relation in self.relations
        ):
            raise ValueError("relation references unknown node")
        return self


def ontology_schema() -> dict[str, object]:
    return OntologyDocument.model_json_schema()


def render_ontology_schema() -> str:
    return (
        json.dumps(ontology_schema(), ensure_ascii=True, indent=2, sort_keys=True)
        + "\n"
    )


def ontology_schema_hash() -> str:
    return hashlib.sha256(render_ontology_schema().encode("utf-8")).hexdigest()
