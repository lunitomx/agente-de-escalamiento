"""S87.2 T1: one knowledge root for registry, content and progress."""

from __future__ import annotations

from pathlib import Path

from coaching.core import read_yaml, write_yaml
from coaching.progress import _get_worksheets  # pyright: ignore[reportPrivateUsage]
from coaching.worksheet import (
    PACKAGE_KNOWLEDGE,
    PACKAGE_ROOT,
    find_worksheet,
    knowledge_root,
    list_worksheets,
    load_worksheet_content,
    registry_path,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _seed_client(base: Path) -> None:
    knowledge = base / ".escala" / "knowledge"
    write_yaml(
        knowledge / "registry" / "worksheets.yaml",
        {
            "worksheets": [
                {
                    "id": "client-ws",
                    "name": "Client Worksheet",
                    "decision": "cash",
                    "node_path": "cash/tools/client.yaml",
                }
            ]
        },
    )
    write_yaml(
        knowledge / "cash" / "tools" / "client.yaml",
        {"summary": "Hoja del cliente", "metadata": {"fields": ["q1"]}},
    )


def test_package_registry_file_exists() -> None:
    assert (PACKAGE_ROOT / "conocimiento" / "registry" / "worksheets.yaml").is_file()
    assert PACKAGE_KNOWLEDGE == PACKAGE_ROOT / "conocimiento"


def test_repo_lists_sixteen_worksheets() -> None:
    assert len(list_worksheets(base_path=REPO_ROOT)) == 16


def test_none_base_lists_sixteen_worksheets() -> None:
    assert len(list_worksheets()) == 16


def test_empty_base_falls_back_to_package(tmp_path: Path) -> None:
    assert knowledge_root(tmp_path) == PACKAGE_KNOWLEDGE
    assert len(list_worksheets(base_path=tmp_path)) == 16


def test_client_knowledge_dir_without_registry_falls_back(tmp_path: Path) -> None:
    (tmp_path / ".escala" / "knowledge" / "strategy").mkdir(parents=True)
    assert knowledge_root(tmp_path) == PACKAGE_KNOWLEDGE


def test_client_registry_wins_and_content_reads_same_root(tmp_path: Path) -> None:
    _seed_client(tmp_path)
    assert knowledge_root(tmp_path) == tmp_path / ".escala" / "knowledge"
    assert registry_path(tmp_path) == (
        tmp_path / ".escala" / "knowledge" / "registry" / "worksheets.yaml"
    )
    sheets = list_worksheets(base_path=tmp_path)
    assert [s["id"] for s in sheets] == ["client-ws"]
    sheet = find_worksheet("client-ws", tmp_path)
    assert sheet is not None
    content = load_worksheet_content(sheet, tmp_path)
    assert content["summary"] == "Hoja del cliente"


def test_package_content_loads_from_conocimiento(tmp_path: Path) -> None:
    sheet = find_worksheet("worksheet-core-customer", tmp_path)
    assert sheet is not None
    content = load_worksheet_content(sheet, tmp_path)
    assert content["metadata"]["fields"]


def test_registry_total_matches_list() -> None:
    registry = read_yaml(PACKAGE_KNOWLEDGE / "registry" / "worksheets.yaml")
    assert registry["total_worksheets"] == len(registry["worksheets"])


def test_progress_counts_sixteen_on_empty_base(tmp_path: Path) -> None:
    all_ws, completed = _get_worksheets(tmp_path)
    assert len(all_ws) == 16
    assert completed == {}
