from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/skill_golden_cases"
CORE_FIXTURES = FIXTURES / "core"
OUTPUTS = FIXTURES / "outputs"
SPEC = importlib.util.spec_from_file_location(
    "skill_golden_cases",
    ROOT / "validators/skill_golden_cases.py",
)
assert SPEC is not None
assert SPEC.loader is not None
SKILL_GOLDEN_CASES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SKILL_GOLDEN_CASES)

load_golden_case_directory = SKILL_GOLDEN_CASES.load_golden_case_directory
validate_golden_case_output_file = SKILL_GOLDEN_CASES.validate_golden_case_output_file
validate_golden_case_output_directory = (
    SKILL_GOLDEN_CASES.validate_golden_case_output_directory
)


def _case(case_id: str):
    cases = load_golden_case_directory(CORE_FIXTURES)
    return next(case for case in cases if case.case_id == case_id)


def test_compliant_strategy_output_passes_drift_check() -> None:
    case = _case("core-strategy-voc-evidence-gate")

    errors = validate_golden_case_output_file(
        case,
        OUTPUTS / "core-strategy-voc-evidence-gate.pass.md",
    )

    assert errors == []


def test_missing_section_output_fails_drift_check() -> None:
    case = _case("core-strategy-voc-evidence-gate")

    errors = validate_golden_case_output_file(
        case,
        OUTPUTS / "core-strategy-voc-evidence-gate.missing-section.md",
    )

    assert any(
        "missing expected section: Recommended Next Tool" in error for error in errors
    )


def test_forbidden_claim_output_fails_drift_check() -> None:
    case = _case("core-strategy-voc-evidence-gate")

    errors = validate_golden_case_output_file(
        case,
        OUTPUTS / "core-strategy-voc-evidence-gate.forbidden-claim.md",
    )

    assert any(
        "forbidden claim pattern found: Core Customer is" in error for error in errors
    )


def test_missing_evidence_behavior_fails_drift_check() -> None:
    case = _case("core-strategy-voc-evidence-gate")

    errors = validate_golden_case_output_file(
        case,
        OUTPUTS / "core-strategy-voc-evidence-gate.missing-evidence.md",
    )

    assert any("missing evidence behavior" in error for error in errors)


def test_output_directory_reports_missing_case_outputs(tmp_path: Path) -> None:
    cases = load_golden_case_directory(CORE_FIXTURES)

    errors = validate_golden_case_output_directory(cases, tmp_path)

    assert any(
        "core-strategy-voc-evidence-gate: output file not found" in error
        for error in errors
    )
