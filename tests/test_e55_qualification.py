"""Regression guard for the deterministic E55 qualification script."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import qualify_e55


def test_e55_qualification_passes_and_writes_a_local_receipt(
    tmp_path: Path, monkeypatch
) -> None:
    evidence_dir = tmp_path / "evidence"
    monkeypatch.setattr(qualify_e55, "EVIDENCE_DIR", evidence_dir)
    monkeypatch.setattr(qualify_e55, "EVIDENCE_PATH", evidence_dir / "e55.json")
    monkeypatch.setattr(qualify_e55, "MARKDOWN_PATH", evidence_dir / "e55.md")

    assert qualify_e55.main() == 0
    payload = json.loads((evidence_dir / "e55.json").read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert len(payload["checks"]) == 5
