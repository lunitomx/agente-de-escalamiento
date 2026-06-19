#!/usr/bin/env python3
"""Release check for skill golden-case validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.skill_golden_cases import (  # noqa: E402
    load_golden_case_directory,
    validate_golden_case_changelog,
    validate_golden_case_directory,
    validate_golden_case_output_directory,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate skill golden cases for release review.",
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=ROOT / "tests/fixtures/skill_golden_cases/core",
    )
    parser.add_argument(
        "--skills-root",
        type=Path,
        default=ROOT / ".claude/skills",
    )
    parser.add_argument(
        "--changelog",
        type=Path,
        default=ROOT / ".raise/skill-golden-cases/changelog.yaml",
    )
    parser.add_argument(
        "--outputs-dir",
        type=Path,
        default=ROOT / "tests/fixtures/skill_golden_cases/release_outputs",
    )
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()

    report = build_report(
        fixtures_dir=args.fixtures_dir,
        skills_root=args.skills_root,
        changelog_path=args.changelog,
        outputs_dir=args.outputs_dir,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    return 0 if report["status"] == "pass" else 1


def build_report(
    fixtures_dir: Path,
    skills_root: Path,
    changelog_path: Path,
    outputs_dir: Path,
) -> dict[str, Any]:
    """Build a release-check report for golden cases."""
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    fixture_errors = validate_golden_case_directory(fixtures_dir, skills_root)
    checks.append(_check_result("fixture_validation", fixture_errors))
    errors.extend(fixture_errors)

    try:
        cases = load_golden_case_directory(fixtures_dir)
    except (OSError, ValueError) as exc:
        cases = []
        errors.append(str(exc))

    changelog_errors = validate_golden_case_changelog(cases, changelog_path)
    checks.append(_check_result("changelog_validation", changelog_errors))
    errors.extend(changelog_errors)

    output_errors = validate_golden_case_output_directory(cases, outputs_dir)
    checks.append(_check_result("output_drift", output_errors))
    errors.extend(output_errors)

    return {
        "status": "pass" if not errors else "fail",
        "checks": checks,
        "errors": errors,
    }


def print_text_report(report: dict[str, Any]) -> None:
    """Print a compact human-readable report."""
    print(f"skill golden cases: {report['status']}")
    for check in report["checks"]:
        print(f"- {check['name']}: {check['status']}")
    for error in report["errors"]:
        print(f"ERROR: {error}")


def _check_result(name: str, errors: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "status": "pass" if not errors else "fail",
        "errors": errors,
    }


if __name__ == "__main__":
    raise SystemExit(main())
