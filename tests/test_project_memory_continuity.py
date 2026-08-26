"""Public-language contract for the local memory continuity adapter."""

from pathlib import Path

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
