"""Regression checks for the manifest gate used by portable installations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.verify_portable_bundle import verify


def _manifest_entry(path: Path, relative: str) -> dict[str, object]:
    payload = path.read_bytes()
    return {
        "path": relative,
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _write_manifest(root: Path, entries: list[dict[str, object]]) -> None:
    (root / "ESCALA-MANIFEST.json").write_text(
        json.dumps({"entries": entries}), encoding="utf-8"
    )


def test_portable_bundle_verifier_accepts_exact_manifest(tmp_path: Path) -> None:
    payload = tmp_path / "escala-skills" / "escala" / "SKILL.md"
    payload.parent.mkdir(parents=True)
    payload.write_text("# ESCALA\n", encoding="utf-8")
    _write_manifest(
        tmp_path, [_manifest_entry(payload, "escala-skills/escala/SKILL.md")]
    )

    assert verify(tmp_path) is True


def test_portable_bundle_verifier_rejects_tampered_or_unexpected_files(
    tmp_path: Path,
) -> None:
    payload = tmp_path / "payload.txt"
    payload.write_text("original", encoding="utf-8")
    _write_manifest(tmp_path, [_manifest_entry(payload, "payload.txt")])

    payload.write_text("changed", encoding="utf-8")
    assert verify(tmp_path) is False

    payload.write_text("original", encoding="utf-8")
    (tmp_path / "unexpected.txt").write_text("no", encoding="utf-8")
    assert verify(tmp_path) is False
