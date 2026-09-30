"""Every live epic must be traceable to its own Jira epic.

E56–E81 were planned as files without /rai-epic-start, so none reached Jira,
and E55 cited keys that belonged to E48. This guard fails as soon as an open
or planned epic scope lacks a real ESCALA key or reuses another epic's key.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EPICS = ROOT / "work" / "epics"
LIVE_STATUSES = {"planned", "in_progress"}
KEY_PATTERN = re.compile(r"^ESCALA-\d+$")


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    block = text.split("---\n", 2)[1]
    fields: dict[str, str] = {}
    for line in block.splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "-")):
            fields[key.strip()] = value.strip().strip('"')
    return fields


def _epic_scopes() -> list[tuple[Path, dict[str, str]]]:
    return [(scope, _frontmatter(scope)) for scope in sorted(EPICS.glob("e*/scope.md"))]


@pytest.mark.parametrize(
    ("scope", "fields"),
    [(s, f) for s, f in _epic_scopes() if f.get("status") in LIVE_STATUSES],
    ids=lambda value: value.parent.name if isinstance(value, Path) else "",
)
def test_live_epic_has_jira_key(scope: Path, fields: dict[str, str]) -> None:
    assert KEY_PATTERN.match(fields.get("jira_key", "")), (
        f"{scope.relative_to(ROOT)} is {fields['status']} without a Jira key; "
        "create it with `rai backlog create ... -t Epic --adapter jira`"
    )


def test_epic_jira_keys_are_unique() -> None:
    owners: dict[str, list[str]] = {}
    for scope, fields in _epic_scopes():
        key = fields.get("jira_key", "")
        if key:
            owners.setdefault(key, []).append(scope.parent.name)
    duplicated = {key: epics for key, epics in owners.items() if len(epics) > 1}
    assert duplicated == {}
