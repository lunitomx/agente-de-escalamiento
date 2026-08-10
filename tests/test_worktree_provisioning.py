from __future__ import annotations

import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_editable_package_metadata_is_ignored() -> None:
    completed = subprocess.run(
        ["git", "check-ignore", "-q", "escala_coaching.egg-info/PKG-INFO"],
        capture_output=True,
        check=False,
        cwd=REPOSITORY_ROOT,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
