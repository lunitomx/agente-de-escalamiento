"""coaching.evidence.engine — pure evidence discovery and classification logic.

No I/O. Accepts an in-memory description of local sources and returns a
classified EvidencePackage.
"""

from __future__ import annotations

from datetime import date
from typing import Any, cast

from ..decision.engine import AREA_KEYWORDS
from .models import DecisionRef, EvidenceConfidence, EvidencePackage, EvidenceSource

DEFAULT_FRESHNESS_DAYS = 90


def _parse_date(value: str | None) -> date | None:
    """Parse an ISO date string, returning None on failure."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _matches_area(text: str | None, area: str) -> bool:
    """True if the text contains keywords for the given decision area."""
    if not text:
        return False
    cleaned = text.lower()
    return any(keyword in cleaned for keyword in AREA_KEYWORDS.get(area, []))


def _is_trustworthy(
    source: dict[str, Any], today: date, freshness_days: int
) -> tuple[bool, str]:
    """Return (is_trustworthy, reason) for a source."""
    completed = source.get("completed")
    if completed is False:
        return False, "Worksheet incompleto; no se puede usar como hecho."

    source_date = _parse_date(source.get("date"))
    if source_date is None:
        return False, "Sin fecha conocida; no se puede evaluar la frescura."

    age = (today - source_date).days
    if age > freshness_days:
        return (
            False,
            f"Fuente desactualizada ({source_date}); los datos pueden no reflejar la situación actual.",
        )

    return True, "Fuente reciente y completa."


def _confidence_for(
    source: dict[str, Any], trustworthy: bool, reason: str
) -> tuple[str, str]:
    """Return (confidence_level, human_reason) for a source."""
    if not trustworthy:
        return "low", reason

    has_date = bool(_parse_date(source.get("date")))
    completed = source.get("completed")
    if has_date and completed is not False:
        return "high", reason
    if has_date:
        return "medium", reason
    return "medium", "Fuente disponible sin fecha de actualización confirmada."


def classify_status(
    source: dict[str, Any], today: date, freshness_days: int = DEFAULT_FRESHNESS_DAYS
) -> str:
    """Classify a source as available, missing, or not_trustworthy."""
    if source.get("missing"):
        return "missing"

    trustworthy, _ = _is_trustworthy(source, today, freshness_days)
    if not trustworthy:
        return "not_trustworthy"
    return "available"


def _build_source(
    source_id: str,
    source_type: str,
    title: str,
    decision: str,
    source: dict[str, Any],
    today: date,
    freshness_days: int,
) -> EvidenceSource:
    """Classify a single source and return an EvidenceSource model."""
    status = classify_status(source, today, freshness_days)
    if status == "missing":
        return EvidenceSource(
            source_id=source_id,
            source_type=source_type,
            title=title,
            decision=decision,
            status="missing",
            period=source.get("period", ""),
            confidence="low",
            reason=source.get("reason", "No se encontró la fuente esperada."),
        )

    trustworthy, reason = _is_trustworthy(source, today, freshness_days)
    confidence, confidence_reason = _confidence_for(source, trustworthy, reason)
    return EvidenceSource(
        source_id=source_id,
        source_type=source_type,
        title=title,
        decision=decision,
        status="not_trustworthy" if not trustworthy else "available",
        period=source.get("date", ""),
        confidence=cast(EvidenceConfidence, confidence),
        reason=confidence_reason,
        locator=source.get("locator"),
    )


def _question_for_missing(source: EvidenceSource) -> str:
    """Generate a clarification question for a missing source."""
    return f"¿Tienes disponible '{source.title}' para esta decisión?"


def _source_matches_decision(source: dict[str, Any], area: str) -> bool:
    """True if a source is relevant for the decision area."""
    source_area = source.get("decision") or source.get("decision_focus") or ""
    if source_area == area:
        return True
    title = source.get("name") or source.get("title") or ""
    return _matches_area(title, area)


def discover_sources(
    decision_ref: DecisionRef,
    local_sources: dict[str, Any],
    freshness_days: int = DEFAULT_FRESHNESS_DAYS,
    today: str | date | None = None,
) -> EvidencePackage:
    """Discover and classify all evidence for a confirmed decision."""
    if today is None:
        today_date = date.today()
    elif isinstance(today, str):
        today_date = date.fromisoformat(today)
    else:
        today_date = today

    area = decision_ref.area
    sources: list[EvidenceSource] = []
    not_trustworthy: list[EvidenceSource] = []
    missing: list[EvidenceSource] = []

    # Sessions
    for session in local_sources.get("sessions", []):
        if not _source_matches_decision(session, area):
            continue
        title = f"Sesión {session.get('date', '—')} — {area.title()}"
        source = _build_source(
            source_id=session.get("id", ""),
            source_type="session_log",
            title=title,
            decision=area,
            source=session,
            today=today_date,
            freshness_days=freshness_days,
        )
        if source.status == "available":
            sources.append(source)
        else:
            not_trustworthy.append(source)

    # Worksheets
    local_worksheet_ids = set()
    for worksheet in local_sources.get("worksheets", []):
        worksheet_id = worksheet.get("id", "")
        local_worksheet_ids.add(worksheet_id)
        if not _source_matches_decision(worksheet, area):
            continue
        source = _build_source(
            source_id=worksheet_id,
            source_type="worksheet",
            title=worksheet.get("name", worksheet_id),
            decision=area,
            source=worksheet,
            today=today_date,
            freshness_days=freshness_days,
        )
        if source.status == "available":
            sources.append(source)
        else:
            not_trustworthy.append(source)

    # Tasks
    for task in local_sources.get("tasks", []):
        if not _source_matches_decision(task, area):
            continue
        source = _build_source(
            source_id=task.get("id", ""),
            source_type="task",
            title=task.get("title", "Tarea vinculada"),
            decision=area,
            source=task,
            today=today_date,
            freshness_days=freshness_days,
        )
        if source.status == "available":
            sources.append(source)
        else:
            not_trustworthy.append(source)

    # Metrics
    for metric in local_sources.get("metrics", []):
        if not _source_matches_decision(metric, area):
            continue
        source = _build_source(
            source_id=metric.get("id", ""),
            source_type="metric",
            title=metric.get("name", "Métrica vinculada"),
            decision=area,
            source=metric,
            today=today_date,
            freshness_days=freshness_days,
        )
        if source.status == "available":
            sources.append(source)
        else:
            not_trustworthy.append(source)

    # Missing sources from worksheet registry
    for worksheet in local_sources.get("registry", {}).get("worksheets", []):
        if worksheet.get("decision") != area:
            continue
        worksheet_id = worksheet.get("id", "")
        if worksheet_id in local_worksheet_ids:
            continue
        missing_source = EvidenceSource(
            source_id=worksheet_id,
            source_type="worksheet",
            title=worksheet.get("name", worksheet_id),
            decision=area,
            status="missing",
            period="",
            confidence="low",
            reason=f"No se encontró {worksheet.get('name', worksheet_id)} para el área {area}.",
        )
        missing.append(missing_source)

    questions = [_question_for_missing(m) for m in missing]

    return EvidencePackage(
        decision_ref=decision_ref,
        sources=sources,
        missing=missing,
        not_trustworthy=not_trustworthy,
        questions=questions,
    )
