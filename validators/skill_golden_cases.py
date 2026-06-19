"""Validation for deterministic skill golden-case fixtures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


class SkillGoldenCase(BaseModel):
    """Fixture contract for expected skill behavior properties."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    skill: str = Field(min_length=1)
    input_context: dict[str, Any] = Field(min_length=1)
    expected_sections: list[str] = Field(min_length=1)
    required_methodology_terms: list[str] = Field(min_length=1)
    forbidden_claim_patterns: list[str] = Field(min_length=1)
    evidence_required: bool
    notes: str = Field(min_length=1)


class GoldenCaseOutput(BaseModel):
    """Mapping from a golden case to a deterministic output artifact."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    output_path: Path


class GoldenCaseChangelogEntry(BaseModel):
    """Review evidence for accepted golden-case expectation changes."""

    model_config = ConfigDict(extra="forbid")

    change_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    skill: str = Field(min_length=1)
    expectation_hash: str = Field(min_length=64, max_length=64)
    reason: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    changed_fields: list[str] = Field(min_length=1)
    expected_behavior_change: str = Field(min_length=1)


SkillGoldenCase.model_rebuild()
GoldenCaseOutput.model_rebuild()
GoldenCaseChangelogEntry.model_rebuild()


def load_golden_cases(fixture_path: Path) -> list[SkillGoldenCase]:
    """Load golden cases from a YAML list."""
    data = yaml.safe_load(fixture_path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ValueError("Golden case fixture file must contain a list")
    return [SkillGoldenCase.model_validate(item) for item in data]


def load_golden_case_directory(fixtures_dir: Path) -> list[SkillGoldenCase]:
    """Load golden cases from all YAML files in a directory."""
    fixture_paths = sorted(fixtures_dir.glob("*.yaml"))
    if not fixture_paths:
        raise ValueError(f"No golden case YAML files found in {fixtures_dir}")

    cases: list[SkillGoldenCase] = []
    for fixture_path in fixture_paths:
        cases.extend(load_golden_cases(fixture_path))
    return cases


def load_golden_case_changelog(changelog_path: Path) -> list[GoldenCaseChangelogEntry]:
    """Load accepted golden-case expectation changes from YAML."""
    data = yaml.safe_load(changelog_path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ValueError("Golden case changelog file must contain a list")
    return [GoldenCaseChangelogEntry.model_validate(item) for item in data]


def golden_case_expectation_hash(case: SkillGoldenCase) -> str:
    """Return a stable hash for expectation-bearing fields."""
    payload = {
        "evidence_required": case.evidence_required,
        "expected_sections": case.expected_sections,
        "forbidden_claim_patterns": case.forbidden_claim_patterns,
        "required_methodology_terms": case.required_methodology_terms,
    }
    serialized = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def validate_golden_case_file(
    fixture_path: Path,
    skills_root: Path = Path(".claude/skills"),
) -> list[str]:
    """Return readable validation errors for one golden-case fixture file."""
    try:
        cases = load_golden_cases(fixture_path)
    except ValidationError as exc:
        return [_format_validation_error(error) for error in exc.errors()]
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [str(exc)]

    errors: list[str] = []
    for case in cases:
        skill_path = skills_root / case.skill / "SKILL.md"
        if not skill_path.exists():
            errors.append(f"{case.case_id}: skill not found: {case.skill}")
    return errors


def validate_golden_case_directory(
    fixtures_dir: Path,
    skills_root: Path = Path(".claude/skills"),
) -> list[str]:
    """Return readable validation errors for all YAML fixtures in a directory."""
    fixture_paths = sorted(fixtures_dir.glob("*.yaml"))
    if not fixture_paths:
        return [f"No golden case YAML files found in {fixtures_dir}"]

    errors: list[str] = []
    for fixture_path in fixture_paths:
        for error in validate_golden_case_file(fixture_path, skills_root):
            errors.append(f"{fixture_path.name}: {error}")
    return errors


def validate_golden_case_changelog(
    cases: Sequence[SkillGoldenCase],
    changelog_path: Path,
) -> list[str]:
    """Return errors when current expectations lack accepted-change evidence."""
    try:
        entries = load_golden_case_changelog(changelog_path)
    except ValidationError as exc:
        return [_format_validation_error(error) for error in exc.errors()]
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [str(exc)]

    entry_index = {
        (entry.case_id, entry.skill, entry.expectation_hash): entry for entry in entries
    }
    errors: list[str] = []

    for case in cases:
        expectation_hash = golden_case_expectation_hash(case)
        key = (case.case_id, case.skill, expectation_hash)
        if key not in entry_index:
            errors.append(
                f"{case.case_id}: missing changelog entry for expectation hash "
                f"{expectation_hash}"
            )

    return errors


def validate_golden_case_output(
    case: SkillGoldenCase,
    output_text: str,
) -> list[str]:
    """Return drift errors for one golden case and output text."""
    normalized_output = output_text.casefold()
    errors: list[str] = []

    for section in case.expected_sections:
        if section.casefold() not in normalized_output:
            errors.append(f"{case.case_id}: missing expected section: {section}")

    for term in case.required_methodology_terms:
        if term.casefold() not in normalized_output:
            errors.append(f"{case.case_id}: missing methodology term: {term}")

    for pattern in case.forbidden_claim_patterns:
        if pattern.casefold() in normalized_output:
            errors.append(f"{case.case_id}: forbidden claim pattern found: {pattern}")

    if case.evidence_required and not _has_evidence_behavior(normalized_output):
        errors.append(f"{case.case_id}: missing evidence behavior")

    return errors


def validate_golden_case_output_file(
    case: SkillGoldenCase,
    output_path: Path,
) -> list[str]:
    """Return drift errors for one golden case output file."""
    try:
        output_text = output_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{case.case_id}: output file not found: {output_path} ({exc})"]
    return validate_golden_case_output(case, output_text)


def validate_golden_case_output_directory(
    cases: Sequence[SkillGoldenCase],
    outputs_dir: Path,
) -> list[str]:
    """Return drift errors for outputs named after their case ids."""
    errors: list[str] = []
    for case in cases:
        output_path = outputs_dir / f"{case.case_id}.md"
        errors.extend(validate_golden_case_output_file(case, output_path))
    return errors


def _has_evidence_behavior(normalized_output: str) -> bool:
    evidence_markers = (
        "evidence id",
        "evidence ids",
        "citation",
        "cited",
        "missing evidence",
    )
    return any(marker in normalized_output for marker in evidence_markers)


def _format_validation_error(error: Mapping[str, Any]) -> str:
    location = ".".join(str(part) for part in error.get("loc", ())) or "record"
    message = str(error.get("msg", "invalid value"))
    return f"{location}: {message}"
