#!/usr/bin/env python3
"""Sanitized local exposure-inventory CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.exposure_inventory import (  # noqa: E402
    ScanStatus,
    load_exposure_policy,
    render_exposure_inventory_json,
    render_exposure_inventory_markdown,
    scan_exposure_inventory,
    write_exposure_inventory_receipts,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inventory bounded local exposure surfaces without mutation.",
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--public-candidate", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        policy = load_exposure_policy(args.policy)
        receipt = scan_exposure_inventory(
            args.repo,
            args.public_candidate,
            policy,
        )
        if receipt.scan_status is not ScanStatus.COMPLETE:
            raise ValueError("incomplete exposure inventory")
        write_exposure_inventory_receipts(
            receipt,
            json_output=args.json_output,
            markdown_output=args.markdown_output,
        )
    except Exception:  # Safe boundary: never reproduce paths, values, or raw errors.
        print(
            "exposure inventory: unable to produce a safe receipt",
            file=sys.stderr,
        )
        return 1

    if args.format == "json":
        print(render_exposure_inventory_json(receipt), end="")
    else:
        print(render_exposure_inventory_markdown(receipt), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
