"""Strict typed contracts for local governance identity and closure truth."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


_DISPOSITION_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*(?:/[a-z][a-z0-9-]*)?$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ClosureDisposition(_StrictModel):
    """One data-owned closure posture and its executable semantics."""

    id: str = Field(min_length=3, max_length=128)
    terminal: bool
    completed: bool
    reviewable: bool
    activation_eligible: bool

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if _DISPOSITION_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe closure disposition ID")
        return value

    @model_validator(mode="after")
    def validate_semantics(self) -> ClosureDisposition:
        if self.completed and not self.terminal:
            raise ValueError("completed dispositions must be terminal")
        if self.completed and not self.reviewable:
            raise ValueError("completed dispositions must be reviewable")
        if self.completed and self.activation_eligible:
            raise ValueError("completed dispositions cannot be activation eligible")
        if self.activation_eligible and self.terminal:
            raise ValueError("activation-eligible dispositions cannot be terminal")
        if self.activation_eligible and not self.reviewable:
            raise ValueError("activation-eligible dispositions must be reviewable")
        return self


class ClosureDispositionPolicy(_StrictModel):
    """Versioned source of truth for accepted closure dispositions."""

    schema_version: Literal[1]
    dispositions: list[ClosureDisposition] = Field(min_length=1)

    @field_validator("dispositions")
    @classmethod
    def validate_dispositions(
        cls,
        values: list[ClosureDisposition],
    ) -> list[ClosureDisposition]:
        identifiers = [item.id for item in values]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("duplicate closure disposition IDs")
        return sorted(values, key=lambda item: item.id)


ClosureDisposition.model_rebuild()
ClosureDispositionPolicy.model_rebuild()


def load_closure_disposition_policy(policy_path: Path) -> ClosureDispositionPolicy:
    """Load and strictly validate a local closure-disposition policy."""
    data: Any = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    return ClosureDispositionPolicy.model_validate(data)


def closure_disposition_policy_hash(policy: ClosureDispositionPolicy) -> str:
    """Return a stable SHA-256 for normalized closure-policy semantics."""
    payload = json.dumps(
        policy.model_dump(mode="json"),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
