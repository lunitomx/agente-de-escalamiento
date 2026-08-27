"""Regression test for resolvable knowledge references in escala-skills."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "escala-skills"

# Mapping of repaired references to their real source-of-truth files.
REPAIRED_REFS: dict[str, Path] = {
    "conocimiento/strategy/tools/opsp.yaml": ROOT
    / "conocimiento/strategy/tools/opsp.yaml",
    "conocimiento/strategy/tools/7-strata.yaml": ROOT
    / "conocimiento/strategy/tools/7-strata.yaml",
    "conocimiento/strategy/tools/swt.yaml": ROOT
    / "conocimiento/strategy/tools/swt.yaml",
    "conocimiento/people/concepts/core-values.yaml": ROOT
    / "conocimiento/people/concepts/core-values.yaml",
    "conocimiento/people/tools/face.yaml": ROOT / "conocimiento/people/tools/face.yaml",
    "conocimiento/people/tools/topgrading.yaml": ROOT
    / "conocimiento/people/tools/topgrading.yaml",
    "conocimiento/execution/tools/execution-habits.yaml": ROOT
    / "conocimiento/execution/tools/execution-habits.yaml",
    "conocimiento/execution/concepts/meeting-rhythm.yaml": ROOT
    / "conocimiento/execution/concepts/meeting-rhythm.yaml",
}


def _skill_files() -> list[Path]:
    return sorted(SKILLS_DIR.glob("*/SKILL.md"))


def _extract_conocimiento_refs(text: str) -> set[str]:
    """Find all conocimiento/ file references in a SKILL.md body."""
    return set(re.findall(r"conocimiento/[a-zA-Z0-9_\-/]+\.(?:yaml|yml|md)", text))


@pytest.mark.parametrize("ref", list(REPAIRED_REFS.keys()))
def test_repaired_knowledge_reference_exists(ref: str) -> None:
    path = REPAIRED_REFS[ref]
    assert path.exists(), f"Repaired reference target missing: {ref}"


def test_all_conocimiento_references_exist() -> None:
    """Every conocimiento/ path referenced by an escala-skill must exist."""
    missing: list[tuple[str, str]] = []
    for skill_file in _skill_files():
        text = skill_file.read_text(encoding="utf-8")
        for ref in _extract_conocimiento_refs(text):
            if not (ROOT / ref).exists():
                missing.append((skill_file.name, ref))

    assert not missing, f"Missing conocimiento references: {missing}"


def test_no_descriptive_escala_knowledge_md_references_remain() -> None:
    """The old broken pattern (.escala/knowledge/**/*.md descriptive names) must not return."""
    descriptive_md_pattern = re.compile(
        r"\.escala/knowledge/[a-z]+/(tools|frameworks)/[a-z-]+\.md"
    )
    offenders: list[str] = []
    for skill_file in _skill_files():
        text = skill_file.read_text(encoding="utf-8")
        if descriptive_md_pattern.search(text):
            offenders.append(str(skill_file.relative_to(ROOT)))

    assert not offenders, f"Old broken .md references remain in: {offenders}"


@pytest.mark.parametrize(
    "path",
    [
        ROOT / ".escala/agent/sub-agents/strategy.md",
        ROOT / ".escala/agent/sub-agents/people.md",
        ROOT / ".escala/agent/sub-agents/execution.md",
        ROOT / ".escala/agent/sub-agents/cash.md",
        ROOT / ".escala/knowledge/strategy/overview.md",
        ROOT / ".escala/knowledge/people/overview.md",
        ROOT / ".escala/knowledge/execution/overview.md",
    ],
)
def test_decision_subagents_and_overviews_exist(path: Path) -> None:
    assert path.exists(), f"Missing decision context file: {path.relative_to(ROOT)}"
    assert path.stat().st_size > 0, (
        f"Decision context file is empty: {path.relative_to(ROOT)}"
    )
