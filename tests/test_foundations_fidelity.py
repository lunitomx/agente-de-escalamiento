from __future__ import annotations

import pytest

from validators.foundations_fidelity import (
    FoundationsFidelityError,
    validate_foundation_candidates_against_manifest,
    validate_foundations_review_queue,
)
from validators.ontology_v2 import EvidenceRef, ReviewQueue
from validators.source_manifest import SourceManifest


def _manifest() -> SourceManifest:
    return SourceManifest.model_validate(
        {
            "schema_version": 1,
            "source_id": "source.example",
            "source_sha256": "0" * 64,
            "source_line_count": 4,
            "units": [
                {
                    "source_id": "source.example",
                    "unit_id": "source.example.u0001",
                    "line_start": 1,
                    "line_end": 4,
                    "content_type": "section",
                    "sha256": "1" * 64,
                }
            ],
        }
    )


def _queue(
    *,
    locator: str = "source.example.u0001",
    text: str = "A distinct semantic summary for the reviewed concept.",
) -> ReviewQueue:
    evidence = [{"source_id": "source.example", "unit_ids": [locator]}]
    return ReviewQueue.model_validate(
        {
            "schema_version": 2,
            "candidates": [
                {
                    "candidate_id": "candidate.framework.example",
                    "extractor_id": "extractor.example",
                    "extraction_run_id": "run.extract.example",
                    "confidence": 0.9,
                    "working_text": text,
                    "locators": [locator],
                    "proposed_node": {
                        "id": "framework.example",
                        "kind": "framework",
                        "canonical_name": "Example framework",
                        "origin": "source-explicit",
                        "review_state": "needs-review",
                        "evidence": evidence,
                    },
                }
            ],
            "decisions": [
                {
                    "candidate_id": "candidate.framework.example",
                    "state": "needs-review",
                    "outcome": "approve-candidate",
                    "reviewer_id": "reviewer.example",
                    "review_run_id": "run.review.example",
                    "rationale": "Independently checked against the structural locator.",
                    "evidence": evidence,
                }
            ],
        }
    )


def test_foundations_queue_binds_to_manifest() -> None:
    validate_foundations_review_queue(_queue(), _manifest())


def test_foundations_queue_rejects_unknown_locator() -> None:
    with pytest.raises(FoundationsFidelityError, match="absent from manifest"):
        validate_foundations_review_queue(
            _queue(locator="source.example.u9999"), _manifest()
        )


def test_foundations_queue_rejects_non_distinct_working_text() -> None:
    queue = _queue()
    duplicate = queue.candidates[0].model_copy(
        update={"candidate_id": "candidate.framework.other"}
    )
    duplicate_decision = queue.decisions[0].model_copy(
        update={"candidate_id": duplicate.candidate_id}
    )
    queue = queue.model_copy(
        update={
            "candidates": [queue.candidates[0], duplicate],
            "decisions": [queue.decisions[0], duplicate_decision],
        }
    )
    with pytest.raises(FoundationsFidelityError, match="distinct"):
        validate_foundations_review_queue(queue, _manifest())


def test_foundations_queue_revalidates_mutated_in_memory_model() -> None:
    unsafe_queue = _queue().model_copy(update={"decisions": []})
    with pytest.raises(ValueError, match="every candidate"):
        validate_foundations_review_queue(unsafe_queue, _manifest())


def test_foundations_queue_rejects_decision_evidence_mismatch() -> None:
    queue = _queue()
    decision = queue.decisions[0].model_copy(
        update={
            "evidence": [
                EvidenceRef(
                    source_id="source.example", unit_ids=["source.example.u0002"]
                )
            ]
        }
    )
    unsafe_queue = queue.model_copy(update={"decisions": [decision]})
    with pytest.raises(FoundationsFidelityError, match="differs from candidate"):
        validate_foundations_review_queue(unsafe_queue, _manifest())


def test_foundations_queue_revalidates_mutated_reviewer_identity() -> None:
    queue = _queue()
    candidate = queue.candidates[0].model_copy(
        update={"extractor_id": queue.decisions[0].reviewer_id}
    )
    unsafe_queue = queue.model_copy(update={"candidates": [candidate]})
    with pytest.raises(ValueError, match="independent"):
        validate_foundations_review_queue(unsafe_queue, _manifest())


def test_candidate_evidence_must_exist_in_manifest() -> None:
    candidate = _queue().candidates[0]
    proposed_node = candidate.proposed_node.model_copy(
        update={
            "evidence": [
                EvidenceRef(
                    source_id="source.example", unit_ids=["source.example.u9999"]
                )
            ]
        }
    )
    unsafe_candidate = candidate.model_copy(
        update={
            "proposed_node": proposed_node,
            "locators": ["source.example.u9999"],
        }
    )
    with pytest.raises(FoundationsFidelityError, match="absent from manifest"):
        validate_foundation_candidates_against_manifest([unsafe_candidate], _manifest())
