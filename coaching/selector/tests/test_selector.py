"""Tests for the coaching.selector module."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent))

import pytest
from pydantic import ValidationError

from coaching.evidence.models import DecisionRef, EvidencePackage, EvidenceSource
from coaching.selector.engine import TOOL_CATALOG, select_tool
from coaching.selector import run
from coaching.selector.formatter import format_clarify, format_selection
from coaching.selector.models import (
    SelectionReceipt,
    SelectionResult,
    ToolSelection,
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
    area: str,
    sources: list[EvidenceSource],
    missing: list[EvidenceSource] | None = None,
) -> EvidencePackage:
    return EvidencePackage(
        decision_ref=DecisionRef(
            decision=f"Decisión de ejemplo en {area}",
            area=area,
            horizon="inmediato",
            outcome="mejorar",
        ),
        sources=sources,
        missing=missing or [],
        not_trustworthy=[],
        questions=[f"¿Tienes disponible '{m.title}'?" for m in (missing or [])],
    )


class TestToolSelection:
    def test_valid_tool_selection(self):
        selection = ToolSelection(
            tool="cash_analysis",
            label="Cash Analysis",
            skills=["/escala-cash", "/escala-cash-ccc", "/escala-cash-power1"],
        )
        assert selection.tool == "cash_analysis"
        assert selection.skills == [
            "/escala-cash",
            "/escala-cash-ccc",
            "/escala-cash-power1",
        ]

    def test_skills_default_empty(self):
        selection = ToolSelection(tool="x", label="X")
        assert selection.skills == []

    def test_missing_required_fields_rejected(self):
        with pytest.raises(ValidationError):
            ToolSelection(tool="x")  # type: ignore[call-arg]


class TestSelectionReceipt:
    def test_valid_receipt_for_selection(self):
        receipt = SelectionReceipt(
            area="cash",
            decision="¿Cuánto cash tengo?",
            tool="cash_analysis",
            label="Cash Analysis",
            skills=["/escala-cash"],
            evidence_used=["worksheet-cash-ccc"],
            reason="Área Cash con workbook financiero disponible.",
            missing_minimum=False,
        )
        assert receipt.missing_minimum is False

    def test_receipt_for_clarify_allows_null_tool(self):
        receipt = SelectionReceipt(
            area="cash",
            decision="¿Cuánto cash tengo?",
            reason="No hay evidencia mínima disponible para el área Cash.",
            missing_minimum=True,
        )
        assert receipt.tool is None
        assert receipt.label is None
        assert receipt.skills == []
        assert receipt.evidence_used == []


class TestSelectionResult:
    def test_valid_result(self):
        receipt = SelectionReceipt(
            area="cash",
            decision="¿Cuánto cash tengo?",
            tool="cash_analysis",
            label="Cash Analysis",
            skills=["/escala-cash"],
            evidence_used=["worksheet-cash-ccc"],
            reason="OK",
        )
        result = SelectionResult(
            action="tool_selected",
            receipt=receipt,
            output="## Herramienta seleccionada",
        )
        assert result.action == "tool_selected"

    def test_invalid_action_rejected(self):
        receipt = SelectionReceipt(
            area="cash",
            decision="x",
            reason="OK",
        )
        with pytest.raises(ValidationError):
            SelectionResult(
                action="unknown",  # type: ignore[typeddict-item]
                receipt=receipt,
                output="x",
            )


class TestToolCatalog:
    def test_catalog_contains_cash_and_execution(self):
        assert "cash" in TOOL_CATALOG
        assert "execution" in TOOL_CATALOG
        assert TOOL_CATALOG["cash"].tool == "cash_analysis"
        assert TOOL_CATALOG["execution"].tool == "execution_rhythms"


class TestSelectTool:
    def test_cash_workbook_selects_cash_analysis(self):
        package = _build_package(
            "cash",
            [
                _build_source(
                    {
                        "source_id": "worksheet-cash-ccc",
                        "source_type": "worksheet",
                        "title": "Cash Conversion Cycle Worksheet",
                        "decision": "cash",
                    }
                )
            ],
        )
        result = select_tool(package)
        assert result.action == "tool_selected"
        assert result.receipt.tool == "cash_analysis"
        assert result.receipt.label == "Cash Analysis"
        assert "/escala-cash" in result.receipt.skills
        assert result.receipt.evidence_used == ["worksheet-cash-ccc"]
        assert result.receipt.missing_minimum is False

    def test_execution_session_log_selects_execution_rhythms(self):
        package = _build_package(
            "execution",
            [
                _build_source(
                    {
                        "source_id": "session-2026-07-15",
                        "source_type": "session_log",
                        "title": "Sesión 2026-07-15 — Execution",
                        "decision": "execution",
                    }
                )
            ],
        )
        result = select_tool(package)
        assert result.action == "tool_selected"
        assert result.receipt.tool == "execution_rhythms"
        assert result.receipt.label == "Execution Rhythms"
        assert "/escala-execution" in result.receipt.skills
        assert result.receipt.evidence_used == ["session-2026-07-15"]

    def test_missing_minimum_returns_clarify(self):
        missing = [
            _build_source(
                {
                    "source_id": "worksheet-cash-ccc",
                    "source_type": "worksheet",
                    "title": "Cash Conversion Cycle Worksheet",
                    "decision": "cash",
                    "status": "missing",
                    "confidence": "low",
                    "reason": "No se encontró worksheet de cash para el área cash.",
                }
            )
        ]
        package = _build_package("cash", [], missing)
        result = select_tool(package)
        assert result.action == "clarify"
        assert result.receipt.tool is None
        assert result.receipt.missing_minimum is True
        assert result.questions == [
            "¿Tienes disponible 'Cash Conversion Cycle Worksheet'?"
        ]

    def test_unrecognized_evidence_for_area_returns_clarify(self):
        # A source that is available but does not match the cash evidence pattern.
        package = _build_package(
            "cash",
            [
                _build_source(
                    {
                        "source_id": "session-2026-07-15",
                        "source_type": "session_log",
                        "title": "Sesión de ejecución",
                        "decision": "execution",
                    }
                )
            ],
        )
        result = select_tool(package)
        assert result.action == "clarify"
        assert result.receipt.missing_minimum is True


class TestFormatter:
    def test_format_selection_cash(self):
        package = _build_package(
            "cash",
            [
                _build_source(
                    {
                        "source_id": "worksheet-cash-ccc",
                        "source_type": "worksheet",
                        "title": "Cash Conversion Cycle Worksheet",
                        "decision": "cash",
                    }
                )
            ],
        )
        receipt = SelectionReceipt(
            area="cash",
            decision="¿Cuánto cash tengo disponible para agosto?",
            tool="cash_analysis",
            label="Cash Analysis",
            skills=["/escala-cash", "/escala-cash-ccc", "/escala-cash-power1"],
            evidence_used=["worksheet-cash-ccc"],
            reason="Área Cash con workbook financiero disponible.",
            missing_minimum=False,
        )
        output = format_selection(receipt, package)
        assert "## Lo que vamos a revisar: tu dinero" in output  # S86.2
        assert "**Área:** Tu dinero" in output
        assert "¿Cuánto cash tengo disponible para agosto?" in output
        assert "Cash Conversion Cycle Worksheet (2026-07)" in output
        assert "Área Cash con workbook financiero disponible." in output
        assert "/escala-" not in output  # S86.2: el paso siguiente es una pregunta
        assert "Próximo paso: ¿Vemos cuántos días tardas en cobrar" in output

    def test_format_selection_execution(self):
        package = _build_package(
            "execution",
            [
                _build_source(
                    {
                        "source_id": "session-2026-07-15",
                        "source_type": "session_log",
                        "title": "Sesión 2026-07-15 — Execution",
                        "decision": "execution",
                    }
                )
            ],
        )
        receipt = SelectionReceipt(
            area="execution",
            decision="¿Por qué no avanzan las prioridades del trimestre?",
            tool="execution_rhythms",
            label="Execution Rhythms",
            skills=[
                "/escala-execution",
                "/escala-execution-rhythms",
                "/escala-execution-priorities",
            ],
            evidence_used=["session-2026-07-15"],
            reason="Área Execution con registros de reuniones/prioridades disponibles.",
            missing_minimum=False,
        )
        output = format_selection(receipt, package)
        assert "## Lo que vamos a revisar: tu día a día" in output
        assert "**Área:** Tu día a día" in output
        assert "Sesión 2026-07-15 — Execution" in output
        assert "/escala-" not in output

    def test_format_clarify_cash(self):
        receipt = SelectionReceipt(
            area="cash",
            decision="¿Cuánto cash tengo disponible?",
            reason="No hay evidencia mínima disponible para el área Cash.",
            missing_minimum=True,
        )
        questions = ["¿Tienes disponible 'Cash Conversion Cycle Worksheet'?"]
        output = format_clarify(receipt, questions, _build_package("cash", []))
        assert "## Falta información" in output
        assert "**tu dinero**" in output
        assert "tus números recientes" in output
        assert questions[0] in output


class TestRun:
    def test_run_with_cash_package_returns_tool_selected(self):
        package = _build_package(
            "cash",
            [
                _build_source(
                    {
                        "source_id": "worksheet-cash-ccc",
                        "source_type": "worksheet",
                        "title": "Cash Conversion Cycle Worksheet",
                        "decision": "cash",
                    }
                )
            ],
        )
        context = {
            "base_path": ".",
            "decision": {
                "decision": "¿Cuánto cash tengo disponible?",
                "area": "cash",
                "horizon": "inmediato",
                "outcome": "conocer liquidez actual",
            },
            "package": package.model_dump(),
        }
        result = run(context)
        assert result["errors"] == []
        assert result["artifacts"]["action"] == "tool_selected"
        assert result["artifacts"]["receipt"]["tool"] == "cash_analysis"
        assert "## Lo que vamos a revisar" in result["output"]

    def test_run_with_execution_package_returns_execution_rhythms(self):
        package = _build_package(
            "execution",
            [
                _build_source(
                    {
                        "source_id": "session-2026-07-15",
                        "source_type": "session_log",
                        "title": "Sesión 2026-07-15 — Execution",
                        "decision": "execution",
                    }
                )
            ],
        )
        context = {
            "base_path": ".",
            "decision": {
                "decision": "¿Por qué no avanzan las prioridades del trimestre?",
                "area": "execution",
                "horizon": "corto",
                "outcome": "recuperar ritmo",
            },
            "package": package.model_dump(),
        }
        result = run(context)
        assert result["errors"] == []
        assert result["artifacts"]["action"] == "tool_selected"
        assert result["artifacts"]["receipt"]["tool"] == "execution_rhythms"

    def test_run_without_package_returns_error(self):
        context = {
            "base_path": ".",
            "decision": {
                "decision": "¿Cuánto cash tengo?",
                "area": "cash",
                "horizon": "inmediato",
                "outcome": "x",
            },
        }
        result = run(context)
        assert result["errors"]
        assert "paquete de evidencia" in result["errors"][0]

    def test_run_missing_minimum_returns_clarify(self):
        missing = [
            _build_source(
                {
                    "source_id": "worksheet-cash-ccc",
                    "source_type": "worksheet",
                    "title": "Cash Conversion Cycle Worksheet",
                    "decision": "cash",
                    "status": "missing",
                    "confidence": "low",
                    "reason": "No se encontró worksheet de cash.",
                }
            )
        ]
        package = _build_package("cash", [], missing)
        context = {
            "base_path": ".",
            "decision": {
                "decision": "¿Cuánto cash tengo disponible?",
                "area": "cash",
                "horizon": "inmediato",
                "outcome": "conocer liquidez",
            },
            "package": package.model_dump(),
        }
        result = run(context)
        assert result["errors"] == []
        assert result["artifacts"]["action"] == "clarify"
        assert result["artifacts"]["receipt"]["missing_minimum"] is True
        assert "## Falta información" in result["output"]

    def test_run_loads_decision_from_profile(self, tmp_path):
        profile_dir = tmp_path / ".escala" / "agent" / "memory"
        profile_dir.mkdir(parents=True)
        profile = {
            "focus": {
                "current_decision": {
                    "decision": "¿Cuánto cash tengo?",
                    "area": "cash",
                    "horizon": "inmediato",
                    "outcome": "conocer liquidez",
                }
            }
        }
        import yaml

        (profile_dir / "company-profile.yaml").write_text(yaml.dump(profile))

        package = _build_package(
            "cash",
            [
                _build_source(
                    {
                        "source_id": "worksheet-cash-ccc",
                        "source_type": "worksheet",
                        "title": "Cash Conversion Cycle Worksheet",
                        "decision": "cash",
                    }
                )
            ],
        )
        context = {"base_path": str(tmp_path), "package": package.model_dump()}
        result = run(context)
        assert result["errors"] == []
        assert result["artifacts"]["receipt"]["decision"] == "¿Cuánto cash tengo?"
