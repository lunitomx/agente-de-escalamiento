"""E2E qualification tests for E42.

These tests exercise the end-to-end qualification scripts for S42.1-S42.4 and
verify that they produce the expected evidence artifacts. They do not replace
clean-hardware or human acceptance runs; they guard the local qualification
path that the product owner has chosen to accept for closing E42.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    ("scripts/qualify_e42_s42.1.py", "s42.1-local-journey.json"),
    ("scripts/qualify_e42_s42.2.py", "s42.2-skill-inventory.json"),
    ("scripts/qualify_e42_s42.3.py", "s42.3-security-recovery.json"),
    ("scripts/qualify_e42_s42.4.py", "s42.4-catalog-receipt.json"),
]
EVIDENCE_DIR = (
    ROOT / "work/epics/e42-product-qualification-and-functional-catalog/evidence"
)


@pytest.mark.e2e
@pytest.mark.parametrize("script_path,evidence_file", SCRIPTS)
def test_qualification_script_passes(script_path: str, evidence_file: str) -> None:
    """Each E42 qualification script exits cleanly and writes evidence."""
    script = ROOT / script_path
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"{script_path} failed with exit code {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    evidence_path = EVIDENCE_DIR / evidence_file
    assert evidence_path.exists(), f"Evidence not found: {evidence_path}"

    data = json.loads(evidence_path.read_text(encoding="utf-8"))
    overall = data.get("overall_status") or data.get("result") or data.get("status")
    assert overall in {"pass", "partial", "ok"}, (
        f"Unexpected overall status in {evidence_file}: {overall}"
    )


@pytest.mark.e2e
def test_e42_catalog_pdf_generated() -> None:
    """The S42.4 catalog PDF artifact is produced."""
    pdf_path = EVIDENCE_DIR / "catalog.pdf"
    assert pdf_path.exists(), f"Catalog PDF not found: {pdf_path}"
    assert pdf_path.stat().st_size > 0


def test_e42_catalog_exposes_only_public_front_door() -> None:
    """The entrepreneur catalog must not surface internal capabilities as commands."""

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/qualify_e42_s42.4.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    catalog = (EVIDENCE_DIR / "catalog.md").read_text(encoding="utf-8")
    receipt = json.loads(
        (EVIDENCE_DIR / "s42.4-catalog-receipt.json").read_text(encoding="utf-8")
    )

    assert "`escala`" in catalog
    assert "`escala-board`" not in catalog
    assert "62 capacidades internas" in catalog
    assert receipt["public_skill_count"] == 1
    assert receipt["internal_capability_count"] == 62
