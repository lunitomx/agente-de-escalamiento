"""Contracts for the anonymous, local-only bugreport skill."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL_PATHS = (
    ROOT / "escala-skills/escala-bugreport/SKILL.md",
    ROOT / "escala-agent/skills/escala-bugreport/SKILL.md",
)
REQUIRED_SECTIONS = (
    "## Purpose",
    "## Mastery Levels (ShuHaRi)",
    "## Context",
    "## Steps",
    "## Output",
    "## Quality Checklist",
    "## References",
)
FORBIDDEN_AUTOMATION = (
    "No llamar APIs",
    "No leer ni recolectar",
    "no se enviará por internet",
    "local_outbox_manual_share",
)


def test_canonical_and_installed_skill_are_mirrors() -> None:
    contents = [path.read_text(encoding="utf-8") for path in SKILL_PATHS]

    assert all(path.is_file() for path in SKILL_PATHS)
    assert contents[0] == contents[1]


def test_skill_has_adr_sections_and_stays_small() -> None:
    content = SKILL_PATHS[0].read_text(encoding="utf-8")

    assert len(content.splitlines()) <= 150
    assert all(section in content for section in REQUIRED_SECTIONS)
    assert "name: escala-bugreport" in content
    assert "schema_version: 1" in content


def test_skill_is_fail_closed_on_identity_and_network_collection() -> None:
    content = SKILL_PATHS[0].read_text(encoding="utf-8")

    assert all(marker in content for marker in FORBIDDEN_AUTOMATION)
    assert "identity: omitted" in content
    assert "company_data: omitted" in content
    assert "consent: confirmed" in content
    assert "~/.escala/feedback/outbox/" in content
