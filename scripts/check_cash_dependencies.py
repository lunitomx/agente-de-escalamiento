"""Validate E63's private formula-dependency receipt without printing source text."""

from __future__ import annotations

import argparse
from pathlib import Path

from validators.cash_dependencies import (
    CashDependencyReceipt,
    validate_cash_dependencies,
)
from validators.ontology_v2 import load_review_queue


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("queue", type=Path)
    args = parser.parse_args()
    receipt = CashDependencyReceipt.model_validate_json(args.receipt.read_text("utf-8"))
    queue = load_review_queue(args.queue)
    candidate_evidence = {
        candidate.candidate_id: {
            unit_id
            for ref in candidate.proposed_node.evidence
            for unit_id in ref.unit_ids
        }
        for candidate in queue.candidates
    }
    validate_cash_dependencies(receipt, candidate_evidence)
    print(f"cash dependency receipt pass: {len(receipt.dependencies)} dependencies")


if __name__ == "__main__":
    main()
