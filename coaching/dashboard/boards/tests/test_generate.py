# pyright: strict
"""S84.4: ``generate`` only for an accepted board, and the full synthetic run.

Integration checkpoint of E84 (M2/M3): request -> proposal -> decision ->
local file, plus the journey case. Synthetic company only, in ``tmp_path``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from coaching.dashboard.boards.flow import FlowResult, run
from coaching.dashboard.boards.render import FORBIDDEN
from coaching.journey.decision import choose, propose, save_journey
from coaching.journey.models import Journey, JourneyStage, StageCount

ROOT = Path(__file__).resolve().parents[4]
TODAY = "2026-10-01"
_FACTS: list[dict[str, object]] = [
    {
        "metric_definition": "Personas que preguntan",
        "period": "septiembre de 2026",
        "source": "tus mensajes de WhatsApp",
        "confidence": "high",
        "value": 120,
    }
]


def _files(base: Path) -> list[str]:
    return sorted(
        p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()
    )


def _step(base: Path, action: str, **extra: object) -> dict[str, object]:
    return {"action": action, "base_path": str(base), "today": TODAY, **extra}


def _cli(context: dict[str, object]) -> FlowResult:
    done = subprocess.run(
        [sys.executable, "-m", "coaching.dashboard.boards"],
        input=json.dumps(context),
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    )
    return FlowResult.model_validate_json(done.stdout)


def test_not_accepted_generates_nothing(tmp_path: Path) -> None:
    result = run(_step(tmp_path, "generate", board_id="ventas-etapas", facts=_FACTS))
    assert result.errors == ["not_accepted"]
    assert result.saved_files == []
    assert _files(tmp_path) == []


def test_postponed_or_declined_generates_nothing(tmp_path: Path) -> None:
    run(_step(tmp_path, "decide", board_id="ventas-etapas", outcome="no"))
    result = run(_step(tmp_path, "generate", board_id="ventas-etapas", facts=_FACTS))
    assert result.errors == ["not_accepted"]
    assert not list(tmp_path.rglob("*.html"))


def test_unknown_board_is_an_error(tmp_path: Path) -> None:
    result = run(_step(tmp_path, "generate", board_id="inventado"))
    assert result.errors == ["unknown_board"]


def test_accepted_without_numbers_lists_the_data_to_get(tmp_path: Path) -> None:
    run(_step(tmp_path, "decide", board_id="ventas-etapas", outcome="construir"))
    result = run(_step(tmp_path, "generate", board_id="ventas-etapas", facts=[]))
    assert result.errors == []
    assert result.saved_files == []
    assert not list(tmp_path.rglob("*.html"))
    assert "Todavía no" in result.message
    assert "Personas que preguntan" in result.message


def test_full_synthetic_run_request_proposal_decision_file(tmp_path: Path) -> None:
    proposed = _cli(
        _step(tmp_path, "recommend", request="Tablero de mis ventas", facts=_FACTS)
    )
    assert proposed.recommendation is not None
    proposals = proposed.recommendation.proposals
    assert 1 <= len(proposals) <= 2
    assert _files(tmp_path) == []

    board_id = proposals[0].board_id
    decided = _cli(_step(tmp_path, "decide", board_id=board_id, outcome="construir"))
    assert decided.errors == []

    made = _cli(_step(tmp_path, "generate", board_id=board_id, facts=_FACTS))

    assert made.errors == []
    assert made.saved_files == [
        ".escala/my-company/tableros/2026-10-01-ventas-etapas.html",
        ".escala/my-company/tableros/2026-10-01-ventas-etapas.md",
    ]
    html_text = (tmp_path / made.saved_files[0]).read_text(encoding="utf-8")
    assert not any(token in html_text.lower() for token in FORBIDDEN)
    assert "Falta: Clientes que compran" in html_text
    assert "120" in html_text and "Sólo en tu computadora; no se publica." in html_text
    assert made.markdown is not None and "Falta: Clientes que compran" in made.markdown
    assert "no se publica" in made.message
    assert _files(tmp_path) == [
        ".escala/my-company/tableros/2026-10-01-ventas-etapas.html",
        ".escala/my-company/tableros/2026-10-01-ventas-etapas.md",
        ".escala/my-company/tableros/index.yaml",
    ]


def _journey() -> Journey:
    counts = {"pregunta": 120, "compra": 18}
    return Journey(
        built_on=date(2026, 10, 1),
        stages=[
            JourneyStage(
                stage=stage,
                count=None
                if stage not in counts
                else StageCount(
                    value=counts[stage],
                    period="2026-09",
                    source="tu cuaderno de ventas",
                    origin="dato_con_periodo",
                ),
            )
            for stage in ("se_entera", "pregunta", "compra", "recibe", "regresa")
        ],
    )


def test_full_synthetic_run_from_the_saved_journey(tmp_path: Path) -> None:
    journey = _journey()
    decision = propose(journey, date(2026, 10, 1), experiment=None)
    save_journey(
        tmp_path, journey, choose(decision, decision.recommendation), date(2026, 10, 1)
    )

    proposed = run(_step(tmp_path, "recommend", request="Tablero de mis ventas"))
    assert proposed.recommendation is not None
    stages = proposed.recommendation.proposals[0]
    assert stages.feasibility == "se_puede_hoy"
    run(_step(tmp_path, "decide", board_id=stages.board_id, outcome="construir"))

    made = run(_step(tmp_path, "generate", board_id=stages.board_id))

    assert made.errors == []
    html_text = (tmp_path / made.saved_files[0]).read_text(encoding="utf-8")
    for piece in ("120", "18", "1.5", "tu cuaderno de ventas", "septiembre de 2026"):
        assert piece in html_text
    assert "Falta" not in html_text
