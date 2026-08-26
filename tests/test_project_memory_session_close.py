"""Contract tests for explicit, project-local consent memory."""

import sqlite3
from pathlib import Path

from escala_server.project_memory import ProjectMemoryRuntime
from escala_server.project_memory_session_close import (
    CandidateSource,
    MemoryCandidate,
    ProjectMemorySessionClose,
)
from escala_server.schema import SCHEMA_VERSION


def candidate(
    kind: str = "fact",
    statement: str = "Meta Q4: 2 M",
    observations: tuple[str, ...] = ("obs-1",),
    **kwargs: object,
) -> MemoryCandidate:
    return MemoryCandidate(
        kind=kind,  # type: ignore[arg-type]
        statement=statement,
        source=CandidateSource(
            "s-1", observations, kwargs.pop("origin", "explicit_user_statement")
        ),  # type: ignore[arg-type]
        **kwargs,
    )


def test_v5_creates_local_consent_tables_and_upgrades_v4(tmp_path: Path) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready
    with sqlite3.connect(runtime.db_path) as db:
        db.execute("UPDATE _meta SET value = '4' WHERE key = 'schema_version'")
    result = runtime.ensure_memory()
    assert result.ready
    with sqlite3.connect(runtime.db_path) as db:
        assert db.execute(
            "SELECT value FROM _meta WHERE key = 'schema_version'"
        ).fetchone()[0] == str(SCHEMA_VERSION)
        assert {
            row[0]
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        } >= {
            "project_memory_sessions",
            "session_memory_proposals",
            "confirmed_memory_entries",
        }


def test_proposal_needs_explicit_yes_and_persists_auditable_entry(
    tmp_path: Path,
) -> None:
    close = ProjectMemorySessionClose(tmp_path)
    assert close.open_session("s-1").ready
    proposal = close.propose(
        "s-1", candidate(kind="decision", statement="Contratar líder de ventas")
    )
    assert proposal.status == "proposed"
    assert close.confirm(proposal.id or "", "tal vez").status == "proposed"
    confirmed = close.confirm(proposal.id or "", " Sí ")
    assert confirmed.status == "confirmed"
    assert close.confirm(proposal.id or "", "sí").status == "confirmed"
    with sqlite3.connect(ProjectMemoryRuntime(tmp_path).db_path) as db:
        entry = db.execute(
            "SELECT kind, statement, source, confirmation_confidence, confidence_reason, status FROM confirmed_memory_entries"
        ).fetchone()
        assert entry[:2] == ("decision", "Contratar líder de ventas")
        assert '"origin": "explicit_user_statement"' in entry[2]
        assert entry[3:] == (1.0, "explicit_confirmation", "active")
        assert db.execute("SELECT COUNT(*) FROM memory_facts").fetchone()[0] == 0


def test_reject_pending_and_close_state_machine(tmp_path: Path) -> None:
    close = ProjectMemorySessionClose(tmp_path)
    close.open_session("s-1")
    rejected = close.propose(
        "s-1", candidate(kind="pattern", observations=("o-1", "o-2"))
    )
    pending = close.propose(
        "s-1", candidate(statement="Caja 320000", observations=("o-3",))
    )
    assert close.confirm(rejected.id or "", "no").status == "rejected"
    assert close.close("s-1").reason == "confirmation_pending"
    assert close.confirm(pending.id or "", "yes").status == "confirmed"
    assert close.close("s-1").closed
    assert close.close("s-1").closed


def test_invalid_inference_secrets_and_pattern_evidence_never_persist(
    tmp_path: Path,
) -> None:
    close = ProjectMemorySessionClose(tmp_path)
    close.open_session("s-1")
    assert close.propose("s-1", candidate(origin="model_inference")).status == "invalid"
    assert close.propose("s-1", candidate(statement="APIKey=abc")).status == "invalid"
    assert close.propose("s-1", candidate(kind="pattern")).status == "invalid"
    with sqlite3.connect(ProjectMemoryRuntime(tmp_path).db_path) as db:
        assert (
            db.execute("SELECT COUNT(*) FROM session_memory_proposals").fetchone()[0]
            == 0
        )


def test_confirmation_failure_rolls_back_the_state_transition(tmp_path: Path) -> None:
    close = ProjectMemorySessionClose(tmp_path)
    close.open_session("s-1")
    proposal = close.propose("s-1", candidate())
    db_path = ProjectMemoryRuntime(tmp_path).db_path
    with sqlite3.connect(db_path) as db:
        db.execute(
            """CREATE TRIGGER reject_entry BEFORE INSERT ON confirmed_memory_entries
            BEGIN SELECT RAISE(ABORT, 'injected'); END"""
        )
    assert close.confirm(proposal.id or "", "yes").status == "fallback"
    with sqlite3.connect(db_path) as db:
        assert (
            db.execute(
                "SELECT response_state FROM session_memory_proposals WHERE id = ?",
                (proposal.id,),
            ).fetchone()[0]
            == "proposed"
        )
        assert (
            db.execute("SELECT COUNT(*) FROM confirmed_memory_entries").fetchone()[0]
            == 0
        )


def test_isolation_conflicts_and_explicit_replacement(tmp_path: Path) -> None:
    first = ProjectMemorySessionClose(tmp_path / "a")
    second = ProjectMemorySessionClose(tmp_path / "b")
    first.open_session("s-1")
    second.open_session("s-1")
    one = first.propose("s-1", candidate(kind="decision", statement="Abrir Monterrey"))
    assert first.confirm(one.id or "", "si").status == "confirmed"
    with sqlite3.connect(ProjectMemoryRuntime(tmp_path / "a").db_path) as db:
        entry_id = db.execute("SELECT id FROM confirmed_memory_entries").fetchone()[0]
    conflict = first.propose(
        "s-1",
        candidate(
            kind="decision", statement="No abrir Monterrey", observations=("o-2",)
        ),
    )
    assert first.confirm(conflict.id or "", "yes").status == "confirmed"
    replacement = first.propose(
        "s-1",
        candidate(
            kind="decision",
            statement="Abrir Guadalajara",
            observations=("o-3",),
            replaces_entry_id=entry_id,
        ),
    )
    assert first.confirm(replacement.id or "", "yes").status == "confirmed"
    with sqlite3.connect(ProjectMemoryRuntime(tmp_path / "a").db_path) as db:
        assert (
            db.execute(
                "SELECT status FROM confirmed_memory_entries WHERE id = ?", (entry_id,)
            ).fetchone()[0]
            == "superseded"
        )
        assert (
            db.execute("SELECT COUNT(*) FROM confirmed_memory_entries").fetchone()[0]
            == 3
        )
    assert second.close("s-1").closed
