"""Tests for the coaching.reviewer module."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent))

import pytest
from pydantic import ValidationError

from coaching.evidence.models import DecisionRef, EvidencePackage, EvidenceSource
from coaching.reviewer import run
from coaching.reviewer.engine import review
from coaching.reviewer.formatter import format_report
from coaching.reviewer.models import ReviewFinding, ReviewReport, ReviewResult
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
    not_trustworthy: list[EvidenceSource] | None = None,
    area: str = "cash",
) -> EvidencePackage:
    return EvidencePackage(
        decision_ref=_build_decision(area),
        sources=sources,
        missing=missing or [],
        not_trustworthy=not_trustworthy or [],
        questions=[f"¿Tienes disponible '{m.title}'?" for m in (missing or [])],
    )


def _build_selection(
    area: str = "cash",
    tool: str | None = "cash_analysis",
    evidence_used: list[str] | None = None,
) -> SelectionReceipt:
    return SelectionReceipt(
        area=area,
        decision="¿Cuánto cash tengo disponible?",
        tool=tool,
        label="Cash Analysis" if tool else None,
        skills=["/escala-cash"],
        evidence_used=evidence_used or [],
        reason="OK",
        missing_minimum=evidence_used is None or not evidence_used,
    )


class TestReviewFinding:
    def test_valid_finding(self):
        finding = ReviewFinding(
            kind="fact",
            severity="info",
            source_ids=["s1"],
            message="Fuente disponible.",
        )
        assert finding.kind == "fact"

    def test_invalid_kind_rejected(self):
        with pytest.raises(ValidationError):
            ReviewFinding(
                kind="invalid",  # type: ignore[typeddict-item]
                severity="info",
                message="x",
            )


class TestReviewReport:
    def test_valid_report(self):
        report = ReviewReport(
            decision="¿Cuánto cash tengo?",
            area="cash",
            tool="cash_analysis",
            findings=[],
            can_proceed=True,
        )
        assert report.can_proceed is True


class TestReviewResult:
    def test_valid_result(self):
        report = ReviewReport(
            decision="¿Cuánto cash tengo?",
            area="cash",
            findings=[],
        )
        result = ReviewResult(
            action="reviewed",
            report=report,
            output="OK",
        )
        assert result.action == "reviewed"


class TestReview:
    def test_consistent_evidence_returns_reviewed(self):
        package = _build_package(
            [
                _build_source(
                    {
                        "source_id": "worksheet-cash-ccc",
                        "source_type": "worksheet",
                        "title": "Cash Conversion Cycle Worksheet",
                    }
                )
            ]
        )
        selection = _build_selection(evidence_used=["worksheet-cash-ccc"])
        result = review(package.decision_ref, package, selection)
        assert result.action == "reviewed"
        assert result.report.can_proceed is True

    def test_not_trustworthy_returns_clarify(self):
        package = _build_package(
            [
                _build_source(
                    {
                        "source_id": "worksheet-cash-ccc",
                        "source_type": "worksheet",
                        "title": "Cash Conversion Cycle Worksheet",
                    }
                )
            ],
            not_trustworthy=[
                _build_source(
                    {
                        "source_id": "worksheet-old",
                        "source_type": "worksheet",
                        "title": "Cash Worksheet 2025",
                        "status": "not_trustworthy",
                        "confidence": "low",
                        "reason": "Desactualizado.",
                    }
                )
            ],
        )
        selection = _build_selection(evidence_used=["worksheet-cash-ccc"])
        result = review(package.decision_ref, package, selection)
        assert result.action == "clarify"
        assert any(finding.kind == "unknown" for finding in result.report.findings)

    def test_contradiction_returns_blocked(self):
        package = _build_package(
            [
                _build_source(
                    {
                        "source_id": "worksheet-a",
                        "source_type": "worksheet",
                        "title": "Worksheet A",
                        "confidence": "low",
                    }
                ),
                _build_source(
                    {
                        "source_id": "worksheet-b",
                        "source_type": "worksheet",
                        "title": "Worksheet B",
                        "confidence": "low",
                    }
                ),
            ]
        )
        selection = _build_selection(evidence_used=["worksheet-a", "worksheet-b"])
        result = review(package.decision_ref, package, selection)
        assert result.action == "blocked"
        assert any(
            finding.kind == "contradiction" for finding in result.report.findings
        )

    def test_area_mismatch_returns_blocked(self):
        package = _build_package(
            [_build_source({"source_id": "worksheet-cash-ccc"})], area="cash"
        )
        selection = _build_selection(area="execution", tool="execution_rhythms")
        result = review(package.decision_ref, package, selection)
        assert result.action == "blocked"
        assert any(finding.kind == "alignment" for finding in result.report.findings)

    def test_tool_without_evidence_returns_blocked(self):
        package = _build_package([_build_source({"source_id": "worksheet-cash-ccc"})])
        selection = _build_selection(tool="cash_analysis", evidence_used=[])
        result = review(package.decision_ref, package, selection)
        assert result.action == "blocked"

    def test_period_mismatch_returns_clarify(self):
        package = _build_package(
            [
                _build_source({"source_id": "s1", "period": "2026-07"}),
                _build_source({"source_id": "s2", "period": "2026-06"}),
            ]
        )
        selection = _build_selection(evidence_used=["s1", "s2"])
        result = review(package.decision_ref, package, selection)
        assert result.action == "clarify"
        assert any(finding.kind == "fact" for finding in result.report.findings)

    def test_no_available_evidence_returns_clarify(self):
        package = _build_package([])
        selection = _build_selection(tool=None, evidence_used=[])
        result = review(package.decision_ref, package, selection)
        assert result.action == "clarify"


class TestFormatter:
    def test_format_reviewed(self):
        report = ReviewReport(
            decision="¿Cuánto cash tengo?",
            area="cash",
            tool="cash_analysis",
            findings=[],
            can_proceed=True,
        )
        output = format_report(report)
        assert "## Revisión de calidad" in output
        assert "La recomendación puede avanzar" in output
        assert "Cash" in output

    def test_format_clarify(self):
        report = ReviewReport(
            decision="¿Cuánto cash tengo?",
            area="cash",
            tool="cash_analysis",
            findings=[
                ReviewFinding(
                    kind="unknown",
                    severity="warning",
                    source_ids=["old"],
                    message="Fuente desactualizada.",
                )
            ],
            can_proceed=False,
        )
        output = format_report(report)
        assert "## Revisión de calidad: falta información" in output
        assert "⚠️" in output

    def test_format_blocked(self):
        report = ReviewReport(
            decision="¿Cuánto cash tengo?",
            area="cash",
            tool="cash_analysis",
            findings=[
                ReviewFinding(
                    kind="contradiction",
                    severity="critical",
                    source_ids=["a", "b"],
                    message="Contradicción detectada.",
                )
            ],
            can_proceed=False,
        )
        output = format_report(report)
        assert "## Revisión de calidad: bloqueada" in output
        assert "❌" in output


class TestRun:
    def _build_context(self, package: EvidencePackage, selection: SelectionReceipt):
        return {
            "base_path": ".",
            "decision": package.decision_ref.model_dump(),
            "package": package.model_dump(),
            "selection": {"action": "tool_selected", "receipt": selection.model_dump()},
        }

    def test_run_reviewed(self):
        package = _build_package([_build_source({"source_id": "worksheet-cash-ccc"})])
        selection = _build_selection(evidence_used=["worksheet-cash-ccc"])
        result = run(self._build_context(package, selection))
        assert result["errors"] == []
        assert result["artifacts"]["action"] == "reviewed"
        assert result["artifacts"]["report"]["can_proceed"] is True

    def test_run_clarify(self):
        package = _build_package(
            [],
            missing=[
                _build_source(
                    {
                        "source_id": "worksheet-cash-ccc",
                        "source_type": "worksheet",
                        "title": "Cash Conversion Cycle Worksheet",
                        "status": "missing",
                        "confidence": "low",
                        "reason": "No encontrado.",
                    }
                )
            ],
        )
        selection = _build_selection(tool=None, evidence_used=[])
        result = run(self._build_context(package, selection))
        assert result["errors"] == []
        assert result["artifacts"]["action"] == "clarify"

    def test_run_blocked(self):
        package = _build_package(
            [
                _build_source({"source_id": "a", "confidence": "low"}),
                _build_source({"source_id": "b", "confidence": "low"}),
            ]
        )
        selection = _build_selection(evidence_used=["a", "b"])
        result = run(self._build_context(package, selection))
        assert result["errors"] == []
        assert result["artifacts"]["action"] == "blocked"

    def test_run_missing_package_returns_error(self):
        selection = _build_selection()
        result = run(
            {
                "base_path": ".",
                "decision": _build_decision().model_dump(),
                "selection": {"receipt": selection.model_dump()},
            }
        )
        assert result["errors"]

    def test_run_missing_selection_returns_error(self):
        package = _build_package([])
        result = run(
            {
                "base_path": ".",
                "decision": _build_decision().model_dump(),
                "package": package.model_dump(),
            }
        )
        assert result["errors"]
