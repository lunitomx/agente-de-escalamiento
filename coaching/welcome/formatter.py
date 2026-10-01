"""coaching.welcome.formatter — pure YAML renderer for company profile.

No I/O. Accepts structured profile dict, returns YAML string.
"""

from __future__ import annotations

from coaching.core import OWNER_AREA_NAMES, owner_area_name

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
        "## Tu empresa",
        "",
        f"**Nombre:** {company.get('name', 'N/A')}",
        f"**Giro:** {company.get('industry', 'N/A')}",
        f"**Empleados:** {company.get('employees', 'N/A')}",
        f"**Etapa:** {company.get('growth_stage', 'N/A')}",
    ]
    if company.get("revenue"):
        lines.append(f"**Ventas:** {company['revenue']}")
    if company.get("years_in_business"):
        lines.append(f"**Años en el negocio:** {company['years_in_business']}")
    if company.get("location"):
        lines.append(f"**Dónde:** {company['location']}")

    assessment = profile.get("narrative_assessment")
    if isinstance(assessment, dict):
        lines.extend(["", "### Lo que entendí de tu negocio"])
        summary = assessment.get("company_summary")
        if isinstance(summary, str) and summary.strip():
            lines.append(summary.strip())
        lines.append(f"**Estado:** {assessment.get('confirmation_status', 'pending')}")

    scores = profile.get("scores", {})
    scored = {key: value for key, value in scores.items() if value is not None}
    if scored:
        lines.extend(["", "### Calificación cuantitativa opcional"])
        for decision, score in scored.items():
            lines.append(f"- **{owner_area_name(decision, capital=True)}:** {score}/5")
    elif not isinstance(assessment, dict):
        lines.extend(
            [
                "",
                "*Todavía no revisamos tu negocio. Cuéntale a ESCALA lo que más "
                "te preocupa y empezamos por ahí.*",
            ]
        )

    focus = profile.get("focus")
    if focus:
        name = owner_area_name(focus) if focus in OWNER_AREA_NAMES else focus
        lines.extend(["", f"**Ahora trabajamos en:** {name}"])

    lines.append("")
    return "\n".join(lines)
