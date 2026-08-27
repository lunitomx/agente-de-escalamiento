"""Validate a private visual-layout receipt without reading the source asset."""

from __future__ import annotations

import argparse
from pathlib import Path

from validators.form_layout_review import (
    FormLayoutReviewReceipt,
    validate_form_layout_review,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    receipt = FormLayoutReviewReceipt.model_validate_json(
        args.receipt.read_text(encoding="utf-8")
    )
    validate_form_layout_review(receipt)
    print(f"form layout review pass: {receipt.domain}; {len(receipt.forms)} forms")


if __name__ == "__main__":
    main()
