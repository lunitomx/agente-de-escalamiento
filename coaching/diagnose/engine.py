"""coaching.diagnose.engine — pure scoring logic for the 4 decisions.

No I/O. Accepts answers dict, returns structured diagnosis dict.
"""

from __future__ import annotations

from typing import Any

DECISIONS = ["people", "strategy", "execution", "cash"]

SCORE_RANGE = (1, 5)

SCORE_LABELS = {
    1: "No iniciado",
    2: "Ad hoc",
    3: "Emergente",
    4: "Establecido",
    5: "Optimizado",
}


def validate_scores(scores: dict[str, Any]) -> list[str]:
    errors = []
    for dec in DECISIONS:
        val = scores.get(dec)
        if val is None:
            errors.append(f"Missing score for: {dec}")
        elif not isinstance(val, int):
            errors.append(f"{dec} score must be integer, got: {type(val).__name__}")
        elif val < SCORE_RANGE[0] or val > SCORE_RANGE[1]:
            errors.append(
                f"{dec} score out of range ({SCORE_RANGE[0]}-{SCORE_RANGE[1]}): {val}"
            )
    return errors


def calculate_focus(scores: dict[str, Any]) -> str:
    valid = {k: v for k, v in scores.items() if k in DECISIONS and isinstance(v, int)}
    if not valid:
        return "people"
    return min(valid, key=lambda decision: valid[decision])


def build_diagnosis(data: dict[str, Any]) -> dict[str, Any]:
    scores: dict[str, int] = {}
    for dec in DECISIONS:
        val = data.get(dec)
        if isinstance(val, int):
            scores[dec] = val

    focus = calculate_focus(scores)
    total = sum(scores.values()) if scores else 0
    avg = total / len(scores) if scores else 0

    return {
        "scores": scores,
        "focus": {
            "decision": focus,
            "label": SCORE_LABELS.get(scores.get(focus, 1), ""),
            "last_diagnosis": data.get("date", ""),
        },
        "summary": {
            "total": total,
            "average": round(avg, 1),
            "lowest": focus,
            "highest": max(scores, key=lambda decision: scores[decision])
            if scores
            else "",
        },
        "labels": {dec: SCORE_LABELS.get(s, "") for dec, s in scores.items()},
    }
