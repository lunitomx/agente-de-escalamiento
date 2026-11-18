"""E88 · Cobertura del workbook Strategy 2026 y orden del Strategy Day (S88.6).

Vigila el mapa `tests/fixtures/workbook-2026-coverage.yaml`: 24 de 24 páginas
(hoja o `no_tool` con razón), los 10 ejercicios en el orden del taller y que la
cadena `next_sheet` de las hojas siga ese orden. Reusa las reglas de E87.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from coaching.worksheet import find_worksheet, load_worksheet_content, name_es
from coaching.worksheet.guide import parse_guide
from tests.test_e87_workbook_coverage import (
    build_node_index,
    build_registry_index,
    check_coverage,
)

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "conocimiento"
REGISTRY = KNOWLEDGE / "registry" / "worksheets.yaml"
# Fuera del contenido público: tests/ es not_eligible en governance/public-boundary.yaml.
COVERAGE_FILE = ROOT / "tests" / "fixtures" / "workbook-2026-coverage.yaml"
FIRST_SHEET = "worksheet-swt"


def load_coverage() -> dict[str, Any]:
    data: Any = yaml.safe_load(COVERAGE_FILE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def exercise_sheets(coverage: dict[str, Any]) -> list[str]:
    """Hojas de `exercises` en orden, sin repetir (AI Setup vive en swt)."""
    sheets: list[str] = []
    for exercise in coverage["exercises"]:
        sheet = str(exercise["sheet"])
        if sheet not in sheets:
            sheets.append(sheet)
    return sheets


def next_sheet_of(sheet_id: str) -> tuple[str, str] | None:
    """`(id, title)` del `next_sheet` del último paso de la hoja, o None."""
    worksheet = find_worksheet(sheet_id)
    assert worksheet is not None, sheet_id
    guide = parse_guide(load_worksheet_content(worksheet))
    assert guide is not None, sheet_id
    bridge = guide.guide.steps[-1].next_sheet
    return (bridge.id, bridge.title) if bridge is not None else None


def chain_from(first: str) -> list[str]:
    """Hojas que recorre el dueño siguiendo `next_sheet` desde `first`."""
    chain = [first]
    while (bridge := next_sheet_of(chain[-1])) is not None:
        assert bridge[0] not in chain, f"ciclo en {bridge[0]}"
        chain.append(bridge[0])
    return chain


def test_real_map_covers_24_pages() -> None:
    coverage = load_coverage()
    assert coverage["workbook"] == "strategy-2026"
    assert coverage["total_pages"] == 24
    assert [p["page"] for p in coverage["pages"]] == list(range(1, 25))
    assert coverage["pending"] == []
    errors = check_coverage(
        coverage,
        build_node_index(KNOWLEDGE),
        build_registry_index(REGISTRY),
        frozen_pending=frozenset(),
    )
    assert errors == []


def test_every_page_has_nodes_or_a_reason() -> None:
    for page in load_coverage()["pages"]:
        if page["class"] == "tool":
            assert page["nodes"], page["page"]
        else:
            assert page["class"] == "no_tool", page["page"]
            assert str(page["reason"]).strip(), page["page"]


def test_ten_exercises_in_workshop_order() -> None:
    exercises = load_coverage()["exercises"]
    assert [e["n"] for e in exercises] == list(range(1, 11))
    assert exercise_sheets(load_coverage()) == [
        "worksheet-swt",
        "worksheet-differentiating-activities",
        "worksheet-core-purpose",
        "worksheet-bhag",
        "worksheet-vivid-vision",
        "worksheet-fanocracy",
        "worksheet-life-purpose",
        "worksheet-vision-summary",
    ]


def test_every_exercise_sheet_is_mapped_to_a_page() -> None:
    mapped = {
        node for page in load_coverage()["pages"] for node in page.get("nodes") or []
    }
    assert set(exercise_sheets(load_coverage())) <= mapped


def test_next_sheet_chain_follows_the_exercises() -> None:
    assert chain_from(FIRST_SHEET) == exercise_sheets(load_coverage())


def test_next_sheet_titles_are_the_registry_names() -> None:
    sheets = exercise_sheets(load_coverage())
    for current, following in zip(sheets, sheets[1:]):
        bridge = next_sheet_of(current)
        assert bridge is not None, current
        worksheet = find_worksheet(following)
        assert worksheet is not None, following
        assert bridge == (following, name_es(worksheet)), current
