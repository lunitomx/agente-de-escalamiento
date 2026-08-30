#!/usr/bin/env python3
"""Render the S64.3 safe coverage matrix from the canonical S64.1 release.

Exact rebuild: ``python scripts/build_coverage_matrix.py --release
ontology/v2/releases/s64.1.json --matrix ontology/v2/releases/s64.3.coverage.json
--check``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validators.ontology_v2 import (
    build_coverage_matrix,
    load_canonical_release,
    render_coverage_matrix,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    release = load_canonical_release(args.release)
    rendered = render_coverage_matrix(build_coverage_matrix(release))
    if args.check:
        return 0 if args.matrix.read_text(encoding="utf-8") == rendered else 1
    args.matrix.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
