#!/usr/bin/env python3
"""Dispatch one reproducible full-epic qualification by canonical ID."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
QUALIFIERS = {
    "E37": ROOT / "scripts/qualify_e37.py",
    "E38": ROOT / "scripts/qualify_e38.py",
    "E39": ROOT / "scripts/qualify_e39.py",
    "E40": ROOT / "scripts/qualify_e40.py",
    "E41": ROOT / "scripts/qualify_e41.py",
}


def qualifier_path(epic_id: str) -> Path:
    try:
        return QUALIFIERS[epic_id]
    except KeyError as exc:
        raise ValueError("unknown qualification epic") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the full local qualification for one accepted ESCALA epic."
    )
    parser.add_argument("--epic", choices=tuple(sorted(QUALIFIERS)), required=True)
    args = parser.parse_args()
    qualifier = qualifier_path(args.epic)
    completed = subprocess.run([sys.executable, str(qualifier)], cwd=ROOT, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
