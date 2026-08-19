"""Pure profile/OPSP prefill and confirmation lifecycle."""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping, cast

from .models import DiagnosticEvidence, Freshness, PrefillResult

KNOWN_FIELDS = (
    "name",
    "industry",
    "employees",
    "revenue",
    "years_in_business",
    "location",
    "description",
)


def _as_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _freshness(captured_at: date | None, today: date, freshness_days: int) -> str:
    if captured_at is None:
        return "unknown"
    return "current" if (today - captured_at).days <= freshness_days else "stale"


def build_prefill(
    profile: Mapping[str, Any],
    *,
    today: str | date | None = None,
    freshness_days: int = 90,
) -> PrefillResult:
    """Build proposed evidence from a profile without persisting or mutating it."""
    today_date = date.today() if today is None else (_as_date(today) or date.today())
    company = profile.get("company")
    company_data = dict(company) if isinstance(company, Mapping) else {}
    opsp = profile.get("opsp")
    opsp_data = dict(opsp) if isinstance(opsp, Mapping) else {}
    captured_at = _as_date(profile.get("updated") or profile.get("created"))
    evidence: list[DiagnosticEvidence] = []

    for field in KNOWN_FIELDS:
        if field in opsp_data and opsp_data[field] not in (None, ""):
            value = opsp_data[field]
            source_kind = "opsp"
            source_ref = f"opsp:company.{field}"
        elif field in company_data and company_data[field] not in (None, ""):
            value = company_data[field]
            source_kind = "profile"
            source_ref = f"profile:company.{field}"
        else:
            continue

        freshness = cast(Freshness, _freshness(captured_at, today_date, freshness_days))
        confidence = "medium" if freshness != "unknown" else "low"
        evidence.append(
            DiagnosticEvidence(
                evidence_id=f"company.{field}",
                question_id=f"company.{field}",
                value=value,
                applicability="applicable",
                answer_status="inference",
                source_kind=source_kind,
                source_ref=source_ref,
                captured_at=captured_at,
                freshness=freshness,
                confidence=confidence,
                rationale="Dato precargado; requiere confirmación explícita.",
            )
        )

    confirmation_ids = [item.evidence_id for item in evidence]
    questions = [
        f"¿Confirmas el dato precargado '{item.evidence_id}'? ({item.freshness})"
        for item in evidence
    ]
    return PrefillResult(
        evidence=evidence,
        confirmation_ids=confirmation_ids,
        questions=questions,
    )


def confirm_prefill(
    result: PrefillResult,
    confirmed_ids: set[str],
    *,
    today: str | date | None = None,
) -> PrefillResult:
    """Return a new result with only selected prefilled facts confirmed."""
    known_ids = {item.evidence_id for item in result.evidence}
    unknown_ids = confirmed_ids - known_ids
    if unknown_ids:
        raise ValueError(f"Unknown prefill evidence IDs: {sorted(unknown_ids)}")
    today_date = date.today() if today is None else (_as_date(today) or date.today())
    evidence = [
        item.model_copy(
            update={
                "answer_status": "fact"
                if item.evidence_id in confirmed_ids
                else item.answer_status,
                "freshness": "current"
                if item.evidence_id in confirmed_ids
                else item.freshness,
                "captured_at": today_date
                if item.evidence_id in confirmed_ids
                else item.captured_at,
                "confidence": "high"
                if item.evidence_id in confirmed_ids
                else item.confidence,
            }
        )
        for item in result.evidence
    ]
    remaining = [item for item in evidence if item.evidence_id not in confirmed_ids]
    return PrefillResult(
        evidence=evidence,
        confirmation_ids=[item.evidence_id for item in remaining],
        questions=[
            f"¿Confirmas el dato precargado '{item.evidence_id}'? ({item.freshness})"
            for item in remaining
        ],
    )
