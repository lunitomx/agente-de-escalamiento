#!/usr/bin/env python3
"""Create only sanitized S64.1 projection/release files from explicit inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validators.ontology_v2 import (
    AuthorizedCandidateProjection,
    ReviewQueue,
    build_canonical_release,
    render_canonical_release,
)


def _opaque_digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True).encode("utf-8")
    return f"digest.sha256.{hashlib.sha256(encoded).hexdigest()}"


def _load_queue(path: Path) -> ReviewQueue:
    try:
        return ReviewQueue.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("authorized queue contract invalid") from exc


def project_queues(
    queue_paths: list[Path],
    blocked_ids: set[str],
    generic_ids: set[str],
    external_ids: set[str],
) -> AuthorizedCandidateProjection:
    candidates: list[dict[str, object]] = []
    for queue_path in queue_paths:
        queue = _load_queue(queue_path)
        decisions = {decision.candidate_id: decision for decision in queue.decisions}
        for candidate in queue.candidates:
            decision = decisions[candidate.candidate_id]
            candidates.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "canonical_id": candidate.proposed_node.id,
                    "kind": candidate.proposed_node.kind.value,
                    "canonical_name": candidate.proposed_node.canonical_name,
                    "origin": candidate.proposed_node.origin.value,
                    "aliases": [],
                    "source_ids": sorted(
                        {
                            evidence.source_id
                            for evidence in candidate.proposed_node.evidence
                        }
                    ),
                    "candidate_receipt": _opaque_digest(
                        candidate.model_dump(mode="json")
                    ),
                    "review_receipt": _opaque_digest(decision.model_dump(mode="json")),
                    "review_outcome": decision.outcome.value,
                    "reviewer_independent": candidate.extractor_id
                    != decision.reviewer_id,
                    "receipts_valid": True,
                    "source_bounded": True,
                    "external_content": candidate.candidate_id in external_ids,
                    "blocked": candidate.candidate_id in blocked_ids,
                    "generic": candidate.candidate_id in generic_ids,
                }
            )
    return AuthorizedCandidateProjection.model_validate(
        {"schema_version": 1, "candidates": candidates}
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", action="append", type=Path, required=True)
    parser.add_argument("--projection", type=Path)
    parser.add_argument("--release", type=Path)
    parser.add_argument("--blocked-candidate", action="append", default=[])
    parser.add_argument("--generic-candidate", action="append", default=[])
    parser.add_argument("--external-candidate", action="append", default=[])
    args = parser.parse_args()
    if args.projection is None and args.release is None:
        parser.error("one of --projection or --release is required")
    projection = project_queues(
        args.queue,
        set(args.blocked_candidate),
        set(args.generic_candidate),
        set(args.external_candidate),
    )
    if args.projection is not None:
        args.projection.write_text(
            json.dumps(
                projection.model_dump(mode="json"),
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    if args.release is not None:
        args.release.write_text(
            render_canonical_release(build_canonical_release(projection)),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
