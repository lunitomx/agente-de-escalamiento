#!/usr/bin/env python3
"""Sanitized local public-boundary CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.public_boundary import (  # noqa: E402
    BoundaryStatus,
    load_public_boundary_policy,
    render_public_boundary_json,
    render_public_boundary_markdown,
    scan_public_boundary,
    write_public_boundary_receipts,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check local public-content boundaries without mutation.",
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--public-candidate", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        policy = load_public_boundary_policy(args.policy)
        receipt = scan_public_boundary(
            args.repo,
            args.public_candidate,
            policy,
            baseline_path=args.baseline,
        )
        if receipt.status is not BoundaryStatus.PASS:
            raise ValueError("public boundary did not pass")
        write_public_boundary_receipts(
            receipt,
            json_output=args.json_output,
            markdown_output=args.markdown_output,
        )
    except Exception:  # Safe boundary: never reproduce paths, values, or raw errors.
        print(
            "public boundary: unable to produce a safe passing receipt",
            file=sys.stderr,
        )
        return 1

    if args.format == "json":
        print(render_public_boundary_json(receipt), end="")
    else:
        print(render_public_boundary_markdown(receipt), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
