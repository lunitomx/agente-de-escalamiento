#!/usr/bin/env python3
"""Build one deterministic local ESCALA distribution artifact."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.public_export import (  # noqa: E402
    build_public_export,
    load_public_export_policy,
    load_third_party_inventory,
    render_public_export_build_json,
    render_public_export_build_markdown,
    write_public_export_build_receipts,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a local artifact from the full current Git commit.",
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        policy = load_public_export_policy(args.policy)
        inventory = load_third_party_inventory(args.inventory)
        result = build_public_export(
            repository=args.repo.resolve(),
            destination=args.destination,
            source_commit=args.source_commit,
            policy=policy,
            inventory=inventory,
        )
        write_public_export_build_receipts(
            result,
            policy,
            json_output=args.json_output,
            markdown_output=args.markdown_output,
        )
        rendered = (
            render_public_export_build_json(result, policy)
            if args.format == "json"
            else render_public_export_build_markdown(result, policy)
        )
    except Exception:  # Safe boundary: never reproduce paths, values, or raw errors.
        print("public export build: failed safely", file=sys.stderr)
        return 2
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
