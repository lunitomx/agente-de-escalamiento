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
