#!/usr/bin/env python3
"""Validate a private source manifest and emit a bounded receipt."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.source_manifest import (  # noqa: E402
    build_source_manifest_receipt,
    render_source_manifest_receipt_json,
    render_source_manifest_receipt_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate private source manifest without source-text output."
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        receipt = build_source_manifest_receipt(args.repo, args.registry, args.manifest)
    except Exception:
        print(
            "source manifest: unable to produce a safe passing receipt", file=sys.stderr
        )
        return 1
    rendered = (
        render_source_manifest_receipt_json(receipt)
        if args.format == "json"
        else render_source_manifest_receipt_markdown(receipt)
    )
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
