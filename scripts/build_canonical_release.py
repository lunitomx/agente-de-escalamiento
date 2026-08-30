#!/usr/bin/env python3
"""Render the S64.1 release from its versioned, safe authorization projection.

Exact rebuild: ``python scripts/build_canonical_release.py --projection
ontology/v2/releases/s64.1.projection.json --release ontology/v2/releases/s64.1.json
--check``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validators.ontology_v2 import (
    AuthorizedCandidateProjection,
    build_canonical_release,
    render_canonical_release,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        projection = AuthorizedCandidateProjection.model_validate_json(
            args.projection.read_text(encoding="utf-8")
        )
    except Exception as exc:
        raise ValueError("authorized projection contract invalid") from exc
    rendered = render_canonical_release(build_canonical_release(projection))
    if args.check:
        return 0 if args.release.read_text(encoding="utf-8") == rendered else 1
    args.release.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
