"""Conservative reconciliation for measurements captured during onboarding."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Literal, Sequence

from pydantic import BaseModel, Field, field_validator

MeasurementKind = Literal[
    "delivered_spend",
    "billed_charge",
    "settlement",
    "accounting_entry",
    "purchase",
    "collection",
    "attributable_revenue",
]
ReconciliationStatus = Literal["ready", "needs_clarification", "blocked"]
FindingKind = Literal["agreement", "conflict", "incompatible", "not_comparable"]


class FinancialMeasurement(BaseModel):
    """One financial measurement; its business nature is never inferred."""

    measurement_id: str = Field(..., min_length=1)
    kind: MeasurementKind
    value: float
    currency: str = Field(..., pattern=r"^[A-Z]{3}$")
    period: str = Field(..., min_length=1)
    basis_date: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    comparable: bool = True

    @field_validator("source")
    @classmethod
    def _source_is_reference_not_content(cls, value: str) -> str:
        if value.startswith(("http://", "https://", "file://", "/")) or ".." in value:
            raise ValueError("source must be a local relative reference")
        return value


class ReconciliationFinding(BaseModel):
    kind: FindingKind
    measurement_ids: tuple[str, str]
    reason: str


class FinancialReconciliation(BaseModel):
    """A reviewable result that exposes prohibited comparisons instead of ratios."""

    status: ReconciliationStatus
    measurements: list[FinancialMeasurement]
    findings: list[ReconciliationFinding] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)


def reconcile_financial_measurements(
    measurements: Sequence[FinancialMeasurement],
) -> FinancialReconciliation:
    """Compare only same-nature measurements under an identical reporting basis."""
    if not measurements:
        return FinancialReconciliation(
            status="blocked",
            measurements=[],
            questions=["Comparte al menos una medición financiera con su fuente."],
        )

    findings: list[ReconciliationFinding] = []
    questions: list[str] = []
    by_kind: dict[MeasurementKind, list[FinancialMeasurement]] = defaultdict(list)
    for item in measurements:
        by_kind[item.kind].append(item)

    for kind, group in by_kind.items():
        for left, right in combinations(group, 2):
            ids = (left.measurement_id, right.measurement_id)
            if not left.comparable or not right.comparable:
                findings.append(
                    ReconciliationFinding(
                        kind="not_comparable",
                        measurement_ids=ids,
                        reason=f"{kind} está marcado no comparable por una de sus fuentes.",
                    )
                )
                continue
            if (left.currency, left.period, left.basis_date) != (
                right.currency,
                right.period,
                right.basis_date,
            ):
                findings.append(
                    ReconciliationFinding(
                        kind="not_comparable",
                        measurement_ids=ids,
                        reason=(
                            f"{kind} no comparte moneda, periodo y fecha base; "
                            "la comparación queda bloqueada."
                        ),
                    )
                )
                questions.append(
                    f"¿Qué moneda, periodo y fecha base deben usarse para reconciliar {kind}?"
                )
                continue
            findings.append(
                ReconciliationFinding(
                    kind="agreement" if left.value == right.value else "conflict",
                    measurement_ids=ids,
                    reason=(
                        f"Dos fuentes de {kind} coinciden."
                        if left.value == right.value
                        else f"Dos fuentes de {kind} difieren; confirma cuál representa el cierre."
                    ),
                )
            )
            if left.value != right.value:
                questions.append(
                    f"¿Cuál de las dos fuentes de {kind} representa el cierre aprobado?"
                )

    representatives = [items[0] for items in by_kind.values()]
    for left, right in combinations(representatives, 2):
        findings.append(
            ReconciliationFinding(
                kind="incompatible",
                measurement_ids=(left.measurement_id, right.measurement_id),
                reason=(
                    f"{left.kind} y {right.kind} son naturalezas distintas; "
                    "ESCALA no calcula una comparación ni ratio entre ellas."
                ),
            )
        )

    status: ReconciliationStatus = "ready"
    if questions:
        status = "needs_clarification"
    return FinancialReconciliation(
        status=status,
        measurements=list(measurements),
        findings=findings,
        questions=list(dict.fromkeys(questions)),
    )
