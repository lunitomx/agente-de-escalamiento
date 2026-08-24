"""Pure business logic for session summaries."""


def build_summary(data: dict) -> dict:
    """Normalize session context into the structure consumed by the formatter."""
    return {
        "date": data.get("date", ""),
        "duration_minutes": data.get("duration_minutes", 0),
        "decision_focus": data.get("decision_focus", ""),
        "worksheets_completed": list(data.get("worksheets_completed") or []),
        "tasks_created": list(data.get("tasks_created") or []),
        "tasks_completed": list(data.get("tasks_completed") or []),
        "notes": list(data.get("notes") or []),
    }
