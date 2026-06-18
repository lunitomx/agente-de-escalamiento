"""Tests for persistent memory validators and renderers."""

from __future__ import annotations

import pathlib
import sys


sys.path.insert(
    0, str(pathlib.Path(__file__).resolve().parent.parent / ".scaleup" / "agent")
)
from validators.memory import render_profile_markdown, validate_company_profile


class TestValidateCompanyProfile:
    def _write_profile(self, tmp_path: pathlib.Path, content: str) -> pathlib.Path:
        p = tmp_path / "company-profile.yaml"
        p.write_text(content)
        return p

    def test_valid_full_profile(self, tmp_path: pathlib.Path) -> None:
        p = self._write_profile(
            tmp_path,
            (
                "company:\n  name: Acme\n  industry: tech\n  employees: 50\n"
                "  growth_stage: scaleup\n  years_in_business: 10\n  revenue_range: 5M-10M\n"
                "  current_challenges: [hiring, cash flow]\n"
                "scores:\n  people: 3\n  strategy: 2\n  execution: 4\n  cash: 1\n"
                "  last_diagnosis: '2026-04-25'\n"
                "focus:\n  current_decision: cash\n  current_tool: ccc\n  last_session: '2026-04-25'\n"
                "diagnosis_history:\n  - {date: '2026-04-25', people: 3, strategy: 2, execution: 4, cash: 1}\n"
            ),
        )
        assert validate_company_profile(p) == []

    def test_missing_file(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "missing.yaml"
        errors = validate_company_profile(p)
        assert any("not found" in e for e in errors)

    def test_empty_name(self, tmp_path: pathlib.Path) -> None:
        p = self._write_profile(tmp_path, 'company:\n  name: ""\n')
        errors = validate_company_profile(p)
        assert any("name is required" in e for e in errors)

    def test_invalid_stage(self, tmp_path: pathlib.Path) -> None:
        p = self._write_profile(
            tmp_path, "company:\n  name: Test\n  growth_stage: mega\n"
        )
        errors = validate_company_profile(p)
        assert any("growth_stage" in e for e in errors)

    def test_non_numeric_employees(self, tmp_path: pathlib.Path) -> None:
        p = self._write_profile(
            tmp_path, 'company:\n  name: Test\n  employees: "many"\n'
        )
        errors = validate_company_profile(p)
        assert any("employees must be numeric" in e for e in errors)

    def test_non_numeric_score(self, tmp_path: pathlib.Path) -> None:
        p = self._write_profile(
            tmp_path, 'company:\n  name: Test\nscores:\n  people: "high"\n'
        )
        errors = validate_company_profile(p)
        assert any("must be numeric" in e for e in errors)

    def test_invalid_history_entry(self, tmp_path: pathlib.Path) -> None:
        p = self._write_profile(
            tmp_path, "company:\n  name: Test\ndiagnosis_history:\n  - not_a_dict\n"
        )
        errors = validate_company_profile(p)
        assert any("must be a mapping" in e for e in errors)

    def test_history_missing_date(self, tmp_path: pathlib.Path) -> None:
        p = self._write_profile(
            tmp_path, "company:\n  name: Test\ndiagnosis_history:\n  - {people: 3}\n"
        )
        errors = validate_company_profile(p)
        assert any("missing 'date'" in e for e in errors)

    def test_minimal_valid(self, tmp_path: pathlib.Path) -> None:
        p = self._write_profile(tmp_path, "company:\n  name: Test\n")
        assert validate_company_profile(p) == []


class TestRenderProfileMarkdown:
    def test_renders_company_name(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "profile.yaml"
        p.write_text(
            "company:\n  name: Acme Corp\n  industry: tech\n  employees: 50\n"
            "  growth_stage: scaleup\n  years_in_business: 10\n"
            "scores:\n  people: 3\n  strategy: 2\n  execution: 4\n  cash: 1\n"
            "focus: {}\ndiagnosis_history: []\n"
        )
        md = render_profile_markdown(p)
        assert "Acme Corp" in md
        assert "| People | 3 |" in md
        assert "| Cash | 1 |" in md

    def test_renders_history(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "profile.yaml"
        p.write_text(
            "company:\n  name: Test\nscores: {}\nfocus: {}\n"
            "diagnosis_history:\n  - {date: '2026-04-25', people: 3, strategy: 2, execution: 4, cash: 1}\n"
        )
        md = render_profile_markdown(p)
        assert "Historial de Diagnósticos" in md
        assert "2026-04-25" in md

    def test_renders_without_challenges(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "profile.yaml"
        p.write_text(
            "company:\n  name: Test\nscores: {}\nfocus: {}\ndiagnosis_history: []\n"
        )
        md = render_profile_markdown(p)
        assert "Sin retos registrados" in md

    def test_renders_focus(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "profile.yaml"
        p.write_text(
            "company:\n  name: Test\nscores: {}\n"
            "focus:\n  current_decision: people\n  current_tool: core-values\n"
            "diagnosis_history: []\n"
        )
        md = render_profile_markdown(p)
        assert "Foco Actual" in md
        assert "people" in md
