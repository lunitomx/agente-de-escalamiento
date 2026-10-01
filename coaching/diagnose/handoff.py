# pyright: strict
"""S86.5: when the owner says yes, the weekly action becomes a commitment row.

ESCALA does not write in the group sheet (E82 S82.6 found no verified way).
The diagnosis only hands the tracker procedure the ``propose`` call it already
knows: one row for the month's commitments, with the date in ISO. The tracker
checks the confirmed tab, reuses the sheet's area labels and gives the block
to paste.
"""

from __future__ import annotations

from coaching.diagnose.narrative import WeeklyAction

_SELF = {"tu", "tú", "yo"}


def commitment_text(action: WeeklyAction) -> str:
    """The row text: the action, plus who does it when it is not the owner."""
    text = action.action.strip()
    text = text[0].upper() + text[1:]
    if not text.endswith((".", "!", "?")):
        text = f"{text}."
    if action.responsible.strip().lower() not in _SELF:
        text = f"{text} (responsable: {action.responsible.strip()})"
    return text


def tracker_request(action: WeeklyAction, base_path: str) -> dict[str, object]:
    """The tracker ``propose`` call; the agent adds the tab it reads."""
    return {
        "action": "propose",
        "base_path": base_path,
        "table": "commitments",
        "month": action.due.strftime("%Y-%m"),
        "plan": {
            "priorities": [
                {
                    "priority": commitment_text(action),
                    "decision": action.decision,
                    "due": action.due.isoformat(),
                }
            ]
        },
    }
