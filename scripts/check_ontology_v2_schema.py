#!/usr/bin/env python3
"""Validate the private ontology v2 schema without reading corpus material."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.ontology_v2 import ontology_schema_hash, render_ontology_schema  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ontology v2 schema.")
    parser.add_argument("--schema", type=Path, required=True)
    args = parser.parse_args()
    try:
        current = args.schema.read_text(encoding="utf-8")
        expected = render_ontology_schema()
    except Exception:
        print(
            "ontology schema: unable to produce a safe passing receipt", file=sys.stderr
        )
        return 1
    if current != expected:
        print(
            "ontology schema: unable to produce a safe passing receipt", file=sys.stderr
        )
        return 1
    print("# ESCALA Ontology v2 Schema Receipt\n")
    print("- Status: `pass`")
    print(f"- Schema SHA-256: `{ontology_schema_hash()}`")
    print("- Authority: private schema contract only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
