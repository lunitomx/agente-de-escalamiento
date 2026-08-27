#!/usr/bin/env python3
"""Emit one bounded receipt for private source integrity."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.source_integrity import (  # noqa: E402
    build_source_integrity_receipt,
    render_source_integrity_json,
    render_source_integrity_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate private source integrity without source-text output."
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        receipt = build_source_integrity_receipt(
            args.repo, args.registry, args.manifest, args.policy
        )
    except Exception:
        print(
            "source integrity: unable to produce a safe passing receipt",
            file=sys.stderr,
        )
        return 1
    rendered = (
        render_source_integrity_json(receipt)
        if args.format == "json"
        else render_source_integrity_markdown(receipt)
    )
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
