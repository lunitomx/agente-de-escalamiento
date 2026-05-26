"""coaching.diagnose.formatter — pure markdown renderer for diagnosis.

No I/O. Accepts structured diagnosis dict, returns markdown string.
"""
from __future__ import annotations


def format_diagnosis(diagnosis: dict) -> str:
    lines = ["## Diagnosis Report", ""]

    scores = diagnosis.get("scores", {})
    labels = diagnosis.get("labels", {})
    for dec in ["people", "strategy", "execution", "cash"]:
        score = scores.get(dec, "—")
        label = labels.get(dec, "")
        bar = _score_bar(score) if isinstance(score, int) else ""
        lines.append(f"- **{dec.capitalize()}:** {score}/5 {bar} ({label})")

    summary = diagnosis.get("summary", {})
    lines.extend([
        "",
        f"**Average:** {summary.get('average', 0)}/5",
        f"**Strongest:** {summary.get('highest', '').capitalize()}",
        f"**Weakest:** {summary.get('lowest', '').capitalize()}",
    ])

    focus = diagnosis.get("focus", {})
    if focus.get("decision"):
        lines.extend([
            "",
            f"### Recommended Focus: **{focus['decision'].capitalize()}**",
            "",
            f"Your lowest score is in **{focus['decision'].capitalize()}** ({focus.get('label', '')}). "
            "Focus coaching sessions on this decision to build your foundation.",
        ])

    lines.append("")
    return "\n".join(lines)


def _score_bar(score: int) -> str:
    filled = score
    empty = 5 - score
    return "[" + "#" * filled + "." * empty + "]"
