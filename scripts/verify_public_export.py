#!/usr/bin/env python3
"""Independently verify one staged local ESCALA artifact."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.public_boundary import load_public_boundary_policy  # noqa: E402
from validators.public_export import (  # noqa: E402
    VerificationStatus,
    load_public_export_policy,
    load_third_party_inventory,
    render_public_export_verification_json,
    render_public_export_verification_markdown,
    verify_public_export,
    write_public_export_verification_receipts,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify a staged local artifact without invoking its assembler.",
    )
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--public-boundary", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        policy = load_public_export_policy(args.policy)
        inventory = load_third_party_inventory(args.inventory)
        boundary_policy = load_public_boundary_policy(args.public_boundary)
        result = verify_public_export(
            artifact=args.artifact,
            policy=policy,
            inventory=inventory,
            boundary_policy=boundary_policy,
        )
        if result.technical_artifact_status is not VerificationStatus.PASS:
            print("public export verification: failed safely", file=sys.stderr)
            return 3
        write_public_export_verification_receipts(
            result,
            policy,
            json_output=args.json_output,
            markdown_output=args.markdown_output,
        )
        rendered = (
            render_public_export_verification_json(result, policy)
            if args.format == "json"
            else render_public_export_verification_markdown(result, policy)
        )
    except Exception:  # Safe boundary: never reproduce paths, values, or raw errors.
        print("public export verification: failed safely", file=sys.stderr)
        return 2
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
