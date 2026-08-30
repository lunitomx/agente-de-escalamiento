#!/usr/bin/env python3
"""Validate the public-safe integrity surface of canonical release S64.1."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.ontology_v2 import (  # noqa: E402
    load_canonical_release,
    load_canonical_release_integrity_manifest,
    render_canonical_release_integrity_receipt,
    validate_canonical_release_integrity,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--relations", type=Path)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()
    try:
        release = load_canonical_release(args.release)
        manifest = (
            load_canonical_release_integrity_manifest(args.relations)
            if args.relations is not None
            else None
        )
        receipt = validate_canonical_release_integrity(release, manifest)
    except Exception:
        print(
            "canonical release integrity: unable to produce a safe passing receipt",
            file=sys.stderr,
        )
        return 1
    if args.format == "json":
        print(render_canonical_release_integrity_receipt(receipt), end="")
        return 0 if receipt.status == "pass" else 2
    print("# ESCALA Canonical Release Integrity Receipt\n")
    print(f"- Status: `{receipt.status}`")
    print(f"- Release: `{receipt.release_id}`")
    print(f"- Nodes verified: {receipt.node_count}")
    print(f"- Exclusions verified: {receipt.exclusion_count}")
    print(f"- Relations verified: {receipt.relation_count}")
    print(f"- Relations state: `{receipt.relations_state}`")
    return 0 if receipt.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
