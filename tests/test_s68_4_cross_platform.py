from __future__ import annotations

from pathlib import Path

from validators.activation_evals import ActivationObservation, load_activation_suite
from validators.cross_platform_evals import evaluate_cross_platform


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "e68"


def _observations(name: str) -> tuple[ActivationObservation, ...]:
    import json

    raw = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return tuple(ActivationObservation.model_validate(item) for item in raw)


def test_aliases_normalize_to_the_same_procedure_cross_platform() -> None:
    result = evaluate_cross_platform(
        load_activation_suite(FIXTURES / "activation_cases.json"),
        _observations("codex-observations.json"),
        _observations("claude-observations.json"),
    )

    assert result.codex_precision == result.claude_precision == 1.0
    assert result.codex_recall == result.claude_recall == 1.0
    assert result.semantic_differences == ()


def test_reports_actual_semantic_difference() -> None:
    claude = list(_observations("claude-observations.json"))
    claude[0] = ActivationObservation(
        case_id="ACT-001", action="route", resolved_intent="build-vision-summary"
    )

    result = evaluate_cross_platform(
        load_activation_suite(FIXTURES / "activation_cases.json"),
        _observations("codex-observations.json"),
        tuple(claude),
    )

    assert result.semantic_differences == ("ACT-001",)
