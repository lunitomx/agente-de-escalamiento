"""Consent-first Accountability Group sessions, commitments and patterns."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from .project_memory import ProjectMemoryRuntime

Decision = Literal["people", "strategy", "execution", "cash"]
SourceType = Literal["manual", "imported_document", "drive_connector"]
ReviewState = Literal["done", "partial", "not_done", "renegotiated"]

WORKSHEET_FIELDS = (
    "personal_update",
    "business_update",
    "issue_statement",
    "pillar_and_tool",
    "background",
    "current_situation",
    "future_options",
    "uncertainty",
    "own_contribution",
    "failure_impact",
    "personal_challenge",
    "desired_outcome",
    "notes",
)
_MAX_TEXT = 5000
_SENSITIVE = {
    "credenciales": re.compile(r"\b(password|contrase(?:n|ñ)a|api[ -]?key|token|secret)\b", re.I),
    "identificadores": re.compile(r"\b(curp|rfc|pasaporte|tarjeta|cuenta bancaria|clabe)\b", re.I),
    "salud": re.compile(r"\b(c[aá]ncer|diagn[oó]stico m[eé]dico|quimio|salud mental)\b", re.I),
    "legal": re.compile(r"\b(demanda|litigio|abogado|proceso legal)\b", re.I),
    "finanzas": re.compile(r"(?:[$€£]\s?\d|\b(?:usd|mxn|mdp)\b)", re.I),
}


@dataclass(frozen=True)
class ImportPreview:
    """Parsed material held only in memory until the user confirms storage."""

    worksheet: dict[str, Any]
    held_on: str
    source_type: SourceType
    source_ref: str
    content_sha256: str
    warnings: tuple[str, ...]
    recognized_fields: tuple[str, ...]


@dataclass(frozen=True)
class AccountabilityResult:
    ready: bool
    data: dict[str, Any] | None = None
    reason: str | None = None


class AccountabilityStore:
    """Own one project's explicitly confirmed Accountability record."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.runtime = ProjectMemoryRuntime(self.project_root)

    def preview_import(
        self,
        text: str,
        *,
        title: str,
        held_on: str,
        source_type: SourceType = "imported_document",
    ) -> ImportPreview:
        clean = _text(text, "document", maximum=100_000)
        worksheet = _parse_eo_worksheet(clean)
        warnings = tuple(name for name, pattern in _SENSITIVE.items() if pattern.search(clean))
        return ImportPreview(
            worksheet=worksheet,
            held_on=_date(held_on, "held_on"),
            source_type=_source_type(source_type),
            source_ref=_text(title, "title", maximum=240),
            content_sha256=hashlib.sha256(clean.encode()).hexdigest(),
            warnings=warnings,
            recognized_fields=tuple(key for key in WORKSHEET_FIELDS if worksheet.get(key)),
        )

    def confirm_import(
        self, preview: ImportPreview, *, explicit_confirmation: bool
    ) -> AccountabilityResult:
        if not explicit_confirmation:
            return AccountabilityResult(False, reason="explicit confirmation is required")
        return self.create_session(
            preview.worksheet,
            held_on=preview.held_on,
            source_type=preview.source_type,
            source_ref=preview.source_ref,
            explicit_confirmation=True,
        )

    def create_session(
        self,
        worksheet: dict[str, Any],
        *,
        held_on: str,
        source_type: SourceType = "manual",
        source_ref: str = "Captura guiada",
        tags: list[str] | tuple[str, ...] = (),
        explicit_confirmation: bool,
    ) -> AccountabilityResult:
        if not explicit_confirmation:
            return AccountabilityResult(False, reason="explicit confirmation is required")
        try:
            clean = _worksheet(worksheet)
            clean_tags = _tags(tags)
            decision = _decision(clean.get("decision_area") or clean.get("pillar_and_tool"))
            confidence = _confidence(clean.get("confidence"))
            if confidence is not None:
                clean["confidence"] = confidence
            status = "ready" if _ready(clean) else "draft"
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return AccountabilityResult(False, reason=memory.reason)
            session_id = str(uuid4())
            consented = _now()
            with sqlite3.connect(memory.db_path) as db:
                db.execute(
                    """INSERT INTO accountability_sessions
                       (id, held_on, source_type, source_ref, worksheet_json,
                        decision_area, confidence, tags_json, status, consented_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        session_id,
                        _date(held_on, "held_on"),
                        _source_type(source_type),
                        _text(source_ref, "source_ref", maximum=240),
                        json.dumps(clean, ensure_ascii=False, sort_keys=True),
                        decision,
                        confidence,
                        json.dumps(clean_tags, ensure_ascii=False),
                        status,
                        consented,
                    ),
                )
                db.commit()
            return AccountabilityResult(True, self.get_session(session_id).data)
        except (OSError, sqlite3.Error, TypeError, ValueError) as error:
            return AccountabilityResult(False, reason=str(error))

    def update_session(
        self,
        session_id: str,
        changes: dict[str, Any],
        *,
        tags: list[str] | tuple[str, ...] | None = None,
        explicit_confirmation: bool,
    ) -> AccountabilityResult:
        if not explicit_confirmation:
            return AccountabilityResult(False, reason="explicit confirmation is required")
        try:
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return AccountabilityResult(False, reason=memory.reason)
            with sqlite3.connect(memory.db_path) as db:
                row = db.execute(
                    "SELECT worksheet_json, tags_json FROM accountability_sessions WHERE id=?",
                    (_id(session_id),),
                ).fetchone()
                if row is None:
                    return AccountabilityResult(False, reason="session not found")
                current = json.loads(row[0])
                current.update(_worksheet(changes))
                current = _worksheet(current)
                current_tags = _tags(tags if tags is not None else json.loads(row[1]))
                decision = _decision(current.get("decision_area") or current.get("pillar_and_tool"))
                confidence = _confidence(current.get("confidence"))
                db.execute(
                    """UPDATE accountability_sessions SET worksheet_json=?, decision_area=?,
                       confidence=?, tags_json=?, status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                    (
                        json.dumps(current, ensure_ascii=False, sort_keys=True),
                        decision,
                        confidence,
                        json.dumps(current_tags, ensure_ascii=False),
                        "ready" if _ready(current) else "draft",
                        session_id,
                    ),
                )
                db.commit()
            return self.get_session(session_id)
        except (OSError, sqlite3.Error, TypeError, ValueError, json.JSONDecodeError) as error:
            return AccountabilityResult(False, reason=str(error))

    def get_session(self, session_id: str) -> AccountabilityResult:
        try:
            memory = self.runtime.health()
            if not memory.ready:
                return AccountabilityResult(False, reason=memory.reason)
            with sqlite3.connect(memory.db_path) as db:
                db.row_factory = sqlite3.Row
                row = db.execute(
                    "SELECT * FROM accountability_sessions WHERE id=?", (_id(session_id),)
                ).fetchone()
                if row is None:
                    return AccountabilityResult(False, reason="session not found")
                commitments = db.execute(
                    "SELECT * FROM accountability_commitments WHERE session_id=? ORDER BY created_at, id",
                    (session_id,),
                ).fetchall()
            return AccountabilityResult(True, _session_row(row, commitments))
        except (OSError, sqlite3.Error, ValueError, json.JSONDecodeError) as error:
            return AccountabilityResult(False, reason=str(error))

    def list_sessions(self, *, include_excluded: bool = False) -> AccountabilityResult:
        try:
            memory = self.runtime.health()
            if not memory.ready:
                return AccountabilityResult(True, {"sessions": []})
            where = "" if include_excluded else "WHERE included=1"
            with sqlite3.connect(memory.db_path) as db:
                db.row_factory = sqlite3.Row
                rows = db.execute(
                    f"SELECT * FROM accountability_sessions {where} ORDER BY held_on, created_at, id"
                ).fetchall()
            return AccountabilityResult(
                True, {"sessions": [_session_row(row, ()) for row in rows]}
            )
        except (OSError, sqlite3.Error, json.JSONDecodeError) as error:
            return AccountabilityResult(False, reason=str(error))

    def latest_session(self) -> AccountabilityResult:
        listed = self.list_sessions()
        if not listed.ready or not listed.data:
            return listed
        sessions = listed.data["sessions"]
        if not sessions:
            return AccountabilityResult(False, reason="no accountability sessions")
        return self.get_session(sessions[-1]["id"])

    def latest_pending_commitment(self) -> AccountabilityResult:
        try:
            memory = self.runtime.health()
            if not memory.ready:
                return AccountabilityResult(False, reason="no accountability commitments")
            with sqlite3.connect(memory.db_path) as db:
                db.row_factory = sqlite3.Row
                row = db.execute(
                    """SELECT c.*, s.held_on FROM accountability_commitments c
                       JOIN accountability_sessions s ON s.id=c.session_id
                       WHERE s.included=1 AND c.status='planned'
                       ORDER BY s.held_on DESC, c.created_at DESC, c.id DESC LIMIT 1"""
                ).fetchone()
            return (
                AccountabilityResult(True, dict(row))
                if row is not None
                else AccountabilityResult(False, reason="no pending accountability commitment")
            )
        except (OSError, sqlite3.Error) as error:
            return AccountabilityResult(False, reason=str(error))

    def set_included(
        self,
        session_id: str,
        *,
        included: bool,
        reason: str,
        explicit_confirmation: bool,
    ) -> AccountabilityResult:
        if not explicit_confirmation:
            return AccountabilityResult(False, reason="explicit confirmation is required")
        try:
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return AccountabilityResult(False, reason=memory.reason)
            with sqlite3.connect(memory.db_path) as db:
                exists = db.execute(
                    "SELECT 1 FROM accountability_sessions WHERE id=?", (_id(session_id),)
                ).fetchone()
                if not exists:
                    return AccountabilityResult(False, reason="session not found")
                db.execute(
                    "UPDATE accountability_sessions SET included=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (1 if included else 0, session_id),
                )
                db.execute(
                    "INSERT INTO accountability_exclusions (id, session_id, state, reason) VALUES (?, ?, ?, ?)",
                    (
                        str(uuid4()),
                        session_id,
                        "included" if included else "excluded",
                        _text(reason, "reason", maximum=500),
                    ),
                )
                db.commit()
            return self.get_session(session_id)
        except (OSError, sqlite3.Error, ValueError) as error:
            return AccountabilityResult(False, reason=str(error))

    def add_commitment(
        self,
        session_id: str,
        *,
        statement: str,
        owner: str,
        due_on: str,
        success_measure: str,
        explicit_confirmation: bool,
    ) -> AccountabilityResult:
        if not explicit_confirmation:
            return AccountabilityResult(False, reason="explicit confirmation is required")
        try:
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return AccountabilityResult(False, reason=memory.reason)
            commitment_id = str(uuid4())
            with sqlite3.connect(memory.db_path) as db:
                if db.execute(
                    "SELECT 1 FROM accountability_sessions WHERE id=?", (_id(session_id),)
                ).fetchone() is None:
                    return AccountabilityResult(False, reason="session not found")
                db.execute(
                    """INSERT INTO accountability_commitments
                       (id, session_id, statement, owner, due_on, success_measure, status)
                       VALUES (?, ?, ?, ?, ?, ?, 'planned')""",
                    (
                        commitment_id,
                        session_id,
                        _text(statement, "statement", maximum=1000),
                        _text(owner, "owner", maximum=240),
                        _date(due_on, "due_on"),
                        _text(success_measure, "success_measure", maximum=1000),
                    ),
                )
                db.commit()
            return AccountabilityResult(True, {"commitment_id": commitment_id})
        except (OSError, sqlite3.Error, ValueError) as error:
            return AccountabilityResult(False, reason=str(error))

    def review_commitment(
        self,
        commitment_id: str,
        *,
        status: ReviewState,
        result: str,
        evidence: str | None,
        blocker: str | None,
        learning: str | None,
        reviewed_on: str,
        explicit_confirmation: bool,
    ) -> AccountabilityResult:
        if not explicit_confirmation:
            return AccountabilityResult(False, reason="explicit confirmation is required")
        try:
            state = _review_state(status)
            result_text = _text(result, "result", maximum=2000)
            evidence_text = _optional_text(evidence, "evidence", 2000)
            blocker_text = _optional_text(blocker, "blocker", 1000)
            learning_text = _optional_text(learning, "learning", 2000)
            if state in {"done", "partial"} and not evidence_text:
                raise ValueError("done or partial review requires evidence")
            if state in {"not_done", "renegotiated"} and not (blocker_text or learning_text):
                raise ValueError("unfinished review requires a blocker or learning")
            review_date = _date(reviewed_on, "reviewed_on")
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return AccountabilityResult(False, reason=memory.reason)
            with sqlite3.connect(memory.db_path) as db:
                row = db.execute(
                    "SELECT due_on, session_id FROM accountability_commitments WHERE id=?",
                    (_id(commitment_id),),
                ).fetchone()
                if row is None:
                    return AccountabilityResult(False, reason="commitment not found")
                rubric = _rubric(
                    state,
                    evidence=bool(evidence_text),
                    on_time=date.fromisoformat(review_date) <= date.fromisoformat(row[0]),
                    learning=bool(learning_text),
                )
                db.execute(
                    """UPDATE accountability_commitments SET status=?, evidence=?, result=?,
                       blocker=?, learning=?, reviewed_on=?, rubric_json=?,
                       follow_through_percent=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                    (
                        state,
                        evidence_text,
                        result_text,
                        blocker_text,
                        learning_text,
                        review_date,
                        json.dumps(rubric, ensure_ascii=False, sort_keys=True),
                        rubric["percent"],
                        commitment_id,
                    ),
                )
                db.execute(
                    "UPDATE accountability_sessions SET status='reviewed', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (row[1],),
                )
                db.commit()
            return AccountabilityResult(True, {"commitment_id": commitment_id, "rubric": rubric})
        except (OSError, sqlite3.Error, ValueError) as error:
            return AccountabilityResult(False, reason=str(error))

    def patterns(self) -> AccountabilityResult:
        """Return deterministic patterns plus their exact supporting sessions."""
        try:
            memory = self.runtime.health()
            if not memory.ready:
                return AccountabilityResult(True, _empty_patterns())
            with sqlite3.connect(memory.db_path) as db:
                db.row_factory = sqlite3.Row
                sessions = db.execute(
                    "SELECT * FROM accountability_sessions WHERE included=1 ORDER BY held_on, id"
                ).fetchall()
                commitments = db.execute(
                    """SELECT c.* FROM accountability_commitments c
                       JOIN accountability_sessions s ON s.id=c.session_id
                       WHERE s.included=1 ORDER BY s.held_on, c.id"""
                ).fetchall()
            return AccountabilityResult(True, _patterns(sessions, commitments))
        except (OSError, sqlite3.Error, json.JSONDecodeError) as error:
            return AccountabilityResult(False, reason=str(error))

    def public_summary(self) -> AccountabilityResult:
        """Return a dashboard-safe view without personal or worksheet narratives."""
        listed = self.list_sessions()
        patterns = self.patterns()
        if not listed.ready:
            return listed
        if not patterns.ready:
            return patterns
        sessions = []
        for item in (listed.data or {}).get("sessions", []):
            detailed = self.get_session(item["id"])
            commitments = []
            for commitment in (detailed.data or {}).get("commitments", []):
                rubric = commitment.get("rubric_json")
                commitments.append(
                    {
                        "id": commitment["id"],
                        "statement": commitment["statement"],
                        "owner": commitment["owner"],
                        "due_on": commitment["due_on"],
                        "success_measure": commitment["success_measure"],
                        "status": commitment["status"],
                        "reviewed_on": commitment.get("reviewed_on"),
                        "follow_through_percent": commitment.get("follow_through_percent"),
                        "rubric": json.loads(rubric) if rubric else None,
                    }
                )
            sessions.append(
                {
                    "id": item["id"],
                    "held_on": item["held_on"],
                    "decision_area": item["decision_area"],
                    "tags": item["tags"],
                    "status": item["status"],
                    "source": item["source"],
                    "commitments": commitments,
                }
            )
        evidence_dates = {item["id"]: item["held_on"] for item in sessions}
        pattern_data = dict(patterns.data or _empty_patterns())
        for group in ("patterns", "observations"):
            pattern_data[group] = [
                {
                    **item,
                    "evidence_dates": [
                        evidence_dates.get(session_id, session_id)
                        for session_id in item.get("session_ids", [])
                    ],
                }
                for item in pattern_data.get(group, [])
            ]
        return AccountabilityResult(
            True,
            {
                "state": "ready" if sessions else "empty",
                "privacy": "No incluye actualización personal ni narrativa del worksheet.",
                "sessions": sessions,
                "analysis": pattern_data,
            },
        )


def _parse_eo_worksheet(text: str) -> dict[str, Any]:
    fields = {
        "personal_update": _between(text, ("Personal:",), ("Business:",)),
        "business_update": _between(text, ("Business:",), ("Accountability Group Sharing",)),
        "issue_statement": _between(
            text,
            ("What is the situation you want to share with the group?",),
            ("2. What Scaling Up Pillar",),
        ),
        "pillar_and_tool": _between(
            text,
            ("Have you tried to implement the tool? Yes or No?",),
            ("3. Overview of Presentation", "3. Overview"),
        ),
        "background": _between(text, ("Background",), ("Current Situation",)),
        "current_situation": _between(text, ("Current Situation",), ("Future Options",)),
        "future_options": _between(text, ("Future Options",), ("4. Digging Deeper",)),
        "uncertainty": _between(
            text,
            ("Where do you feel most uncertain, confused or afraid?",),
            ("How might your own actions",),
        ),
        "own_contribution": _between(
            text,
            ("How might your own actions be contributing to the challenge you face?",),
            ("What would failing in this issue mean",),
        ),
        "failure_impact": _between(
            text,
            ("What would failing in this issue mean for you and those around you?",),
            ("What is your biggest personal challenge",),
        ),
        "personal_challenge": _between(
            text,
            ("What is your biggest personal challenge in facing this situation? What feelings do you have about the situation?",),
            ("What is the outcome you hope for?",),
        ),
        "desired_outcome": _between(
            text,
            ("What is the outcome you hope for?",),
            ("Notes:", "Notes"),
        ),
        "notes": _between(text, ("Notes:", "Notes"), ()),
    }
    fields = {key: value for key, value in fields.items() if value}
    pillar = fields.get("pillar_and_tool", "")
    decision = _decision(pillar)
    if decision:
        fields["decision_area"] = decision
    confidence_matches = re.findall(r"(?<!\d)(100|[1-9]?\d)\s*%", fields.get("desired_outcome", ""))
    if confidence_matches:
        fields["confidence"] = int(confidence_matches[-1])
    return fields


def _between(text: str, starts: tuple[str, ...], ends: tuple[str, ...]) -> str:
    start_positions = [(text.find(marker), marker) for marker in starts if text.find(marker) >= 0]
    if not start_positions:
        return ""
    position, marker = min(start_positions)
    begin = position + len(marker)
    end_positions = [text.find(end, begin) for end in ends if text.find(end, begin) >= 0]
    finish = min(end_positions) if end_positions else len(text)
    return " ".join(text[begin:finish].strip().split())[:_MAX_TEXT]


def _patterns(sessions: list[sqlite3.Row], commitments: list[sqlite3.Row]) -> dict[str, Any]:
    decision_support: dict[str, list[str]] = defaultdict(list)
    tag_support: dict[str, list[str]] = defaultdict(list)
    for row in sessions:
        if row["decision_area"]:
            decision_support[row["decision_area"]].append(row["id"])
        for tag in json.loads(row["tags_json"]):
            tag_support[tag].append(row["id"])

    blocker_support: dict[str, list[str]] = defaultdict(list)
    blocker_labels: dict[str, str] = {}
    reviewed = []
    high_confidence_misses = []
    sessions_by_id = {row["id"]: row for row in sessions}
    for row in commitments:
        if row["status"] != "planned":
            reviewed.append(row)
        if row["blocker"]:
            normalized = _normalize(row["blocker"])
            blocker_support[normalized].append(row["session_id"])
            blocker_labels.setdefault(normalized, row["blocker"])
        session = sessions_by_id.get(row["session_id"])
        if (
            session
            and session["confidence"] is not None
            and session["confidence"] >= 80
            and row["status"] in {"partial", "not_done", "renegotiated"}
        ):
            high_confidence_misses.append(session["id"])

    findings = []
    observations = []
    for decision, ids in sorted(decision_support.items()):
        item = {"kind": "decision_frequency", "label": decision, "count": len(ids), "session_ids": sorted(set(ids))}
        (findings if len(set(ids)) >= 2 else observations).append(item)
    for tag, ids in sorted(tag_support.items()):
        item = {"kind": "confirmed_theme", "label": tag, "count": len(set(ids)), "session_ids": sorted(set(ids))}
        (findings if len(set(ids)) >= 2 else observations).append(item)
    for normalized, ids in sorted(blocker_support.items()):
        item = {"kind": "repeated_blocker", "label": blocker_labels[normalized], "count": len(set(ids)), "session_ids": sorted(set(ids))}
        (findings if len(set(ids)) >= 2 else observations).append(item)
    unique_misses = sorted(set(high_confidence_misses))
    if unique_misses:
        item = {"kind": "confidence_gap", "label": "Confianza ≥80 con compromiso incompleto", "count": len(unique_misses), "session_ids": unique_misses}
        (findings if len(unique_misses) >= 2 else observations).append(item)

    outcome_counts = Counter(row["status"] for row in reviewed)
    percents = [row["follow_through_percent"] for row in reviewed if row["follow_through_percent"] is not None]
    return {
        "session_count": len(sessions),
        "reviewed_commitments": len(reviewed),
        "outcomes": dict(sorted(outcome_counts.items())),
        "average_follow_through_percent": round(sum(percents) / len(percents)) if percents else None,
        "patterns": findings,
        "observations": observations,
        "rule": "pattern requires evidence from at least two included sessions",
    }


def _empty_patterns() -> dict[str, Any]:
    return {"session_count": 0, "reviewed_commitments": 0, "outcomes": {}, "average_follow_through_percent": None, "patterns": [], "observations": [], "rule": "pattern requires evidence from at least two included sessions"}


def _rubric(state: ReviewState, *, evidence: bool, on_time: bool, learning: bool) -> dict[str, Any]:
    result_points = {"done": 50, "partial": 25, "renegotiated": 10, "not_done": 0}[state]
    criteria = {
        "result": {"points": result_points, "max": 50, "reason": state},
        "evidence": {"points": 20 if evidence else 0, "max": 20, "reason": "provided" if evidence else "missing"},
        "timeliness": {"points": 20 if on_time else 0, "max": 20, "reason": "on_or_before_due" if on_time else "after_due"},
        "learning": {"points": 10 if learning else 0, "max": 10, "reason": "captured" if learning else "not_captured"},
    }
    return {"percent": sum(item["points"] for item in criteria.values()), "criteria": criteria, "derived": True}


def _session_row(row: sqlite3.Row, commitments: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "held_on": row["held_on"],
        "source": {"type": row["source_type"], "ref": row["source_ref"], "consented_at": row["consented_at"]},
        "worksheet": json.loads(row["worksheet_json"]),
        "decision_area": row["decision_area"],
        "confidence": row["confidence"],
        "tags": json.loads(row["tags_json"]),
        "status": row["status"],
        "included": bool(row["included"]),
        "commitments": [dict(item) for item in commitments],
    }


def _worksheet(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError("worksheet must be a mapping")
    allowed = set(WORKSHEET_FIELDS) | {"decision_area", "confidence"}
    clean: dict[str, Any] = {}
    for key, item in value.items():
        if key not in allowed or item in (None, ""):
            continue
        if key == "confidence":
            clean[key] = _confidence(item)
        elif key == "decision_area":
            clean[key] = _decision(item)
        elif isinstance(item, list) and key == "future_options":
            clean[key] = [_text(entry, key) for entry in item]
        else:
            clean[key] = _text(item, key)
    return clean


def _ready(worksheet: dict[str, Any]) -> bool:
    return all(worksheet.get(key) for key in ("business_update", "issue_statement", "pillar_and_tool", "desired_outcome"))


def _tags(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple)):
        raise TypeError("tags must be a list")
    result = []
    for value in values:
        tag = _text(value, "tag", maximum=80).casefold()
        if tag not in result:
            result.append(tag)
    return result[:20]


def _decision(value: Any) -> Decision | None:
    if value is None:
        return None
    normalized = _normalize(str(value))
    for decision in ("people", "strategy", "execution", "cash"):
        if re.search(rf"\b{decision}\b", normalized):
            return decision  # type: ignore[return-value]
    return None


def _confidence(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("confidence must be between 0 and 100")
    result = int(value)
    if result != value or not 0 <= result <= 100:
        raise ValueError("confidence must be between 0 and 100")
    return result


def _source_type(value: Any) -> SourceType:
    if value not in {"manual", "imported_document", "drive_connector"}:
        raise ValueError("invalid source_type")
    return value


def _review_state(value: Any) -> ReviewState:
    if value not in {"done", "partial", "not_done", "renegotiated"}:
        raise ValueError("invalid review status")
    return value


def _date(value: Any, label: str) -> str:
    clean = _text(value, label, maximum=10)
    try:
        return date.fromisoformat(clean).isoformat()
    except ValueError as error:
        raise ValueError(f"{label} must use YYYY-MM-DD") from error


def _id(value: Any) -> str:
    clean = _text(value, "id", maximum=64)
    if not re.fullmatch(r"[A-Za-z0-9-]+", clean):
        raise ValueError("invalid id")
    return clean


def _text(value: Any, label: str, maximum: int = _MAX_TEXT) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be text")
    clean = " ".join(value.strip().split())
    if not clean or len(clean) > maximum or "\x00" in clean:
        raise ValueError(f"{label} is invalid")
    return clean


def _optional_text(value: Any, label: str, maximum: int) -> str | None:
    return None if value in (None, "") else _text(value, label, maximum)


def _normalize(value: str) -> str:
    return " ".join(
        "".join(
            char
            for char in unicodedata.normalize("NFD", value.casefold())
            if unicodedata.category(char) != "Mn"
        ).split()
    )


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
