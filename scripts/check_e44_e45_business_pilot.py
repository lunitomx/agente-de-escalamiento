"""Validate a private E44/E45 business-pilot receipt without printing its data."""

from __future__ import annotations

import argparse
from pathlib import Path

from validators.e44_e45_business_pilot import (
    E44E45BusinessPilotReceipt,
    validate_business_pilot,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    receipt = E44E45BusinessPilotReceipt.model_validate_json(
        args.receipt.read_text(encoding="utf-8")
    )
    validate_business_pilot(receipt)
    print("E44/E45 business pilot receipt pass")


if __name__ == "__main__":
    main()
