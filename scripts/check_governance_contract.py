#!/usr/bin/env python3
"""Sanitized local governance-contract CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.governance_contract import (  # noqa: E402
    build_governance_contract_receipt,
    render_governance_contract_json,
    render_governance_contract_markdown,
    write_governance_contract_receipts,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate local typed governance without mutation.",
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--closure-policy", type=Path, required=True)
    parser.add_argument("--identity-policy", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        receipt = build_governance_contract_receipt(
            args.repo,
            args.closure_policy,
            args.identity_policy,
        )
        write_governance_contract_receipts(
            receipt,
            json_output=args.json_output,
            markdown_output=args.markdown_output,
        )
    except Exception:  # Safe boundary: never reproduce paths or raw errors.
        print(
            "governance contract: unable to produce a safe passing receipt",
            file=sys.stderr,
        )
        return 1

    if args.format == "json":
        print(render_governance_contract_json(receipt), end="")
    else:
        print(render_governance_contract_markdown(receipt), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
