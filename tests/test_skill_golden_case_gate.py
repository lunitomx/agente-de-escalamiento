from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_skill_golden_cases.py"
RELEASE_OUTPUTS = ROOT / "tests/fixtures/skill_golden_cases/release_outputs"


def test_skill_golden_case_release_check_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--format",
            "json",
            "--outputs-dir",
            str(RELEASE_OUTPUTS),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["status"] == "pass"
    assert {check["name"] for check in report["checks"]} == {
        "fixture_validation",
        "changelog_validation",
        "output_drift",
    }


def test_skill_golden_case_release_check_fails_with_missing_outputs(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--format",
            "json",
            "--outputs-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["status"] == "fail"
    assert any("output file not found" in error for error in report["errors"])
    assert any("core-strategy-voc-evidence-gate" in error for error in report["errors"])
