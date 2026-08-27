from __future__ import annotations

from pathlib import Path

import pytest

from validators.foundation_relations import (
    RelationReviewQueue,
    validate_relation_queue_against_manifest,
)
from validators.source_manifest import SourceManifest


def _manifest() -> SourceManifest:
    return SourceManifest.model_validate(
        {
            "schema_version": 1,
            "source_id": "source.example",
            "source_sha256": "0" * 64,
            "source_line_count": 1,
            "units": [
                {
                    "source_id": "source.example",
                    "unit_id": "source.example.u0001",
                    "line_start": 1,
                    "line_end": 1,
                    "content_type": "section",
                    "sha256": "1" * 64,
                }
            ],
        }
    )


def _queue() -> RelationReviewQueue:
    evidence = [{"source_id": "source.example", "unit_ids": ["source.example.u0001"]}]
    return RelationReviewQueue.model_validate(
        {
            "schema_version": 1,
            "source_id": "source.example",
            "relations": [
                {
                    "relation_id": "relation.a.b",
                    "source_node_id": "node.a",
                    "target_node_id": "node.b",
                    "relation_type": "feeds-into",
                    "origin": "source-explicit",
                    "evidence": evidence,
                    "locators": ["source.example.u0001"],
                    "confidence": 0.9,
                    "working_text": "The source explicitly connects these two candidate nodes.",
                    "extractor_id": "extractor.example",
                    "extraction_run_id": "run.extract.example",
                }
            ],
            "decisions": [
                {
                    "relation_id": "relation.a.b",
                    "state": "needs-review",
                    "outcome": "approve-candidate",
                    "reviewer_id": "reviewer.example",
                    "review_run_id": "run.review.example",
                    "rationale": "Evidence reviewed without canonical promotion.",
                    "evidence": evidence,
                }
            ],
        }
    )


def test_relation_queue_binds_nodes_and_locators_to_manifest() -> None:
    validate_relation_queue_against_manifest(
        _queue(), _manifest(), {"node.a", "node.b"}
    )


def test_relation_queue_rejects_unknown_node() -> None:
    with pytest.raises(ValueError, match="unknown candidate node"):
        validate_relation_queue_against_manifest(_queue(), _manifest(), {"node.a"})


def test_relation_queue_requires_independent_reviewer() -> None:
    data = _queue().model_dump(mode="json")
    data["decisions"][0]["reviewer_id"] = "extractor.example"
    with pytest.raises(ValueError, match="independent"):
        RelationReviewQueue.model_validate(data)


def test_relation_queue_rejects_self_link() -> None:
    data = _queue().model_dump(mode="json")
    data["relations"][0]["target_node_id"] = "node.a"
    queue = RelationReviewQueue.model_validate(data)
    with pytest.raises(ValueError, match="self-link"):
        validate_relation_queue_against_manifest(queue, _manifest(), {"node.a"})


def test_real_e59_relation_queue_validates_against_real_manifest() -> None:
    from validators.foundation_relations import load_relation_queue
    from validators.ontology_v2 import load_review_queue
    from validators.source_manifest import load_source_manifest

    root = Path(__file__).resolve().parents[1]
    evidence = root / "work/epics/e59-foundations-4d-fidelity/evidence"
    nodes = {
        candidate.proposed_node.id
        for candidate in load_review_queue(
            evidence / "s59-v2-review-queue.json"
        ).candidates
    }
    validate_relation_queue_against_manifest(
        load_relation_queue(evidence / "s59-v2-relation-review-queue.json"),
        load_source_manifest(root / "sources/source-manifest.jsonl"),
        nodes,
    )
