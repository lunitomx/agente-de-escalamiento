"""Validate E62 external-reference locators without printing private source text."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from validators.domain_coverage import DomainInventory
from validators.external_reference_locators import (
    ExternalReferenceLocatorReceipt,
    validate_external_reference_locators,
)


TERMS = {
    "Goldratt": r"\bGoldratt\b",
    "Lean": r"\bLean\b",
    "Lencioni": r"\bLencioni\b",
    "Net Promoter": r"\bNet Promoter\b|\bNPS\b",
    "Stack": r"\bStack\b",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    receipt = ExternalReferenceLocatorReceipt.model_validate_json(
        args.receipt.read_text("utf-8")
    )
    inventory = DomainInventory.model_validate_json(args.inventory.read_text("utf-8"))
    lines = args.source.read_text(encoding="utf-8").splitlines()
    observed: dict[str, set[str]] = {}
    for unit in inventory.units:
        chunk = "\n".join(lines[unit.line_start - 1 : unit.line_end])
        names = {
            name for name, pattern in TERMS.items() if re.search(pattern, chunk, re.I)
        }
        if names:
            observed[unit.unit_id] = names
    validate_external_reference_locators(receipt, inventory, observed)
    print(f"execution external locators pass: {len(observed)} units")


if __name__ == "__main__":
    main()
