"""``python -m coaching.research``: frame -> grade -> report -> save (E83 S83.1).

Includes the end-to-end privacy check: the synthetic company's markers in its
name, people and figures never reach a search the flow hands back.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from coaching.research import messages
from coaching.research.engine import normalize
from coaching.research.flow import run

ROOT = Path(__file__).resolve().parents[3]
MARKERS = ["zorblax", "ximena", "vrkalova", "brunhilda", "okonkwo", "987654", "4321"]
PRIVATE: dict[str, object] = {
    "company_names": ["Tortillería Zorblax"],
    "people": ["Ximena Vrkalova", "Brunhilda Okonkwo"],
    "figures": ["$987,654", "4321"],
}


def _frame(**fields: object) -> dict[str, object]:
    frame: dict[str, object] = {
        "concern": "En Tortillería Zorblax vendemos $987,654; Ximena cree que cobramos poco",
        "question": "¿Zorblax cobra menos que las tortillerías de Puebla?",
        "decision_informed": "subir o no el precio del kilo en enero",
        "mode": "benchmark",
        "decision_area": "cash",
        "offer_category": "tortillas de maíz",
        "geography": "Puebla",
        "horizon": "2026",
    }
    frame.update(fields)
    return frame


def _source(source_id: str, publisher: str, origin: str = "web") -> dict[str, object]:
    return {
        "source_id": source_id,
        "origin": origin,
        "title": f"Precios {source_id}",
        "publisher": publisher,
        "url": f"https://ejemplo-{source_id}.test/p" if origin == "web" else None,
        "published_on": "2026-09-10",
        "consulted_on": "2026-09-30",
        "excerpt": f"El kilo cuesta 24 pesos ({source_id})",
    }


SOURCES = [
    _source("s1", "Diario Uno"),
    _source("s2", "Revista Dos"),
    _source("s3", "Cámara Tres"),
]
CLAIMS: list[dict[str, object]] = [
    {
        "text": "El kilo cuesta entre 22 y 26 pesos en Puebla.",
        "kind": "dato",
        "supporting": ["s1", "s2", "s3"],
    }
]
OPTIONS: list[dict[str, object]] = [
    {"label": "A", "text": "Subir 8% en enero"},
    {"label": "B", "text": "Mantener el precio y cambiar el paquete"},
]


def _report_context(action: str, base: Path, **extra: object) -> dict[str, object]:
    context: dict[str, object] = {
        "action": action,
        "base_path": str(base),
        "today": "2026-09-30",
        "frame": _frame(
            confirmed=True, queries=["precios de tortillas de maíz en Puebla 2026"]
        ),
        "sources": SOURCES,
        "claims": CLAIMS,
        "not_found": [],
        "options": OPTIONS,
        "recommendation": "A",
        "recommendation_reason": "estás abajo del rango",
    }
    context.update(extra)
    return context


def _flat(text: str) -> str:
    return normalize(text).replace(" ", "").replace(",", "").replace(".", "")


def test_frame_builds_clean_searches_and_asks_permission_in_one_message() -> None:
    result = run({"action": "frame", "frame": _frame(), "private": PRIVATE})

    assert result.errors == []
    assert result.frame is not None
    assert not result.frame.confirmed
    assert 2 <= len(result.frame.queries) <= 3
    for query in result.frame.queries:
        assert f"*{query}*" in result.message
        for marker in MARKERS:
            assert marker not in _flat(query)
    assert "No llevo tu nombre ni tus cifras" in result.message
    assert result.message.endswith("¿Va, o cambio algo?")


def test_frame_rejects_proposed_searches_with_private_data() -> None:
    proposed = ["precios Zorblax Puebla", "precios de tortillas de maíz en Puebla 2026"]
    result = run(
        {"action": "frame", "frame": _frame(queries=proposed), "private": PRIVATE}
    )

    assert result.frame is not None
    assert result.frame.queries == ["precios de tortillas de maíz en Puebla 2026"]
    assert [item.reason for item in result.rejected] == ["empresa"]
    assert "Zorblax" not in result.message


def test_frame_with_only_private_searches_asks_again() -> None:
    result = run(
        {
            "action": "frame",
            "frame": _frame(queries=["Ximena tortillas"]),
            "private": PRIVATE,
        }
    )

    assert result.errors == ["no_safe_query"]
    assert result.message == messages.NO_SAFE_QUERY


def test_frame_needs_the_private_terms_to_check_searches() -> None:
    result = run({"action": "frame", "frame": _frame()})

    assert result.errors == ["needs_private_terms"]


def test_frame_without_offer_category_asks_what_is_sold() -> None:
    result = run(
        {"action": "frame", "frame": _frame(offer_category=None), "private": PRIVATE}
    )

    assert result.errors == ["needs_offer_category"]
    assert result.message == messages.NEEDS_OFFER


def test_frame_without_search_says_so_in_one_line_and_asks_for_sources() -> None:
    result = run(
        {
            "action": "frame",
            "frame": _frame(search_mode="sin_busqueda"),
            "private": PRIVATE,
        }
    )

    assert result.errors == []
    assert result.frame is not None and result.frame.queries == []
    first_line = result.message.splitlines()[0]
    assert first_line == messages.SEARCH_OFF
    assert "prenderla" in first_line
    assert "dos o tres fuentes" in first_line


def test_grade_returns_graded_claims() -> None:
    result = run(
        {"action": "grade", "today": "2026-09-30", "sources": SOURCES, "claims": CLAIMS}
    )

    assert [claim.status for claim in result.claims] == ["confirmado"]


def test_report_shows_the_result_and_saves_nothing(tmp_path: Path) -> None:
    result = run(_report_context("report", tmp_path))

    assert result.errors == []
    assert result.report is not None
    assert result.message.endswith("¿Cuál tomas?")
    assert not (tmp_path / ".escala").exists()


def test_report_needs_a_confirmed_frame(tmp_path: Path) -> None:
    result = run(_report_context("report", tmp_path, frame=_frame()))

    assert "frame_not_confirmed" in result.errors


def test_report_recheck_blocks_private_searches(tmp_path: Path) -> None:
    frame = _frame(confirmed=True, queries=["precios Zorblax"])
    result = run(_report_context("report", tmp_path, frame=frame, private=PRIVATE))

    assert result.errors == ["private_query"]


def test_save_needs_the_owner_yes_and_a_choice(tmp_path: Path) -> None:
    no_yes = run(_report_context("save", tmp_path, chosen="A"))
    no_choice = run(_report_context("save", tmp_path, user_confirmed=True))

    assert no_yes.errors == ["needs_user_confirmation"]
    assert no_choice.errors == ["needs_chosen_option"]
    assert no_choice.message == messages.NEEDS_CHOICE
    assert not (tmp_path / ".escala").exists()


def test_save_writes_only_under_the_company_research_folder(tmp_path: Path) -> None:
    result = run(_report_context("save", tmp_path, chosen="A", user_confirmed=True))

    assert result.errors == []
    assert result.saved_to == ".escala/my-company/research/2026-09-30-benchmark.md"
    written = sorted(
        p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()
    )
    assert written == [
        ".escala/my-company/research/2026-09-30-benchmark.md",
        ".escala/my-company/research/index.yaml",
    ]
    assert "29 de diciembre de 2026" in result.message


def test_invalid_input_returns_readable_errors() -> None:
    result = run(
        {
            "action": "grade",
            "sources": [{"source_id": "x", "origin": "modelo"}],
            "claims": [],
        }
    )

    assert result.errors and result.errors[0].startswith("invalid:")


def test_unknown_action() -> None:
    assert run({"action": "adivinar"}).errors == ["unknown_action"]


def test_module_entry_point_speaks_json() -> None:
    payload = json.dumps({"action": "frame", "frame": _frame(), "private": PRIVATE})
    completed = subprocess.run(
        [sys.executable, "-m", "coaching.research"],
        input=payload,
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    )

    out = json.loads(completed.stdout)
    assert out["action"] == "frame"
    assert out["frame"]["queries"]
    for marker in MARKERS:
        assert marker not in _flat(" ".join(out["frame"]["queries"]))
