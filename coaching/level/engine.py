"""coaching.level.engine — pure logic for coaching level detection (Shu/Ha/Ri).

No I/O. Accepts scores + activity data, returns level assessment.
"""
from __future__ import annotations

LEVELS = {
    "shu": {"label": "Shu (Follow)", "label_es": "Shu (Seguir)", "min_avg": 0, "max_avg": 2.0},
    "ha": {"label": "Ha (Break)", "label_es": "Ha (Adaptar)", "min_avg": 2.1, "max_avg": 3.5},
    "ri": {"label": "Ri (Transcend)", "label_es": "Ri (Trascender)", "min_avg": 3.6, "max_avg": 5.0},
}

LEVEL_GUIDANCE = {
    "shu": "Explain concepts in detail. Guide step-by-step. Show examples. Check understanding.",
    "ha": "Explain new or non-obvious signals only. Allow adaptation of frameworks.",
    "ri": "Minimal output. Context line, focus, signals. Trust expertise.",
}


def detect_level(avg_score: float, worksheets_completed: int, sessions_count: int) -> str:
    if avg_score >= 3.6 and worksheets_completed >= 8 and sessions_count >= 10:
        return "ri"
    if avg_score >= 2.1 and worksheets_completed >= 3 and sessions_count >= 3:
        return "ha"
    return "shu"


def build_level_assessment(data: dict) -> dict:
    avg = data.get("average_score", 0)
    ws = data.get("worksheets_completed", 0)
    sessions = data.get("sessions_count", 0)

    level = data.get("override") or detect_level(avg, ws, sessions)

    return {
        "level": level,
        "label": LEVELS.get(level, {}).get("label", level),
        "label_es": LEVELS.get(level, {}).get("label_es", level),
        "guidance": LEVEL_GUIDANCE.get(level, ""),
        "inputs": {
            "average_score": avg,
            "worksheets_completed": ws,
            "sessions_count": sessions,
        },
        "override": data.get("override"),
    }
