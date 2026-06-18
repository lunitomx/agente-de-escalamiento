"""coaching.level.formatter — pure renderer for coaching level.

No I/O. Accepts level assessment dict, returns markdown string.
"""

from __future__ import annotations


def format_level(assessment: dict) -> str:
    lines = [
        "## Coaching Level",
        "",
        f"**Level:** {assessment.get('label', '')}",
        f"**Guidance:** {assessment.get('guidance', '')}",
        "",
    ]

    inputs = assessment.get("inputs", {})
    lines.extend(
        [
            "### Assessment Inputs",
            "",
            f"- Average Score: {inputs.get('average_score', 0)}/5",
            f"- Worksheets Completed: {inputs.get('worksheets_completed', 0)}",
            f"- Sessions: {inputs.get('sessions_count', 0)}",
        ]
    )

    if assessment.get("override"):
        lines.extend(["", f"*Level manually set to: {assessment['override']}*"])

    lines.append("")
    return "\n".join(lines)
