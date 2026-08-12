"""Tests for the coaching.responder module."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent))

from coaching.evidence.models import DecisionRef, EvidencePackage, EvidenceSource
from coaching.responder import run
from coaching.responder.engine import build_response
from coaching.responder.formatter import format_response
from coaching.responder.models import ExecutiveResponse
from coaching.reviewer.models import ReviewFinding, ReviewReport
from coaching.selector.models import SelectionReceipt


def _build_decision(area: str = "cash") -> DecisionRef:
    return DecisionRef(
        decision="¿Cuánto cash tengo disponible?",
        area=area,
        horizon="inmediato",
        outcome="conocer liquidez",
    )


def _build_source(overrides: dict[str, object]) -> EvidenceSource:
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


def _build_package(
    sources: list[EvidenceSource],
    missing: list[EvidenceSource] | None = None,
) -> EvidencePackage:
    return EvidencePackage(
        decision_ref=_build_decision(),
        sources=sources,
        missing=missing or [],
        not_trustworthy=[],
        questions=[],
    )


def _build_selection(evidence_used: list[str]) -> SelectionReceipt:
    return SelectionReceipt(
        area="cash",
        decision="¿Cuánto cash tengo disponible?",
        tool="cash_analysis",
        label="Cash Analysis",
        skills=["/escala-cash", "/escala-cash-ccc", "/escala-cash-power1"],
        evidence_used=evidence_used,
        reason="OK",
        missing_minimum=False,
    )


def _build_report(
    can_proceed: bool, findings: list[ReviewFinding] | None = None
) -> ReviewReport:
    return ReviewReport(
        decision="¿Cuánto cash tengo disponible?",
        area="cash",
        tool="cash_analysis",
        findings=findings or [],
        can_proceed=can_proceed,
    )


class TestExecutiveResponse:
    def test_valid_response(self):
        response = ExecutiveResponse(
            decision="¿Cuánto cash tengo?",
            area="cash",
            what_i_see="Veo",
            why_it_matters="Importa",
            evidence=["E1"],
            what_i_dont_know="No sé",
            next_step="Acción",
        )
        assert response.can_proceed is True


class TestBuildResponse:
    def test_build_response_with_approval(self):
        package = _build_package(
            [
                _build_source(
                    {"source_id": "worksheet-cash-ccc", "title": "Cash Worksheet"}
                )
            ]
        )
        selection = _build_selection(["worksheet-cash-ccc"])
        report = _build_report(True)
        response = build_response(package.decision_ref, package, selection, report)
        assert response.can_proceed is True
        assert "Cash Worksheet (2026-07)" in response.evidence
        assert "/escala-cash" in response.next_step

    def test_build_response_when_blocked(self):
        package = _build_package([])
        selection = _build_selection([])
        report = _build_report(
            False,
            [
                ReviewFinding(
                    kind="contradiction",
                    severity="critical",
                    message="Contradicción.",
                )
            ],
        )
        response = build_response(package.decision_ref, package, selection, report)
        assert response.can_proceed is False
        assert response.evidence == []


class TestFormatter:
    def test_format_response_has_five_blocks(self):
        response = ExecutiveResponse(
            decision="¿Cuánto cash tengo?",
            area="cash",
            what_i_see="Veo",
            why_it_matters="Importa",
            evidence=["E1"],
            what_i_dont_know="No sé",
            next_step="Acción",
        )
        output = format_response(response)
        assert "## Respuesta ejecutiva" in output
        assert "### 1. Qué veo" in output
        assert "### 2. Por qué importa" in output
        assert "### 3. Evidencia relevante" in output
        assert "### 4. Qué no sé todavía" in output
        assert "### 5. Acción recomendada" in output
        assert "E1" in output


class TestRun:
    def _build_context(self, can_proceed: bool = True):
        package = _build_package(
            [
                _build_source(
                    {"source_id": "worksheet-cash-ccc", "title": "Cash Worksheet"}
                )
            ]
        )
        selection = _build_selection(["worksheet-cash-ccc"])
        report = _build_report(can_proceed)
        return {
            "base_path": ".",
            "decision": package.decision_ref.model_dump(),
            "package": package.model_dump(),
            "selection": {"receipt": selection.model_dump()},
            "review": {"report": report.model_dump()},
        }

    def test_run_responded(self):
        result = run(self._build_context(True))
        assert result["errors"] == []
        assert result["artifacts"]["action"] == "responded"
        assert "## Respuesta ejecutiva" in result["output"]

    def test_run_blocked(self):
        result = run(self._build_context(False))
        assert result["errors"] == []
        assert result["artifacts"]["action"] == "blocked"
        assert "No tengo elementos suficientes" in result["output"]

    def test_run_missing_review_returns_error(self):
        ctx = self._build_context(True)
        del ctx["review"]
        result = run(ctx)
        assert result["errors"]
