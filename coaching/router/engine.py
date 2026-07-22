"""coaching.router.engine — deterministic routing to sub-agents.

No I/O. Accepts scores dict, returns routing decision.
"""

from __future__ import annotations

from typing import Any

DECISIONS = ["people", "strategy", "execution", "cash"]

SUB_AGENTS = {
    "people": {"skill": "escala-people", "label": "People Coach"},
    "strategy": {"skill": "escala-strategy", "label": "Strategy Coach"},
    "execution": {"skill": "escala-execution", "label": "Execution Coach"},
    "cash": {"skill": "escala-cash", "label": "Cash Coach"},
}


def route(scores: dict[str, Any], explicit: str | None = None) -> dict[str, Any]:
    if explicit and explicit in DECISIONS:
        agent = SUB_AGENTS[explicit]
        return {
            "decision": explicit,
            "skill": agent["skill"],
            "label": agent["label"],
            "reason": "explicit_request",
            "score": scores.get(explicit),
        }

    valid = {k: v for k, v in scores.items() if k in DECISIONS and isinstance(v, int)}

    if not valid:
        return {
            "decision": "people",
            "skill": SUB_AGENTS["people"]["skill"],
            "label": SUB_AGENTS["people"]["label"],
            "reason": "no_scores_default",
            "score": None,
        }

    lowest = min(valid, key=lambda decision: valid[decision])
    agent = SUB_AGENTS[lowest]
    return {
        "decision": lowest,
        "skill": agent["skill"],
        "label": agent["label"],
        "reason": "lowest_score",
        "score": valid[lowest],
    }
