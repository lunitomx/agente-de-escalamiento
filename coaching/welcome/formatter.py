"""coaching.welcome.formatter — pure YAML renderer for company profile.

No I/O. Accepts structured profile dict, returns YAML string.
"""

from __future__ import annotations

try:
    import yaml
except ImportError as e:
    raise ImportError("PyYAML required: pip install pyyaml") from e


def format_profile(profile: dict) -> str:
    return yaml.dump(
        profile, default_flow_style=False, allow_unicode=True, sort_keys=False
    )


def format_summary(profile: dict) -> str:
    company = profile.get("company", {})
    lines = [
        "## Company Profile",
        "",
        f"**Name:** {company.get('name', 'N/A')}",
        f"**Industry:** {company.get('industry', 'N/A')}",
        f"**Employees:** {company.get('employees', 'N/A')}",
        f"**Growth Stage:** {company.get('growth_stage', 'N/A')}",
    ]
    if company.get("revenue"):
        lines.append(f"**Revenue:** {company['revenue']}")
    if company.get("years_in_business"):
        lines.append(f"**Years in Business:** {company['years_in_business']}")
    if company.get("location"):
        lines.append(f"**Location:** {company['location']}")

    assessment = profile.get("narrative_assessment")
    if isinstance(assessment, dict):
        lines.extend(["", "### Assessment narrativo"])
        summary = assessment.get("company_summary")
        if isinstance(summary, str) and summary.strip():
            lines.append(summary.strip())
        lines.append(f"**Estado:** {assessment.get('confirmation_status', 'pending')}")

    scores = profile.get("scores", {})
    scored = {key: value for key, value in scores.items() if value is not None}
    if scored:
        lines.extend(["", "### Calificación cuantitativa opcional"])
        for decision, score in scored.items():
            lines.append(f"- **{decision.capitalize()}:** {score}/5")
    elif not isinstance(assessment, dict):
        lines.extend(
            [
                "",
                "*Aún no hay assessment. Ejecuta `/escala-diagnose` para explicar "
                "el contexto antes de elegir un foco.*",
            ]
        )

    focus = profile.get("focus")
    if focus:
        lines.extend(["", f"**Current Focus:** {focus}"])

    lines.append("")
    return "\n".join(lines)
