"""S87.7: the owner finds and starts a sheet by its Spanish name, in Spanish."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from coaching.core import read_yaml
from coaching.worksheet import engine, find_worksheet, registry_path, run


def _registry() -> list[dict[str, Any]]:
    return list(read_yaml(registry_path())["worksheets"])


@pytest.mark.parametrize(
    ("query", "sheet_id"),
    [
        ("promesa de marca", "worksheet-brand-promise"),
        ("Promesa De Marca", "worksheet-brand-promise"),
        ("cliente central", "worksheet-core-customer"),
        ("Lienzo del modelo de negocio", "worksheet-bmc"),
        ("plan estrategico de una pagina", "worksheet-opsp"),
        ("Plan estratégico de una página", "worksheet-opsp"),
        ("worksheet-brand-promise", "worksheet-brand-promise"),
        ("Brand Promise", "worksheet-brand-promise"),
    ],
)
def test_find_by_spanish_name_without_accents(query: str, sheet_id: str) -> None:
    found = engine.find_worksheet(_registry(), query)
    assert found is not None and found["id"] == sheet_id
    via_root = find_worksheet(query)
    assert via_root is not None and via_root["id"] == sheet_id


def test_exact_id_wins_over_a_name_match() -> None:
    registry = [
        {"id": "worksheet-b", "name": "worksheet-a extra", "name_es": "B"},
        {"id": "worksheet-a", "name": "A", "name_es": "A"},
    ]
    found = engine.find_worksheet(registry, "worksheet-a")
    assert found is not None and found["id"] == "worksheet-a"


def test_empty_or_unknown_query_finds_nothing() -> None:
    assert engine.find_worksheet(_registry(), "") is None
    assert engine.find_worksheet(_registry(), "no existe esta hoja") is None


def test_every_registry_entry_has_short_spanish_name_and_time() -> None:
    for entry in _registry():
        assert str(entry.get("name_es", "")).strip(), entry["id"]
        assert str(entry.get("time_es", "")).strip(), entry["id"]
        assert "Hoja" not in entry["name_es"], entry["id"]


def test_step_one_is_in_spanish(tmp_path: Path) -> None:
    result = run(
        {
            "action": "start",
            "worksheet_name": "promesa de marca",
            "base_path": str(tmp_path),
        }
    )
    assert result["errors"] == []
    assert result["artifacts"]["worksheet"]["id"] == "worksheet-brand-promise"
    out = result["output"]
    assert out.startswith("## Promesa de marca\n")
    assert "**Decisión:** Estrategia" in out
    assert "**Dificultad:** Intermedio" in out
    assert "**Tiempo estimado:** 1-2 horas" in out
    assert "Prerrequisitos completados: Cliente central" in out
    assert "worksheet-core-customer" not in out


def test_list_is_in_spanish(tmp_path: Path) -> None:
    out = run({"action": "list", "base_path": str(tmp_path)})["output"]
    assert "| Promesa de marca (`worksheet-brand-promise`) | Estrategia |" in out
    assert "| Intermedio | 1-2 horas |" in out
    assert "Brand Promise Worksheet" not in out


def test_client_registry_without_spanish_fields_falls_back(tmp_path: Path) -> None:
    registry = [{"id": "client-ws", "name": "Client Worksheet", "decision": "cash"}]
    found = engine.find_worksheet(registry, "client worksheet")
    assert found is not None and found["id"] == "client-ws"


# --- retry 1 (C1, C2): the whole step-1 header is Spanish and agrees --------

_IDS = [str(entry["id"]) for entry in _registry()]
_ENGLISH_MARKERS = (" the ", " and ", "worksheet", "template")


def test_every_registry_entry_has_a_spanish_summary() -> None:
    for entry in _registry():
        summary = str(entry.get("summary_es", "")).strip()
        assert summary, entry["id"]
        lowered = f" {summary.lower()} "
        for marker in _ENGLISH_MARKERS:
            assert marker not in lowered, (entry["id"], marker)


@pytest.mark.parametrize("sheet_id", _IDS)
def test_step_one_header_uses_the_spanish_summary_and_its_own_time(
    sheet_id: str, tmp_path: Path
) -> None:
    entry = next(e for e in _registry() if e["id"] == sheet_id)
    result = run(
        {"action": "start", "worksheet_name": sheet_id, "base_path": str(tmp_path)}
    )
    assert result["errors"] == []
    out = result["output"]
    assert str(entry["summary_es"]).strip() in out
    assert f"- [ ] {entry['time_es']} sin interrupciones" in out
    assert out.count(" sin interrupciones") == 1


def test_canvas_step_one_does_not_contradict_its_time(tmp_path: Path) -> None:
    out = run(
        {
            "action": "start",
            "worksheet_name": "lienzo de estrategia",
            "base_path": str(tmp_path),
        }
    )["output"]
    assert "**Tiempo estimado:** 30-60 minutos" in out
    assert "1-2 horas" not in out


def test_list_title_and_column_are_spanish(tmp_path: Path) -> None:
    out = run({"action": "list", "base_path": str(tmp_path)})["output"]
    assert out.startswith("## Hojas disponibles\n")
    assert "| Hoja | Decisión | Dificultad | Tiempo | Estado |" in out
    assert "Worksheet" not in out
