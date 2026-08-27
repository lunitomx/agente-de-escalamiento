#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from validators.e6_migration import build_e6_migration_map, render_e6_migration_map  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--repo", type=Path, required=True)
p.add_argument("--output", type=Path, required=True)
a = p.parse_args()
try:
    if a.output.exists():
        raise ValueError("output exists")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(
        render_e6_migration_map(build_e6_migration_map(a.repo)), encoding="utf-8"
    )
except Exception:
    print("e6 migration: unable to produce a safe map", file=sys.stderr)
    raise SystemExit(1)
