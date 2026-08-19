"""Build a validated, source-neutral diagnostic evidence pack."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .models import DiagnosticEvidence, DiagnosticIntake, FunnelMetrics


def build_diagnostic_intake(
    *,
    company: Mapping[str, Any] | None = None,
    evidence: Sequence[DiagnosticEvidence | Mapping[str, Any]] = (),
    funnel: Mapping[str, Any] | None = None,
    open_context: Mapping[str, str] | None = None,
    owner_context: Mapping[str, str] | None = None,
) -> DiagnosticIntake:
    """Normalize optional inputs without dropping supplied values silently."""
    evidence_items = [
        item
        if isinstance(item, DiagnosticEvidence)
        else DiagnosticEvidence.model_validate(item)
        for item in evidence
    ]
    funnel_metrics = (
        FunnelMetrics.model_validate(funnel) if funnel is not None else None
    )
    return DiagnosticIntake(
        company=dict(company or {}),
        evidence=evidence_items,
        funnel=funnel_metrics,
        open_context=dict(open_context or {}),
        owner_context=dict(owner_context or {}),
    )
