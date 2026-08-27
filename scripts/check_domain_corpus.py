"""Check one private domain-corpus evidence bundle without printing source text."""

from __future__ import annotations

import argparse
from pathlib import Path

from validators.domain_coverage import (
    DomainCoverageMatrix,
    DomainInventory,
    validate_domain_coverage,
)
from validators.ontology_v2 import load_review_queue
from validators.source_manifest import load_source_manifest


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--queue", required=True)
    parser.add_argument("--coverage", required=True)
    parser.add_argument(
        "--manifest", type=Path, default=Path("sources/source-manifest.jsonl")
    )
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    inventory = DomainInventory.model_validate_json(
        (args.evidence_dir / args.inventory).read_text(encoding="utf-8")
    )
    matrix = DomainCoverageMatrix.model_validate_json(
        (args.evidence_dir / args.coverage).read_text(encoding="utf-8")
    )
    queue = load_review_queue(args.evidence_dir / args.queue)
    evidence_by_node = {
        candidate.proposed_node.id: {
            unit_id
            for evidence in candidate.proposed_node.evidence
            for unit_id in evidence.unit_ids
        }
        for candidate in queue.candidates
    }
    validate_domain_coverage(
        matrix, inventory, load_source_manifest(args.manifest), evidence_by_node
    )
    print(
        f"domain corpus pass: {inventory.domain}; "
        f"{inventory.unit_count} units; {len(queue.candidates)} candidates"
    )


if __name__ == "__main__":
    main()
