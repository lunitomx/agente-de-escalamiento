"""Explicit-consent, project-local memory session close bridge."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .project_memory import ProjectMemoryRuntime

MemoryKind = Literal["fact", "decision", "pattern"]


@dataclass(frozen=True)
class CandidateSource:
    """Auditable evidence identifiers, never transcript text or model output."""

    session_id: str
    observation_ids: tuple[str, ...]
    origin: str


@dataclass(frozen=True)
class MemoryCandidate:
    """A caller-prepared proposal that needs an explicit human response."""

    kind: MemoryKind
    statement: str
    source: CandidateSource
    replaces_entry_id: str | None = None


@dataclass(frozen=True)
class ProposalResult:
    ready: bool
    accepted: bool
    id: str | None = None
    status: Literal["proposed", "confirmed", "rejected", "invalid", "fallback"] = (
        "fallback"
    )
    reason: str | None = None


@dataclass(frozen=True)
class SessionCloseResult:
    ready: bool
    closed: bool
    reason: str | None = None


_SENSITIVE_PARTS = frozenset(
    {"api", "credential", "key", "password", "secret", "token"}
)
_SENSITIVE_COMPACT = frozenset(
    {
        "apikey",
        "accesskey",
        "authkey",
        "clientkey",
        "privatekey",
        "secretkey",
        "password",
        "secret",
        "token",
        "credential",
    }
)
_MAX_STATEMENT = 500
_MAX_IDENTIFIER = 160
_IDENTIFIER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,159}\Z")
_ABSOLUTE_PATH_RE = re.compile(r"(?:^|[\s\"'`=:(\[])(?:/|\\\\|[A-Za-z]:[\\/])")
_TRAVERSAL_PATH_RE = re.compile(r"(?:^|[\\/])\.\.(?:[\\/]|$)")
_TILDE_HOME_PATH_RE = re.compile(r"(?:^|[\s\"'`=:(\[])~[\\/]")


class ProjectMemorySessionClose:
    """Persist only caller-proposed, explicitly confirmed local memory."""

    def __init__(self, project_root: str | Path) -> None:
        self.runtime = ProjectMemoryRuntime(project_root)

    def open_session(self, session_id: str) -> SessionCloseResult:
        if not self._valid_identifier(session_id):
            return SessionCloseResult(False, False, "invalid_session")
        ready = self.runtime.ensure_memory()
        if not ready.ready:
            return self._close_fallback(ready.reason)
        try:
            with self._connection() as db:
                db.execute(
                    "INSERT OR IGNORE INTO project_memory_sessions (id, status) VALUES (?, 'open')",
                    (session_id,),
                )
            return SessionCloseResult(True, False)
        except sqlite3.Error:
            return self._close_fallback()

    def propose(self, session_id: str, candidate: MemoryCandidate) -> ProposalResult:
        invalid = self._candidate_reason(session_id, candidate)
        if invalid is not None:
            return ProposalResult(False, False, status="invalid", reason=invalid)
        ready = self.runtime.ensure_memory()
        if not ready.ready:
            return ProposalResult(
                False, False, status="fallback", reason="local_memory_unavailable"
            )
        fingerprint = self._fingerprint(candidate)
        try:
            with self._connection() as db:
                session = db.execute(
                    "SELECT status FROM project_memory_sessions WHERE id = ?",
                    (session_id,),
                ).fetchone()
                if session is None or session[0] != "open":
                    return ProposalResult(
                        True, False, status="invalid", reason="session_not_open"
                    )
                existing = db.execute(
                    "SELECT id, response_state FROM session_memory_proposals WHERE fingerprint = ?",
                    (fingerprint,),
                ).fetchone()
                if existing is not None:
                    return ProposalResult(True, True, existing[0], existing[1])
                proposal_id = str(uuid.uuid4())
                db.execute(
                    """INSERT INTO session_memory_proposals
                    (id, fingerprint, session_id, kind, statement, origin, observation_ids,
                     provenance_format_version, replaces_entry_id, response_state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 'proposed')""",
                    (
                        proposal_id,
                        fingerprint,
                        session_id,
                        candidate.kind,
                        candidate.statement.strip(),
                        candidate.source.origin,
                        json.dumps(candidate.source.observation_ids),
                        candidate.replaces_entry_id,
                    ),
                )
            return ProposalResult(True, True, proposal_id, "proposed")
        except sqlite3.Error:
            return ProposalResult(
                False, False, status="fallback", reason="local_memory_unavailable"
            )

    def confirm(self, proposal_id: str, answer: str) -> ProposalResult:
        if not self._valid_identifier(proposal_id):
            return ProposalResult(
                False, False, status="invalid", reason="invalid_proposal"
            )
        ready = self.runtime.health()
        if not ready.ready:
            return ProposalResult(
                False, False, status="fallback", reason="local_memory_unavailable"
            )
        response = self._response(answer)
        try:
            with self._connection() as db:
                row = db.execute(
                    """SELECT id, session_id, kind, statement, origin, observation_ids,
                              replaces_entry_id, response_state
                       FROM session_memory_proposals WHERE id = ?""",
                    (proposal_id,),
                ).fetchone()
                if row is None:
                    return ProposalResult(
                        True, False, status="invalid", reason="proposal_not_found"
                    )
                if row[7] != "proposed" or response is None:
                    return ProposalResult(
                        True,
                        True,
                        proposal_id,
                        row[7],
                        "confirmation_pending" if response is None else None,
                    )
                if response == "no":
                    db.execute(
                        "UPDATE session_memory_proposals SET response_state = 'rejected', responded_at = datetime('now') WHERE id = ?",
                        (proposal_id,),
                    )
                    return ProposalResult(True, True, proposal_id, "rejected")
                replacement = row[6]
                if replacement is not None and not self._valid_replacement(
                    db, replacement, row[2]
                ):
                    return ProposalResult(
                        True, False, proposal_id, "proposed", "invalid_replacement"
                    )
                entry_id = str(uuid.uuid4())
                source = json.dumps(
                    {
                        "session_id": row[1],
                        "origin": row[4],
                        "observation_ids": json.loads(row[5]),
                        "format_version": 1,
                    },
                    sort_keys=True,
                )
                db.execute(
                    """INSERT INTO confirmed_memory_entries
                    (id, proposal_id, session_id, kind, statement, source,
                     entry_format_version, provenance_format_version, confirmation_confidence,
                     confidence_reason, status, replaces_entry_id)
                    VALUES (?, ?, ?, ?, ?, ?, 1, 1, 1.0, 'explicit_confirmation', 'active', ?)""",
                    (
                        entry_id,
                        proposal_id,
                        row[1],
                        row[2],
                        row[3],
                        source,
                        replacement,
                    ),
                )
                if replacement is not None:
                    db.execute(
                        "UPDATE confirmed_memory_entries SET status = 'superseded' WHERE id = ?",
                        (replacement,),
                    )
                db.execute(
                    "UPDATE session_memory_proposals SET response_state = 'confirmed', responded_at = datetime('now') WHERE id = ?",
                    (proposal_id,),
                )
            return ProposalResult(True, True, proposal_id, "confirmed")
        except (sqlite3.Error, TypeError, ValueError):
            return ProposalResult(
                False, False, proposal_id, "fallback", "local_memory_unavailable"
            )

    def close(self, session_id: str) -> SessionCloseResult:
        if not self._valid_identifier(session_id):
            return SessionCloseResult(False, False, "invalid_session")
        ready = self.runtime.health()
        if not ready.ready:
            return self._close_fallback(ready.reason)
        try:
            with self._connection() as db:
                row = db.execute(
                    "SELECT status FROM project_memory_sessions WHERE id = ?",
                    (session_id,),
                ).fetchone()
                if row is None:
                    return SessionCloseResult(True, False, "session_not_open")
                if row[0] == "closed":
                    return SessionCloseResult(True, True)
                pending = db.execute(
                    "SELECT 1 FROM session_memory_proposals WHERE session_id = ? AND response_state = 'proposed' LIMIT 1",
                    (session_id,),
                ).fetchone()
                if pending is not None:
                    return SessionCloseResult(True, False, "confirmation_pending")
                db.execute(
                    "UPDATE project_memory_sessions SET status = 'closed', closed_at = datetime('now'), close_reason = 'all_resolved' WHERE id = ?",
                    (session_id,),
                )
            return SessionCloseResult(True, True)
        except sqlite3.Error:
            return self._close_fallback()

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.runtime.db_path)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @staticmethod
    def _response(answer: object) -> str | None:
        if not isinstance(answer, str):
            return None
        normalized = unicodedata.normalize("NFKC", answer).strip().casefold()
        return normalized if normalized in {"sí", "si", "yes", "no"} else None

    @staticmethod
    def _valid_identifier(value: object) -> bool:
        return (
            isinstance(value, str)
            and bool(_IDENTIFIER_RE.fullmatch(value))
            and not ProjectMemorySessionClose._sensitive(value)
        )

    def _candidate_reason(self, session_id: str, candidate: object) -> str | None:
        if not isinstance(candidate, MemoryCandidate) or not self._valid_identifier(
            session_id
        ):
            return "invalid_candidate"
        source = candidate.source
        if candidate.kind not in {"fact", "decision", "pattern"} or not isinstance(
            source, CandidateSource
        ):
            return "invalid_candidate"
        if (
            source.origin != "explicit_user_statement"
            or source.session_id != session_id
        ):
            return "invalid_source"
        statement = (
            candidate.statement.strip() if isinstance(candidate.statement, str) else ""
        )
        if (
            not statement
            or len(statement) > _MAX_STATEMENT
            or self._sensitive(statement)
            or self._has_external_path_form(statement)
        ):
            return "sensitive_or_invalid_statement"
        observations = source.observation_ids
        if not isinstance(observations, tuple) or not all(
            self._valid_identifier(item) for item in observations
        ):
            return "invalid_observations"
        required = 2 if candidate.kind == "pattern" else 1
        if len(observations) < required or len(set(observations)) != len(observations):
            return "insufficient_observations"
        if candidate.replaces_entry_id is not None and not self._valid_identifier(
            candidate.replaces_entry_id
        ):
            return "invalid_replacement"
        return None

    @staticmethod
    def _has_external_path_form(statement: str) -> bool:
        """Reject path-bearing proposals without treating ordinary prose as paths."""
        return bool(
            _ABSOLUTE_PATH_RE.search(statement)
            or _TRAVERSAL_PATH_RE.search(statement)
            or _TILDE_HOME_PATH_RE.search(statement)
        )

    @staticmethod
    def _sensitive(value: str) -> bool:
        normalized = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
        normalized = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", normalized).casefold()
        compact = re.sub(r"[^a-z0-9]+", "", normalized)
        tokens = set(re.split(r"[^a-z0-9]+", normalized))
        return bool(
            tokens & _SENSITIVE_PARTS
            or any(token in compact for token in _SENSITIVE_COMPACT)
        )

    @staticmethod
    def _fingerprint(candidate: MemoryCandidate) -> str:
        payload = json.dumps(
            {
                "kind": candidate.kind,
                "statement": candidate.statement.strip(),
                "source": candidate.source.__dict__,
                "replaces": candidate.replaces_entry_id,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def _valid_replacement(db: sqlite3.Connection, entry_id: str, kind: str) -> bool:
        row = db.execute(
            "SELECT kind, status FROM confirmed_memory_entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
        return row is not None and row[0] == kind and row[1] == "active"

    @staticmethod
    def _close_fallback(reason: str | None = None) -> SessionCloseResult:
        return SessionCloseResult(False, False, reason or "local_memory_unavailable")
