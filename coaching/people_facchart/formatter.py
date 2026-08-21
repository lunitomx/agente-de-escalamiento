"""Render a FACChart into markdown."""

from __future__ import annotations

from .engine import FACChart, MISSING


def render_markdown(chart: FACChart, company_name: str = "") -> str:
    """Render the chart using the same structure as the FACChart template."""
    functions = chart.functions

    lines = [
        "# Function Accountability Chart (FACChart)",
        "",
    ]
    if company_name:
        lines.append(f"> Empresa: {company_name}")
        lines.append("")

    if not functions:
        lines.append("*No hay funciones definidas todavía.*")
        return "\n".join(lines)

    lines.extend(
        [
            "| Función | Accountable | KPIs |",
            "|---------|-------------|------|",
        ]
    )

    for func in functions:
        name = func.name.strip() or MISSING
        accountable = func.accountable.strip() or MISSING
        kpis = ", ".join(func.kpis) if func.kpis else MISSING
        lines.append(f"| {name} | {accountable} | {kpis} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append(f"**Total funciones:** {len(functions)}")

    return "\n".join(lines)
