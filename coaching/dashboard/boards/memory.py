# pyright: strict
"""Memory of the owner's board decisions (E84 S84.3, absorbed from E73).

``.escala/my-company/tableros/index.yaml`` (ignored by git) keeps, per
decision, the date, the catalogue board id, the outcome (``construir`` /
``esperar`` / ``no``) and, for ``esperar``, the date the owner gave. Never the
owner's words. A board declined or postponed is not proposed again for 30 days.

A corrupt file never turns into nagging: every catalogue board counts as
declined on the day it last changed, and the next write first moves it to
``index.yaml.bak`` (``.bak.2``... if one exists).
"""

from __future__ import annotations

import os
import tempfile
from datetime import date
from pathlib import Path
from typing import cast

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)

from coaching.dashboard.boards.models import OptionCode
from coaching.dashboard.boards.patterns import PATTERNS

BOARDS_DIR = Path(".escala") / "my-company" / "tableros"
INDEX_NAME = "index.yaml"


class BoardDecision(BaseModel):
    """What the owner decided about one proposed board."""

    model_config = ConfigDict(extra="forbid")

    decided_on: date
    board_id: str
    outcome: OptionCode
    review_on: date | None = None

    @field_validator("board_id")
    @classmethod
    def _known_board(cls, value: str) -> str:
        if value not in PATTERNS:
            raise ValueError("unknown_board")
        return value

    @model_validator(mode="after")
    def _waiting_has_a_date(self) -> BoardDecision:
        if self.outcome == "esperar" and self.review_on is None:
            raise ValueError("esperar_requires_review_on")
        return self


_RECORDS = TypeAdapter(list[BoardDecision])


class DecisionsFile(BaseModel):
    """What ``index.yaml`` holds; ``corrupt_on`` is set when it is unreadable."""

    model_config = ConfigDict(extra="forbid")

    records: list[BoardDecision]
    corrupt_on: date | None = None


def index_path(base: Path) -> Path:
    """Where the decision memory lives, relative to the project root ``base``."""
    return base / BOARDS_DIR / INDEX_NAME


def _changed_on(path: Path) -> date:
    try:
        return date.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return date.today()


def read_decisions(base: Path) -> DecisionsFile:
    """Recorded decisions; a missing file means none."""
    path = index_path(base)
    if not path.exists():
        return DecisionsFile(records=[])
    try:
        raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "decisions" in raw:
            items = cast(dict[str, object], raw)["decisions"]
            return DecisionsFile(records=_RECORDS.validate_python(items))
    except (OSError, yaml.YAMLError, ValidationError):
        pass
    return DecisionsFile(records=[], corrupt_on=_changed_on(path))


def _backup(path: Path) -> Path:
    target = path.with_name(f"{path.name}.bak")
    number = 2
    while target.exists():
        target = path.with_name(f"{path.name}.bak.{number}")
        number += 1
    path.replace(target)
    return target


def record_decision(base: Path, decision: BoardDecision) -> tuple[Path, Path | None]:
    """Append one decision atomically; returns the file and any corrupt backup."""
    memory = read_decisions(base)
    path = index_path(base)
    backup = _backup(path) if memory.corrupt_on is not None else None
    records = [*memory.records, decision]
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(
        {"decisions": [item.model_dump(mode="json") for item in records]},
        allow_unicode=True,
        sort_keys=False,
    )
    handle, tmp = tempfile.mkstemp(dir=path.parent, prefix=".index-", suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(text)
    Path(tmp).replace(path)
    return path, backup


def declined_boards(base: Path) -> dict[str, date]:
    """Latest "esperar" or "no" per board; a corrupt file declines them all."""
    memory = read_decisions(base)
    if memory.corrupt_on is not None:
        return dict.fromkeys(PATTERNS, memory.corrupt_on)
    declined: dict[str, date] = {}
    for item in memory.records:
        if item.outcome != "construir":
            previous = declined.get(item.board_id)
            if previous is None or item.decided_on > previous:
                declined[item.board_id] = item.decided_on
    return declined
