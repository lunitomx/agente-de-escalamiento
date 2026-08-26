from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOUCHED_SKILLS = (
    "escala-strategy",
    "escala-strategy-opsp",
    "escala-strategy-7strata",
)


def _skill_text(skill: str) -> str:
    return (ROOT / "escala-skills" / skill / "SKILL.md").read_text(encoding="utf-8")


def test_strategy_entrypoint_requires_customer_evidence() -> None:
    text = _skill_text("escala-strategy")

    assert "Gate de evidencia de clientes" in text
    assert "identificadores" in text
    assert "evidencia" in text
    assert "una sola pregunta" in text
    assert "No inventar" in text


def test_opsp_requires_evidence_for_brand_promise_and_sandbox() -> None:
    text = _skill_text("escala-strategy-opsp")

    assert "Gate de evidencia de clientes" in text
    assert "Brand Promise" in text
    assert "Sandbox" in text
    assert "identificadores" in text
    assert "evidencia" in text


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

    text = _skill_text("escala-strategy-opsp")
    assert "templates/opsp.md" not in text
    assert "one-page-strategic-plan.md" not in text
    assert "work/strategy/opsp.md" not in text
    assert "Actions / Goals / Targets" in text
    assert "Your Accountability" in text
    assert "Key Capabilities" in text
    assert "coaching.strategy_opsp" in text
    assert ".escala/my-company/opsp.yaml" in text


def test_7strata_requires_evidence_for_differentiation_claims() -> None:
    text = _skill_text("escala-strategy-7strata")

    assert "Gate de evidencia de clientes" in text
    assert "Words you own" in text
    assert "One-Phrase Strategy" in text
    assert "Brand Promise" in text
    assert "identificadores" in text
    assert "evidencia" in text


def test_strategy_capabilities_are_internal_to_the_public_orchestrator() -> None:
    public_skill = (ROOT / "escala-skills/escala/SKILL.md").read_text(encoding="utf-8")

    assert "Capacidades internas" in public_skill
    assert all(_skill_text(skill) for skill in TOUCHED_SKILLS)
