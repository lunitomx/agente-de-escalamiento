# pyright: strict
"""S84.3: ``python -m coaching.dashboard.boards`` (synthetic company only)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from coaching.dashboard.boards.flow import run
from coaching.dashboard.boards.patterns import PATTERNS
from coaching.journey.asks import AskRecord, record_ask

ROOT = Path(__file__).resolve().parents[4]
TODAY = "2026-10-01"


def _files(base: Path) -> list[str]:
    return sorted(
        p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()
    )


def _recommend(base: Path, text: str, **extra: object) -> dict[str, object]:
    return {
        "action": "recommend",
        "base_path": str(base),
        "today": TODAY,
        "request": text,
        **extra,
    }


def test_sales_board_proposes_and_consults_the_journey_trigger(tmp_path: Path) -> None:
    result = run(_recommend(tmp_path, "Tablero de mis ventas"))
    assert result.errors == []
    assert result.recommendation is not None
    assert result.recommendation.outcome == "propuestas"
    assert result.journey is not None
    assert result.journey.ask is True
    assert result.journey.reason == "T4"
    assert result.journey_question
    assert result.journey_question not in result.message  # one question per message
    assert _files(tmp_path) == []  # recommending never writes


def test_a_recent_journey_decline_keeps_the_question_silent(tmp_path: Path) -> None:
    record_ask(
        tmp_path,
        AskRecord.model_validate(
            {"asked_on": "2026-09-25", "outcome": "despues", "reason": "T1"}
        ),
    )
    result = run(_recommend(tmp_path, "Tablero de mis ventas"))
    assert result.journey is not None
    assert result.journey.ask is False
    assert result.journey.reason == "N2"
    assert result.journey_question is None


def test_asked_this_conversation_is_passed_to_the_journey_check(tmp_path: Path) -> None:
    result = run(
        _recommend(tmp_path, "Tablero de mis ventas", asked_this_conversation=True)
    )
    assert result.journey is not None and result.journey.reason == "N3"


def test_facts_on_disk_feed_the_metric_state(tmp_path: Path) -> None:
    metric = PATTERNS["ventas-etapas"].metrics[0].metric_definition
    facts = [
        {
            "metric_definition": metric,
            "period": "septiembre 2026",
            "source": "whatsapp.csv",
            "confidence": "medium",
            "value": 120,
        }
    ]
    result = run(_recommend(tmp_path, "Tablero de mis ventas", facts=facts))
    assert result.recommendation is not None
    first = result.recommendation.proposals[0]
    assert first.metrics[0].status == "conocido"
    assert first.feasibility == "necesita_datos"


def test_a_cash_request_points_to_the_report_on_disk(tmp_path: Path) -> None:
    report = tmp_path / ".escala-cash-reports" / "abc"
    report.mkdir(parents=True)
    (report / "cash-report.html").write_text("<p>x</p>", encoding="utf-8")
    result = run(_recommend(tmp_path, "flujo de caja en una gráfica"))
    assert result.recommendation is not None
    assert result.recommendation.outcome == "existe"
    assert result.recommendation.points_to_existing == ".escala-cash-reports/"
    assert result.journey is None


def test_tracker_and_research_on_disk_are_found(tmp_path: Path) -> None:
    company = tmp_path / ".escala" / "my-company"
    (company / "research").mkdir(parents=True)
    (company / "tracker.yaml").write_text("items: []\n", encoding="utf-8")
    (company / "research" / "index.yaml").write_text("reports: []\n", encoding="utf-8")
    tracker = run(_recommend(tmp_path, "tablero de mis prioridades"))
    research = run(_recommend(tmp_path, "gráfica de mi competencia"))
    assert tracker.recommendation is not None
    assert (
        tracker.recommendation.points_to_existing == ".escala/my-company/tracker.yaml"
    )
    assert research.recommendation is not None
    assert (
        research.recommendation.points_to_existing
        == ".escala/my-company/research/index.yaml"
    )


def test_decide_saves_only_codes_and_hides_the_board_for_a_month(
    tmp_path: Path,
) -> None:
    saved = run(
        {
            "action": "decide",
            "base_path": str(tmp_path),
            "today": TODAY,
            "board_id": "ventas-etapas",
            "outcome": "no",
            "owner_text": "MARCADOR-PRIVADO no me sirve",
        }
    )
    assert saved.errors == []
    assert saved.saved_to == ".escala/my-company/tableros/index.yaml"
    text = (tmp_path / saved.saved_to).read_text(encoding="utf-8")
    assert "MARCADOR-PRIVADO" not in text
    again = run(_recommend(tmp_path, "Tablero de mis ventas"))
    assert again.recommendation is not None
    assert [p.board_id for p in again.recommendation.proposals] == ["ventas-regresan"]


def test_decide_wait_needs_a_date(tmp_path: Path) -> None:
    result = run(
        {
            "action": "decide",
            "base_path": str(tmp_path),
            "today": TODAY,
            "board_id": "ventas-etapas",
            "outcome": "esperar",
        }
    )
    assert result.errors
    assert _files(tmp_path) == []


def test_decide_build_confirms_it_stays_local(tmp_path: Path) -> None:
    result = run(
        {
            "action": "decide",
            "base_path": str(tmp_path),
            "today": TODAY,
            "board_id": "equipo-carga",
            "outcome": "construir",
        }
    )
    assert "no se publica" in result.message


def test_unknown_action_is_an_error(tmp_path: Path) -> None:
    assert run({"action": "render", "base_path": str(tmp_path)}).errors == [
        "unknown_action"
    ]


def test_module_entry_point_reads_stdin(tmp_path: Path) -> None:
    payload = json.dumps(_recommend(tmp_path, "muéstrame un dashboard"))
    done = subprocess.run(
        [sys.executable, "-m", "coaching.dashboard.boards"],
        input=payload,
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    )
    out = json.loads(done.stdout)
    assert out["recommendation"]["outcome"] == "pregunta_decision"
