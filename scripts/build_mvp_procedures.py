#!/usr/bin/env python3
"""Build or exactly verify the internal E65 six-procedure MVP release."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validators.procedure_compiler import build_mvp_procedure_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return 0 if build_mvp_procedure_files(check=args.check) else 1


if __name__ == "__main__":
    raise SystemExit(main())
