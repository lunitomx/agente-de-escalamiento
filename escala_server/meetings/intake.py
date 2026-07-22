"""Filesystem-only transcript intake and bounded context extraction."""

from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata

from pydantic import ValidationError

from escala_server.workspace.authority import WorkspaceConfig, validate_workspace
from escala_server.workspace.ingestion import (
    SourceIngestionError,
    build_source_identity,
)

from .models import (
    MeetingContext,
    MeetingItemResult,
    MeetingLedger,
    MeetingLedgerEntry,
    MeetingProvenance,
    MeetingQuestion,
    MeetingRunResult,
    MeetingType,
    evidence_hash,
)


class MeetingIntakeError(ValueError):
    """Stable local failure without machine paths or source content."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


_SUPPORTED_SUFFIXES = {".txt", ".md", ".transcript"}
_TYPE_LABELS = ("tipo", "tipo de reunion", "tipo de reunión", "meeting type", "type")
_DATE_LABELS = ("fecha", "date", "meeting date")
_TEAM_LABELS = ("equipo", "team", "area", "área")
_PARTICIPANT_LABELS = ("participantes", "participants", "asistentes", "attendees")
_TYPE_MAP: dict[str, MeetingType] = {
    "daily": "daily",
    "diaria": "daily",
    "daily meeting": "daily",
    "weekly": "weekly",
    "semanal": "weekly",
    "weekly meeting": "weekly",
    "one on one": "one_on_one",
    "one-on-one": "one_on_one",
    "1:1": "one_on_one",
    "planning": "planning",
    "planeacion": "planning",
    "planeación": "planning",
    "review": "review",
    "revision": "review",
    "revisión": "review",
}


def _ledger_path(config: WorkspaceConfig) -> Path:
    return (
        config.data_root.expanduser().resolve(strict=False)
        / ".escala-meeting-ledger.json"
    )


def load_meeting_ledger(config: WorkspaceConfig) -> MeetingLedger:
    """Load only the installer-local ledger and fail closed on corruption."""

    _ensure_valid_workspace(config)
    path = _ledger_path(config)
    if not path.exists():
        return MeetingLedger()
    try:
        return MeetingLedger.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError):
        raise MeetingIntakeError("ledger_corrupt") from None


def save_meeting_ledger(config: WorkspaceConfig, ledger: MeetingLedger) -> None:
    """Atomically persist derived metadata under data_root only."""

    _ensure_valid_workspace(config)
    path = _ledger_path(config)
    normalized = ledger.model_copy(
        update={
            "entries": tuple(sorted(ledger.entries, key=lambda entry: entry.source_id))
        }
    )
    payload = json.dumps(
        normalized.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    try:
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, path)
    except OSError:
        raise MeetingIntakeError("ledger_write_failed") from None


def scan_meeting_inbox(config: WorkspaceConfig) -> MeetingRunResult:
    """Scan direct exchange entries without moving or mutating transcripts."""

    _ensure_valid_workspace(config)
    exchange = config.exchange_root.expanduser().resolve(strict=False)
    if not exchange.exists() or not exchange.is_dir():
        raise MeetingIntakeError("exchange_missing")
    ledger = load_meeting_ledger(config)
    known = ledger.by_source_id()
    entries = list(ledger.entries)
    items: list[MeetingItemResult] = []
    changed = False

    try:
        paths = sorted(exchange.iterdir(), key=lambda path: path.name.casefold())
    except OSError:
        raise MeetingIntakeError("exchange_unreadable") from None

    for path in paths:
        relative = path.relative_to(exchange).as_posix()
        if path.is_symlink():
            items.append(
                MeetingItemResult(
                    relative_path=relative,
                    status="rejected",
                    code="entry_symlink",
                )
            )
            continue
        if path.is_dir():
            items.append(
                MeetingItemResult(
                    relative_path=relative,
                    status="rejected",
                    code="entry_directory",
                )
            )
            continue
        if path.suffix.casefold() not in _SUPPORTED_SUFFIXES:
            items.append(
                MeetingItemResult(
                    relative_path=relative,
                    status="rejected",
                    code="format_unsupported",
                )
            )
            continue
        try:
            identity = build_source_identity(path, exchange)
        except SourceIngestionError as error:
            items.append(
                MeetingItemResult(
                    relative_path=relative,
                    status="rejected",
                    code=error.code,
                )
            )
            continue
        if identity.source_id in known:
            existing = known[identity.source_id]
            items.append(
                MeetingItemResult(
                    relative_path=relative,
                    status="duplicate",
                    code="source_seen",
                    source_id=identity.source_id,
                    context=existing.context,
                )
            )
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            items.append(
                MeetingItemResult(
                    relative_path=relative,
                    status="rejected",
                    code="source_unreadable",
                    source_id=identity.source_id,
                )
            )
            continue
        context, questions = _extract_context(identity.source_id, relative, text)
        status = "ready" if context.context_status == "ready" else "unresolved"
        code = "context_ready" if status == "ready" else "context_unresolved"
        item = MeetingItemResult(
            relative_path=relative,
            status=status,
            code=code,
            source_id=identity.source_id,
            context=context,
            questions=questions,
        )
        items.append(item)
        entry = MeetingLedgerEntry(
            source_id=identity.source_id,
            relative_path=relative,
            status=status,
            context=context,
        )
        entries.append(entry)
        known[identity.source_id] = entry
        changed = True

    updated = MeetingLedger(entries=tuple(entries))
    if changed:
        save_meeting_ledger(config, updated)
    else:
        updated = ledger
    run_id = hashlib.sha256(
        json.dumps(
            [item.model_dump(mode="json") for item in items],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return MeetingRunResult(
        run_id=run_id,
        items=tuple(items),
        ledger=updated,
        ledger_changed=changed,
    )


def render_meeting_intake_receipt_json(result: MeetingRunResult) -> str:
    """Render safe disposition fields only; omit context values and text."""

    payload = {
        "status": result.status,
        "run_id": result.run_id,
        "ledger_changed": result.ledger_changed,
        "items": [
            {
                "relative_path": item.relative_path,
                "status": item.status,
                "code": item.code,
                "source_id": item.source_id,
                "questions": [question.code for question in item.questions],
            }
            for item in result.items
        ],
    }
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def render_meeting_intake_receipt_markdown(result: MeetingRunResult) -> str:
    """Render the same bounded fields in human-readable form."""

    lines = [
        "# Meeting Intake Receipt",
        "",
        f"- status: {result.status}",
        f"- run_id: {result.run_id}",
        "",
        "## Items",
    ]
    if not result.items:
        lines.append("- none")
    else:
        for item in result.items:
            questions = (
                ", ".join(question.code for question in item.questions) or "none"
            )
            lines.append(
                f"- {item.relative_path}: {item.status} ({item.code}); questions: {questions}"
            )
    return "\n".join(lines) + "\n"


def _ensure_valid_workspace(config: WorkspaceConfig) -> None:
    receipt = validate_workspace(config)
    if receipt.status != "pass":
        code = receipt.findings[0].code if receipt.findings else "workspace_invalid"
        raise MeetingIntakeError(code)


def _extract_context(
    source_id: str,
    relative_path: str,
    text: str,
) -> tuple[MeetingContext, tuple[MeetingQuestion, ...]]:
    lines = text.splitlines()
    if not lines:
        raise MeetingIntakeError("source_empty")
    values: dict[str, tuple[str, int]] = {}
    for line_number, line in enumerate(lines, start=1):
        match = re.match(r"^\s*([^:–—-]{2,40})\s*[:–—-]\s*(.*?)\s*$", line)
        if match:
            values[_normalize(match.group(1))] = (match.group(2).strip(), line_number)

    raw_type, type_line = _find_label(values, _TYPE_LABELS)
    meeting_type = (
        _parse_type(raw_type) if raw_type else _parse_filename_type(relative_path)
    )
    type_evidence = (
        _evidence(
            source_id,
            relative_path,
            lines,
            type_line or 1,
            origin="line" if type_line else "filename",
        )
        if meeting_type != "unknown"
        else None
    )

    raw_date, date_line = _find_label(values, _DATE_LABELS)
    meeting_date = (
        _parse_date(raw_date) if raw_date else _parse_filename_date(relative_path)
    )
    date_evidence = (
        _evidence(
            source_id,
            relative_path,
            lines,
            date_line or 1,
            origin="line" if date_line else "filename",
        )
        if meeting_date
        else None
    )

    raw_team, team_line = _find_label(values, _TEAM_LABELS)
    team = raw_team or None
    team_evidence = (
        _evidence(source_id, relative_path, lines, team_line) if team_line else None
    )

    raw_participants, participants_line = _find_label(values, _PARTICIPANT_LABELS)
    participants = _split_people(raw_participants) if raw_participants else ()
    participant_evidence = (
        _evidence(source_id, relative_path, lines, participants_line)
        if participants_line
        else None
    )

    questions: list[MeetingQuestion] = []
    if meeting_type == "unknown":
        questions.append(
            MeetingQuestion(
                code="meeting_type_unresolved",
                options=("daily", "weekly", "one_on_one", "other"),
            )
        )
    if meeting_date is None:
        questions.append(
            MeetingQuestion(
                code="meeting_date_unresolved", options=("provide_date", "unknown")
            )
        )
    if team is None:
        questions.append(
            MeetingQuestion(
                code="team_unresolved", options=("provide_team", "not_applicable")
            )
        )
    if not participants:
        questions.append(
            MeetingQuestion(
                code="participants_unresolved",
                options=("provide_participants", "none"),
            )
        )
    evidence = tuple(
        evidence_item
        for evidence_item in (
            type_evidence,
            date_evidence,
            team_evidence,
            participant_evidence,
        )
        if evidence_item is not None
    )
    confidence = "high" if not questions else "medium" if len(evidence) >= 2 else "low"
    provenance = _evidence(source_id, relative_path, lines, 1)
    context = MeetingContext(
        context_status="ready" if not questions else "unresolved",
        meeting_type=meeting_type,
        meeting_date=meeting_date,
        team=team,
        participants=participants,
        provenance=provenance,
        evidence=evidence,
        confidence=confidence,
    )
    return context, tuple(questions)


def _find_label(
    values: dict[str, tuple[str, int]], labels: tuple[str, ...]
) -> tuple[str | None, int | None]:
    for label in labels:
        found = values.get(_normalize(label))
        if found:
            return found
    return None, None


def _parse_type(value: str | None) -> MeetingType:
    if not value:
        return "unknown"
    normalized = _normalize(value)
    return _TYPE_MAP.get(normalized, "unknown")


def _parse_filename_type(relative_path: str) -> MeetingType:
    normalized = _normalize(
        Path(relative_path).stem.replace("-", " ").replace("_", " ")
    )
    for token, meeting_type in _TYPE_MAP.items():
        if token in normalized:
            return meeting_type
    return "unknown"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value.strip(), pattern).date()
        except ValueError:
            continue
    return None


def _parse_filename_date(relative_path: str) -> date | None:
    match = re.search(r"(?<!\d)(20\d{2})[-_](\d{2})[-_](\d{2})(?!\d)", relative_path)
    return _parse_date("-".join(match.groups())) if match else None


def _split_people(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    normalized = re.sub(r"\s+y\s+", ",", value, flags=re.IGNORECASE)
    return tuple(part.strip() for part in re.split(r"[,;]", normalized) if part.strip())


def _evidence(
    source_id: str,
    relative_path: str,
    lines: list[str],
    line_number: int,
    *,
    origin: str = "line",
) -> MeetingProvenance:
    safe_line = max(1, min(line_number, len(lines)))
    return MeetingProvenance(
        source_id=source_id,
        relative_path=relative_path,
        line_start=safe_line,
        line_end=safe_line,
        evidence_sha256=evidence_hash(lines[safe_line - 1]),
        origin=origin,  # type: ignore[arg-type]
    )


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(
        char for char in decomposed if not unicodedata.combining(char)
    ).strip()
