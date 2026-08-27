from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest
import yaml
from pydantic import ValidationError

from validators.ontology_v2 import (
    NodeKind,
    CandidateNode,
    OntologyDocument,
    ReviewDecision,
    ReviewQueue,
    load_review_queue,
    render_review_queue,
    OriginKind,
    ReviewState,
    ontology_schema_hash,
    render_ontology_schema,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "ontology/v2/schema.json"
VOCABULARY = ROOT / "ontology/v2/vocabulary.yaml"
SCRIPT = ROOT / "scripts/check_ontology_v2_schema.py"
QUEUE = ROOT / "ontology/v2/review-queue.json"
QUEUE_SCRIPT = ROOT / "scripts/check_ontology_review_queue.py"


def test_checked_in_schema_is_deterministic_and_private_contract_only() -> None:
    rendered = render_ontology_schema()

    assert SCHEMA.read_text(encoding="utf-8") == rendered
    assert len(ontology_schema_hash()) == 64
    assert "scaling_up_llamaparse" not in rendered
    assert {item.value for item in NodeKind} >= {"decision-area", "tool", "rule"}
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
            "unresolved_questions": ["confirm scope"],
        }
    )
    approved = ReviewDecision.model_validate(
        {
            "candidate_id": candidate.candidate_id,
            "state": "approved",
            "rationale": "Evidence reviewed.",
            "evidence": [
                {"source_id": "source.example", "unit_ids": ["source.example.u0001"]}
            ],
        }
    )
    queue = ReviewQueue(schema_version=2, candidates=[candidate], decisions=[approved])
    assert "Example" in render_review_queue(queue)

    with pytest.raises(
        ValidationError, match="approved review decision requires evidence"
    ):
        ReviewDecision.model_validate(
            {
                "candidate_id": candidate.candidate_id,
                "state": "approved",
                "rationale": "No evidence.",
            }
        )
    with pytest.raises(ValidationError, match="unknown candidate"):
        ReviewQueue(schema_version=2, decisions=[approved])


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
