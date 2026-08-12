"""Pure logic for the OPSP persist/resume/export module (S47.4).

Keeps the same fields as templates/opsp.md so state <-> markdown is a
straight mapping, and never fabricates a value the user hasn't given.
"""

from __future__ import annotations

from typing import Any

MISSING = "[PENDIENTE]"

SECTIONS = (
    "core_values",
    "purpose",
    "bhag",
    "sandbox",
    "brand_promise",
    "profit_per_x",
    "annual_goals",
    "quarterly_plan",
)


def merge_section(state: dict[str, Any], section: str, data: Any) -> dict[str, Any]:
    """Return a new state with `section` set to `data`. Rejects unknown
    sections so a typo doesn't silently create a dead field."""
    if section not in SECTIONS:
        raise ValueError(
            f"Sección desconocida: {section!r}. Válidas: {', '.join(SECTIONS)}"
        )
    new_state = dict(state)
    new_state[section] = data
    return new_state


def missing_fields(state: dict[str, Any]) -> list[str]:
    """Sections with no saved value yet — never inferred, only absent."""
    return [section for section in SECTIONS if not state.get(section)]
