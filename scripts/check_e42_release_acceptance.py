#!/usr/bin/env python3
"""Validate a private E42 hardware and human-acceptance receipt."""

from __future__ import annotations

import argparse
from pathlib import Path

from pydantic import ValidationError

from validators.e42_release_acceptance import (
    E42ReleaseAcceptanceReceipt,
    validate_release_acceptance,
    validation_errors,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        receipt = E42ReleaseAcceptanceReceipt.model_validate_json(
            args.receipt.read_text(encoding="utf-8")
        )
        validate_release_acceptance(receipt)
    except (OSError, UnicodeError, ValidationError, ValueError):
        print("E42 release acceptance receipt invalid")
        return 2
    if validation_errors(receipt):
        print("E42 release acceptance blocked")
        return 1
    print("E42 release acceptance pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
