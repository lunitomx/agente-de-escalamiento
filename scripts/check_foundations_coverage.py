#!/usr/bin/env python3
"""Validate private E59 coverage without exposing the corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validators.foundations_coverage import (
    FoundationCoverageMatrix,
    validate_foundation_coverage,
)
from validators.foundations_fidelity import (
    validate_foundation_candidates_against_manifest,
    validate_foundations_review_queue,
)
from validators.ontology_v2 import CandidateNode, load_review_queue
from validators.source_authority import load_source_registry
from validators.source_manifest import load_source_manifest, validate_source_manifest


def _load_draft_candidates(path: Path) -> list[CandidateNode]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("foundation draft candidates missing")
    return [CandidateNode.model_validate(candidate) for candidate in candidates]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument(
        "--repository", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--registry", type=Path, default=None)
    args = parser.parse_args()
    registry_path = args.registry or args.repository / "sources/source-registry.yaml"
    try:
        registry = load_source_registry(registry_path)
        manifest = load_source_manifest(args.manifest)
        validate_source_manifest(args.repository, registry, manifest)
        queue = load_review_queue(args.queue)
        validate_foundations_review_queue(queue, manifest)
        draft_candidates = _load_draft_candidates(args.draft)
        validate_foundation_candidates_against_manifest(draft_candidates, manifest)
        matrix = FoundationCoverageMatrix.model_validate_json(
            args.matrix.read_text(encoding="utf-8")
        )
        all_candidates = [*queue.candidates, *draft_candidates]
        known_node_evidence = {
            candidate.proposed_node.id: {
                unit_id
                for evidence in candidate.proposed_node.evidence
                for unit_id in evidence.unit_ids
            }
            for candidate in all_candidates
        }
        validate_foundation_coverage(matrix, manifest, known_node_evidence)
    except Exception as exc:
        print(f"Status: `fail`\nReason: {exc}")
        return 1
    print(
        f"Status: `pass`\nUnits: {len(matrix.rows)}\n"
        f"Queue candidates: {len(queue.candidates)}\n"
        f"Draft input candidates: {len(draft_candidates)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
