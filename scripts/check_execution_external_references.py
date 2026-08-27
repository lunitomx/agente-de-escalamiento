"""Validate private external-reference locators without embedding source vocabulary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from validators.domain_coverage import DomainInventory
from validators.external_reference_locators import (
    ExternalReferenceLocatorReceipt,
    validate_external_reference_locators,
)


def load_private_terms(path: Path) -> dict[str, str]:
    """Load opaque search patterns from an ignored, source-bounded artifact."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not raw:
        raise ValueError("private search terms must be a non-empty mapping")
    terms: dict[str, str] = {}
    for name, pattern in raw.items():
        if (
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(pattern, str)
            or not pattern.strip()
        ):
            raise ValueError("private search term entries must be non-empty strings")
        terms[name] = pattern
    return terms


def scan_reference_locators(
    inventory: DomainInventory, source: Path, terms: dict[str, str]
) -> dict[str, set[str]]:
    """Return exact unit-to-reference matches without rendering source fragments."""
    lines = source.read_text(encoding="utf-8").splitlines()
    observed: dict[str, set[str]] = {}
    for unit in inventory.units:
        chunk = "\n".join(lines[unit.line_start - 1 : unit.line_end])
        names = {
            name for name, pattern in terms.items() if re.search(pattern, chunk, re.I)
        }
        if names:
            observed[unit.unit_id] = names
    return observed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("--terms", type=Path, required=True)
    args = parser.parse_args()
    receipt = ExternalReferenceLocatorReceipt.model_validate_json(
        args.receipt.read_text(encoding="utf-8")
    )
    inventory = DomainInventory.model_validate_json(
        args.inventory.read_text(encoding="utf-8")
    )
    observed = scan_reference_locators(
        inventory, args.source, load_private_terms(args.terms)
    )
    validate_external_reference_locators(receipt, inventory, observed)
    print(f"execution external locators pass: {len(observed)} units")


if __name__ == "__main__":
    main()
