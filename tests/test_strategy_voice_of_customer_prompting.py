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
