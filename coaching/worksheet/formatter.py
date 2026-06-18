"""coaching.worksheet.formatter — pure markdown renderer for worksheets.

No I/O. Accepts structured worksheet dict, returns markdown string.
"""

from __future__ import annotations


def format_worksheet_list(worksheets: list[dict], decision: str | None = None) -> str:
    title = (
        f"## Worksheets: {decision.capitalize()}" if decision else "## All Worksheets"
    )
    lines = [title, ""]

    by_decision: dict[str, list[dict]] = {}
    for w in worksheets:
        d = w.get("decision", "other")
        by_decision.setdefault(d, []).append(w)

    for dec in ["people", "strategy", "execution", "cash"]:
        group = by_decision.get(dec, [])
        if not group:
            continue
        lines.append(f"### {dec.capitalize()} ({len(group)})")
        lines.append("")
        for w in group:
            difficulty = w.get("difficulty", "")
            time_est = w.get("time_estimate", "")
            lines.append(f"- **{w['name']}** (`{w['id']}`) — {difficulty}, {time_est}")
        lines.append("")

    return "\n".join(lines)


def format_worksheet_guide(session: dict) -> str:
    lines = [
        f"## {session['name']}",
        "",
        f"**Decision:** {session['decision'].capitalize()}",
        f"**Difficulty:** {session['difficulty']}",
        f"**Time Estimate:** {session['time_estimate']}",
        f"**Fields:** {session['total_fields']}",
        "",
    ]

    if session.get("sections"):
        for section in session["sections"]:
            lines.append(f"### {section.get('name', 'Section')}")
            lines.append("")
            if section.get("description"):
                lines.append(section["description"])
                lines.append("")
            for field in section.get("fields", []):
                lines.append(
                    f"- **{field.get('name', '')}**: {field.get('description', '')}"
                )
            lines.append("")
    elif session.get("fields"):
        lines.append("### Fields")
        lines.append("")
        for field in session["fields"]:
            lines.append(
                f"- **{field.get('name', '')}**: {field.get('description', '')}"
            )
        lines.append("")

    if session.get("outputs"):
        lines.append("### Expected Outputs")
        lines.append("")
        for output in session["outputs"]:
            lines.append(f"- {output}")
        lines.append("")

    return "\n".join(lines)


def format_completed(worksheet_data: dict) -> str:
    lines = [
        f"## Completed: {worksheet_data.get('worksheet_name', '')}",
        "",
        f"**Decision:** {worksheet_data.get('decision', '')}",
        f"**Status:** {worksheet_data.get('status', '')}",
        "",
    ]

    fields = worksheet_data.get("fields", {})
    if isinstance(fields, dict):
        for key, value in fields.items():
            lines.append(f"- **{key}:** {value}")
    lines.append("")
    return "\n".join(lines)
