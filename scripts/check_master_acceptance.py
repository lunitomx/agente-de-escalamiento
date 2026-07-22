#!/usr/bin/env python3
"""Safe local CLI for the ESCALA Local V2 acceptance ledger."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.master_acceptance import (  # noqa: E402
    AcceptanceMode,
    MissionReadiness,
    build_master_acceptance_receipt,
    load_master_acceptance_ledger,
    render_master_acceptance_receipt_json,
    render_master_acceptance_receipt_markdown,
    write_master_acceptance_receipts,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the local master acceptance ledger without mutation.",
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=tuple(item.value for item in AcceptanceMode),
        required=True,
    )
    parser.add_argument("--epic")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        ledger = load_master_acceptance_ledger(args.ledger)
        mode = AcceptanceMode(args.mode)
        receipt = build_master_acceptance_receipt(
            args.repo,
            ledger,
            mode=mode,
            epic_filter=args.epic,
        )
        write_master_acceptance_receipts(
            receipt,
            max_receipt_bytes=ledger.limits.max_receipt_bytes,
            json_output=args.json_output,
            markdown_output=args.markdown_output,
        )
    except Exception:  # Safe boundary: never reproduce paths or raw errors.
        print(
            "master acceptance: unable to produce a safe contract receipt",
            file=sys.stderr,
        )
        return 1

    if args.format == "json":
        print(render_master_acceptance_receipt_json(receipt), end="")
    else:
        print(render_master_acceptance_receipt_markdown(receipt), end="")
    if mode is AcceptanceMode.READINESS and (
        receipt.mission_readiness is MissionReadiness.UNPROVED
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
