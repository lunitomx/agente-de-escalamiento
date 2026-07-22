"""TDD contract tests for flexible local source ingestion."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from escala_server.workspace.ingestion import (
    SourceIdentity,
    SourceRegistry,
    SourceIngestionError,
    build_source_identity,
)


def test_registry_reports_declared_capabilities() -> None:
    registry = SourceRegistry.default()

    assert registry.capability_for("ventas.csv").status == "supported"
    assert registry.capability_for("cash.tsv").format == "tsv"
    assert registry.capability_for("estado.xlsx").status == "supported"
    assert registry.capability_for("reporte.pdf").status == "provider_unavailable"
    assert registry.capability_for("misterio.bin").status == "unsupported"


def test_source_identity_is_stable_and_changes_with_bytes(tmp_path: Path) -> None:
    exchange = tmp_path / "exchange"
    exchange.mkdir()
    source = exchange / "ventas.csv"
    source.write_text("fecha,cliente,importe\n2026-07-22,Acme,10\n", encoding="utf-8")

    first = build_source_identity(source, exchange)
    second = build_source_identity(source, exchange)

    assert isinstance(first, SourceIdentity)
    assert first == second
    assert first.relative_path == "ventas.csv"
    assert len(first.content_sha256) == 64
    assert len(first.source_id) == 64
    assert str(tmp_path) not in first.model_dump_json()

    source.write_text("fecha,cliente,importe\n2026-07-22,Acme,11\n", encoding="utf-8")
    changed = build_source_identity(source, exchange)

    assert changed.content_sha256 != first.content_sha256
    assert changed.source_id != first.source_id


def test_source_identity_rejects_file_outside_exchange(tmp_path: Path) -> None:
    exchange = tmp_path / "exchange"
    exchange.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_text("a,b\n1,2\n", encoding="utf-8")

    with pytest.raises(SourceIngestionError, match="source_outside_exchange"):
        build_source_identity(outside, exchange)


def test_identity_model_is_closed() -> None:
    with pytest.raises(ValidationError):
        SourceIdentity(
            relative_path="ventas.csv",
            format="csv",
            content_sha256="a" * 64,
            source_id="b" * 64,
            absolute_path="/private/company/ventas.csv",  # type: ignore[call-arg]
        )
