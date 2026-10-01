# pyright: strict
"""What the owner reads when the diagnosis closes (S86.5, plain Spanish).

The closing is one message: the main constraint, one action for this week,
who does it, the date in words and, once, the offer to note it in the group
sheet. Dates stay ISO in the data; only this text spells them out.
"""

from __future__ import annotations

from datetime import date

from coaching.tracker.proposal import MONTHS

WEEKDAYS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")

# With the owner's tab already confirmed (E82): one yes/no question.
SHEET_OFFER = "¿Lo anoto como compromiso en tu hoja?"
# Without a confirmed tab: offered once; "después" is never asked again (E84).
SHEET_OFFER_NO_TAB = (
    "¿Lo anoto como compromiso en tu hoja del grupo? Primero buscamos juntos "
    "tu pestaña. Si prefieres, lo vemos después."
)


def owner_date(day: date) -> str:
    """``2026-10-09`` → ``viernes 9 de octubre``."""
    return f"{WEEKDAYS[day.weekday()]} {day.day} de {MONTHS[day.month - 1]}"


def _sentence(text: str) -> str:
    text = text.strip()
    return text if text.endswith((".", "!", "?")) else f"{text}."


def closing_message(
    constraint: str,
    action: str,
    responsible: str,
    due: date,
    offer: str | None,
) -> str:
    """The last message of the diagnosis."""
    parts = [
        _sentence(constraint),
        f"Esta semana: {_sentence(action)}",
        f"Responsable: {_sentence(responsible)}",
        f"Fecha: {owner_date(due)}.",
    ]
    if offer:
        parts.append(offer)
    return " ".join(parts)
