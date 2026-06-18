"""coaching.progress.formatter — pure markdown renderer for progress dashboard.

No I/O. Accepts progress dict, returns markdown string.
"""

from __future__ import annotations

DECISIONS = ["people", "strategy", "execution", "cash"]


def format_progress(progress: dict, suggestion: dict | None = None) -> str:
    lines = ["## Progress Dashboard", ""]

    scores = progress.get("scores", {})
    for dec in DECISIONS:
        score = scores.get(dec)
        if score is not None:
            bar = "[" + "#" * score + "." * (5 - score) + "]"
            lines.append(f"- **{dec.capitalize()}:** {score}/5 {bar}")
        else:
            lines.append(f"- **{dec.capitalize()}:** —")

    lines.extend(
        [
            "",
            f"**Average Score:** {progress.get('average_score', 0)}/5",
            f"**Worksheets:** {progress.get('worksheets_completed', 0)}/{progress.get('worksheets_total', 0)} ({progress.get('completion_pct', 0)}%)",
        ]
    )

    focus = progress.get("focus")
    if focus:
        lines.append(f"**Current Focus:** {focus.capitalize()}")

    if suggestion:
        lines.extend(["", "### Next Step", ""])
        action = suggestion.get("action")
        if action == "diagnose":
            lines.append("Run `/scaleup-diagnose` to get your baseline scores.")
        elif action == "worksheet":
            lines.append(
                f"Run `/scaleup-worksheet {suggestion['worksheet_id']}` — {suggestion.get('worksheet_name', '')}"
            )
            lines.append(f"*Reason: {suggestion.get('reason', '')}*")
        elif action == "coaching":
            lines.append(
                f"Run `/scaleup-{suggestion['decision']}` for deep coaching on {suggestion['decision'].capitalize()}."
            )
            lines.append(f"*Reason: {suggestion.get('reason', '')}*")

    lines.append("")
    return "\n".join(lines)
