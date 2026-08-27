#!/usr/bin/env python3
"""Emit a bounded receipt for private ESCALA source custody."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.source_authority import (  # noqa: E402
    build_source_authority_receipt,
    render_source_authority_json,
    render_source_authority_markdown,
    write_source_authority_receipts,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate private source custody without emitting source content."
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        receipt = build_source_authority_receipt(args.repo, args.registry)
        write_source_authority_receipts(
            receipt,
            json_output=args.json_output,
            markdown_output=args.markdown_output,
        )
    except Exception:
        print(
            "source authority: unable to produce a safe passing receipt",
            file=sys.stderr,
        )
        return 1
    rendered = (
        render_source_authority_json(receipt)
        if args.format == "json"
        else render_source_authority_markdown(receipt)
    )
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
