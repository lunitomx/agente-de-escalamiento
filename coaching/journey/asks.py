# pyright: strict
"""Memory of the journey question (E84 S84.1, blocker N2).

``.escala/my-company/journey/asks.yaml`` (ignored by git) keeps, per ask, the
date, the owner's answer (``si`` / ``despues`` / ``no``) and the trigger code.
Never the owner's words: the reason is a code, so the file carries no company
data.
"""

from __future__ import annotations

import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Literal, cast

import yaml
from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from coaching.journey.triggers import TriggerCode

AskOutcome = Literal["si", "despues", "no"]
JOURNEY_DIR = Path(".escala") / "my-company" / "journey"
ASKS_NAME = "asks.yaml"


class AskRecord(BaseModel):
    """One time ESCALA asked for the journey, and what the owner answered."""

    model_config = ConfigDict(extra="forbid")

    asked_on: date
    outcome: AskOutcome
    reason: TriggerCode


_RECORDS = TypeAdapter(list[AskRecord])


def asks_path(base: Path) -> Path:
    """Where the ask memory lives, relative to the project root ``base``."""
    return base / JOURNEY_DIR / ASKS_NAME


def load_asks(base: Path) -> list[AskRecord]:
    """Recorded asks; a missing or unreadable file means "never asked"."""
    path = asks_path(base)
    if not path.exists():
        return []
    try:
        raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return []
        return _RECORDS.validate_python(cast(dict[str, object], raw).get("asks", []))
    except (OSError, yaml.YAMLError, ValidationError):
        return []


def record_ask(base: Path, record: AskRecord) -> Path:
    """Append one ask and rewrite the file atomically."""
    records = [*load_asks(base), record]
    path = asks_path(base)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(
        {"asks": [item.model_dump(mode="json") for item in records]},
        allow_unicode=True,
        sort_keys=False,
    )
    handle, tmp = tempfile.mkstemp(dir=path.parent, prefix=".asks-", suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(text)
    Path(tmp).replace(path)
    return path


def last_declined_on(records: list[AskRecord]) -> date | None:
    """Latest "no" or "después"; a "sí" never silences the question."""
    declined = [item.asked_on for item in records if item.outcome != "si"]
    return max(declined, default=None)
