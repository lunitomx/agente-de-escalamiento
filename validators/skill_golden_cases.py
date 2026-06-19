"""Validation for deterministic skill golden-case fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

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


SkillGoldenCase.model_rebuild()


def load_golden_cases(fixture_path: Path) -> list[SkillGoldenCase]:
    """Load golden cases from a YAML list."""
    data = yaml.safe_load(fixture_path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ValueError("Golden case fixture file must contain a list")
    return [SkillGoldenCase.model_validate(item) for item in data]


def validate_golden_case_file(
    fixture_path: Path,
    skills_root: Path = Path(".agents/skills"),
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


def _format_validation_error(error: Mapping[str, Any]) -> str:
    location = ".".join(str(part) for part in error.get("loc", ())) or "record"
    message = str(error.get("msg", "invalid value"))
    return f"{location}: {message}"
