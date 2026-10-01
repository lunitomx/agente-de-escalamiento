"""S86.1: the owner only talks to ESCALA — no slash commands, no stale shortcuts."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "escala-skills"
FRONT_DOOR = "escala"


def _internal_procedures() -> list[Path]:
    return sorted(
        path
        for path in SKILLS.glob("*/SKILL.md")
        if path.parent.name != FRONT_DOOR
    )


def test_internal_procedures_never_show_slash_commands() -> None:
    offenders = [
        f"{path.relative_to(ROOT)}:{number}"
        for path in _internal_procedures()
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if "/escala-" in line
    ]

    assert offenders == []


def test_internal_references_still_name_existing_procedures() -> None:
    """A rewritten internal reference must keep a real procedure id."""

    known = {path.parent.name for path in SKILLS.glob("escala*/SKILL.md")}
    pattern = re.compile(r"procedimiento interno `(escala[a-z0-9-]*)`")
    referenced = {
        match
        for path in _internal_procedures()
        for match in pattern.findall(path.read_text(encoding="utf-8"))
    }

    assert referenced, "expected internal references to procedures"
    assert referenced - known == set()
