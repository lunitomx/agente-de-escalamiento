"""coaching.welcome.engine — pure business logic for company onboarding.

No I/O. Accepts company data dict, returns structured profile dict.
"""

from __future__ import annotations

GROWTH_STAGES = {
    "startup": {
        "min_employees": 1,
        "max_employees": 9,
        "label": "Startup",
        "label_es": "Startup",
    },
    "growth": {
        "min_employees": 10,
        "max_employees": 50,
        "label": "Growth",
        "label_es": "Crecimiento",
    },
    "scaleup": {
        "min_employees": 51,
        "max_employees": 250,
        "label": "Scale-Up",
        "label_es": "Escalamiento",
    },
    "enterprise": {
        "min_employees": 251,
        "max_employees": 99999,
        "label": "Enterprise",
        "label_es": "Empresa",
    },
}

REQUIRED_FIELDS = ["name", "industry", "employees"]


def detect_growth_stage(employees: int) -> str:
    for stage_id, bounds in GROWTH_STAGES.items():
        if bounds["min_employees"] <= employees <= bounds["max_employees"]:
            return stage_id
    return "enterprise"


def validate_intake(data: dict) -> list[str]:
    errors = []
    for field in REQUIRED_FIELDS:
        if not data.get(field):
            errors.append(f"Missing required field: {field}")
    employees = data.get("employees")
    if employees is not None:
        if not isinstance(employees, int) or employees < 1:
            errors.append(f"employees must be a positive integer, got: {employees}")
    return errors


def build_profile(data: dict) -> dict:
    employees = data.get("employees", 0)
    growth_stage = data.get("growth_stage") or detect_growth_stage(employees)

    return {
        "company": {
            "name": data.get("name", ""),
            "industry": data.get("industry", ""),
            "employees": employees,
            "growth_stage": growth_stage,
            "revenue": data.get("revenue", ""),
            "years_in_business": data.get("years_in_business", ""),
            "location": data.get("location", ""),
            "description": data.get("description", ""),
        },
        "scores": data.get("scores")
        or {
            "people": None,
            "strategy": None,
            "execution": None,
            "cash": None,
        },
        "focus": data.get("focus") or None,
    }
