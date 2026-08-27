#!/usr/bin/env python3
"""Validate private E59 historical/external classifications safely."""

from __future__ import annotations

import argparse
from pathlib import Path

from validators.foundations_classification import (
    SpecialSourceClassificationSet,
    validate_special_source_classifications,
)
from validators.source_authority import load_source_registry
from validators.source_manifest import load_source_manifest, validate_source_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--classifications", type=Path, required=True)
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
        classifications = SpecialSourceClassificationSet.model_validate_json(
            args.classifications.read_text(encoding="utf-8")
        )
        validate_special_source_classifications(classifications, manifest)
    except Exception as exc:
        print(f"Status: `fail`\nReason: {exc}")
        return 1
    print(f"Status: `pass`\nClassifications: {len(classifications.entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
