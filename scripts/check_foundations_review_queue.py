#!/usr/bin/env python3
"""Validate a private E59 review queue against its source manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from validators.foundations_fidelity import (
    FoundationsFidelityError,
    validate_foundations_review_queue,
)
from validators.ontology_v2 import load_review_queue
from validators.source_authority import load_source_registry
from validators.source_manifest import (
    SourceManifestError,
    load_source_manifest,
    validate_source_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
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
    except (ValueError, FoundationsFidelityError, SourceManifestError) as exc:
        print(f"Status: `fail`\nReason: {exc}")
        return 1
    print(
        f"Status: `pass`\nCandidates: {len(queue.candidates)}\nDecisions: {len(queue.decisions)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
