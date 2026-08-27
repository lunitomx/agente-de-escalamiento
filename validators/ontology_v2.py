"""Typed, source-safe ontology v2 contracts; no corpus extraction occurs here."""

from __future__ import annotations

from enum import Enum
import hashlib
import json
from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class NodeKind(str, Enum):
    DECISION_AREA = "decision-area"
    FRAMEWORK = "framework"
    PRINCIPLE = "principle"
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
    unresolved_questions: list[str] = Field(default_factory=list, max_length=32)

    @field_validator("candidate_id")
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
        return self


class ReviewDecision(_StrictModel):
    candidate_id: str = Field(min_length=3, max_length=192)
    state: ReviewState
    rationale: str = Field(min_length=1, max_length=1024)
    evidence: list[EvidenceRef] = Field(default_factory=list, max_length=64)

    @field_validator("candidate_id")
    @classmethod
    def validate_candidate_id(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe candidate ID")
        return value

    @model_validator(mode="after")
    def validate_decision(self) -> ReviewDecision:
        if self.state is ReviewState.CANDIDATE:
            raise ValueError("review decision cannot retain candidate state")
        if self.state is ReviewState.APPROVED and not self.evidence:
            raise ValueError("approved review decision requires evidence")
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


def ontology_schema() -> dict[str, object]:
    return OntologyDocument.model_json_schema()


def render_ontology_schema() -> str:
    return (
        json.dumps(ontology_schema(), ensure_ascii=True, indent=2, sort_keys=True)
        + "\n"
    )


def ontology_schema_hash() -> str:
    return hashlib.sha256(render_ontology_schema().encode("utf-8")).hexdigest()
