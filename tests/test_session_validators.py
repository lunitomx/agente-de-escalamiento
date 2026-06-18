"""Tests for session lifecycle quality gate validators."""

from __future__ import annotations

import pathlib
import sys


sys.path.insert(
    0, str(pathlib.Path(__file__).resolve().parent.parent / ".scaleup" / "agent")
)
from validators.session import validate_context_bundle, validate_session_log


# ── validate_session_log ──────────────────────────────────────────────


class TestValidateSessionLog:
    def test_valid_log(self, tmp_path: pathlib.Path) -> None:
        log = tmp_path / "2026-04-25.md"
        log.write_text(
            "---\ndate: 2026-04-25\nduration_minutes: 45\ndecision_focus: people\n---\n## Notes\n- test\n"
        )
        assert validate_session_log(log) == []

    def test_valid_log_with_optional_fields(self, tmp_path: pathlib.Path) -> None:
        log = tmp_path / "2026-04-25.md"
        log.write_text(
            "---\ndate: 2026-04-25\nduration_minutes: 30\ndecision_focus: cash\n"
            "worksheets_completed: [ccc-worksheet]\ntasks_created: [task-1]\n---\n"
        )
        assert validate_session_log(log) == []

    def test_missing_file(self, tmp_path: pathlib.Path) -> None:
        log = tmp_path / "nonexistent.md"
        errors = validate_session_log(log)
        assert len(errors) == 1
        assert "File not found" in errors[0]

    def test_no_frontmatter(self, tmp_path: pathlib.Path) -> None:
        log = tmp_path / "bad.md"
        log.write_text("# Just markdown\nNo frontmatter here\n")
        errors = validate_session_log(log)
        assert len(errors) == 1
        assert "No YAML frontmatter" in errors[0]

    def test_missing_required_keys(self, tmp_path: pathlib.Path) -> None:
        log = tmp_path / "partial.md"
        log.write_text("---\ndate: 2026-04-25\n---\n")
        errors = validate_session_log(log)
        assert len(errors) == 1
        assert "Missing required keys" in errors[0]
        assert "decision_focus" in errors[0]
        assert "duration_minutes" in errors[0]

    def test_invalid_date_type(self, tmp_path: pathlib.Path) -> None:
        log = tmp_path / "bad-date.md"
        log.write_text(
            '---\ndate: "not-a-date"\nduration_minutes: 45\ndecision_focus: people\n---\n'
        )
        errors = validate_session_log(log)
        assert any("'date' must be a valid date" in e for e in errors)

    def test_invalid_duration_zero(self, tmp_path: pathlib.Path) -> None:
        log = tmp_path / "zero-dur.md"
        log.write_text(
            "---\ndate: 2026-04-25\nduration_minutes: 0\ndecision_focus: people\n---\n"
        )
        errors = validate_session_log(log)
        assert any("positive integer" in e for e in errors)

    def test_invalid_duration_negative(self, tmp_path: pathlib.Path) -> None:
        log = tmp_path / "neg-dur.md"
        log.write_text(
            "---\ndate: 2026-04-25\nduration_minutes: -5\ndecision_focus: people\n---\n"
        )
        errors = validate_session_log(log)
        assert any("positive integer" in e for e in errors)

    def test_invalid_duration_string(self, tmp_path: pathlib.Path) -> None:
        log = tmp_path / "str-dur.md"
        log.write_text(
            '---\ndate: 2026-04-25\nduration_minutes: "forty"\ndecision_focus: people\n---\n'
        )
        errors = validate_session_log(log)
        assert any("positive integer" in e for e in errors)

    def test_invalid_decision_focus(self, tmp_path: pathlib.Path) -> None:
        log = tmp_path / "bad-focus.md"
        log.write_text(
            "---\ndate: 2026-04-25\nduration_minutes: 30\ndecision_focus: marketing\n---\n"
        )
        errors = validate_session_log(log)
        assert any("must be one of" in e for e in errors)

    def test_invalid_yaml(self, tmp_path: pathlib.Path) -> None:
        log = tmp_path / "bad-yaml.md"
        log.write_text("---\n: : : broken\n---\n")
        errors = validate_session_log(log)
        assert any("Invalid YAML" in e for e in errors)


# ── validate_context_bundle ───────────────────────────────────────────


class TestValidateContextBundle:
    def test_valid_profile(self, tmp_path: pathlib.Path) -> None:
        profile = tmp_path / "company-profile.yaml"
        profile.write_text(
            "company:\n  name: Acme Corp\n  industry: tech\nscores:\n  people: 3\n  strategy: 2\n  execution: 1\n  cash: 4\n"
        )
        assert validate_context_bundle(profile) == []

    def test_missing_file(self, tmp_path: pathlib.Path) -> None:
        profile = tmp_path / "missing.yaml"
        errors = validate_context_bundle(profile)
        assert len(errors) == 1
        assert "Profile not found" in errors[0]

    def test_empty_company_name(self, tmp_path: pathlib.Path) -> None:
        profile = tmp_path / "empty.yaml"
        profile.write_text('company:\n  name: ""\nscores:\n  people: 0\n')
        errors = validate_context_bundle(profile)
        assert any("Company name is empty" in e for e in errors)

    def test_no_company_name_key(self, tmp_path: pathlib.Path) -> None:
        profile = tmp_path / "no-name.yaml"
        profile.write_text("company:\n  industry: tech\n")
        errors = validate_context_bundle(profile)
        assert any("Company name is empty" in e for e in errors)

    def test_non_numeric_score(self, tmp_path: pathlib.Path) -> None:
        profile = tmp_path / "bad-score.yaml"
        profile.write_text('company:\n  name: Test\nscores:\n  people: "high"\n')
        errors = validate_context_bundle(profile)
        assert any("must be numeric" in e for e in errors)

    def test_scores_with_zero(self, tmp_path: pathlib.Path) -> None:
        profile = tmp_path / "zero.yaml"
        profile.write_text(
            "company:\n  name: Test\nscores:\n  people: 0\n  strategy: 0\n"
        )
        assert validate_context_bundle(profile) == []

    def test_scores_with_none(self, tmp_path: pathlib.Path) -> None:
        profile = tmp_path / "none-scores.yaml"
        profile.write_text("company:\n  name: Test\nscores:\n  people: null\n")
        assert validate_context_bundle(profile) == []
