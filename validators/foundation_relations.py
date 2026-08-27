"""Typed, manifest-bound relation candidates for E59 foundations."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.ontology_v2 import (
    CandidateReviewOutcome,
    EvidenceRef,
    OriginKind,
    ReviewState,
)
from validators.source_manifest import SourceManifest

_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RelationCandidate(_StrictModel):
    relation_id: str = Field(min_length=3, max_length=192)
    source_node_id: str = Field(min_length=3, max_length=192)
    target_node_id: str = Field(min_length=3, max_length=192)
    relation_type: str = Field(min_length=3, max_length=96)
    origin: OriginKind
    evidence: list[EvidenceRef] = Field(min_length=1, max_length=64)
    locators: list[str] = Field(min_length=1, max_length=64)
    confidence: float = Field(ge=0, le=1)
    working_text: str = Field(min_length=12, max_length=1024)
    extractor_id: str = Field(min_length=3, max_length=192)
    extraction_run_id: str = Field(min_length=3, max_length=192)
    unresolved_questions: list[str] = Field(default_factory=list, max_length=32)

    @field_validator(
        "relation_id",
        "source_node_id",
        "target_node_id",
        "relation_type",
        "extractor_id",
        "extraction_run_id",
    )
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        if _ID.fullmatch(value) is None:
            raise ValueError("unsafe relation identifier")
        return value

    @model_validator(mode="after")
    def validate_evidence(self) -> "RelationCandidate":
        evidence_units = {unit for ref in self.evidence for unit in ref.unit_ids}
        if evidence_units != set(self.locators):
            raise ValueError("relation locators must match evidence")
        if self.origin is OriginKind.SOURCE_SYNTHESIS and len(evidence_units) < 2:
            raise ValueError("synthesis relation requires multiple evidence units")
        return self


class RelationReviewDecision(_StrictModel):
    relation_id: str = Field(min_length=3, max_length=192)
    state: ReviewState
    outcome: CandidateReviewOutcome
    reviewer_id: str = Field(min_length=3, max_length=192)
    review_run_id: str = Field(min_length=3, max_length=192)
    rationale: str = Field(min_length=1, max_length=1024)
    evidence: list[EvidenceRef] = Field(min_length=1, max_length=64)

    @field_validator("relation_id", "reviewer_id", "review_run_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        if _ID.fullmatch(value) is None:
            raise ValueError("unsafe relation-review identifier")
        return value

    @model_validator(mode="after")
    def validate_outcome(self) -> "RelationReviewDecision":
        if self.state in {ReviewState.CANDIDATE, ReviewState.APPROVED}:
            raise ValueError("relation review cannot promote canonical relation")
        expected = (
            ReviewState.REJECTED
            if self.outcome is CandidateReviewOutcome.REJECT_CANDIDATE
            else ReviewState.NEEDS_REVIEW
        )
        if self.state is not expected:
            raise ValueError("relation review state conflicts with outcome")
        return self


class RelationReviewQueue(_StrictModel):
    schema_version: Literal[1]
    source_id: str = Field(min_length=3, max_length=128)
    relations: list[RelationCandidate] = Field(min_length=1)
    decisions: list[RelationReviewDecision] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_references(self) -> "RelationReviewQueue":
        relation_ids = [item.relation_id for item in self.relations]
        if len(relation_ids) != len(set(relation_ids)):
            raise ValueError("duplicate relation ID")
        decision_ids = [item.relation_id for item in self.decisions]
        if set(relation_ids) != set(decision_ids) or len(decision_ids) != len(
            set(decision_ids)
        ):
            raise ValueError("every relation requires exactly one review decision")
        relations = {item.relation_id: item for item in self.relations}
        for decision in self.decisions:
            relation = relations[decision.relation_id]
            if decision.reviewer_id == relation.extractor_id:
                raise ValueError("relation extractor and reviewer must be independent")
        return self


def validate_relation_queue_against_manifest(
    queue: RelationReviewQueue, manifest: SourceManifest, known_node_ids: set[str]
) -> None:
    if queue.source_id != manifest.source_id:
        raise ValueError("relation queue source differs from manifest")
    known_units = {unit.unit_id for unit in manifest.units}
    relations = {item.relation_id: item for item in queue.relations}
    for relation in queue.relations:
        if relation.source_node_id == relation.target_node_id:
            raise ValueError("relation cannot be a self-link")
        if (
            relation.source_node_id not in known_node_ids
            or relation.target_node_id not in known_node_ids
        ):
            raise ValueError("relation references unknown candidate node")
        if not set(relation.locators).issubset(known_units):
            raise ValueError("relation locator is absent from manifest")
    for decision in queue.decisions:
        if {
            (ref.source_id, unit) for ref in decision.evidence for unit in ref.unit_ids
        } != {
            (ref.source_id, unit)
            for ref in relations[decision.relation_id].evidence
            for unit in ref.unit_ids
        }:
            raise ValueError("relation decision evidence differs from relation")


def load_relation_queue(path: Path) -> RelationReviewQueue:
    return RelationReviewQueue.model_validate_json(path.read_text(encoding="utf-8"))


def render_relation_queue(queue: RelationReviewQueue) -> str:
    return (
        json.dumps(
            queue.model_dump(mode="json"), ensure_ascii=True, indent=2, sort_keys=True
        )
        + "\n"
    )
