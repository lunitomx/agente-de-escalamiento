"""Saved outside findings as external evidence for the one SWT (E83 S83.4, D9).

Synthetic data only. The SWT is never written here: the action hands back the
evidence, marked as outside and graded, for ``escala-strategy-swt`` to add to
the same file it already writes.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from coaching.research import messages
from coaching.research.flow import run
from coaching.research.models import ResearchClaim
from coaching.research.report import build_report, save_report
from coaching.research.swt import SwtEvidence, load_swt_evidence
from coaching.research.tests.test_strengths import (
    CANDIDATE,
    NAMED,
    OPTIONS,
    SOURCES,
    TODAY,
    _claim,
    _frame,
)


def _claims() -> list[ResearchClaim]:
    return [
        _claim(),
        _claim(
            text="El Sol abre más temprano",
            side="debilidad",
            supporting=["s1", "s2", "s3"],
        ),
        _claim(
            text="Sube el precio del maíz, ver https://ejemplo.test/maiz",
            side="tendencia",
            against=[],
            supporting=["s2"],
        ),
    ]


def _save(base: Path, *, researched_on: date = TODAY, mode: str | None = None) -> str:
    shift = TODAY - researched_on
    sources = [
        source.model_copy(
            update={
                "published_on": None
                if source.published_on is None
                else source.published_on - shift,
                "consulted_on": researched_on,
            }
        )
        for source in SOURCES
    ]
    frame = _frame() if mode is None else _frame(mode=mode, competitors=[])
    report = build_report(
        frame=frame,
        researched_on=researched_on,
        sources=sources,
        claims=_claims() if mode is None else [_claim(side=None, against=[])],
        options=OPTIONS,
        recommendation="A",
        recommendation_reason="es lo que te distingue",
        chosen="A",
        comparables=[NAMED, CANDIDATE] if mode is None else [],
    )
    return save_report(report, base).relative_to(base).as_posix()


def test_saved_findings_come_back_as_marked_graded_outside_evidence(
    tmp_path: Path,
) -> None:
    reference = _save(tmp_path)
    inputs = load_swt_evidence(tmp_path, TODAY)
    assert inputs.reference == reference
    assert [item.side for item in inputs.evidence] == [
        "fortaleza",
        "debilidad",
        "tendencia",
    ]
    assert {item.status for item in inputs.evidence} <= {"confirmado", "por_confirmar"}
    for item in inputs.evidence:
        assert item.label == "Según fuentes externas, septiembre de 2026"
        assert item.reference == reference
        assert "://" not in item.text
    assert inputs.evidence[0].against == ["Tortillería El Sol"]
    assert inputs.evidence[2].against == []


def test_the_text_is_never_cut(tmp_path: Path) -> None:
    _save(tmp_path)
    texts = [item.text for item in load_swt_evidence(tmp_path, TODAY).evidence]
    assert texts[:2] == ["El Sol no entrega a domicilio", "El Sol abre más temprano"]
    assert texts[2].startswith("Sube el precio del maíz, ver")


def test_only_the_strengths_mode_feeds_the_swt(tmp_path: Path) -> None:
    _save(tmp_path, mode="mercado")
    inputs = load_swt_evidence(tmp_path, TODAY)
    assert inputs.evidence == []
    assert inputs.reference is None


def test_the_newest_research_wins(tmp_path: Path) -> None:
    _save(tmp_path, researched_on=TODAY - timedelta(days=40))
    newest = _save(tmp_path, researched_on=TODAY - timedelta(days=5))
    assert load_swt_evidence(tmp_path, TODAY).reference == newest


def test_a_stale_research_does_not_enter_and_is_offered_for_refresh(
    tmp_path: Path,
) -> None:
    _save(tmp_path, researched_on=TODAY - timedelta(days=91))
    inputs = load_swt_evidence(tmp_path, TODAY)
    assert inputs.evidence == []
    assert inputs.refresh_offer is not None
    assert "fecha de revisión" in inputs.refresh_offer


def test_action_with_nothing_saved_asks_the_design_question(tmp_path: Path) -> None:
    result = run(
        {"action": "swt", "base_path": str(tmp_path), "today": TODAY.isoformat()}
    )
    assert result.errors == []
    assert result.swt_evidence == []
    assert result.message == messages.SWT_ASK
    assert messages.SWT_ASK == (
        "¿Quieres que revise qué dicen fuera de tu empresa antes de cerrar tu "
        "análisis de fortalezas, debilidades y tendencias (SWT)?"
    )


def test_action_groups_by_side_and_never_writes_an_swt(tmp_path: Path) -> None:
    _save(tmp_path)
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    result = run(
        {"action": "swt", "base_path": str(tmp_path), "today": TODAY.isoformat()}
    )
    assert result.errors == []
    assert len(result.swt_evidence) == 3
    assert all(isinstance(item, SwtEvidence) for item in result.swt_evidence)
    text = result.message
    assert "Según fuentes externas, septiembre de 2026" in text
    for title in ("Fortalezas", "Debilidades", "Tendencias"):
        assert title in text
    assert (
        text.index("Fortalezas") < text.index("Debilidades") < text.index("Tendencias")
    )
    assert "frente a Tortillería El Sol" in text
    assert "por confirmar" in text
    assert "://" not in text
    assert text.rstrip().endswith("?")
    assert sorted(path.as_posix() for path in tmp_path.rglob("*")) == before
    assert not list(tmp_path.rglob("swt-*"))


def test_action_with_a_stale_research_offers_to_refresh(tmp_path: Path) -> None:
    _save(tmp_path, researched_on=TODAY - timedelta(days=91))
    result = run(
        {"action": "swt", "base_path": str(tmp_path), "today": TODAY.isoformat()}
    )
    assert result.swt_evidence == []
    assert "fecha de revisión" in result.message
