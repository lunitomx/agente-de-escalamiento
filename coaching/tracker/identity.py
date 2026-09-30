# pyright: strict
"""Find the participant's own tab of the shared tracker (E82 S82.3).

The shared workbook holds the whole group's data. A tab is proposed by its
**name only**, the user always confirms it, and only the confirmed tab's cells
are ever parsed. Other tabs contribute their name and nothing else.
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from coaching.tracker.parser import Grid, parse_connector_text

START_HERE = "start here"
_SHEET_PREFIX = "### Sheet Name:"
_PLACEHOLDER = re.compile(
    r"^(?:name|nombre|participant(?: name)?|participante)\s*\d*$|^#[a-z0-9/]+[!?]?$"
)


def _key(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(folded.lower().split())


def _tokens(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", _key(text)) if token}


def is_placeholder_name(name: str | None) -> bool:
    """True for an empty name, a template placeholder or a formula error."""
    if name is None or not name.strip():
        return True
    return _PLACEHOLDER.match(_key(name)) is not None


class SheetCandidate(BaseModel):
    """A tab that might be the user's; never a final choice."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tab_name: str
    score: int
    business_match: bool = False
    placeholder: bool = False
    needs_confirmation: Literal[True] = True


def _score(tab: set[str], name: set[str]) -> int:
    if not tab or not name:
        return 0
    if tab == name:
        return 3
    if tab <= name or name <= tab:
        return 2
    return 1 if tab & name else 0


def rank_candidates(
    tab_names: list[str], name: str, business: str | None = None
) -> list[SheetCandidate]:
    """Rank tabs by how well their name matches the user's name.

    ``START HERE`` is excluded, placeholder tabs are flagged and never scored,
    and ``business`` only breaks ties between tabs that already match the name.
    """
    wanted = _tokens(name)
    business_tokens = _tokens(business) if business else set[str]()
    ranked: list[tuple[int, int, int, SheetCandidate]] = []
    for index, tab_name in enumerate(tab_names):
        if _key(tab_name) == START_HERE:
            continue
        placeholder = is_placeholder_name(tab_name)
        tab = _tokens(tab_name)
        score = 0 if placeholder else _score(tab, wanted)
        business_match = score > 0 and bool(tab & business_tokens)
        candidate = SheetCandidate(
            tab_name=tab_name,
            score=score,
            business_match=business_match,
            placeholder=placeholder,
        )
        ranked.append((-score, -int(business_match), index, candidate))
    return [candidate for *_, candidate in sorted(ranked, key=lambda r: r[:3])]


def list_tab_names(connector_text: str) -> list[str]:
    """Tab names of the connector rendering; no cell is read."""
    names: list[str] = []
    for line in connector_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(_SHEET_PREFIX):
            tab = stripped[len(_SHEET_PREFIX) :].strip()
            if tab not in names:
                names.append(tab)
    return names


def confirmed_tab_grid(connector_text: str, tab_name: str) -> Grid | None:
    """Grid of the confirmed tab only; other tabs' lines are dropped unread."""
    kept: list[str] = []
    inside = found = False
    for line in connector_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(_SHEET_PREFIX):
            inside = stripped[len(_SHEET_PREFIX) :].strip() == tab_name
            found = found or inside
        if inside:
            kept.append(line)
    if not found:
        return None
    return parse_connector_text("\n".join(kept)).get(tab_name, [])


def parse_pasted_tab(text: str) -> Grid:
    """Grid from a tab copied in Sheets (tab-separated, quoted multi-line cells)."""
    grid: Grid = [
        [cell.strip() or None for cell in row]
        for row in csv.reader(io.StringIO(text), delimiter="\t")
    ]
    while grid and not any(grid[-1]):
        grid.pop()
    return grid


class TrackerLink(BaseModel):
    """Which file and tab are the user's. A reference only, never sheet content."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    file_title: str | None = None
    file_id: str | None = None
    tab_name: str
    participant_confirmed: Literal[True] = True
    confirmed_at: datetime


def link_path(base: Path) -> Path:
    return base / ".escala" / "my-company" / "tracker.yaml"


def save_link(link: TrackerLink, base: Path) -> Path:
    """Persist the confirmed choice under ``.escala/my-company/`` (git-ignored)."""
    path = link_path(base)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            link.model_dump(mode="json"), allow_unicode=True, sort_keys=False
        ),
        encoding="utf-8",
    )
    return path


def load_link(base: Path) -> TrackerLink | None:
    """The remembered choice, or ``None`` if missing or unreadable."""
    try:
        raw: object = yaml.safe_load(link_path(base).read_text(encoding="utf-8"))
        return TrackerLink.model_validate(raw)
    except (OSError, yaml.YAMLError, ValidationError):
        return None


def link_matches(
    link: TrackerLink,
    file_title: str | None,
    file_id: str | None,
    tab_names: list[str],
) -> bool:
    """Reuse the choice only for the same file while the tab still exists."""
    if link.file_id and file_id:
        same_file = link.file_id == file_id
    else:
        same_file = bool(
            link.file_title and file_title and _key(link.file_title) == _key(file_title)
        )
    return same_file and link.tab_name in tab_names
