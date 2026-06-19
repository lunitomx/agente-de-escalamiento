from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/skill_golden_cases"
SKILLS_ROOT = ROOT / ".agents/skills"
SPEC = importlib.util.spec_from_file_location(
    "skill_golden_cases",
    ROOT / "validators/skill_golden_cases.py",
)
assert SPEC is not None
assert SPEC.loader is not None
SKILL_GOLDEN_CASES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SKILL_GOLDEN_CASES)

load_golden_cases = SKILL_GOLDEN_CASES.load_golden_cases
validate_golden_case_file = SKILL_GOLDEN_CASES.validate_golden_case_file


def test_valid_golden_case_fixture_passes() -> None:
    cases = load_golden_cases(FIXTURES / "valid.yaml")

    assert cases[0].case_id == "strategy-evidence-gate"
    assert cases[0].skill == "scaleup-strategy"
    assert validate_golden_case_file(FIXTURES / "valid.yaml", SKILLS_ROOT) == []


def test_missing_skill_fixture_fails_with_actionable_error() -> None:
    errors = validate_golden_case_file(FIXTURES / "missing_skill.yaml", SKILLS_ROOT)

    assert any("skill not found" in error for error in errors)
    assert any("scaleup-missing-skill" in error for error in errors)


def test_missing_expected_properties_fail_validation() -> None:
    errors = validate_golden_case_file(
        FIXTURES / "missing_expected_properties.yaml",
        SKILLS_ROOT,
    )

    assert any("expected_sections" in error for error in errors)
    assert any("required_methodology_terms" in error for error in errors)
    assert any("forbidden_claim_patterns" in error for error in errors)


def test_non_list_fixture_root_fails(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.yaml"
    fixture.write_text("case_id: not-a-list\n", encoding="utf-8")

    errors = validate_golden_case_file(fixture, SKILLS_ROOT)

    assert errors == ["Golden case fixture file must contain a list"]
