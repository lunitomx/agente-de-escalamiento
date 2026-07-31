"""Tests for the coaching.evidence module."""

from __future__ import annotations

import pathlib
import sys
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent))

import pytest
from pydantic import ValidationError

from coaching.evidence.models import (
    SAFE_LOCATOR_PREFIX,
    VALID_CONFIDENCES,
    VALID_STATUSES,
    DecisionRef,
    EvidencePackage,
    EvidenceSource,
)


def _build_source(overrides: dict[str, Any]) -> EvidenceSource:
    """Build an EvidenceSource from a dict to test invalid literal values."""
    defaults: dict[str, Any] = {
        "source_id": "x",
        "source_type": "y",
        "title": "z",
        "decision": "people",
        "status": "available",
        "period": "2026-05",
        "confidence": "medium",
        "reason": "r",
    }
    defaults.update(overrides)
    return EvidenceSource(**defaults)


class TestEvidenceSource:
    def test_valid_available_source(self):
        source = EvidenceSource(
            source_id="session-2026-05-06",
            source_type="session_log",
            title="Sesión 2026-05-06 — People",
            decision="people",
            status="available",
            period="2026-05-06",
            confidence="high",
            reason="Sesión reciente con foco People y worksheets completados.",
        )
        assert source.status == "available"
        assert source.confidence == "high"

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError) as exc:
            _build_source({"status": "unknown"})
        assert "status" in str(exc.value)

    def test_invalid_confidence_rejected(self):
        with pytest.raises(ValidationError) as exc:
            _build_source({"confidence": "very-high"})
        assert "confidence" in str(exc.value)

    def test_safe_locator_relative_to_escala(self):
        source = EvidenceSource(
            source_id="worksheet-face",
            source_type="worksheet",
            title="FACE Worksheet",
            decision="people",
            status="available",
            period="2026-05",
            confidence="medium",
            reason="Worksheet completado.",
            locator=".escala/my-company/worksheets/face.yaml",
        )
        assert source.locator == ".escala/my-company/worksheets/face.yaml"

    @pytest.mark.parametrize(
        "bad_locator",
        [
            "/absolute/path.yaml",
            "file:///etc/passwd",
            "https://example.com/data.yaml",
            "../../outside/escala.yaml",
            "C:\\Windows\\secret.txt",
        ],
    )
    def test_unsafe_locator_rejected(self, bad_locator: str):
        with pytest.raises(ValidationError) as exc:
            EvidenceSource(
                source_id="x",
                source_type="y",
                title="z",
                decision="people",
                status="available",
                period="2026-05",
                confidence="medium",
                reason="r",
                locator=bad_locator,
            )
        assert "locator" in str(exc.value)


class TestEvidencePackage:
    def test_package_with_all_sections(self):
        pkg = EvidencePackage(
            decision_ref=DecisionRef(
                decision="contratar a María en ventas",
                area="people",
                horizon="inmediato",
                outcome="cubrir la vacante y mejorar cobertura comercial",
            ),
            sources=[
                EvidenceSource(
                    source_id="session-2026-05-06",
                    source_type="session_log",
                    title="Sesión 2026-05-06 — People",
                    decision="people",
                    status="available",
                    period="2026-05-06",
                    confidence="high",
                    reason="Sesión reciente con foco People.",
                )
            ],
            missing=[
                EvidenceSource(
                    source_id="worksheet-topgrading",
                    source_type="worksheet",
                    title="Topgrading Interview Guide",
                    decision="people",
                    status="missing",
                    period="",
                    confidence="low",
                    reason="No se encontró worksheet de entrevista para el puesto.",
                )
            ],
            not_trustworthy=[],
            questions=["¿Tienes evaluaciones de desempeño del último trimestre?"],
        )
        assert pkg.decision_ref.area == "people"
        assert len(pkg.sources) == 1
        assert len(pkg.missing) == 1


class TestDomainConstants:
    def test_status_constants(self):
        assert set(VALID_STATUSES) == {"available", "missing", "not_trustworthy"}

    def test_confidence_constants(self):
        assert set(VALID_CONFIDENCES) == {"high", "medium", "low"}

    def test_safe_locator_prefix(self):
        assert SAFE_LOCATOR_PREFIX == ".escala/"


class TestEvidenceEngine:
    def test_available_source_classified_high_confidence(self):
        from coaching.evidence.engine import discover_sources
        from coaching.evidence.models import DecisionRef

        decision = DecisionRef(
            decision="contratar a María en ventas",
            area="people",
            horizon="inmediato",
            outcome="cubrir la vacante",
        )
        local_sources = {
            "sessions": [
                {
                    "id": "session-2026-05-06",
                    "date": "2026-05-06",
                    "decision_focus": "people",
                    "worksheets_completed": ["FACE Worksheet"],
                    "locator": ".escala/my-company/sessions/2026-05-06.md",
                }
            ],
            "worksheets": [
                {
                    "id": "worksheet-face",
                    "name": "FACE Worksheet",
                    "decision": "people",
                    "completed": True,
                    "date": "2026-05-06",
                    "locator": ".escala/my-company/worksheets/face.yaml",
                }
            ],
            "tasks": [],
            "metrics": [],
            "registry": {"worksheets": []},
        }
        package = discover_sources(decision, local_sources, today="2026-05-10")

        assert len(package.sources) == 2
        assert any(s.source_id == "session-2026-05-06" for s in package.sources)
        assert any(s.source_id == "worksheet-face" for s in package.sources)
        assert all(s.status == "available" for s in package.sources)
        assert package.sources[0].confidence == "high"

    def test_missing_source_generates_clarification_question(self):
        from coaching.evidence.engine import discover_sources
        from coaching.evidence.models import DecisionRef

        decision = DecisionRef(
            decision="contratar a María en ventas",
            area="people",
            horizon="inmediato",
            outcome="cubrir la vacante",
        )
        registry_worksheets = [
            {
                "id": "worksheet-topgrading",
                "decision": "people",
                "name": "Topgrading Interview Guide",
            }
        ]
        local_sources = {
            "sessions": [],
            "worksheets": [],
            "tasks": [],
            "metrics": [],
            "registry": {"worksheets": registry_worksheets},
        }
        package = discover_sources(decision, local_sources, today="2026-05-10")

        assert len(package.missing) == 1
        assert package.missing[0].source_id == "worksheet-topgrading"
        assert package.missing[0].status == "missing"
        assert len(package.questions) == 1
        assert "topgrading" in package.questions[0].lower()

    def test_outdated_source_marked_not_trustworthy(self):
        from coaching.evidence.engine import discover_sources
        from coaching.evidence.models import DecisionRef

        decision = DecisionRef(
            decision="contratar a María en ventas",
            area="people",
            horizon="inmediato",
            outcome="cubrir la vacante",
        )
        local_sources = {
            "sessions": [
                {
                    "id": "session-2025-01-10",
                    "date": "2025-01-10",
                    "decision_focus": "people",
                    "worksheets_completed": [],
                    "locator": ".escala/my-company/sessions/2025-01-10.md",
                }
            ],
            "worksheets": [],
            "tasks": [],
            "metrics": [],
            "registry": {"worksheets": []},
        }
        package = discover_sources(decision, local_sources, today="2026-05-10")

        assert len(package.not_trustworthy) == 1
        assert package.not_trustworthy[0].source_id == "session-2025-01-10"
        assert package.not_trustworthy[0].status == "not_trustworthy"
        assert "desactualizada" in package.not_trustworthy[0].reason.lower()

    def test_incomplete_worksheet_marked_not_trustworthy(self):
        from coaching.evidence.engine import discover_sources
        from coaching.evidence.models import DecisionRef

        decision = DecisionRef(
            decision="¿Podemos pagar la nómina de agosto?",
            area="cash",
            horizon="inmediato",
            outcome="evitar crisis de liquidez",
        )
        local_sources = {
            "sessions": [],
            "worksheets": [
                {
                    "id": "worksheet-ccc",
                    "name": "Cash Conversion Cycle Worksheet",
                    "decision": "cash",
                    "completed": False,
                    "date": "2026-07-15",
                    "locator": ".escala/my-company/worksheets/ccc-worksheet.yaml",
                }
            ],
            "tasks": [],
            "metrics": [],
            "registry": {"worksheets": []},
        }
        package = discover_sources(decision, local_sources, today="2026-07-31")

        assert len(package.not_trustworthy) == 1
        assert package.not_trustworthy[0].source_id == "worksheet-ccc"
        assert "incompleto" in package.not_trustworthy[0].reason.lower()


class TestFormatter:
    def test_format_package_no_absolute_paths(self):
        from coaching.evidence.formatter import format_package
        from coaching.evidence.models import (
            DecisionRef,
            EvidencePackage,
            EvidenceSource,
        )

        package = EvidencePackage(
            decision_ref=DecisionRef(
                decision="contratar a María en ventas",
                area="people",
                horizon="inmediato",
                outcome="cubrir la vacante",
            ),
            sources=[
                EvidenceSource(
                    source_id="session-2026-05-06",
                    source_type="session_log",
                    title="Sesión 2026-05-06",
                    decision="people",
                    status="available",
                    period="2026-05-06",
                    confidence="high",
                    reason="Sesión reciente.",
                    locator=".escala/my-company/sessions/2026-05-06.md",
                )
            ],
            missing=[],
            not_trustworthy=[],
            questions=[],
        )
        text = format_package(package)
        assert "contratar a María en ventas" in text
        assert "/Users/" not in text
        assert ".escala" not in text


class TestRun:
    def test_run_with_confirmed_decision_returns_package(self, tmp_path):
        from coaching.evidence import run

        profile = {
            "focus": {
                "current_decision": {
                    "decision": "contratar a María en ventas",
                    "area": "people",
                    "horizon": "inmediato",
                    "outcome": "cubrir la vacante",
                    "confirmed": "2026-05-06",
                }
            }
        }
        profile_path = (
            tmp_path / ".escala" / "agent" / "memory" / "company-profile.yaml"
        )
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        import yaml

        profile_path.write_text(yaml.dump(profile))

        result = run({"base_path": str(tmp_path)})
        assert result["errors"] == []
        assert result["artifacts"]["action"] == "evidence_package"
        assert "Paquete de evidencia" in result["output"]
        assert result["artifacts"]["package"]["decision_ref"]["area"] == "people"

    def test_run_without_decision_returns_error(self, tmp_path):
        from coaching.evidence import run

        profile_path = (
            tmp_path / ".escala" / "agent" / "memory" / "company-profile.yaml"
        )
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text("focus:\n")

        result = run({"base_path": str(tmp_path)})
        assert result["errors"]
        assert "/escala-decision" in result["errors"][0]
