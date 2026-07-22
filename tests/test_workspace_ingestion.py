"""TDD contract tests for flexible local source ingestion."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest
from pydantic import ValidationError

from escala_server.workspace.ingestion import (
    SourceIdentity,
    SourceRegistry,
    SourceIngestionError,
    build_source_identity,
    profile_source,
    render_ingestion_receipt_json,
    render_ingestion_receipt_markdown,
)
from escala_server.workspace.authority import WorkspaceConfig
from escala_server import workspace


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


def _config(tmp_path: Path) -> WorkspaceConfig:
    return WorkspaceConfig(
        platform="macos",
        data_root=tmp_path / "data",
        database_path=tmp_path / "data" / "escala.sqlite",
        exchange_root=tmp_path / "exchange",
    )


def test_profiles_tabular_sources(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config.exchange_root.mkdir()
    source = config.exchange_root / "ventas.csv"
    source.write_text(
        "fecha,cliente,importe\n2026-07-22,Acme,10\n2026-07-23,Beta,20\n",
        encoding="utf-8",
    )

    result = profile_source(config, source)

    assert result.status == "ready"
    assert result.profile is not None
    table = result.profile.tables[0]
    assert table.row_count == 3
    assert table.column_count == 3
    assert table.header_candidates[0].row_index == 0
    assert {field.kind for field in table.field_candidates} >= {
        "date",
        "entity",
        "unit",
    }


def test_ambiguous_profile_is_fail_closed(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config.exchange_root.mkdir()
    source = config.exchange_root / "cash.tsv"
    source.write_text(
        "fecha\tcliente\timporte\nFecha\tCliente\tImporte\n2026-07-22\tAcme\t10\n",
        encoding="utf-8",
    )

    result = profile_source(config, source)

    assert result.status == "needs_clarification"
    assert result.profile is not None
    assert result.questions[0].code == "header_row_ambiguous"
    assert result.questions[0].options == ("row_0", "row_1")


def _write_minimal_xlsx(path: Path) -> None:
    sheet = """<?xml version='1.0' encoding='UTF-8'?>
<worksheet xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'>
  <sheetData>
    <row r='1'><c r='A1' t='inlineStr'><is><t>fecha</t></is></c><c r='B1' t='inlineStr'><is><t>cliente</t></is></c><c r='C1' t='inlineStr'><is><t>importe</t></is></c></row>
    <row r='2'><c r='A2' t='inlineStr'><is><t>2026-07-22</t></is></c><c r='B2' t='inlineStr'><is><t>Acme</t></is></c><c r='C2' t='n'><v>10</v></c></row>
  </sheetData>
</worksheet>"""
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", sheet)


def test_profiles_xlsx_and_transcript_without_template(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config.exchange_root.mkdir()
    workbook = config.exchange_root / "ventas.xlsx"
    _write_minimal_xlsx(workbook)
    transcript = config.exchange_root / "weekly.transcript"
    transcript.write_text("Acuerdos\nRiesgos\n", encoding="utf-8")

    workbook_result = profile_source(config, workbook)
    transcript_result = profile_source(config, transcript)

    assert workbook_result.status == "ready"
    assert workbook_result.profile is not None
    assert workbook_result.profile.tables[0].row_count == 2
    assert workbook_result.profile.tables[0].column_count == 3
    assert transcript_result.status == "ready"
    assert transcript_result.profile is not None
    assert transcript_result.profile.tables[0].row_count == 2


def test_corrupt_xlsx_is_explicit_and_source_is_unchanged(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config.exchange_root.mkdir()
    workbook = config.exchange_root / "broken.xlsx"
    workbook.write_bytes(b"not a zip workbook")
    before = workbook.read_bytes()

    result = profile_source(config, workbook)

    assert result.status == "corrupt"
    assert result.findings == ("source_unreadable",)
    assert workbook.read_bytes() == before


def test_failure_receipts_are_redacted_and_deterministic(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config.exchange_root.mkdir()
    pdf = config.exchange_root / "estado.pdf"
    pdf.write_bytes(b"%PDF-1.7 private balance content")
    unknown = config.exchange_root / "misterio.bin"
    unknown.write_bytes(b"private bytes")

    pdf_result = profile_source(config, pdf)
    unknown_result = profile_source(config, unknown)

    assert pdf_result.status == "provider_unavailable"
    assert unknown_result.status == "unsupported"
    pdf_json = render_ingestion_receipt_json(pdf_result)
    assert pdf_json == render_ingestion_receipt_json(pdf_result)
    assert render_ingestion_receipt_markdown(pdf_result).endswith("\n")
    for receipt in (pdf_json, render_ingestion_receipt_markdown(pdf_result)):
        assert str(tmp_path) not in receipt
        assert "private balance content" not in receipt
        assert "https://" not in receipt


def test_public_workspace_seam_profiles_without_canonical_mutation(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    config.exchange_root.mkdir()
    source = config.exchange_root / "daily.csv"
    source.write_text("fecha,cliente,importe\n2026-07-22,Acme,10\n", encoding="utf-8")
    before_entries = sorted(path.name for path in tmp_path.iterdir())

    result = workspace.profile_source(config, source)

    assert result.status == "ready"
    assert workspace.render_ingestion_receipt_json(result)
    assert (
        workspace.SourceRegistry.default().capability_for("daily.csv").format == "csv"
    )
    assert not (config.data_root / "escala.sqlite").exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == before_entries
