"""coaching.summary.engine — pure business logic.

No I/O. Accepts session data dict, returns structured summary dict.
"""
from __future__ import annotations


def build_summary(data: dict) -> dict:
    """Build a structured summary dict from session context data.

    Args:
        data: Session context dict with keys:
            date, duration_minutes, decision_focus,
            worksheets_completed, tasks_created, tasks_completed,
            notes, scores_before (optional/None)

    Returns:
        Structured summary dict ready for formatting.
    """
    return {
        "date": data.get("date", ""),
        "duration_minutes": data.get("duration_minutes", 0),
        "decision_focus": data.get("decision_focus", ""),
        "worksheets_completed": list(data.get("worksheets_completed") or []),
        "tasks_created": list(data.get("tasks_created") or []),
        "tasks_completed": list(data.get("tasks_completed") or []),
        "notes": list(data.get("notes") or []),
        "scores_before": data.get("scores_before"),
    }
