#!/usr/bin/env python3
"""Credential-safe repository-truth verification CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.repository_truth import (  # noqa: E402
    load_repository_truth_policy,
    render_repository_truth_json,
    render_repository_truth_markdown,
    verify_repository,
    write_repository_truth_receipts,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify canonical Git repository truth without mutation.",
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        policy = load_repository_truth_policy(args.policy)
        receipt = verify_repository(args.repo, policy)
        write_repository_truth_receipts(
            receipt,
            json_output=args.json_output,
            markdown_output=args.markdown_output,
        )
    except Exception:  # Safe boundary: never reproduce paths, URLs, or raw errors.
        print("repository truth: unable to produce a safe receipt", file=sys.stderr)
        return 1

    if args.format == "json":
        print(render_repository_truth_json(receipt), end="")
    else:
        print(render_repository_truth_markdown(receipt), end="")
    return 0 if receipt.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
