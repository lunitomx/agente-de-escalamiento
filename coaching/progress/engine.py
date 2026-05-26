"""coaching.progress.engine — pure logic for progress dashboard.

No I/O. Accepts profile + completed worksheets, returns progress dict.
"""
from __future__ import annotations

DECISIONS = ["people", "strategy", "execution", "cash"]


def calculate_progress(scores: dict, completed_worksheets: list[str], total_worksheets: int) -> dict:
    scored = {k: v for k, v in scores.items() if k in DECISIONS and isinstance(v, int)}
    avg = sum(scored.values()) / len(scored) if scored else 0
    completion = len(completed_worksheets) / total_worksheets if total_worksheets > 0 else 0

    return {
        "scores": scored,
        "average_score": round(avg, 1),
        "worksheets_completed": len(completed_worksheets),
        "worksheets_total": total_worksheets,
        "completion_pct": round(completion * 100),
        "focus": min(scored, key=scored.get) if scored else None,
    }


def suggest_next_action(scores: dict, completed_ids: set[str], registry: list[dict]) -> dict | None:
    focus = min(
        (k for k in DECISIONS if isinstance(scores.get(k), int)),
        key=lambda k: scores[k],
        default=None,
    )
    if not focus:
        return {"action": "diagnose", "reason": "No scores yet"}

    for ws in registry:
        if ws.get("decision") == focus and ws.get("id") not in completed_ids:
            prereqs = set(ws.get("prerequisites", []))
            if prereqs.issubset(completed_ids):
                return {
                    "action": "worksheet",
                    "worksheet_id": ws["id"],
                    "worksheet_name": ws.get("name", ""),
                    "decision": focus,
                    "reason": f"Next worksheet for {focus} (lowest score)",
                }

    return {"action": "coaching", "decision": focus, "reason": f"All {focus} worksheets done — deep coaching needed"}
