from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOUCHED_SKILLS = (
    "scaleup-strategy",
    "scaleup-strategy-opsp",
    "scaleup-strategy-7strata",
)


def _skill_text(root: str, skill: str) -> str:
    return (ROOT / root / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")


def test_strategy_entrypoint_requires_voice_of_customer_mapping() -> None:
    text = _skill_text(".agents", "scaleup-strategy")

    assert "Voice of Customer Evidence Gate" in text
    assert "map_evidence_to_strategy" in text
    assert "CustomerEvidenceRecord" in text
    assert "one missing-evidence question at a time" in text
    assert "do not invent" in text


def test_opsp_requires_evidence_ids_for_brand_promise_and_sandbox() -> None:
    text = _skill_text(".agents", "scaleup-strategy-opsp")

    assert "Voice of Customer Evidence Gate" in text
    assert "Brand Promise" in text
    assert "Sandbox" in text
    assert "evidence ids" in text
    assert "map_evidence_to_strategy" in text


def test_opsp_resources_define_one_execution_model_without_missing_templates() -> None:
    tool = (ROOT / ".scaleup/knowledge/strategy/tools/opsp.yaml").read_text(
        encoding="utf-8"
    )
    worksheet = (ROOT / ".scaleup/knowledge/strategy/worksheets/opsp.yaml").read_text(
        encoding="utf-8"
    )

    for text in (tool, worksheet):
        assert "Columns 1-3" in text
        assert "Columns 4-7" in text
        assert "Actions / Goals / Targets" in text
        assert "Your Accountability" in text
        assert "Key Capabilities" in text
        assert "last four" not in text

    skill_paths = (
        ROOT / "escala-skills/escala-strategy-opsp/SKILL.md",
        ROOT / ".agents/skills/scaleup-strategy-opsp/SKILL.md",
        ROOT / ".claude/skills/scaleup-strategy-opsp/SKILL.md",
    )
    for skill_path in skill_paths:
        text = skill_path.read_text(encoding="utf-8")
        assert "templates/opsp.md" not in text
        assert "one-page-strategic-plan.md" not in text
        assert "work/strategy/opsp.md" not in text
        assert "Actions / Goals / Targets" in text
        assert "Your Accountability" in text
        assert "Key Capabilities" in text

    # S47.4 shipped real persistence for the live, coach-facing catalog
    # (escala-skills/) — the deferral marker is gone there, replaced by an
    # assertion that persistence is actually wired. The .agents/.claude
    # scaleup- mirrors are a separate, not-yet-canonical catalog (parity
    # between the two is deferred catalog cleanup, not part of S47.4) and
    # still honestly defer persistence.
    escala_text = (ROOT / "escala-skills/escala-strategy-opsp/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "coaching.strategy_opsp" in escala_text
    assert ".escala/my-company/opsp.yaml" in escala_text

    for skill_path in skill_paths[1:]:
        assert "S47.4" in skill_path.read_text(encoding="utf-8")


def test_7strata_requires_evidence_ids_for_differentiation_claims() -> None:
    text = _skill_text(".agents", "scaleup-strategy-7strata")

    assert "Voice of Customer Evidence Gate" in text
    assert "Words you own" in text
    assert "One-Phrase Strategy" in text
    assert "Brand Promise" in text
    assert "evidence ids" in text


def test_agent_and_claude_strategy_skill_mirrors_stay_aligned() -> None:
    for skill in TOUCHED_SKILLS:
        assert _skill_text(".agents", skill) == _skill_text(".claude", skill)
