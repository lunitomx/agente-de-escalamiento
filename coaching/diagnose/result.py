"""Build a bounded, explainable diagnostic result."""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping, Sequence

from .models import (
    DiagnosticIntake,
    DiagnosticResult,
    ExplainableDiagnosis,
    RouteAction,
)

DEFAULT_ROUTES: dict[str, tuple[RouteAction, ...]] = {
    "people": (
        RouteAction(
            quarter="Q1",
            decision="people",
            action="Dibujar responsabilidades y un dueño por función clave",
            metric="% de funciones clave con dueño único",
        ),
        RouteAction(
            quarter="Q1",
            decision="people",
            action="Definir una cadencia de conversación de crecimiento",
            metric="% de personas clave con revisión mensual",
        ),
    ),
    "strategy": (
        RouteAction(
            quarter="Q1",
            decision="strategy",
            action="Redactar una meta con número y fecha que el equipo repita",
            metric="% del equipo que puede repetir la meta",
        ),
        RouteAction(
            quarter="Q1",
            decision="strategy",
            action="Validar cliente ideal y diferenciador con cinco clientes",
            metric="entrevistas de cliente completadas",
        ),
    ),
    "execution": (
        RouteAction(
            quarter="Q1",
            decision="execution",
            action="Definir un número crítico y un KPI semanal por persona clave",
            metric="tablero actualizado cada semana",
        ),
        RouteAction(
            quarter="Q1",
            decision="execution",
            action="Instalar una reunión semanal con prioridades, dueño y fecha",
            metric="% de prioridades completadas por trimestre",
        ),
    ),
    "cash": (
        RouteAction(
            quarter="Q1",
            decision="cash",
            action="Mapear el ciclo de conversión de efectivo y sus días",
            metric="CCC en días",
        ),
        RouteAction(
            quarter="Q1",
            decision="cash",
            action="Crear una proyección de caja de 13 semanas",
            metric="semanas de caja actualizadas",
        ),
    ),
}


def build_diagnostic_result(
    intake: DiagnosticIntake,
    diagnosis: ExplainableDiagnosis,
    *,
    route: Sequence[RouteAction | Mapping[str, Any]] | None = None,
    generated_at: str | date | None = None,
) -> DiagnosticResult:
    """Combine intake and diagnosis into a bounded result contract."""
    if route is None:
        route_items = list(DEFAULT_ROUTES.get(diagnosis.focus or "", ()))
    else:
        route_items = [
            item if isinstance(item, RouteAction) else RouteAction.model_validate(item)
            for item in route
        ]
    if len(route_items) > 2:
        raise ValueError("Diagnostic route cannot contain more than two actions")
    if generated_at is None:
        generated = date.today()
    elif isinstance(generated_at, date):
        generated = generated_at
    else:
        generated = date.fromisoformat(generated_at)
    return DiagnosticResult(
        diagnosis=diagnosis,
        funnel=intake.funnel,
        route=route_items,
        company=intake.company,
        open_context=intake.open_context,
        owner_context=intake.owner_context,
        generated_at=generated,
        provenance={
            "evidence_count": len(intake.evidence),
            "selection_rule": diagnosis.selection_rule,
        },
    )
