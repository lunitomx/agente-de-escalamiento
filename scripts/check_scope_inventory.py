#!/usr/bin/env python3
"""Validate canonical, legacy, and story scope classification."""

from __future__ import annotations

import argparse
from pathlib import Path

from validators.governance_contract import load_closure_disposition_policy
from validators.scope_inventory import load_scope_inventory, validate_scope_inventory


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--closure-policy", type=Path, required=True)
    args = parser.parse_args()
    validate_scope_inventory(
        args.repo,
        load_scope_inventory(args.inventory),
        load_closure_disposition_policy(args.closure_policy),
    )
    print("scope inventory pass")


if __name__ == "__main__":
    main()
