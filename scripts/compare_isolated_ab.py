"""Create a privacy-preserving JSON summary from E68 isolated receipts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.isolated_ab import (  # noqa: E402
    IsolatedABError,
    SessionReceipt,
    compare_isolated_ab,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare E68 isolated receipts.")
    parser.add_argument("--receipts", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        raw = json.loads(arguments.receipts.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise IsolatedABError("receipts_invalid")
        comparisons = compare_isolated_ab(
            tuple(SessionReceipt.model_validate(item) for item in raw)
        )
    except (OSError, ValueError, IsolatedABError) as exc:
        print(f"isolated A/B evaluation failed: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            [
                {
                    "platform": comparison.platform,
                    "available_receipt_id": comparison.available_receipt_id,
                    "unavailable_receipt_id": comparison.unavailable_receipt_id,
                    "compared_case_ids": comparison.compared_case_ids,
                    "changed_case_ids": comparison.changed_case_ids,
                }
                for comparison in comparisons
            ],
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
