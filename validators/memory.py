"""Persistent memory validators and renderers.

Validates company profile schema and renders YAML to markdown views.
"""

from __future__ import annotations

import pathlib
from typing import Any

try:
    import yaml
except ImportError as e:
    raise ImportError("PyYAML required: pip install pyyaml") from e


_REQUIRED_COMPANY_FIELDS = {"name"}
_VALID_STAGES = {"startup", "scaling", "established", "enterprise", ""}
_SCORE_KEYS = ("people", "strategy", "execution", "cash")


def validate_company_profile(profile_path: pathlib.Path) -> list[str]:
    """Validate company profile YAML schema. Returns list of errors (empty = valid)."""
    errors: list[str] = []

    if not profile_path.exists():
        return [f"Profile not found: {profile_path}"]

    try:
        data: dict[str, Any] = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"Invalid YAML: {exc}"]

    if not isinstance(data, dict):
        return ["Profile is not a mapping"]

    company = data.get("company", {})
    if not isinstance(company, dict):
        errors.append("'company' must be a mapping")
    else:
        if not company.get("name"):
            errors.append("company.name is required")
        stage = company.get("growth_stage", "")
        if stage and stage not in _VALID_STAGES:
            errors.append(
                f"company.growth_stage must be one of {_VALID_STAGES}, got: {stage!r}"
            )
        emp = company.get("employees", 0)
        if emp is not None and not isinstance(emp, (int, float)):
            errors.append(f"company.employees must be numeric, got: {emp!r}")

    scores = data.get("scores", {})
    if isinstance(scores, dict):
        for key in _SCORE_KEYS:
            val = scores.get(key)
            if val is not None and not isinstance(val, (int, float)):
                errors.append(f"scores.{key} must be numeric, got: {val!r}")

    history = data.get("diagnosis_history", [])
    if not isinstance(history, list):
        errors.append("diagnosis_history must be a list")
    else:
        for i, entry in enumerate(history):
            if not isinstance(entry, dict):
                errors.append(f"diagnosis_history[{i}] must be a mapping")
                continue
            if "date" not in entry:
                errors.append(f"diagnosis_history[{i}] missing 'date'")

    return errors


def render_profile_markdown(profile_path: pathlib.Path) -> str:
    """Render company-profile.yaml into human-readable markdown."""
    data = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    company = data.get("company", {})
    scores = data.get("scores", {})
    focus = data.get("focus", {})
    history = data.get("diagnosis_history", [])

    lines = [
        "# Mi Empresa",
        "",
        "## Información General",
        "",
        f"- **Nombre:** {company.get('name', '—')}",
        f"- **Industria:** {company.get('industry', '—')}",
        f"- **Año de fundación:** {company.get('years_in_business', '—')} años",
        f"- **Empleados:** {company.get('employees', '—')}",
        f"- **Etapa:** {company.get('growth_stage', '—')}",
        f"- **Revenue:** {company.get('revenue_range', '—')}",
        "",
        "## Retos Principales",
        "",
    ]

    challenges = company.get("current_challenges", [])
    if challenges:
        for c in challenges:
            lines.append(f"1. {c}")
    else:
        lines.append("*Sin retos registrados*")

    lines.extend(
        [
            "",
            "## Scores de Diagnóstico",
            "",
            "| Decisión | Score |",
            "|----------|-------|",
            f"| People | {scores.get('people', 0)} |",
            f"| Strategy | {scores.get('strategy', 0)} |",
            f"| Execution | {scores.get('execution', 0)} |",
            f"| Cash | {scores.get('cash', 0)} |",
            "",
            f"*Último diagnóstico: {scores.get('last_diagnosis', 'pendiente')}*",
            "",
        ]
    )

    if history:
        lines.extend(
            [
                "## Historial de Diagnósticos",
                "",
                "| Fecha | People | Strategy | Execution | Cash |",
                "|-------|--------|----------|-----------|------|",
            ]
        )
        for entry in history:
            lines.append(
                f"| {entry.get('date', '?')} | {entry.get('people', '?')} | "
                f"{entry.get('strategy', '?')} | {entry.get('execution', '?')} | "
                f"{entry.get('cash', '?')} |"
            )
        lines.append("")

    if focus.get("current_decision"):
        lines.extend(
            [
                "## Foco Actual",
                "",
                f"- **Decisión:** {focus['current_decision']}",
                f"- **Herramienta:** {focus.get('current_tool', '—')}",
                f"- **Última sesión:** {focus.get('last_session', '—')}",
                "",
            ]
        )

    lines.append("*Generado automáticamente desde company-profile.yaml*")
    return "\n".join(lines) + "\n"
