#!/usr/bin/env python3
"""Build one private structural manifest without emitting source text."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.source_authority import load_source_registry  # noqa: E402
from validators.source_manifest import (  # noqa: E402
    build_source_manifest,
    render_source_manifest_jsonl,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a private structural source manifest."
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        registry = load_source_registry(args.registry)
        manifest = build_source_manifest(args.repo, registry, args.source_id)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_source_manifest_jsonl(manifest), encoding="utf-8")
    except Exception:
        print("source manifest: unable to build safely", file=sys.stderr)
        return 1
    print("source manifest: built private structural metadata only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
