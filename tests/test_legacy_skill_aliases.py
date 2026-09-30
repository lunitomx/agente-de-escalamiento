"""E56 prevents legacy wrappers from drifting back into duplicate logic."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "refresh_legacy_skill_aliases.py"


def test_legacy_aliases_are_generated_from_the_catalog() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "legacy aliases synchronized: 42" in result.stdout


def test_legacy_aliases_only_redirect_to_a_canonical_contract() -> None:
    for root in (ROOT / ".claude/legacy-skills", ROOT / ".agents/legacy-skills"):
        for path in root.glob("scaleup-*/SKILL.md"):
            content = path.read_text(encoding="utf-8")
            assert "Alias temporal de compatibilidad" in content
            assert "no contiene lógica ni metodología propia" in content
            assert "../../../escala-skills/escala-" in content


def test_legacy_aliases_are_not_in_discoverable_skill_roots() -> None:
    for root in (ROOT / ".claude/skills", ROOT / ".agents/skills"):
        if root.exists():
            assert not list(root.glob("scaleup-*/SKILL.md"))
