from __future__ import annotations

import json
from pathlib import Path

from scripts import qualify_e40


def test_e40_qualification_accepts_a_complete_canonical_opsp(
    monkeypatch,
    tmp_path: Path,
) -> None:
    evidence_dir = tmp_path / "evidence"
    monkeypatch.setattr(qualify_e40, "EVIDENCE_DIR", evidence_dir)
    monkeypatch.setattr(
        qualify_e40,
        "EVIDENCE_PATH",
        evidence_dir / "master-acceptance-e40.json",
    )
    monkeypatch.setattr(
        qualify_e40,
        "MARKDOWN_PATH",
        evidence_dir / "master-acceptance-e40.md",
    )
    monkeypatch.setattr(
        qualify_e40,
        "_write_requirement_receipts",
        lambda checks: None,
    )

    assert qualify_e40.main() == 0

    payload = json.loads((evidence_dir / "master-acceptance-e40.json").read_text())
    assert payload["status"] == "pass"
    assert payload["requirements_proved"] == [
        f"REQ-E40-{index:03d}" for index in range(1, 9)
    ]
