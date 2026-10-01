# pyright: strict
"""Memory of the journey question (E84 S84.1, blocker N2).

A corrupt file never turns into "never asked": it counts as declined on the
day it last changed (so a lost "no" never produces nagging), and it is never
rewritten silently: the next ``record_ask`` moves it to ``asks.yaml.bak``
(``.bak.2``... if one exists) before writing.

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


class AsksFile(BaseModel):
    """What ``asks.yaml`` holds; ``corrupt_on`` is set when it is unreadable."""

    model_config = ConfigDict(extra="forbid")

    records: list[AskRecord]
    corrupt_on: date | None = None


def asks_path(base: Path) -> Path:
    """Where the ask memory lives, relative to the project root ``base``."""
    return base / JOURNEY_DIR / ASKS_NAME


def read_asks(base: Path) -> AsksFile:
    """Recorded asks; a missing file means "never asked".

    An unreadable or invalid file, or a mapping without ``asks`` (YAML such as
    ``"::: x ["`` parses as a dict), keeps its last-change date in
    ``corrupt_on``.
    """
    path = asks_path(base)
    if not path.exists():
        return AsksFile(records=[])
    try:
        raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "asks" in raw:
            items = cast(dict[str, object], raw)["asks"]
            return AsksFile(records=_RECORDS.validate_python(items))
    except (OSError, yaml.YAMLError, ValidationError):
        pass
    return AsksFile(records=[], corrupt_on=_changed_on(path))


def _changed_on(path: Path) -> date:
    try:
        return date.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return date.today()


def load_asks(base: Path) -> list[AskRecord]:
    """The readable records only (empty for a missing or corrupt file)."""
    return read_asks(base).records


def _backup(path: Path) -> Path:
    """Move a corrupt file aside without overwriting an earlier backup."""
    target = path.with_name(f"{path.name}.bak")
    number = 2
    while target.exists():
        target = path.with_name(f"{path.name}.bak.{number}")
        number += 1
    path.replace(target)
    return target


def record_ask(base: Path, record: AskRecord) -> tuple[Path, Path | None]:
    """Append one ask and rewrite the file atomically.

    Returns the file and, when the old one was corrupt, where it was kept.
    """
    memory = read_asks(base)
    path = asks_path(base)
    backup = _backup(path) if memory.corrupt_on is not None else None
    records = [*memory.records, record]
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
    return path, backup


def last_declined_on(records: list[AskRecord]) -> date | None:
    """Latest "no" or "después"; a "sí" never silences the question."""
    declined = [item.asked_on for item in records if item.outcome != "si"]
    return max(declined, default=None)


def declined_on(base: Path) -> date | None:
    """Latest decline on disk; a corrupt file counts as declined on its change."""
    memory = read_asks(base)
    days = [
        day
        for day in (last_declined_on(memory.records), memory.corrupt_on)
        if day is not None
    ]
    return max(days, default=None)
