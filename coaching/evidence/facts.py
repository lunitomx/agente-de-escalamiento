"""Fact persistence with provenance for multi-source onboarding."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from coaching.core import ensure_dir, read_yaml, require_local_ref, write_yaml

Confidence = Literal["high", "medium", "low"]
Decision = Literal["people", "strategy", "execution", "cash"]


class Fact(BaseModel):
    """A single traceable business fact captured during onboarding."""

    fact_id: str = Field(default_factory=lambda: str(uuid4()))
    metric_definition: str = Field(..., min_length=1)
    period: str = Field(..., min_length=1)
    basis_date: str | None = None
    source: str = Field(..., min_length=1)
    confidence: Confidence
    comparable: bool = True
    value: Any
    unit: str | None = None
    decision: Decision | None = None
    notes: str | None = None
    created_at: str = Field(
        default_factory=lambda: datetime.datetime.now(
            tz=datetime.timezone.utc
        ).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.datetime.now(
            tz=datetime.timezone.utc
        ).isoformat()
    )

    @field_validator("source")
    @classmethod
    def _source_must_not_escape_local_boundary(cls, value: str) -> str:
        """Same locality rule as DiagnosticEvidence.source_ref (E55 D4)."""
        return require_local_ref(value, "source")


def _facts_path(base_path: Path) -> Path:
    return base_path / ".escala" / "agent" / "memory" / "facts.yaml"


def _load_facts_data(base_path: Path) -> dict[str, Any]:
    return read_yaml(_facts_path(base_path))


def save_fact(base_path: Path, fact: Fact) -> Path:
    """Persist a fact, updating it if the same fact_id already exists."""
    path = _facts_path(base_path)
    ensure_dir(path.parent)
    data = _load_facts_data(base_path)
    facts = data.get("facts", [])
    facts_by_id = {f["fact_id"]: f for f in facts}

    fact.updated_at = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    facts_by_id[fact.fact_id] = fact.model_dump(mode="json")

    data["facts"] = list(facts_by_id.values())
    write_yaml(path, data)
    return path


def load_facts(base_path: Path, decision: Decision | None = None) -> list[Fact]:
    """Load persisted facts, optionally filtered by decision."""
    data = _load_facts_data(base_path)
    facts = data.get("facts", [])
    if decision:
        facts = [f for f in facts if f.get("decision") == decision]
    return [Fact.model_validate(f) for f in facts]


def get_fact(base_path: Path, fact_id: str) -> Fact | None:
    """Retrieve a single fact by id, or None if absent."""
    for fact in load_facts(base_path):
        if fact.fact_id == fact_id:
            return fact
    return None


def delete_fact(base_path: Path, fact_id: str) -> bool:
    """Remove a fact by id. Returns True if it existed."""
    path = _facts_path(base_path)
    data = _load_facts_data(base_path)
    facts = data.get("facts", [])
    remaining = [f for f in facts if f.get("fact_id") != fact_id]
    if len(remaining) == len(facts):
        return False
    data["facts"] = remaining
    write_yaml(path, data)
    return True
