"""Pure logic for the Function Accountability Chart (FACChart).

Validates organizational accountability:
- Every function has one accountable person.
- No one holds more than 3 functions.
- The CEO (or owner) cannot be accountable for every function.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

MISSING = "[PENDIENTE]"
MAX_FUNCTIONS_PER_PERSON = 3


@dataclass
class Function:
    """A single function in the accountability chart."""

    name: str
    accountable: str
    kpis: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "accountable": self.accountable,
            "kpis": list(self.kpis),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Function":
        return cls(
            name=str(data.get("name", "")),
            accountable=str(data.get("accountable", "")),
            kpis=[str(k) for k in data.get("kpis", []) if k],
        )


@dataclass
class FACChart:
    """A complete Function Accountability Chart."""

    functions: list[Function] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"functions": [f.to_dict() for f in self.functions]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FACChart":
        raw_functions = data.get("functions", []) if isinstance(data, dict) else []
        return cls(
            functions=[
                Function.from_dict(f) for f in raw_functions if isinstance(f, dict)
            ]
        )


def validate(chart: FACChart, ceo_names: list[str] | None = None) -> list[str]:
    """Return a list of validation errors. Empty list means valid."""
    errors: list[str] = []

    if not chart.functions:
        errors.append("El FACChart no tiene funciones definidas.")
        return errors

    for i, func in enumerate(chart.functions, 1):
        if not func.name.strip():
            errors.append(f"Función #{i}: falta el nombre.")
        if not func.accountable.strip():
            errors.append(f"Función '{func.name or i}': falta la persona accountable.")
        if len(func.kpis) == 0:
            errors.append(f"Función '{func.name or i}': debe tener al menos un KPI.")

    counts = Counter(
        f.accountable.strip() for f in chart.functions if f.accountable.strip()
    )
    for person, count in counts.items():
        if count > MAX_FUNCTIONS_PER_PERSON:
            errors.append(
                f"{person} es accountable de {count} funciones; el máximo recomendado es {MAX_FUNCTIONS_PER_PERSON}."
            )

    if len(chart.functions) > 1 and len(counts) == 1:
        only_person = next(iter(counts))
        errors.append(
            f"{only_person} es accountable de todas las funciones. "
            "Delega al menos una función."
        )

    # CEO check: if a known CEO name is accountable for all but one or fewer,
    # flag it as a warning. We treat common CEO/owner titles as case-insensitive.
    if ceo_names:
        normalized_ceos = {name.lower().strip() for name in ceo_names if name.strip()}
    else:
        normalized_ceos = {"ceo", "fundador", "owner", "dueño", "presidente"}

    for person, count in counts.items():
        if person.lower() in normalized_ceos and count >= len(chart.functions):
            errors.append(
                f"{person} (CEO/dueño) no puede ser accountable de todo. "
                "El CEO debe delegar funciones operativas."
            )

    return errors


def score(chart: FACChart) -> dict[str, Any]:
    """Return completeness and health scores for the chart."""
    if not chart.functions:
        return {
            "completeness": 0,
            "health": 0,
            "overall": 0,
            "function_count": 0,
        }

    total = len(chart.functions)
    complete = sum(
        1
        for f in chart.functions
        if f.name.strip() and f.accountable.strip() and f.kpis
    )
    completeness = round((complete / total) * 100)

    errors = validate(chart)
    # Health starts at 100 and loses points for structural errors.
    # Each overloaded person or CEO-everything error costs 25 points.
    structural_errors = [
        e for e in errors if "máximo recomendado" in e or "delega" in e.lower()
    ]
    health = max(0, 100 - len(structural_errors) * 25)

    overall = round(completeness * 0.6 + health * 0.4)

    return {
        "completeness": completeness,
        "health": health,
        "overall": overall,
        "function_count": total,
    }
