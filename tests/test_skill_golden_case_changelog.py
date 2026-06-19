from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_FIXTURES = ROOT / "tests/fixtures/skill_golden_cases/core"
CHANGELOG = ROOT / ".raise/skill-golden-cases/changelog.yaml"
SPEC = importlib.util.spec_from_file_location(
    "skill_golden_cases",
    ROOT / "validators/skill_golden_cases.py",
)
assert SPEC is not None
assert SPEC.loader is not None
SKILL_GOLDEN_CASES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SKILL_GOLDEN_CASES)

load_golden_case_directory = SKILL_GOLDEN_CASES.load_golden_case_directory
golden_case_expectation_hash = SKILL_GOLDEN_CASES.golden_case_expectation_hash
validate_golden_case_changelog = SKILL_GOLDEN_CASES.validate_golden_case_changelog


def test_current_golden_case_changelog_validates() -> None:
    cases = load_golden_case_directory(CORE_FIXTURES)

    errors = validate_golden_case_changelog(cases, CHANGELOG)

    assert errors == []


def test_changed_expectation_without_matching_changelog_fails() -> None:
    cases = load_golden_case_directory(CORE_FIXTURES)
    changed_case = cases[0].model_copy(
        update={"expected_sections": [*cases[0].expected_sections, "New Section"]}
    )
    cases[0] = changed_case

    errors = validate_golden_case_changelog(cases, CHANGELOG)

    assert any(changed_case.case_id in error for error in errors)
    assert any(
        "missing changelog entry for expectation hash" in error for error in errors
    )


def test_changelog_entry_without_reason_fails(tmp_path: Path) -> None:
    case = load_golden_case_directory(CORE_FIXTURES)[0]
    changelog = tmp_path / "changelog.yaml"
    changelog.write_text(
        "\n".join(
            [
                "- change_id: missing-reason",
                f"  case_id: {case.case_id}",
                f"  skill: {case.skill}",
                f"  expectation_hash: {golden_case_expectation_hash(case)}",
                "  reason: ''",
                "  reviewer: S35.4",
                "  changed_fields:",
                "    - expected_sections",
                "  expected_behavior_change: Test change.",
            ]
        ),
        encoding="utf-8",
    )

    errors = validate_golden_case_changelog([case], changelog)

    assert any("reason" in error for error in errors)
