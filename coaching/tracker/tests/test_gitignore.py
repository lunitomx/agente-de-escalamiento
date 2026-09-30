"""The company folder holding the tracker link never reaches git (S82.3)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def test_company_folder_is_ignored_by_git() -> None:
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")

    result = subprocess.run(
        ["git", "check-ignore", "-q", ".escala/my-company/tracker.yaml"],
        cwd=ROOT,
        check=False,
    )

    assert result.returncode == 0
