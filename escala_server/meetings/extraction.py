"""Deterministic meeting fact extraction and declared rhythm assessment."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import hashlib
from pathlib import Path
import re
from typing import Iterable

from escala_server.workspace.authority import WorkspaceConfig, validate_workspace
from escala_server.workspace.ingestion import (
    SourceIngestionError,
    build_source_identity,
)

from .intake import _SUPPORTED_SUFFIXES, _normalize
from .models import (
    FactKind,
    MeetingFact,
    MeetingFactResult,
    MeetingItemResult,
    MeetingProvenance,
    MeetingQuestion,
    RhythmAssessment,
    RhythmRule,
    evidence_hash,
)


_FACT_LABELS: dict[str, FactKind] = {
    "decision": "decision",
    "decisión": "decision",
    "acuerdo": "decision",
    "action": "action",
    "acción": "action",
    "tarea": "action",
    "owner": "owner",
    "responsable": "owner",
    "due": "due_date",
    "vence": "due_date",
    "fecha limite": "due_date",
    "fecha límite": "due_date",
    "deadline": "due_date",
    "blocker": "blocker",
    "bloqueador": "blocker",
    "bloqueo": "blocker",
    "risk": "risk",
    "riesgo": "risk",
    "commitment": "commitment",
    "compromiso": "commitment",
}
_FACT_LABELS = {_normalize(label): kind for label, kind in _FACT_LABELS.items()}
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")


def extract_meeting_facts(
    config: WorkspaceConfig,
    item: MeetingItemResult,
) -> MeetingFactResult:
    """Re-read a source only when its E37 identity is still current."""

    source_id = item.source_id
    if source_id is None:
        return MeetingFactResult(
            status="blocked",
            source_id="0" * 64,
            findings=("source_identity_missing",),
        )
    if validate_workspace(config).status != "pass":
        return MeetingFactResult(
            status="blocked", source_id=source_id, findings=("workspace_invalid",)
        )
    path = _source_path(config, item.relative_path)
    if path is None or path.suffix.casefold() not in _SUPPORTED_SUFFIXES:
        return MeetingFactResult(
            status="blocked", source_id=source_id, findings=("source_invalid",)
        )
    try:
        identity = build_source_identity(path, config.exchange_root)
    except SourceIngestionError:
        return MeetingFactResult(
            status="blocked", source_id=source_id, findings=("source_unreadable",)
        )
    if identity.source_id != source_id:
        return MeetingFactResult(
            status="blocked", source_id=source_id, findings=("source_changed",)
        )
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError):
        return MeetingFactResult(
            status="blocked", source_id=source_id, findings=("source_unreadable",)
        )

    facts: list[MeetingFact] = []
    questions: list[MeetingQuestion] = []
    for line_number, line in enumerate(lines, start=1):
        match = re.match(r"^\s*([^:–—-]{2,40})\s*[:–—-]\s*(.*?)\s*$", line)
        if match is None:
            continue
        kind = _FACT_LABELS.get(_normalize(match.group(1)))
        if kind is None:
            continue
        payload = match.group(2).strip()
        if not payload:
            questions.append(
                MeetingQuestion(
                    code=f"{kind}_unresolved", options=("provide_value", "unknown")
                )
            )
            continue
        value, owner, due_date, due_unresolved = _parse_payload(kind, payload)
        if due_unresolved:
            questions.append(
                MeetingQuestion(
                    code="due_date_unresolved", options=("provide_date", "unknown")
                )
            )
        if not value:
            questions.append(
                MeetingQuestion(
                    code=f"{kind}_unresolved", options=("provide_value", "unknown")
                )
            )
            continue
        evidence = MeetingProvenance(
            source_id=source_id,
            relative_path=item.relative_path,
            line_start=line_number,
            line_end=line_number,
            evidence_sha256=evidence_hash(line),
        )
        fact_id = hashlib.sha256(
            f"v1\0{source_id}\0{line_number}\0{kind}\0{value}".encode("utf-8")
        ).hexdigest()
        facts.append(
            MeetingFact(
                fact_id=fact_id,
                source_id=source_id,
                kind=kind,
                value=value,
                owner=owner,
                due_date=due_date,
                evidence=evidence,
                confidence="high",
            )
        )
    status = "ready" if facts and not questions else "partial"
    findings = (
        ("context_unresolved",)
        if item.context and item.context.context_status == "unresolved"
        else ()
    )
    return MeetingFactResult(
        status=status,
        source_id=source_id,
        facts=tuple(facts),
        questions=tuple(questions),
        findings=findings,
    )


def assess_rhythm(
    contexts: Iterable[object],
    rule: RhythmRule,
    *,
    period_start: date,
    period_end: date,
) -> RhythmAssessment:
    """Compare declared expected dates with observed evidence only."""

    if period_end < period_start:
        raise ValueError("period_end must not precede period_start")
    expected = tuple(
        period_start + timedelta(days=offset)
        for offset in range(0, (period_end - period_start).days + 1, rule.cadence_days)
    )
    observed: set[date] = set()
    unresolved = False
    for context in contexts:
        meeting_type = getattr(context, "meeting_type", "unknown")
        meeting_date = getattr(context, "meeting_date", None)
        if meeting_type != rule.meeting_type:
            continue
        if meeting_date is None:
            unresolved = True
        else:
            observed.add(meeting_date)
    observed_dates = tuple(sorted(observed))
    missing = tuple(
        expected_date for expected_date in expected if expected_date not in observed
    )
    if unresolved:
        status = "unresolved"
        note_code = "context_unresolved"
    elif missing:
        status = "evidence_missing"
        note_code = "evidence_missing"
    else:
        status = "supported"
        note_code = "rhythm_supported"
    return RhythmAssessment(
        status=status,
        rule_id=rule.rule_id,
        meeting_type=rule.meeting_type,
        observed_dates=observed_dates,
        expected_dates=expected,
        missing_dates=missing,
        note_code=note_code,
    )


def _source_path(config: WorkspaceConfig, relative_path: str) -> Path | None:
    if "\x00" in relative_path:
        return None
    exchange = config.exchange_root.expanduser().resolve(strict=False)
    candidate = (exchange / relative_path).resolve(strict=False)
    if candidate != exchange and exchange not in candidate.parents:
        return None
    if candidate.is_symlink() or not candidate.is_file():
        return None
    return candidate


def _parse_payload(
    kind: FactKind,
    payload: str,
) -> tuple[str, str | None, date | None, bool]:
    owner: str | None = None
    due_date: date | None = None
    due_unresolved = False
    value = payload.strip()
    due_match = re.search(
        r"(?:vence|due|deadline|fecha\s+l[ií]mite)\s*[:=]\s*([^—–;]+)",
        value,
        flags=re.IGNORECASE,
    )
    if due_match:
        raw_due = due_match.group(1).strip()
        due_date = _parse_date(raw_due)
        due_unresolved = due_date is None
        value = value[: due_match.start()].strip(" —–;")
    if kind in {"action", "commitment"}:
        parts = re.split(r"\s+[—–]\s+", value, maxsplit=1)
        if len(parts) == 2 and parts[0].strip():
            owner = parts[0].strip()
            value = parts[1].strip()
    if kind == "owner":
        owner = value
    if kind == "due_date":
        due_date = _parse_date(value)
        due_unresolved = due_date is None
        if due_date:
            value = due_date.isoformat()
    return value, owner, due_date, due_unresolved


def _parse_date(value: str) -> date | None:
    for pattern in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), pattern).date()
        except ValueError:
            continue
    return None
