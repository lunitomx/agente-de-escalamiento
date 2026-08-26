"""Public-language contract for the local memory continuity adapter."""

import sqlite3
from pathlib import Path

import pytest

from escala_server.project_memory_session_close import (
    CandidateSource,
    MemoryCandidate,
    ProjectMemorySessionClose,
)


def test_confirmed_entry_is_rendered_as_a_short_safe_resume_prefix(
    tmp_path: Path,
) -> None:
    from escala_server.project_memory_continuity import ProjectMemoryContinuity

    close = ProjectMemorySessionClose(tmp_path)
    assert close.open_session("s-1").ready
    proposal = close.propose(
        "s-1",
        MemoryCandidate(
            "decision",
            "Contrataremos una líder de ventas en septiembre",
            CandidateSource("s-1", ("obs-1",), "explicit_user_statement"),
        ),
    )
    assert close.confirm(proposal.id or "", "sí").status == "confirmed"

    turn = ProjectMemoryContinuity(tmp_path).resume()

    assert turn.prefix
    assert "líder de ventas" in turn.prefix.lower()
    assert all(
        token not in turn.prefix.lower()
        for token in (".scaleup", "sqlite", " db", "skill", "session", "id")
    )


def test_missing_or_unsafe_context_has_no_public_text_and_does_not_create_data(
    tmp_path: Path,
) -> None:
    from escala_server.project_memory_continuity import ProjectMemoryContinuity

    turn = ProjectMemoryContinuity(tmp_path).resume()

    assert turn.prefix is None
    assert not (tmp_path / ".scaleup" / "memory" / "escala.db").exists()


def test_explicit_capture_requires_confirmation_and_keeps_ambiguous_pending(
    tmp_path: Path,
) -> None:
    from escala_server.project_memory_continuity import ProjectMemoryContinuity

    continuity = ProjectMemoryContinuity(tmp_path)
    pause = continuity.begin_pause()
    assert pause.stage == "capture"
    assert pause.session_id

    proposal = continuity.capture_statement(
        pause.session_id, "Contrataremos una líder de ventas en septiembre"
    )
    assert proposal.stage == "confirm"
    assert proposal.proposal_id
    assert "quieres que lo recuerde" in (proposal.next_question or "").lower()

    ambiguous = continuity.answer_confirmation(
        pause.session_id, proposal.proposal_id, "tal vez"
    )
    assert ambiguous.stage == "confirm"
    assert "no lo voy a dar por hecho" in (ambiguous.next_question or "").lower()

    confirmed = continuity.answer_confirmation(
        pause.session_id, proposal.proposal_id, "sí"
    )
    assert confirmed.stage == "normal"
    assert "próxima vez" in (confirmed.next_question or "").lower()


def test_public_policy_keeps_legitimate_business_data() -> None:
    from escala_server.project_memory_public_text import public_text

    assert public_text("Los datos de ventas son semanales") == (
        "Los datos de ventas son semanales"
    )
    assert public_text("El indicador clave de ventas es conversión") == (
        "El indicador clave de ventas es conversión"
    )
    assert public_text("El indicadorClaveDeVentas es conversión") == (
        "El indicadorClaveDeVentas es conversión"
    )
    assert public_text("El indicador clave de ventas requiere contraseña") is None


@pytest.mark.parametrize(
    "statement",
    (
        "La APIKey es abc",
        "La contraseña es abc",
        "La clave de acceso es abc",
        "El identificador es 42",
        "El sessionId es 42",
        "La base de datos está lista",
        "La base-de-datos está lista",
        "La base_de_datos está lista",
        "La baseDeDatos está lista",
        "Ejecuta el comando de ventas",
        "La habilidad de ventas está lista",
        "El log dice que sigamos",
        "La ruta es /tmp/secreto",
        "DBPassword=abc",
    ),
)
def test_public_policy_rejects_sensitive_or_technical_capture_before_proposal(
    tmp_path: Path, statement: str
) -> None:
    from escala_server.project_memory_continuity import ProjectMemoryContinuity

    continuity = ProjectMemoryContinuity(tmp_path)
    pause = continuity.begin_pause()
    assert pause.session_id

    response = continuity.capture_statement(pause.session_id, statement)

    assert response.stage == "normal"
    assert "no voy a guardar nada" in (response.next_question or "").lower()
    with sqlite3.connect(continuity.close.runtime.db_path) as db:
        assert (
            db.execute("SELECT COUNT(*) FROM session_memory_proposals").fetchone()[0]
            == 0
        )
        assert (
            db.execute("SELECT COUNT(*) FROM confirmed_memory_entries").fetchone()[0]
            == 0
        )


@pytest.mark.parametrize(
    "statement",
    (
        "La base-de-datos está lista",
        "La base_de_datos está lista",
        "La baseDeDatos está lista",
        "La contraseña del ERP es 1234",
        "The database password is 1234",
        "El identificador de sesión es 42",
        "The session ID is 42",
    ),
)
def test_unsafe_pause_capture_yes_resume_never_persists_or_resumes(
    tmp_path: Path, statement: str
) -> None:
    from escala_server.project_memory_continuity import ProjectMemoryContinuity

    continuity = ProjectMemoryContinuity(tmp_path)
    pause = continuity.begin_pause()
    assert pause.session_id

    capture = continuity.capture_statement(pause.session_id, statement)

    assert capture.stage == "normal"
    assert capture.proposal_id is None
    # A later affirmative reply cannot turn a rejected capture into memory.
    yes = continuity.answer_confirmation(pause.session_id, "missing-proposal", "sí")
    assert yes.stage == "normal"
    assert continuity.resume().prefix is None
    with sqlite3.connect(continuity.close.runtime.db_path) as db:
        assert (
            db.execute("SELECT COUNT(*) FROM session_memory_proposals").fetchone()[0]
            == 0
        )
        assert (
            db.execute("SELECT COUNT(*) FROM confirmed_memory_entries").fetchone()[0]
            == 0
        )


def test_context_projection_omits_legacy_sensitive_values_before_rendering(
    tmp_path: Path,
) -> None:
    from escala_server.project_memory_continuity import ProjectMemoryContinuity

    close = ProjectMemorySessionClose(tmp_path)
    assert close.open_session("s-safe").ready
    proposal = close.propose(
        "s-safe",
        MemoryCandidate(
            "fact",
            "El foco es puntualidad de entrega",
            CandidateSource("s-safe", ("obs-safe",), "explicit_user_statement"),
        ),
    )
    assert close.confirm(proposal.id or "", "sí").status == "confirmed"
    with sqlite3.connect(close.runtime.db_path) as db:
        db.execute(
            "UPDATE confirmed_memory_entries SET statement = 'La habilidad de ventas'"
        )
        db.execute(
            "UPDATE session_memory_proposals SET statement = 'La habilidad de ventas'"
        )

    assert ProjectMemoryContinuity(tmp_path).resume().prefix is None
