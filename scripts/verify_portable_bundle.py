#!/usr/bin/env python3
"""Verify a materialized ESCALA portable artifact using only the standard library."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ESCALA-MANIFEST.json"


def _safe_relative_path(value: object) -> Path | None:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        return None
    return Path(*path.parts)


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(root: Path = ROOT) -> bool:
    """Return true only when manifest entries exactly match regular artifact files."""

    manifest_path = root / MANIFEST.name
    try:
        raw: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = raw["entries"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
        return False
    if not isinstance(entries, list) or not entries:
        return False

    expected: set[Path] = {Path(MANIFEST.name)}
    for entry in entries:
        if not isinstance(entry, dict):
            return False
        relative = _safe_relative_path(entry.get("path"))
        size = entry.get("size_bytes")
        digest = entry.get("sha256")
        if (
            relative is None
            or not isinstance(size, int)
            or size < 0
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            return False
        target = root / relative
        if target.is_symlink() or not target.is_file():
            return False
        if target.stat().st_size != size or _digest(target) != digest:
            return False
        expected.add(relative)

    observed: set[Path] = set()
    try:
        for path in root.rglob("*"):
            if path.is_symlink() or not path.is_file():
                continue
            observed.add(path.relative_to(root))
    except OSError:
        return False
    return observed == expected


def main() -> int:
    if verify():
        print("portable bundle verification: pass")
        return 0
    print("portable bundle verification: failed", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
