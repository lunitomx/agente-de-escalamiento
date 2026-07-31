"""coaching.qualifier.cases — positive and negative test cases for E43.

Each case covers one of the four decisions (people, strategy, execution, cash)
and exercises the full coaching loop through selector, reviewer and responder.
"""

from __future__ import annotations

from dataclasses import dataclass

from coaching.evidence.models import DecisionRef, EvidencePackage, EvidenceSource


@dataclass(frozen=True)
class QualifierCase:
    """A single qualification case for the reliable coaching loop."""

    case_id: str
    area: str
    expected_action: str
    description: str
    decision: DecisionRef
    package: EvidencePackage


def _source(overrides: dict[str, object]) -> EvidenceSource:
    defaults: dict[str, object] = {
        "source_id": "x",
        "source_type": "worksheet",
        "title": "Source",
        "decision": "cash",
        "status": "available",
        "period": "2026-07",
        "confidence": "high",
        "reason": "r",
    }
    defaults.update(overrides)
    return EvidenceSource(**defaults)  # type: ignore[arg-type]


def _decision(area: str, decision: str, outcome: str) -> DecisionRef:
    return DecisionRef(
        decision=decision,
        area=area,
        horizon="inmediato",
        outcome=outcome,
    )


def _package(area: str, sources: list[EvidenceSource], **kwargs) -> EvidencePackage:
    return EvidencePackage(
        decision_ref=_decision(area, kwargs["decision"], kwargs["outcome"]),
        sources=sources,
        missing=kwargs.get("missing", []),
        not_trustworthy=kwargs.get("not_trustworthy", []),
        questions=kwargs.get("questions", []),
    )


ALL_CASES: list[QualifierCase] = [
    # Positive cases
    QualifierCase(
        case_id="cash-positive",
        area="cash",
        expected_action="responded",
        description="Cash workbook available yields executive response.",
        decision=_decision(
            "cash",
            "¿Cuánto cash tengo disponible para agosto?",
            "evitar sorpresas de liquidez",
        ),
        package=_package(
            "cash",
            [
                _source(
                    {
                        "source_id": "worksheet-cash-ccc",
                        "source_type": "worksheet",
                        "title": "Cash Conversion Cycle Worksheet",
                        "decision": "cash",
                    }
                )
            ],
            decision="¿Cuánto cash tengo disponible para agosto?",
            outcome="evitar sorpresas de liquidez",
        ),
    ),
    QualifierCase(
        case_id="execution-positive",
        area="execution",
        expected_action="responded",
        description="Execution session log available yields executive response.",
        decision=_decision(
            "execution",
            "¿Por qué no avanzan las prioridades del trimestre?",
            "recuperar ritmo de ejecución",
        ),
        package=_package(
            "execution",
            [
                _source(
                    {
                        "source_id": "session-2026-07-15",
                        "source_type": "session_log",
                        "title": "Sesión 2026-07-15 — Execution",
                        "decision": "execution",
                    }
                )
            ],
            decision="¿Por qué no avanzan las prioridades del trimestre?",
            outcome="recuperar ritmo de ejecución",
        ),
    ),
    QualifierCase(
        case_id="people-positive",
        area="people",
        expected_action="responded",
        description="People worksheet available yields executive response.",
        decision=_decision(
            "people",
            "¿Debería contratar a María para ventas?",
            "cubrir la vacante y mejorar cobertura comercial",
        ),
        package=_package(
            "people",
            [
                _source(
                    {
                        "source_id": "worksheet-people-values",
                        "source_type": "worksheet",
                        "title": "Core Values Worksheet",
                        "decision": "people",
                    }
                )
            ],
            decision="¿Debería contratar a María para ventas?",
            outcome="cubrir la vacante y mejorar cobertura comercial",
        ),
    ),
    QualifierCase(
        case_id="strategy-positive",
        area="strategy",
        expected_action="responded",
        description="Strategy worksheet available yields executive response.",
        decision=_decision(
            "strategy",
            "¿Cuál es nuestra propuesta de valor diferenciada?",
            "alinear la estrategia de la empresa",
        ),
        package=_package(
            "strategy",
            [
                _source(
                    {
                        "source_id": "worksheet-strategy-opsp",
                        "source_type": "worksheet",
                        "title": "One-Page Strategic Plan",
                        "decision": "strategy",
                    }
                )
            ],
            decision="¿Cuál es nuestra propuesta de valor diferenciada?",
            outcome="alinear la estrategia de la empresa",
        ),
    ),
    # Negative cases
    QualifierCase(
        case_id="cash-negative-missing",
        area="cash",
        expected_action="blocked",
        description="Cash with no available evidence is blocked before responding.",
        decision=_decision(
            "cash",
            "¿Cuánto cash tengo disponible?",
            "conocer liquidez actual",
        ),
        package=_package(
            "cash",
            [],
            missing=[
                _source(
                    {
                        "source_id": "worksheet-cash-ccc",
                        "source_type": "worksheet",
                        "title": "Cash Conversion Cycle Worksheet",
                        "decision": "cash",
                        "status": "missing",
                        "confidence": "low",
                        "reason": "No se encontró worksheet.",
                    }
                )
            ],
            questions=["¿Tienes disponible 'Cash Conversion Cycle Worksheet'?"],
            decision="¿Cuánto cash tengo disponible?",
            outcome="conocer liquidez actual",
        ),
    ),
    QualifierCase(
        case_id="execution-negative-contradiction",
        area="execution",
        expected_action="blocked",
        description="Execution with contradictory low-confidence sources is blocked.",
        decision=_decision(
            "execution",
            "¿Por qué no avanzan las prioridades?",
            "recuperar ritmo",
        ),
        package=_package(
            "execution",
            [
                _source(
                    {
                        "source_id": "session-a",
                        "source_type": "session_log",
                        "title": "Sesión A",
                        "decision": "execution",
                        "confidence": "low",
                    }
                ),
                _source(
                    {
                        "source_id": "session-b",
                        "source_type": "session_log",
                        "title": "Sesión B",
                        "decision": "execution",
                        "confidence": "low",
                    }
                ),
            ],
            decision="¿Por qué no avanzan las prioridades?",
            outcome="recuperar ritmo",
        ),
    ),
    QualifierCase(
        case_id="people-negative-untrustworthy",
        area="people",
        expected_action="blocked",
        description="People with only untrustworthy evidence is blocked.",
        decision=_decision(
            "people",
            "¿Contratamos al candidato?",
            "cubrir vacante",
        ),
        package=_package(
            "people",
            [],
            not_trustworthy=[
                _source(
                    {
                        "source_id": "worksheet-people-old",
                        "source_type": "worksheet",
                        "title": "Core Values Worksheet",
                        "decision": "people",
                        "status": "not_trustworthy",
                        "confidence": "low",
                        "reason": "Desactualizado.",
                    }
                )
            ],
            decision="¿Contratamos al candidato?",
            outcome="cubrir vacante",
        ),
    ),
    QualifierCase(
        case_id="strategy-negative-missing",
        area="strategy",
        expected_action="blocked",
        description="Strategy with no matching evidence is blocked.",
        decision=_decision(
            "strategy",
            "¿Dónde invertir el próximo año?",
            "definir foco estratégico",
        ),
        package=_package(
            "strategy",
            [],
            missing=[
                _source(
                    {
                        "source_id": "worksheet-strategy-opsp",
                        "source_type": "worksheet",
                        "title": "One-Page Strategic Plan",
                        "decision": "strategy",
                        "status": "missing",
                        "confidence": "low",
                        "reason": "No se encontró OPSP.",
                    }
                )
            ],
            questions=["¿Tienes disponible 'One-Page Strategic Plan'?"],
            decision="¿Dónde invertir el próximo año?",
            outcome="definir foco estratégico",
        ),
    ),
]
