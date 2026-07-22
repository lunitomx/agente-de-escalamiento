"""Qualification tests for E39 local meeting intake and intelligence."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path

from escala_server.meetings import (
    RhythmRule,
    MeetingIntakeError,
    assess_rhythm,
    extract_meeting_facts,
    render_meeting_intake_receipt_json,
    scan_meeting_inbox,
)
from escala_server.workspace.authority import WorkspaceConfig


def _config(tmp_path: Path) -> WorkspaceConfig:
    exchange = tmp_path / "exchange"
    exchange.mkdir()
    return WorkspaceConfig(
        platform="macos",
        data_root=tmp_path / "data",
        database_path=tmp_path / "data" / "escala.sqlite",
        exchange_root=exchange,
    )


def test_intake_identifies_context_and_is_idempotent(tmp_path: Path) -> None:
    config = _config(tmp_path)
    source = config.exchange_root / "daily-2026-07-21.transcript"
    source.write_text(
        "Tipo: daily\n"
        "Fecha: 2026-07-21\n"
        "Equipo: Operaciones\n"
        "Participantes: Ana, Luis\n"
        "Acuerdos: revisar inventario\n",
        encoding="utf-8",
    )
    before = source.read_bytes()

    first = scan_meeting_inbox(config)
    second = scan_meeting_inbox(config)

    item = first.items[0]
    assert item.status == "ready"
    assert item.context is not None
    assert item.context.meeting_type == "daily"
    assert item.context.meeting_date is not None
    assert item.context.meeting_date.isoformat() == "2026-07-21"
    assert item.context.team == "Operaciones"
    assert item.context.participants == ("Ana", "Luis")
    assert item.context.evidence
    assert second.items[0].status == "duplicate"
    assert first.ledger.entries[0].source_id == second.ledger.entries[0].source_id
    assert source.read_bytes() == before
    ledger = config.data_root / ".escala-meeting-ledger.json"
    assert ledger.exists()
    assert str(tmp_path) not in ledger.read_text(encoding="utf-8")


def test_ambiguous_context_asks_bounded_questions(tmp_path: Path) -> None:
    config = _config(tmp_path)
    source = config.exchange_root / "seguimiento.transcript"
    source.write_text(
        "Equipo: Operaciones\nParticipantes: Ana, Luis\nTema: seguimiento\n",
        encoding="utf-8",
    )

    result = scan_meeting_inbox(config)

    item = result.items[0]
    assert item.status == "unresolved"
    assert item.context is not None
    assert item.context.meeting_type == "unknown"
    assert {question.code for question in item.questions} >= {
        "meeting_type_unresolved",
        "meeting_date_unresolved",
    }
    assert all(question.options for question in item.questions)


def test_unsupported_directory_and_symlink_are_rejected(tmp_path: Path) -> None:
    config = _config(tmp_path)
    (config.exchange_root / "private.bin").write_bytes(b"private")
    (config.exchange_root / "nested").mkdir()
    target = config.exchange_root / "real.transcript"
    target.write_text("Tipo: daily\nFecha: 2026-07-21\n", encoding="utf-8")
    (config.exchange_root / "link.transcript").symlink_to(target)

    result = scan_meeting_inbox(config)

    by_path = {item.relative_path: item for item in result.items}
    assert by_path["private.bin"].status == "rejected"
    assert by_path["nested"].code == "entry_directory"
    assert by_path["link.transcript"].code == "entry_symlink"
    assert by_path["real.transcript"].status == "unresolved"


def test_receipt_is_deterministic_and_redacted(tmp_path: Path) -> None:
    config = _config(tmp_path)
    source = config.exchange_root / "weekly.md"
    source.write_text(
        "Tipo: weekly\nFecha: 21/07/2026\nEquipo: Dirección\n"
        "Participantes: Lalo\nNota privada: margen bajo\n",
        encoding="utf-8",
    )

    result = scan_meeting_inbox(config)
    first = render_meeting_intake_receipt_json(result)
    second = render_meeting_intake_receipt_json(result)

    assert first == second
    assert str(tmp_path) not in first
    assert "Nota privada" not in first
    assert "margen bajo" not in first
    payload = json.loads(first)
    assert payload["status"] == "pass"
    assert payload["items"][0]["source_id"]


def test_missing_exchange_fails_with_stable_code(tmp_path: Path) -> None:
    config = WorkspaceConfig(
        platform="macos",
        data_root=tmp_path / "data",
        database_path=tmp_path / "data" / "escala.sqlite",
        exchange_root=tmp_path / "missing-exchange",
    )

    try:
        scan_meeting_inbox(config)
    except MeetingIntakeError as error:
        assert error.code == "exchange_missing"
    else:  # pragma: no cover - assertion guard
        raise AssertionError("missing exchange must fail closed")


def test_extracts_required_facts_with_provenance_and_attachments(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    source = config.exchange_root / "daily-2026-07-21.transcript"
    source.write_text(
        "Tipo: daily\n"
        "Fecha: 2026-07-21\n"
        "Equipo: Operaciones\n"
        "Participantes: Ana, Luis\n"
        "Decisión: Mantener proveedor A\n"
        "Acción: Ana — revisar inventario — vence: 2026-07-25\n"
        "Bloqueador: aprobación de compras\n"
        "Riesgo: proveedor atrasado\n"
        "Compromiso: Luis entregará presupuesto\n"
        "Responsable: Ana\n"
        "Vence: 2026-07-25\n",
        encoding="utf-8",
    )

    intake = scan_meeting_inbox(config)
    result = extract_meeting_facts(config, intake.items[0])

    assert result.status == "ready"
    assert {fact.kind for fact in result.facts} >= {
        "decision",
        "action",
        "blocker",
        "risk",
        "commitment",
        "owner",
        "due_date",
    }
    action = next(fact for fact in result.facts if fact.kind == "action")
    assert action.owner == "Ana"
    assert action.due_date == date(2026, 7, 25)
    assert action.confidence == "high"
    assert action.evidence.source_id == intake.items[0].source_id
    assert action.evidence.line_start == 6
    assert all(fact.value for fact in result.facts)


def test_changed_source_blocks_stale_extraction(tmp_path: Path) -> None:
    config = _config(tmp_path)
    source = config.exchange_root / "daily-2026-07-21.transcript"
    source.write_text(
        "Tipo: daily\nFecha: 2026-07-21\nEquipo: Operaciones\n"
        "Participantes: Ana\nAcción: Ana — revisar inventario\n",
        encoding="utf-8",
    )
    intake = scan_meeting_inbox(config)
    source.write_text(
        source.read_text(encoding="utf-8") + "Riesgo: cambio\n", encoding="utf-8"
    )

    result = extract_meeting_facts(config, intake.items[0])

    assert result.status == "blocked"
    assert "source_changed" in result.findings
    assert not result.facts


def test_rhythm_reports_missing_evidence_without_person_failure() -> None:
    context = scan_context("daily", date(2026, 7, 20))

    assessment = assess_rhythm(
        (context,),
        RhythmRule(rule_id="daily", meeting_type="daily", cadence_days=1),
        period_start=date(2026, 7, 20),
        period_end=date(2026, 7, 22),
    )

    assert assessment.status == "evidence_missing"
    assert assessment.missing_dates == (date(2026, 7, 21), date(2026, 7, 22))
    assert assessment.person_impact == "not_assessed"


def scan_context(meeting_type: str, meeting_date: date):
    """Build a context through the public intake seam for rhythm tests."""

    from escala_server.meetings import MeetingContext, MeetingProvenance

    return MeetingContext(
        context_status="ready",
        meeting_type=meeting_type,  # type: ignore[arg-type]
        meeting_date=meeting_date,
        team="Operaciones",
        participants=("Ana",),
        provenance=MeetingProvenance(
            source_id="a" * 64,
            relative_path="daily.transcript",
            line_start=1,
            line_end=1,
            evidence_sha256="b" * 64,
        ),
        confidence="high",
    )
