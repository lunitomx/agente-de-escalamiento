"""Pure logic for the OPSP persist/resume/export module (S47.4, S50.4.1).

Keeps the same fields as templates/opsp.md so state <-> markdown is a
straight mapping, and never fabricates a value the user hasn't given.

S50.4.1 adds:
- per-section schemas with required keys
- completeness scoring
- next-missing-section guidance
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

# Expected keys per section. A section is "complete" when all required keys
# are present and non-empty.
SECTION_SCHEMAS: dict[str, dict[str, type | tuple[type, ...]]] = {
    "core_values": {"values": list},
    "purpose": {"statement": str},
    "bhag": {
        "statement": str,
        "target_date": str,
    },
    "sandbox": {
        "revenue_target": (str, int, float),
        "profit_target": (str, int, float),
        "market_geography": str,
        "customer_segment": str,
        "product_focus": str,
    },
    "brand_promise": {
        "promise": str,
        "kpi": str,
    },
    "profit_per_x": {
        "x": str,
        "amount": (str, int, float),
    },
    "annual_goals": {
        "year": (str, int),
        "revenue_target": (str, int, float),
        "profit_target": (str, int, float),
        "priorities": list,
    },
    "quarterly_plan": {
        "quarter": str,
        "critical_number": str,
        "priorities": list,
        "theme": dict,
    },
}


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


def _is_non_empty(value: Any) -> bool:
    """Return True if value is present and non-empty."""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    if isinstance(value, list) and len(value) == 0:
        return False
    if isinstance(value, dict) and len(value) == 0:
        return False
    return True


def _has_required_type(value: Any, expected: type | tuple[type, ...]) -> bool:
    """Check value type against schema expectation."""
    if isinstance(expected, tuple):
        return any(isinstance(value, t) for t in expected)
    return isinstance(value, expected)


def section_completeness(state: dict[str, Any], section: str) -> dict[str, Any]:
    """Return completion status for a single section."""
    if section not in SECTIONS:
        raise ValueError(f"Sección desconocida: {section!r}")

    data = state.get(section)
    if not _is_non_empty(data):
        return {"complete": False, "missing_keys": ["section"], "score": 0.0}

    schema = SECTION_SCHEMAS.get(section, {})
    if not schema:
        return {"complete": True, "missing_keys": [], "score": 1.0}

    # For scalar sections stored as a string (e.g., purpose="..."), adapt.
    if isinstance(data, str):
        data = {"statement": data}

    missing_keys = []
    for key, expected_type in schema.items():
        value = data.get(key) if isinstance(data, dict) else None
        if not _is_non_empty(value):
            missing_keys.append(key)
        elif not _has_required_type(value, expected_type):
            missing_keys.append(key)

    total = len(schema)
    filled = total - len(missing_keys)
    score = filled / total if total > 0 else 1.0
    return {
        "complete": len(missing_keys) == 0,
        "missing_keys": missing_keys,
        "score": round(score, 2),
    }


def completeness_score(state: dict[str, Any]) -> dict[str, Any]:
    """Overall OPSP completeness score and per-section breakdown."""
    breakdown = {}
    total_score = 0.0
    for section in SECTIONS:
        status = section_completeness(state, section)
        breakdown[section] = status
        total_score += status["score"]

    overall = round(total_score / len(SECTIONS), 2) if SECTIONS else 1.0
    return {
        "overall": overall,
        "percent": int(overall * 100),
        "sections": breakdown,
        "complete_sections": [s for s, st in breakdown.items() if st["complete"]],
        "incomplete_sections": [s for s, st in breakdown.items() if not st["complete"]],
    }


def next_missing_section(state: dict[str, Any]) -> str | None:
    """Return the first incomplete section in canonical OPSP order."""
    for section in SECTIONS:
        status = section_completeness(state, section)
        if not status["complete"]:
            return section
    return None
