#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from validators.e6_migration import load_and_validate_e6_migration_map  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--repo", type=Path, required=True)
p.add_argument("--map", type=Path, required=True)
a = p.parse_args()
try:
    m = load_and_validate_e6_migration_map(a.repo, a.map)
except Exception:
    print("e6 migration: unable to produce a safe passing receipt", file=sys.stderr)
    raise SystemExit(1)
print("# ESCALA E6 Migration Map Receipt\n")
print("- Status: `pass`")
print(f"- Legacy assets: {len(m.entries)}")
print(
    f"- Nodes awaiting domain evidence: {sum(e.disposition == 'await-domain-evidence' for e in m.entries)}"
)
print(
    f"- Support contracts: {sum(e.disposition == 'support-contract-not-node' for e in m.entries)}"
)
