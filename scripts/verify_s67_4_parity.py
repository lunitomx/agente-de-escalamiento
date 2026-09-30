#!/usr/bin/env python3
"""Generate or validate the deterministic S67.4 portable-adapter report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.adapter_parity import (  # noqa: E402
    REPORT_PATH,
    AdapterParityError,
    build_parity_report,
    validate_parity_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = build_parity_report()
    except AdapterParityError as exc:
        print(f"S67.4 parity report unavailable: {exc}", file=sys.stderr)
        return 1

    if args.check:
        try:
            current = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            print("S67.4 parity report drift: report unavailable", file=sys.stderr)
            return 1
        errors = validate_parity_report(current)
        if errors:
            print("S67.4 parity report drift: " + ",".join(errors), file=sys.stderr)
            return 1
        print("S67.4 parity report synchronized: 6 capabilities")
        return 0

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"S67.4 parity report generated: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
