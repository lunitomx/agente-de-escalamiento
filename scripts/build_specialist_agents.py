#!/usr/bin/env python3
"""Generate or validate S67.5's private specialist agent definitions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.specialist_agents import (  # noqa: E402
    SpecialistAgentError,
    validate_specialist_artifacts,
    write_specialist_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        errors = validate_specialist_artifacts()
        if errors:
            print("S67.5 specialist agent drift: " + ",".join(errors), file=sys.stderr)
            return 1
        print("S67.5 specialist agents synchronized: 4 private agents")
        return 0
    try:
        artifacts = write_specialist_artifacts()
    except SpecialistAgentError as exc:
        print(f"S67.5 specialist agents unavailable: {exc}", file=sys.stderr)
        return 1
    print(f"S67.5 specialist agents generated: {len(artifacts)} artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
