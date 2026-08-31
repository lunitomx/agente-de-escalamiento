from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/skill_golden_cases"
CORE_FIXTURES = FIXTURES / "core"
SKILLS_ROOT = ROOT / ".claude/legacy-skills"
SPEC = importlib.util.spec_from_file_location(
    "skill_golden_cases",
    ROOT / "validators/skill_golden_cases.py",
)
assert SPEC is not None
assert SPEC.loader is not None
SKILL_GOLDEN_CASES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SKILL_GOLDEN_CASES)

load_golden_cases = SKILL_GOLDEN_CASES.load_golden_cases
load_golden_case_directory = SKILL_GOLDEN_CASES.load_golden_case_directory
validate_golden_case_file = SKILL_GOLDEN_CASES.validate_golden_case_file
validate_golden_case_directory = SKILL_GOLDEN_CASES.validate_golden_case_directory

CORE_SKILLS = {
    "scaleup-strategy",
    "scaleup-cash",
    "scaleup-people",
    "scaleup-execution",
}


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


def test_core_skill_golden_case_directory_validates() -> None:
    errors = validate_golden_case_directory(CORE_FIXTURES, SKILLS_ROOT)

    assert errors == []


def test_core_skill_golden_cases_cover_selected_skills() -> None:
    cases = load_golden_case_directory(CORE_FIXTURES)

    covered_skills = {case.skill for case in cases}

    assert CORE_SKILLS <= covered_skills


def test_core_skill_cases_have_methodology_properties() -> None:
    cases = load_golden_case_directory(CORE_FIXTURES)

    for case in cases:
        assert case.expected_sections
        assert case.required_methodology_terms
        assert case.forbidden_claim_patterns


def test_empty_golden_case_directory_fails(tmp_path: Path) -> None:
    assert validate_golden_case_directory(tmp_path, SKILLS_ROOT) == [
        f"No golden case YAML files found in {tmp_path}"
    ]
