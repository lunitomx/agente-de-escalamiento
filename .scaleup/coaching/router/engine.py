"""coaching.router.engine — deterministic routing to sub-agents.

No I/O. Accepts scores dict, returns routing decision.
"""
from __future__ import annotations

DECISIONS = ["people", "strategy", "execution", "cash"]

SUB_AGENTS = {
    "people": {"skill": "scaleup-people", "label": "People Coach"},
    "strategy": {"skill": "scaleup-strategy", "label": "Strategy Coach"},
    "execution": {"skill": "scaleup-execution", "label": "Execution Coach"},
    "cash": {"skill": "scaleup-cash", "label": "Cash Coach"},
}


def route(scores: dict, explicit: str | None = None) -> dict:
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

    lowest = min(valid, key=valid.get)
    agent = SUB_AGENTS[lowest]
    return {
        "decision": lowest,
        "skill": agent["skill"],
        "label": agent["label"],
        "reason": "lowest_score",
        "score": valid[lowest],
    }
