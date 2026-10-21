"""E87 · Cobertura de las 38 páginas del Strategy Workbook (S87.1).

Vigila el mapa `tests/fixtures/e87-workbook-coverage.yaml`, la lista
`pending` (solo puede encoger), cero imágenes del workbook en el repo y que
E87 no agregue archivos bajo `.scaleup/`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "conocimiento"


def build_node_index(root: Path) -> set[str]:
    """Ids de todo yaml bajo `root` que sea un nodo (un dict con `id`)."""
    ids: set[str] = set()
    for path in sorted(root.rglob("*.yaml")):
        data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "id" in data:
            ids.add(str(data["id"]))
    return ids


def build_registry_index(registry: Path) -> set[str]:
    """Ids de las hojas listadas en el registro `worksheets:`."""
    data: Any = yaml.safe_load(registry.read_text(encoding="utf-8"))
    return {str(entry["id"]) for entry in data.get("worksheets") or []}


def check_coverage(
    coverage: dict[str, Any],
    node_ids: set[str],
    registry_ids: set[str],
    frozen_pending: frozenset[int],
) -> list[str]:
    """Reglas del mapa de cobertura. Devuelve errores `p. N: ...`; vacío = verde.

    Una página sale de `pending` cuando su entrada nombra nodos que existen en
    conocimiento/ (y, si son hojas `worksheet-*`, que están en el registro).
    Los nodos no llevan referencias de página (política pública).
    """
    errors: list[str] = []
    total = int(coverage.get("total_pages", 38))
    pages: list[dict[str, Any]] = list(coverage.get("pages") or [])
    pending: list[int] = [int(p) for p in coverage.get("pending") or []]

    seen: set[int] = set()
    by_page: dict[int, dict[str, Any]] = {}
    for entry in pages:
        number = int(entry["page"])
        if number in seen:
            errors.append(f"página repetida: {number}")
        seen.add(number)
        by_page[number] = entry
    missing = sorted(set(range(1, total + 1)) - seen)
    if missing:
        errors.append(f"faltan páginas: {missing}")

    for number in pending:
        if number not in frozen_pending:
            errors.append(f"p. {number}: fuera de la lista congelada")
        entry = by_page.get(number)
        if entry is not None and entry.get("class") != "tool":
            errors.append(f"p. {number}: en pending pero es no_tool")

    for number, entry in sorted(by_page.items()):
        nodes: list[str] = [str(n) for n in entry.get("nodes") or []]
        if entry.get("class") == "no_tool" and not entry.get("reason"):
            errors.append(f"p. {number}: no_tool sin reason")
        for node in nodes:
            if node not in node_ids:
                errors.append(f"p. {number}: nodo inexistente {node}")
        if entry.get("class") != "tool" or number in pending:
            continue
        if not nodes:
            errors.append(f"p. {number}: tool fuera de pending sin nodos")
        for node in nodes:
            if (
                node.startswith("worksheet-")
                and node in node_ids
                and node not in registry_ids
            ):
                errors.append(f"p. {number}: {node} no está en el registro de hojas")
    return errors


def find_images(dirs: list[Path]) -> list[Path]:
    """Archivos de imagen o PDF bajo `dirs` (los que no existen se ignoran)."""
    found: list[Path] = []
    for base in dirs:
        if base.is_dir():
            found += [p for p in base.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES]
    return sorted(found)


def new_files(actual: list[str], frozen: set[str]) -> list[str]:
    """Archivos de `actual` que no están en la lista congelada."""
    return sorted(set(actual) - frozen)


# --- Tarea 1 · índice de nodos -------------------------------------------


def test_build_node_index_reads_ids(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "bmc.yaml").write_text("id: worksheet-bmc\n", encoding="utf-8")
    (tmp_path / "sandbox.yaml").write_text(
        "id: tool-sandbox\nname: Sandbox\n", encoding="utf-8"
    )
    (tmp_path / "list.yaml").write_text("- 1\n- 2\n", encoding="utf-8")
    assert build_node_index(tmp_path) == {"worksheet-bmc", "tool-sandbox"}


def test_build_registry_index_reads_worksheet_ids(tmp_path: Path) -> None:
    registry = tmp_path / "worksheets.yaml"
    registry.write_text(
        "id: registry-worksheets\nworksheets:\n  - id: worksheet-swt\n  - id: worksheet-opsp\n",
        encoding="utf-8",
    )
    assert build_registry_index(registry) == {"worksheet-swt", "worksheet-opsp"}


# --- Tarea 2 · reglas de estructura ---------------------------------------

TOOL_PAGES = [*range(7, 27), *range(28, 37)]


def _page(n: int) -> dict[str, Any]:
    if n in TOOL_PAGES:
        return {"page": n, "class": "tool"}
    return {"page": n, "class": "no_tool", "reason": "portada o notas"}


def _map(
    pages: list[dict[str, Any]] | None = None, pending: list[int] | None = None
) -> dict[str, Any]:
    return {
        "total_pages": 38,
        "pages": pages if pages is not None else [_page(n) for n in range(1, 39)],
        "pending": pending if pending is not None else list(TOOL_PAGES),
    }


FROZEN = frozenset(TOOL_PAGES)


def test_synthetic_full_map_is_clean() -> None:
    assert check_coverage(_map(), set(), set(), FROZEN) == []


def test_missing_page_is_reported() -> None:
    pages = [_page(n) for n in range(1, 39) if n != 12]
    pending = [p for p in TOOL_PAGES if p != 12]
    assert "faltan páginas: [12]" in check_coverage(
        _map(pages, pending), set(), set(), FROZEN
    )


def test_repeated_page_is_reported() -> None:
    pages = [_page(n) for n in range(1, 39)] + [_page(3)]
    assert "página repetida: 3" in check_coverage(_map(pages), set(), set(), FROZEN)


def test_no_tool_without_reason_is_reported() -> None:
    pages = [_page(n) for n in range(1, 39)]
    pages[36] = {"page": 37, "class": "no_tool"}
    assert "p. 37: no_tool sin reason" in check_coverage(
        _map(pages), set(), set(), FROZEN
    )


# --- Tarea 3 · reglas de pending y nodos ----------------------------------


def test_pending_no_tool_page_is_reported() -> None:
    errors = check_coverage(_map(pending=[*TOOL_PAGES, 5]), set(), set(), FROZEN | {5})
    assert "p. 5: en pending pero es no_tool" in errors


def test_pending_outside_frozen_list_is_reported() -> None:
    errors = check_coverage(_map(pending=[*TOOL_PAGES, 40]), set(), set(), FROZEN)
    assert "p. 40: fuera de la lista congelada" in errors


def test_tool_outside_pending_without_nodes_is_reported() -> None:
    pending = [p for p in TOOL_PAGES if p != 10]
    errors = check_coverage(_map(pending=pending), set(), set(), FROZEN)
    assert "p. 10: tool fuera de pending sin nodos" in errors


def test_worksheet_missing_from_registry_is_reported() -> None:
    pages = [_page(n) for n in range(1, 39)]
    pages[9] = {"page": 10, "class": "tool", "nodes": ["worksheet-bmc"]}
    pending = [p for p in TOOL_PAGES if p != 10]
    errors = check_coverage(_map(pages, pending), {"worksheet-bmc"}, set(), FROZEN)
    assert errors == ["p. 10: worksheet-bmc no está en el registro de hojas"]


def test_existing_nodes_leave_pending_cleanly() -> None:
    pages = [_page(n) for n in range(1, 39)]
    pages[9] = {"page": 10, "class": "tool", "nodes": ["worksheet-bmc", "tool-bmc"]}
    pending = [p for p in TOOL_PAGES if p != 10]
    nodes = {"worksheet-bmc", "tool-bmc"}
    assert check_coverage(_map(pages, pending), nodes, {"worksheet-bmc"}, FROZEN) == []


def test_missing_node_is_reported_even_in_pending() -> None:
    pages = [_page(n) for n in range(1, 39)]
    pages[8] = {"page": 9, "class": "tool", "nodes": ["worksheet-x"]}
    assert check_coverage(_map(pages), set(), set(), FROZEN) == [
        "p. 9: nodo inexistente worksheet-x"
    ]


# --- Tarea 4 · mapa real --------------------------------------------------

# Fuera del contenido público: tests/ es not_eligible en governance/public-boundary.yaml.
COVERAGE_FILE = ROOT / "tests" / "fixtures" / "e87-workbook-coverage.yaml"
REGISTRY = KNOWLEDGE / "registry" / "worksheets.yaml"

# Solo puede encoger: las historias S87.4-S87.9 quitan páginas del archivo,
# nunca se agregan aquí.
FROZEN_PENDING: frozenset[int] = frozenset([*range(7, 27), *range(28, 37)])


def _load_coverage() -> dict[str, Any]:
    data: Any = yaml.safe_load(COVERAGE_FILE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_real_map_is_clean() -> None:
    coverage = _load_coverage()
    assert coverage["total_pages"] == 38
    assert len(coverage["pages"]) == 38
    errors = check_coverage(
        coverage,
        build_node_index(KNOWLEDGE),
        build_registry_index(REGISTRY),
        FROZEN_PENDING,
    )
    assert errors == []


def test_real_pending_is_one_page_per_line() -> None:
    lines = COVERAGE_FILE.read_text(encoding="utf-8").splitlines()
    start = lines.index("pending:")
    items = [line for line in lines[start + 1 :] if line.startswith("  - ")]
    assert len(items) == len(_load_coverage()["pending"])


# --- Tarea 5 · cero imágenes ----------------------------------------------

IMAGE_SUFFIXES = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"})
IMAGE_DIRS = [ROOT / "conocimiento", ROOT / "escala-skills", ROOT / "templates"]


def test_find_images_reports_png(tmp_path: Path) -> None:
    (tmp_path / "hojas").mkdir()
    (tmp_path / "hojas" / "p10.PNG").write_bytes(b"x")
    (tmp_path / "hojas" / "bmc.yaml").write_text("id: x\n", encoding="utf-8")
    assert find_images([tmp_path, tmp_path / "no-existe"]) == [
        tmp_path / "hojas" / "p10.PNG"
    ]


def test_coverage_map_is_not_public_content() -> None:
    assert not (KNOWLEDGE / "strategy" / "workbook-coverage.yaml").exists()


def test_no_workbook_images_in_repo() -> None:
    assert find_images(IMAGE_DIRS) == []


# --- Tarea 6 · .scaleup/ congelado ----------------------------------------

SCALEUP_FROZEN = ROOT / "tests" / "fixtures" / "e87-scaleup-files.txt"


def test_new_files_reports_only_additions() -> None:
    assert new_files(["a", "c"], {"a", "b"}) == ["c"]
    assert new_files(["a"], {"a", "b"}) == []


def test_no_new_files_under_scaleup() -> None:
    try:
        result = subprocess.run(
            ["git", "ls-files", ".scaleup"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        pytest.skip(f"git no disponible para listar .scaleup/: {exc}")
    frozen = set(SCALEUP_FROZEN.read_text(encoding="utf-8").split())
    assert new_files(result.stdout.split(), frozen) == []


# --- Tarea 7 · tarjeta de Caja de arena (p. 28) ---------------------------

SANDBOX = KNOWLEDGE / "strategy" / "tools" / "sandbox.yaml"


def test_sandbox_card_matches_page_28() -> None:
    card: Any = yaml.safe_load(SANDBOX.read_text(encoding="utf-8"))
    assert card["id"] == "tool-sandbox"
    # governance/public-boundary.yaml prohíbe la llave raíz `source` en conocimiento/.
    assert "source" not in card
    questions: list[str] = [str(q) for q in card["questions"]]
    assert len(questions) == 4
    text = " ".join([str(card["summary"]), *questions]).upper()
    for word in ("DÓNDE", "QUÉ", "CANALES", "PRONÓSTICO"):
        assert word in text, word
    assert "WHO/WHERE" not in text


def test_page_28_lists_sandbox_tool() -> None:
    page = next(p for p in _load_coverage()["pages"] if p["page"] == 28)
    assert "tool-sandbox" in page["nodes"]
