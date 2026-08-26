"""Contract tests for explicit, project-local consent memory."""

import sqlite3
import threading
from pathlib import Path

import pytest

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


def test_identifiers_must_be_opaque_and_never_persist_adversarial_input(
    tmp_path: Path,
) -> None:
    close = ProjectMemorySessionClose(tmp_path)
    assert (
        close.open_session("session transcript with words").reason == "invalid_session"
    )
    assert close.open_session("APIKey").reason == "invalid_session"
    assert close.open_session("s-1").ready
    for observations, replacement in (
        (("../../private",), None),
        (("I said the secret",), None),
        (("APIKey",), None),
        (("obs-1",), "../entry"),
    ):
        assert (
            close.propose(
                "s-1",
                candidate(observations=observations, replaces_entry_id=replacement),
            ).status
            == "invalid"
        )
    with sqlite3.connect(ProjectMemoryRuntime(tmp_path).db_path) as db:
        assert (
            db.execute("SELECT COUNT(*) FROM session_memory_proposals").fetchone()[0]
            == 0
        )
        assert (
            db.execute("SELECT COUNT(*) FROM confirmed_memory_entries").fetchone()[0]
            == 0
        )


def test_entries_record_immutable_entry_and_provenance_format_versions(
    tmp_path: Path,
) -> None:
    close = ProjectMemorySessionClose(tmp_path)
    assert close.open_session("s-1").ready
    proposal = close.propose("s-1", candidate())
    assert close.confirm(proposal.id or "", "yes").status == "confirmed"
    with sqlite3.connect(ProjectMemoryRuntime(tmp_path).db_path) as db:
        proposal_version = db.execute(
            "SELECT provenance_format_version FROM session_memory_proposals"
        ).fetchone()[0]
        entry = db.execute(
            "SELECT entry_format_version, provenance_format_version, source "
            "FROM confirmed_memory_entries"
        ).fetchone()
    assert proposal_version == 1
    assert entry[:2] == (1, 1)
    assert '"format_version": 1' in entry[2]


def test_v5_consent_tables_upgrade_format_columns_idempotently(tmp_path: Path) -> None:
    runtime = ProjectMemoryRuntime(tmp_path)
    assert runtime.ensure_memory().ready
    with sqlite3.connect(runtime.db_path) as db:
        db.execute("PRAGMA foreign_keys=OFF")
        db.execute("DROP TABLE session_memory_proposals")
        db.execute("DROP TABLE confirmed_memory_entries")
        db.execute("DROP TABLE project_memory_sessions")
        db.executescript(
            """
            CREATE TABLE project_memory_sessions (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL CHECK(status IN ('open', 'closed')),
                opened_at TEXT NOT NULL DEFAULT (datetime('now')),
                closed_at TEXT DEFAULT NULL,
                close_reason TEXT DEFAULT NULL
            );
            CREATE TABLE session_memory_proposals (
                id TEXT PRIMARY KEY,
                fingerprint TEXT NOT NULL UNIQUE,
                session_id TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('fact', 'decision', 'pattern')),
                statement TEXT NOT NULL,
                origin TEXT NOT NULL CHECK(origin = 'explicit_user_statement'),
                observation_ids TEXT NOT NULL,
                replaces_entry_id TEXT DEFAULT NULL,
                response_state TEXT NOT NULL CHECK(response_state IN ('proposed', 'confirmed', 'rejected')),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                responded_at TEXT DEFAULT NULL,
                FOREIGN KEY(session_id) REFERENCES project_memory_sessions(id),
                FOREIGN KEY(replaces_entry_id) REFERENCES confirmed_memory_entries(id)
            );
            CREATE TABLE confirmed_memory_entries (
                id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL UNIQUE,
                session_id TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('fact', 'decision', 'pattern')),
                statement TEXT NOT NULL,
                source TEXT NOT NULL,
                confirmation_confidence REAL NOT NULL CHECK(confirmation_confidence = 1.0),
                confidence_reason TEXT NOT NULL CHECK(confidence_reason = 'explicit_confirmation'),
                status TEXT NOT NULL CHECK(status IN ('active', 'superseded')),
                replaces_entry_id TEXT DEFAULT NULL,
                confirmed_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(proposal_id) REFERENCES session_memory_proposals(id),
                FOREIGN KEY(session_id) REFERENCES project_memory_sessions(id),
                FOREIGN KEY(replaces_entry_id) REFERENCES confirmed_memory_entries(id)
            );
            """
        )
        db.execute("UPDATE _meta SET value = ? WHERE key = ?", ("5", "schema_version"))

    assert runtime.ensure_memory().ready
    assert runtime.ensure_memory().ready
    with sqlite3.connect(runtime.db_path) as db:
        assert db.execute(
            "SELECT value FROM _meta WHERE key = ?", ("schema_version",)
        ).fetchone()[0] == str(SCHEMA_VERSION)
        proposal_columns = {
            row[1] for row in db.execute("PRAGMA table_info(session_memory_proposals)")
        }
        entry_columns = {
            row[1] for row in db.execute("PRAGMA table_info(confirmed_memory_entries)")
        }
    assert "provenance_format_version" in proposal_columns
    assert {"entry_format_version", "provenance_format_version"} <= entry_columns


def test_path_bearing_statements_are_rejected_before_any_proposal_persists(
    tmp_path: Path,
) -> None:
    close = ProjectMemorySessionClose(tmp_path)
    assert close.open_session("s-1").ready

    for statement in (
        "Guardar /etc/passwd como decisión",
        "Revisar ../../private/plan.yaml",
        r"Abrir C:\\Users\\owner\\secrets.txt",
        r"Consultar \\server\\share\\strategy.md",
        "~/private/plan.yaml",
        r"~\private\plan.yaml",
        "Guardar ~/private/plan.yaml como decisión",
        r"Guardar ~\private\plan.yaml como decisión",
    ):
        result = close.propose("s-1", candidate(statement=statement))
        assert result.status == "invalid"
        assert result.reason == "sensitive_or_invalid_statement"

    ordinary = close.propose(
        "s-1", candidate(statement="Aumentar margen mediante ventas B2B")
    )
    assert ordinary.status == "proposed"
    with sqlite3.connect(ProjectMemoryRuntime(tmp_path).db_path) as db:
        assert (
            db.execute("SELECT COUNT(*) FROM session_memory_proposals").fetchone()[0]
            == 1
        )


def test_environment_variable_path_forms_never_persist(tmp_path: Path) -> None:
    close = ProjectMemorySessionClose(tmp_path)
    assert close.open_session("s-1").ready
    for statement in (
        "Guardar $PLAN_ROOT/strategy.md como decisión",
        "Guardar ${PLAN_ROOT}/strategy.md como decisión",
        r"Guardar %PLAN_ROOT%\strategy.md como decisión",
    ):
        result = close.propose("s-1", candidate(statement=statement))
        assert result.status == "invalid"
        assert result.reason == "sensitive_or_invalid_statement"
    with sqlite3.connect(ProjectMemoryRuntime(tmp_path).db_path) as db:
        assert (
            db.execute("SELECT COUNT(*) FROM session_memory_proposals").fetchone()[0]
            == 0
        )


def test_threaded_close_never_closes_with_a_forced_pending_proposal(
    tmp_path: Path,
) -> None:
    close = ProjectMemorySessionClose(tmp_path)
    assert close.open_session("s-1").ready
    proposed = threading.Event()
    result: dict[str, object] = {}

    def propose() -> None:
        result["proposal"] = close.propose("s-1", candidate())
        proposed.set()

    def close_after_proposal() -> None:
        assert proposed.wait(timeout=2)
        result["close"] = ProjectMemorySessionClose(tmp_path).close("s-1")

    proposal_thread = threading.Thread(target=propose)
    close_thread = threading.Thread(target=close_after_proposal)
    proposal_thread.start()
    close_thread.start()
    proposal_thread.join(timeout=2)
    close_thread.join(timeout=2)

    assert not proposal_thread.is_alive()
    assert not close_thread.is_alive()
    assert result["proposal"].status == "proposed"  # type: ignore[union-attr]
    assert result["close"].reason == "confirmation_pending"  # type: ignore[union-attr]


def test_threaded_proposal_never_appears_after_a_forced_close(tmp_path: Path) -> None:
    close = ProjectMemorySessionClose(tmp_path)
    assert close.open_session("s-1").ready
    closed = threading.Event()
    result: dict[str, object] = {}

    def close_session() -> None:
        result["close"] = close.close("s-1")
        closed.set()

    def propose_after_close() -> None:
        assert closed.wait(timeout=2)
        result["proposal"] = ProjectMemorySessionClose(tmp_path).propose(
            "s-1", candidate()
        )

    close_thread = threading.Thread(target=close_session)
    proposal_thread = threading.Thread(target=propose_after_close)
    close_thread.start()
    proposal_thread.start()
    close_thread.join(timeout=2)
    proposal_thread.join(timeout=2)

    assert not close_thread.is_alive()
    assert not proposal_thread.is_alive()
    assert result["close"].closed  # type: ignore[union-attr]
    assert result["proposal"].reason == "session_not_open"  # type: ignore[union-attr]


def test_close_cannot_pass_a_proposal_already_inside_its_transaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A close waits for an in-flight proposal before deciding it has no pending work."""
    close = ProjectMemorySessionClose(tmp_path)
    assert close.open_session("s-1").ready
    proposal_read = threading.Event()
    close_attempted_begin = threading.Event()
    release_proposal = threading.Event()
    result: dict[str, object] = {}

    original_begin = ProjectMemorySessionClose._begin_immediate

    class ProposalConnection(sqlite3.Connection):
        def execute(self, statement: str, parameters: object = ()) -> sqlite3.Cursor:
            cursor = super().execute(statement, parameters)
            if (
                "SELECT status FROM project_memory_sessions" in statement
                and not proposal_read.is_set()
            ):
                proposal_read.set()
                release_proposal.wait(timeout=5)
            return cursor

    def proposal_connection() -> sqlite3.Connection:
        db = sqlite3.connect(
            close.runtime.db_path, isolation_level=None, factory=ProposalConnection
        )
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def observe_close_begin(db: sqlite3.Connection) -> None:
        if threading.current_thread().name == "competing-close":
            close_attempted_begin.set()
        original_begin(db)

    monkeypatch.setattr(close, "_connection", proposal_connection)
    monkeypatch.setattr(
        ProjectMemorySessionClose,
        "_begin_immediate",
        staticmethod(observe_close_begin),
    )

    def propose() -> None:
        result["proposal"] = close.propose("s-1", candidate())

    def close_session() -> None:
        result["close"] = ProjectMemorySessionClose(tmp_path).close("s-1")

    proposal_thread = threading.Thread(target=propose, name="in-flight-proposal")
    close_thread = threading.Thread(target=close_session, name="competing-close")
    proposal_thread.start()
    assert proposal_read.wait(timeout=2)
    close_thread.start()
    assert close_attempted_begin.wait(timeout=2)
    release_proposal.set()
    proposal_thread.join(timeout=5)
    close_thread.join(timeout=5)

    assert not proposal_thread.is_alive()
    assert not close_thread.is_alive()
    assert result["proposal"].status == "proposed"  # type: ignore[union-attr]
    assert result["close"].reason == "confirmation_pending"  # type: ignore[union-attr]
    with sqlite3.connect(ProjectMemoryRuntime(tmp_path).db_path) as db:
        assert (
            db.execute(
                "SELECT status FROM project_memory_sessions WHERE id = 's-1'"
            ).fetchone()[0]
            == "open"
        )
        assert (
            db.execute(
                "SELECT response_state FROM session_memory_proposals"
            ).fetchone()[0]
            == "proposed"
        )


def test_proposal_cannot_pass_a_close_already_inside_its_transaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A proposal waits for an in-flight close before accepting an open session."""
    close = ProjectMemorySessionClose(tmp_path)
    assert close.open_session("s-1").ready
    close_read = threading.Event()
    proposal_attempted_begin = threading.Event()
    release_close = threading.Event()
    result: dict[str, object] = {}

    original_begin = ProjectMemorySessionClose._begin_immediate

    class CloseConnection(sqlite3.Connection):
        def execute(self, statement: str, parameters: object = ()) -> sqlite3.Cursor:
            cursor = super().execute(statement, parameters)
            if (
                "SELECT 1 FROM session_memory_proposals" in statement
                and not close_read.is_set()
            ):
                close_read.set()
                release_close.wait(timeout=5)
            return cursor

    def close_connection() -> sqlite3.Connection:
        db = sqlite3.connect(
            close.runtime.db_path, isolation_level=None, factory=CloseConnection
        )
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def observe_proposal_begin(db: sqlite3.Connection) -> None:
        if threading.current_thread().name == "competing-proposal":
            proposal_attempted_begin.set()
        original_begin(db)

    monkeypatch.setattr(close, "_connection", close_connection)
    monkeypatch.setattr(
        ProjectMemorySessionClose,
        "_begin_immediate",
        staticmethod(observe_proposal_begin),
    )

    def close_session() -> None:
        result["close"] = close.close("s-1")

    def propose() -> None:
        result["proposal"] = ProjectMemorySessionClose(tmp_path).propose(
            "s-1", candidate()
        )

    close_thread = threading.Thread(target=close_session, name="in-flight-close")
    proposal_thread = threading.Thread(target=propose, name="competing-proposal")
    close_thread.start()
    assert close_read.wait(timeout=2)
    proposal_thread.start()
    assert proposal_attempted_begin.wait(timeout=2)
    release_close.set()
    close_thread.join(timeout=5)
    proposal_thread.join(timeout=5)

    assert not close_thread.is_alive()
    assert not proposal_thread.is_alive()
    assert result["close"].closed  # type: ignore[union-attr]
    assert result["proposal"].reason == "session_not_open"  # type: ignore[union-attr]
    with sqlite3.connect(ProjectMemoryRuntime(tmp_path).db_path) as db:
        assert (
            db.execute(
                "SELECT status FROM project_memory_sessions WHERE id = 's-1'"
            ).fetchone()[0]
            == "closed"
        )
        assert (
            db.execute("SELECT COUNT(*) FROM session_memory_proposals").fetchone()[0]
            == 0
        )
