"""Tests for finding the participant's own tab without reading others (S82.3).

All fixtures are synthetic. Tabs are chosen by tab name only; cells of a tab
are read only after the user confirms it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from coaching.tracker.identity import (
    TrackerLink,
    confirmed_tab_grid,
    is_placeholder_name,
    link_matches,
    list_tab_names,
    load_link,
    parse_pasted_tab,
    rank_candidates,
    save_link,
)

_WORKBOOK = """\
### Sheet Name: START HERE
### Table Range: A1:B2
| | |
|---|---|
| Group | Demo |
| Phone | 555 |

### Sheet Name: Ana
### Table Range: A1:C1
| | | |
|---|---|---|
| Participant Name | | Ana Demo |

### Sheet Name: Beto
### Table Range: A1:C1
| | | |
|---|---|---|
| Participant Name | | Beto Otro |
"""


@pytest.mark.parametrize(
    "name",
    [
        None,
        "",
        "   ",
        "Name 6",
        "name6",
        "Participant Name",
        "#REF!",
        "#N/A",
        "Nombre 3",
    ],
)
def test_placeholder_names_are_detected(name: str | None) -> None:
    assert is_placeholder_name(name)


@pytest.mark.parametrize("name", ["Eduardo", "Ana Demo", "Nameless Co"])
def test_real_names_are_not_placeholders(name: str) -> None:
    assert not is_placeholder_name(name)


def test_candidates_match_tab_name_ignoring_accents_and_case() -> None:
    ranked = rank_candidates(
        ["START HERE", "Paris", "EDUARDO", "Sebas"], "Eduardo Muñoz"
    )

    assert ranked[0].tab_name == "EDUARDO"
    assert ranked[0].score > 0
    assert all(c.score == 0 for c in ranked[1:])


def test_accented_tab_matches_unaccented_name() -> None:
    ranked = rank_candidates(["José", "Luis"], "jose")

    assert ranked[0].tab_name == "José"


def test_start_here_is_never_a_candidate() -> None:
    ranked = rank_candidates(["START HERE", "Start here ", "Ana"], "Start Here")

    assert [c.tab_name for c in ranked] == ["Ana"]


def test_every_candidate_needs_confirmation() -> None:
    ranked = rank_candidates(["Ana", "Beto"], "Ana")

    assert all(c.needs_confirmation for c in ranked)


def test_placeholder_tab_is_flagged_and_never_scored() -> None:
    ranked = rank_candidates(["Name 6", "Ana"], "Name 6")

    placeholder = next(c for c in ranked if c.tab_name == "Name 6")
    assert placeholder.placeholder
    assert placeholder.score == 0


def test_business_only_breaks_ties() -> None:
    tabs = ["Ana - Panadería", "Ana - Taller", "Beto - Taller"]

    ranked = rank_candidates(tabs, "Ana", business="Taller Demo")

    assert ranked[0].tab_name == "Ana - Taller"
    assert ranked[0].business_match
    beto = next(c for c in ranked if c.tab_name == "Beto - Taller")
    assert beto.score == 0  # business alone never makes a tab a candidate


def test_tab_names_are_listed_without_reading_cells() -> None:
    assert list_tab_names(_WORKBOOK) == ["START HERE", "Ana", "Beto"]


def test_confirmed_tab_grid_keeps_only_that_tab() -> None:
    grid = confirmed_tab_grid(_WORKBOOK, "Ana")

    assert grid is not None
    flat = " ".join(str(cell) for row in grid for cell in row)
    assert "Ana Demo" in flat
    assert "Beto Otro" not in flat
    assert "555" not in flat


def test_confirmed_tab_grid_is_none_for_unknown_tab() -> None:
    assert confirmed_tab_grid(_WORKBOOK, "Carla") is None


def test_pasted_tab_is_split_by_tabs_and_lines() -> None:
    text = 'Participant Name\t\tAna Demo\r\nMonthly Commitments\n\tCash\t"Cobrar\ncartera"\t\n\n'

    grid = parse_pasted_tab(text)

    assert grid[0] == ["Participant Name", None, "Ana Demo"]
    assert grid[1] == ["Monthly Commitments"]
    assert grid[2] == [None, "Cash", "Cobrar\ncartera", None]
    assert len(grid) == 3


def _link(**overrides: object) -> TrackerLink:
    data: dict[str, object] = {
        "file_title": "Accountability Group Goal Tracker",
        "file_id": "file-123",
        "tab_name": "Ana",
        "confirmed_at": datetime(2026, 9, 30, tzinfo=timezone.utc),
    }
    data.update(overrides)
    return TrackerLink.model_validate(data)


def test_link_round_trips_under_company_folder(tmp_path: Path) -> None:
    path = save_link(_link(), tmp_path)

    assert path == tmp_path / ".escala" / "my-company" / "tracker.yaml"
    assert load_link(tmp_path) == _link()


def test_missing_or_broken_link_loads_as_none(tmp_path: Path) -> None:
    assert load_link(tmp_path) is None
    path = tmp_path / ".escala" / "my-company" / "tracker.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("tab_name: [", encoding="utf-8")
    assert load_link(tmp_path) is None


def test_link_is_reused_only_for_same_file_and_existing_tab() -> None:
    link = _link()

    assert link_matches(link, "Accountability Group Goal Tracker", "file-123", ["Ana"])
    assert not link_matches(link, "Otro archivo", "file-999", ["Ana"])
    assert not link_matches(
        link, "Accountability Group Goal Tracker", "file-123", ["Beto"]
    )


def test_link_without_file_id_matches_by_title() -> None:
    link = _link(file_id=None)

    assert link_matches(link, "accountability group goal tracker", None, ["Ana"])
