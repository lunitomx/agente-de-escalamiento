#!/usr/bin/env python3
"""Validate the private ontology candidate/review queue safely."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.ontology_v2 import load_review_queue  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ontology review queue.")
    parser.add_argument("--queue", type=Path, required=True)
    args = parser.parse_args()
    try:
        queue = load_review_queue(args.queue)
    except Exception:
        print(
            "ontology review queue: unable to produce a safe passing receipt",
            file=sys.stderr,
        )
        return 1
    print("# ESCALA Ontology v2 Review Queue Receipt\n")
    print("- Status: `pass`")
    print(f"- Candidates: {len(queue.candidates)}")
    print(f"- Decisions: {len(queue.decisions)}")
    print("- Authority: private queue contract only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
