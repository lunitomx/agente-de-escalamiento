"""E87 · Cobertura de las 38 páginas del Strategy Workbook (S87.1).

Vigila el mapa `conocimiento/strategy/workbook-coverage.yaml`, la lista
`pending` (solo puede encoger), cero imágenes del workbook en el repo y que
E87 no agregue archivos bajo `.scaleup/`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "conocimiento"


def build_node_index(root: Path) -> dict[str, list[int]]:
    """Devuelve {id: source.pages} de todo yaml bajo `root` que sea un nodo."""
    index: dict[str, list[int]] = {}
    for path in sorted(root.rglob("*.yaml")):
        data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "id" not in data:
            continue
        node: dict[str, Any] = data
        source: Any = node.get("source")
        pages: list[int] = []
        if isinstance(source, dict):
            raw: Any = source.get("pages")
            if isinstance(raw, list):
                pages = [int(p) for p in raw]
        index[str(node["id"])] = pages
    return index


# --- Tarea 1 · índice de nodos -------------------------------------------


def test_build_node_index_reads_ids_and_pages(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "bmc.yaml").write_text(
        "id: worksheet-bmc\nsource:\n  workbook: strategy-2025\n  pages: [8, 10]\n",
        encoding="utf-8",
    )
    (tmp_path / "sandbox.yaml").write_text("id: tool-sandbox\nname: Sandbox\n", encoding="utf-8")
    (tmp_path / "registry.yaml").write_text("worksheets:\n  - id: x\n", encoding="utf-8")
    (tmp_path / "list.yaml").write_text("- 1\n- 2\n", encoding="utf-8")

    assert build_node_index(tmp_path) == {
        "worksheet-bmc": [8, 10],
        "tool-sandbox": [],
    }
