from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest
import yaml
from pydantic import ValidationError

from validators.ontology_v2 import (
    AuthorizedCandidateProjection,
    CanonicalRelease,
    CandidateReviewOutcome,
    NodeKind,
    CandidateNode,
    OntologyDocument,
    ReviewDecision,
    ReviewQueue,
    load_review_queue,
    render_review_queue,
    OriginKind,
    ReviewState,
    build_canonical_release,
    load_canonical_release,
    ontology_schema_hash,
    render_canonical_release,
    render_ontology_schema,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "ontology/v2/schema.json"
VOCABULARY = ROOT / "ontology/v2/vocabulary.yaml"
SCRIPT = ROOT / "scripts/check_ontology_v2_schema.py"
QUEUE = ROOT / "ontology/v2/review-queue.json"
QUEUE_SCRIPT = ROOT / "scripts/check_ontology_review_queue.py"
RELEASE = ROOT / "ontology/v2/releases/s64.1.json"
PROJECTION = ROOT / "ontology/v2/releases/s64.1.projection.json"
RELEASE_SCRIPT = ROOT / "scripts/build_canonical_release.py"
EXPECTED_RELEASE_MANIFEST = {
    "nodes": 76,
    "exclusions": 3,
    "exclusion_reasons": {"needs-revision": 3},
}


def test_checked_in_schema_is_deterministic_and_private_contract_only() -> None:
    rendered = render_ontology_schema()

    assert SCHEMA.read_text(encoding="utf-8") == rendered
    assert len(ontology_schema_hash()) == 64
    assert "scaling_up_llamaparse" not in rendered
    assert {item.value for item in NodeKind} >= {
        "decision-area",
        "tool",
        "rule",
        "diagnostic-question",
        "result",
    }
    assert {item.value for item in OriginKind} == {
        "source-explicit",
        "source-synthesis",
        "historical-example",
        "external-reference",
        "company-local",
        "model-hypothesis",
    }


def test_checked_in_vocabulary_matches_typed_contract() -> None:
    vocabulary = yaml.safe_load(VOCABULARY.read_text(encoding="utf-8"))

    assert vocabulary["schema_version"] == 2
    assert vocabulary["node_kinds"] == [item.value for item in NodeKind]
    assert vocabulary["origins"] == [item.value for item in OriginKind]
    assert vocabulary["review_states"] == [item.value for item in ReviewState]


def test_source_derived_node_requires_evidence_and_synthesis_requires_two_when_approved() -> (
    None
):
    base = {
        "schema_version": 2,
        "nodes": [
            {
                "id": "tool.example",
                "kind": "tool",
                "canonical_name": "Example",
                "origin": "source-explicit",
                "review_state": "candidate",
            }
        ],
    }
    with pytest.raises(ValidationError, match="source-derived nodes require evidence"):
        OntologyDocument.model_validate(base)

    base["nodes"][0].update(
        {
            "origin": OriginKind.SOURCE_SYNTHESIS,
            "review_state": ReviewState.APPROVED,
            "evidence": [
                {"source_id": "source.example", "unit_ids": ["source.example.u0001"]}
            ],
        }
    )
    with pytest.raises(
        ValidationError, match="approved synthesis requires independent evidence"
    ):
        OntologyDocument.model_validate(base)


def test_review_queue_keeps_candidates_distinct_from_approved_knowledge() -> None:
    candidate = CandidateNode.model_validate(
        {
            "candidate_id": "candidate.tool.example",
            "proposed_node": {
                "id": "tool.example",
                "kind": "tool",
                "canonical_name": "Example",
                "origin": "source-explicit",
                "review_state": "candidate",
                "evidence": [
                    {
                        "source_id": "source.example",
                        "unit_ids": ["source.example.u0001"],
                    }
                ],
            },
            "extractor_id": "extractor.example",
            "extraction_run_id": "run.extract.example",
            "confidence": 0.91,
            "working_text": "A distinct working summary of the candidate concept.",
            "locators": ["source.example.u0001"],
            "unresolved_questions": ["confirm scope"],
        }
    )
    approved = ReviewDecision.model_validate(
        {
            "candidate_id": candidate.candidate_id,
            "state": "needs-review",
            "outcome": CandidateReviewOutcome.APPROVE_CANDIDATE,
            "reviewer_id": "reviewer.example",
            "review_run_id": "run.review.example",
            "rationale": "Evidence reviewed without promoting the candidate.",
            "evidence": [
                {"source_id": "source.example", "unit_ids": ["source.example.u0001"]}
            ],
        }
    )
    queue = ReviewQueue(schema_version=2, candidates=[candidate], decisions=[approved])
    assert "Example" in render_review_queue(queue)

    with pytest.raises(ValidationError, match="review decision requires evidence"):
        ReviewDecision.model_validate(
            {
                "candidate_id": candidate.candidate_id,
                "state": "needs-review",
                "outcome": "approve-candidate",
                "reviewer_id": "reviewer.example",
                "review_run_id": "run.review.example",
                "rationale": "No evidence.",
            }
        )
    with pytest.raises(ValidationError, match="unknown candidate"):
        ReviewQueue(schema_version=2, decisions=[approved])
    with pytest.raises(ValidationError, match="every candidate"):
        ReviewQueue(schema_version=2, candidates=[candidate])


def test_empty_checked_in_review_queue_and_cli_are_safe() -> None:
    queue = load_review_queue(QUEUE)
    completed = subprocess.run(
        [sys.executable, str(QUEUE_SCRIPT), "--queue", str(QUEUE)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert queue.candidates == []
    assert completed.returncode == 0
    assert "Candidates: 0" in completed.stdout
    assert "scaling_up_llamaparse" not in completed.stdout


def test_schema_cli_never_emits_corpus_content() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--schema", str(SCHEMA)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Status: `pass`" in completed.stdout
    assert "scaling_up_llamaparse" not in completed.stdout
    assert completed.stderr == ""


def test_document_blocks_duplicate_ids_and_orphaned_links() -> None:
    base = {
        "schema_version": 2,
        "nodes": [
            {
                "id": "tool.one",
                "kind": "tool",
                "canonical_name": "One",
                "origin": "company-local",
                "review_state": "approved",
            }
        ],
    }
    with pytest.raises(ValidationError, match="unknown canonical"):
        OntologyDocument.model_validate(
            {**base, "aliases": [{"alias": "one", "canonical_id": "tool.missing"}]}
        )
    with pytest.raises(ValidationError, match="unknown node"):
        OntologyDocument.model_validate(
            {
                **base,
                "relations": [
                    {
                        "source_id": "tool.one",
                        "target_id": "tool.missing",
                        "relation_type": "feeds-into",
                    }
                ],
            }
        )


def test_review_queue_requires_independent_extractor_and_reviewer() -> None:
    candidate = CandidateNode.model_validate(
        {
            "candidate_id": "candidate.framework.example",
            "extractor_id": "worker.same",
            "extraction_run_id": "run.extract.same",
            "confidence": 0.9,
            "working_text": "A semantic candidate summary for an example framework.",
            "locators": ["source.example.u0001"],
            "proposed_node": {
                "id": "framework.example",
                "kind": "framework",
                "canonical_name": "Example framework",
                "origin": "source-explicit",
                "review_state": "needs-review",
                "evidence": [
                    {
                        "source_id": "source.example",
                        "unit_ids": ["source.example.u0001"],
                    }
                ],
            },
        }
    )
    decision = ReviewDecision.model_validate(
        {
            "candidate_id": candidate.candidate_id,
            "state": "needs-review",
            "outcome": "approve-candidate",
            "reviewer_id": "worker.same",
            "review_run_id": "run.review.other",
            "rationale": "Review remains separate from canonical promotion.",
            "evidence": [
                {"source_id": "source.example", "unit_ids": ["source.example.u0001"]}
            ],
        }
    )
    with pytest.raises(ValidationError, match="independent"):
        ReviewQueue(schema_version=2, candidates=[candidate], decisions=[decision])


def test_authorized_projection_is_allowlisted_and_requires_independent_review() -> None:
    payload = {
        "schema_version": 1,
        "authorization_scope": "e59-e63-reviewed",
        "candidates": [
            {
                "candidate_id": "candidate.framework.example",
                "canonical_id": "framework.example",
                "kind": "framework",
                "canonical_name": "Example Framework",
                "origin": "source-explicit",
                "aliases": ["Framework example"],
                "source_ids": ["source.example"],
                "evidence_refs": ["digest.sha256.abc123"],
                "candidate_receipt": "digest.candidate.abc123",
                "review_receipt": "digest.review.def456",
                "review_outcome": "approve-candidate",
                "reviewer_independent": True,
                "receipts_valid": True,
                "source_bounded": True,
                "blocked": False,
                "generic": False,
            }
        ],
    }
    projection = AuthorizedCandidateProjection.model_validate(payload)
    assert projection.candidates[0].source_ids == ["source.example"]
    assert projection.candidates[0].candidate_receipt == "digest.candidate.abc123"

    for forbidden_field in (
        "working_text",
        "locators",
        "source_url",
        "source_text",
        "path",
    ):
        unsafe = {
            **payload,
            "candidates": [{**payload["candidates"][0], forbidden_field: "unsafe"}],
        }
        with pytest.raises(ValidationError):
            AuthorizedCandidateProjection.model_validate(unsafe)

    for unsafe_name in (
        "A source-like paragraph that contains enough words to be mistaken for an excerpt from a private source document and must never become a label.",
        "https://private.example/source",
        "/private/source/file.txt",
        "line one\nline two",
    ):
        with pytest.raises(ValidationError, match="safe label"):
            AuthorizedCandidateProjection.model_validate(
                {
                    **payload,
                    "candidates": [
                        {**payload["candidates"][0], "canonical_name": unsafe_name}
                    ],
                }
            )
    for legacy_field, legacy_value in (
        ("candidate_id", "e6.candidate.example"),
        ("canonical_id", "concept-example"),
        ("source_ids", ["e56.source.example"]),
        ("aliases", ["e56.legacy.alias"]),
    ):
        with pytest.raises(ValidationError, match="legacy"):
            AuthorizedCandidateProjection.model_validate(
                {
                    **payload,
                    "candidates": [
                        {**payload["candidates"][0], legacy_field: legacy_value}
                    ],
                }
            )
    with pytest.raises(ValidationError, match="authorization_scope"):
        AuthorizedCandidateProjection.model_validate(
            {**payload, "authorization_scope": "e6-reviewed"}
        )


def test_canonical_release_is_deterministic_and_partitions_projection() -> None:
    approved = {
        "candidate_id": "candidate.framework.example",
        "canonical_id": "framework.example",
        "kind": "framework",
        "canonical_name": "Example Framework",
        "origin": "source-explicit",
        "aliases": ["Framework example", "Example framework"],
        "source_ids": ["source.example"],
        "evidence_refs": ["digest.sha256.evidenceaaa", "digest.sha256.evidencebbb"],
        "candidate_receipt": "digest.candidate.abc123",
        "review_receipt": "digest.review.def456",
        "review_outcome": "approve-candidate",
        "reviewer_independent": True,
        "receipts_valid": True,
        "source_bounded": True,
        "external_content": False,
        "blocked": False,
        "generic": False,
    }
    deferred = {
        **approved,
        "candidate_id": "candidate.cash.example",
        "canonical_id": "cash.example",
        "review_outcome": "needs-revision",
    }
    projection = AuthorizedCandidateProjection.model_validate(
        {
            "schema_version": 1,
            "authorization_scope": "e59-e63-reviewed",
            "candidates": [deferred, approved],
        }
    )
    release = build_canonical_release(projection)
    assert [node.candidate_id for node in release.nodes] == [approved["candidate_id"]]
    assert [item.candidate_id for item in release.exclusions] == [
        deferred["candidate_id"]
    ]
    assert release.exclusions[0].reason_code == "needs-revision"
    assert release.nodes[0].aliases == sorted(approved["aliases"])
    assert release.nodes[0].evidence_refs == sorted(approved["evidence_refs"])
    assert render_canonical_release(release) == render_canonical_release(
        CanonicalRelease.model_validate(release.model_dump())
    )
    assert "working_text" not in render_canonical_release(release)


def test_builder_excludes_unbounded_or_invalid_receipt_candidates() -> None:
    candidate = {
        "candidate_id": "candidate.framework.example",
        "canonical_id": "framework.example",
        "kind": "framework",
        "canonical_name": "Example Framework",
        "origin": "source-explicit",
        "aliases": [],
        "source_ids": ["source.example"],
        "evidence_refs": ["digest.sha256.evidenceaaa"],
        "candidate_receipt": "digest.candidate.abc123",
        "review_receipt": "digest.review.def456",
        "review_outcome": "approve-candidate",
        "reviewer_independent": True,
        "receipts_valid": True,
        "source_bounded": True,
        "external_content": False,
        "blocked": False,
        "generic": False,
    }
    for field, expected_reason, expected_disposition in (
        ("source_bounded", "blocked-source", "review-required"),
        ("receipts_valid", "missing-or-invalid-receipt", "review-required"),
        ("reviewer_independent", "review-not-independent", "review-required"),
        ("blocked", "blocked-source", "review-required"),
        ("generic", "generic-candidate", "excluded"),
        ("external_content", "external-content-source-bounded", "review-required"),
    ):
        projection = AuthorizedCandidateProjection.model_validate(
            {
                "schema_version": 1,
                "authorization_scope": "e59-e63-reviewed",
                "candidates": [{**candidate, field: not candidate[field]}],
            }
        )
        release = build_canonical_release(projection)
        assert release.nodes == []
        assert release.exclusions[0].disposition == expected_disposition
        assert release.exclusions[0].reason_code == expected_reason

    for outcome, expected_reason in (
        ("needs-revision", "needs-revision"),
        ("reject-candidate", "reject-candidate"),
    ):
        projection = AuthorizedCandidateProjection.model_validate(
            {
                "schema_version": 1,
                "authorization_scope": "e59-e63-reviewed",
                "candidates": [{**candidate, "review_outcome": outcome}],
            }
        )
        assert (
            build_canonical_release(projection).exclusions[0].reason_code
            == expected_reason
        )


def test_canonical_release_rejects_unsafe_or_nonexclusive_entries(
    tmp_path: Path,
) -> None:
    valid = {
        "schema_version": 1,
        "release_id": "s64.1",
        "nodes": [
            {
                "canonical_id": "framework.example",
                "candidate_id": "candidate.framework.example",
                "kind": "framework",
                "canonical_name": "Example Framework",
                "origin": "source-explicit",
                "aliases": [],
                "source_ids": ["source.example"],
                "evidence_refs": ["digest.sha256.evidenceaaa"],
                "candidate_receipt": "digest.candidate.abc123",
                "review_receipt": "digest.review.def456",
                "review_outcome": "approve-candidate",
            }
        ],
        "exclusions": [],
    }
    with pytest.raises(ValidationError):
        CanonicalRelease.model_validate(
            {**valid, "nodes": [{**valid["nodes"][0], "locator": "private"}]}
        )
    duplicated = {
        **valid,
        "exclusions": [
            {
                "candidate_id": "candidate.framework.example",
                "disposition": "excluded",
                "reason_code": "generic-candidate",
                "candidate_receipt": "digest.candidate.abc123",
                "review_receipt": "digest.review.def456",
                "source_ids": ["source.example"],
                "evidence_refs": ["digest.sha256.evidenceaaa"],
            }
        ],
    }
    with pytest.raises(ValidationError, match="exactly once"):
        CanonicalRelease.model_validate(duplicated)
    path = tmp_path / "release.json"
    path.write_text(
        render_canonical_release(CanonicalRelease.model_validate(valid)),
        encoding="utf-8",
    )
    assert load_canonical_release(path).release_id == "s64.1"


def test_checked_in_s64_1_release_is_rendered_safe_and_has_expected_partition() -> None:
    projection = AuthorizedCandidateProjection.model_validate_json(
        PROJECTION.read_text(encoding="utf-8")
    )
    release = load_canonical_release(RELEASE)
    rendered = render_canonical_release(release)
    assert RELEASE.read_text(encoding="utf-8") == rendered
    assert len(release.nodes) == EXPECTED_RELEASE_MANIFEST["nodes"]
    assert len(release.exclusions) == EXPECTED_RELEASE_MANIFEST["exclusions"]
    assert {
        reason: sum(item.reason_code == reason for item in release.exclusions)
        for reason in EXPECTED_RELEASE_MANIFEST["exclusion_reasons"]
    } == EXPECTED_RELEASE_MANIFEST["exclusion_reasons"]
    assert all(node.review_outcome == "approve-candidate" for node in release.nodes)
    assert all(node.candidate_receipt and node.review_receipt for node in release.nodes)
    assert all(
        item.candidate_receipt and item.review_receipt for item in release.exclusions
    )
    candidate_ids = [node.candidate_id for node in release.nodes] + [
        item.candidate_id for item in release.exclusions
    ]
    assert len(candidate_ids) == len(set(candidate_ids))
    assert len(projection.candidates) == 79
    assert render_canonical_release(build_canonical_release(projection)) == rendered
    assert all(candidate.evidence_refs for candidate in projection.candidates)
    assert "working_text" not in rendered
    assert "locators" not in rendered
    assert "/home/" not in rendered
    assert "http:" not in rendered
    assert "https:" not in rendered


def test_release_cli_requires_explicit_authorized_input() -> None:
    completed = subprocess.run(
        [sys.executable, str(RELEASE_SCRIPT), "--release", "release.json"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "--projection" in completed.stderr

    completed = subprocess.run(
        [
            sys.executable,
            str(RELEASE_SCRIPT),
            "--projection",
            str(PROJECTION),
            "--release",
            str(RELEASE),
            "--check",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0


def test_projection_allows_duplicate_canonical_id_when_one_candidate_is_excluded() -> (
    None
):
    base = {
        "candidate_id": "candidate.framework.approved",
        "canonical_id": "framework.example",
        "kind": "framework",
        "canonical_name": "Example Framework",
        "origin": "source-explicit",
        "aliases": [],
        "source_ids": ["source.example"],
        "evidence_refs": ["digest.sha256.evidenceaaa"],
        "candidate_receipt": "digest.candidate.abc123",
        "review_receipt": "digest.review.def456",
        "review_outcome": "approve-candidate",
        "reviewer_independent": True,
        "receipts_valid": True,
        "source_bounded": True,
        "blocked": False,
        "generic": False,
    }
    projection = AuthorizedCandidateProjection.model_validate(
        {
            "schema_version": 1,
            "authorization_scope": "e59-e63-reviewed",
            "candidates": [
                base,
                {
                    **base,
                    "candidate_id": "candidate.framework.deferred",
                    "review_outcome": "needs-revision",
                },
            ],
        }
    )
    release = build_canonical_release(projection)
    assert len(release.nodes) == 1
    assert len(release.exclusions) == 1
