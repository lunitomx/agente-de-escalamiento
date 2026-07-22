"""Qualification tests for E38 local financial intelligence."""

from __future__ import annotations

from pathlib import Path
from datetime import date
from zipfile import ZipFile

from escala_server.financial import (
    MappingAnswer,
    profile_financial_workbook,
    reconstruct_statements,
    render_profile_receipt_json,
    resolve_mapping_answers,
)
from escala_server.workspace.authority import WorkspaceConfig


def _config(tmp_path: Path) -> WorkspaceConfig:
    exchange = tmp_path / "exchange"
    exchange.mkdir()
    return WorkspaceConfig(
        platform="macos",
        data_root=tmp_path / "data",
        database_path=tmp_path / "data" / "escala.sqlite",
        exchange_root=exchange,
    )


def _write_xlsx(
    path: Path, rows: list[list[str]], *, sheet_name: str = "Resultados"
) -> None:
    shared = sorted({value for row in rows for value in row if value})
    shared_index = {value: index for index, value in enumerate(shared)}
    shared_xml = "".join(f"<si><t>{value}</t></si>" for value in shared)
    sheet_rows: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells: list[str] = []
        for column_index, value in enumerate(row):
            if not value:
                continue
            column = chr(ord("A") + column_index)
            if value.startswith("="):
                cells.append(f"<c r='{column}{row_index}'><f>{value[1:]}</f></c>")
            elif value.replace(".", "", 1).isdigit():
                cells.append(f"<c r='{column}{row_index}' t='n'><v>{value}</v></c>")
            else:
                cells.append(
                    f"<c r='{column}{row_index}' t='s'><v>{shared_index[value]}</v></c>"
                )
        sheet_rows.append(f"<row r='{row_index}'>{''.join(cells)}</row>")
    workbook = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<workbook xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main' "
        "xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships'>"
        f"<sheets><sheet name='{sheet_name}' sheetId='1' r:id='rId1'/></sheets></workbook>"
    )
    rels = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>"
        "<Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet' "
        "Target='worksheets/sheet1.xml'/></Relationships>"
    )
    sheet = (
        "<?xml version='1.0' encoding='UTF-8'?><worksheet "
        "xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'><sheetData>"
        f"{''.join(sheet_rows)}</sheetData></worksheet>"
    )
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
        archive.writestr(
            "xl/sharedStrings.xml",
            f"<sst xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main' count='{len(shared)}' uniqueCount='{len(shared)}'>{shared_xml}</sst>",
        )


def test_profiles_real_workbook_without_fixed_template(tmp_path: Path) -> None:
    config = _config(tmp_path)
    workbook = config.exchange_root / "nopal-foods.xlsx"
    _write_xlsx(
        workbook,
        [
            ["Cuenta", "2026-06", "2026-07", "Moneda", "Unidad"],
            ["Ventas netas", "100000", "120000", "MXN", "pesos"],
            ["Costo de ventas", "60000", "70000", "MXN", "pesos"],
            ["Caja", "20000", "22000", "MXN", "pesos"],
            ["Margen neto", "=B2-B3", "=C2-C3", "MXN", "pesos"],
        ],
    )

    profile = profile_financial_workbook(config, workbook)

    assert profile.status == "ready"
    assert profile.identity.relative_path == "nopal-foods.xlsx"
    assert profile.sheets[0].name == "Resultados"
    assert profile.sheets[0].periods == ("2026-06", "2026-07")
    assert profile.sheets[0].currencies == ("MXN",)
    assert profile.sheets[0].units == ("pesos",)
    assert profile.sheets[0].formula_count == 2
    assert "revenue" in {candidate.target for candidate in profile.mapping_candidates}
    assert profile.mapping_status == "resolved"


def test_ambiguous_mapping_asks_owner_before_resolving(tmp_path: Path) -> None:
    config = _config(tmp_path)
    workbook = config.exchange_root / "ambiguous.csv"
    workbook.write_text(
        "Cuenta,2026-07,Moneda\nVentas,100,MXN\nIngresos,100,MXN\n",
        encoding="utf-8",
    )

    profile = profile_financial_workbook(config, workbook)

    assert profile.status == "needs_clarification"
    question = next(
        question for question in profile.questions if question.target == "revenue"
    )
    assert question.code == "mapping_ambiguous"
    assert len(question.options) == 2
    assert profile.mapping_status == "unresolved"

    answered = resolve_mapping_answers(
        profile,
        (MappingAnswer(target="revenue", candidate_id=question.options[0]),),
    )
    assert answered.mapping_status == "resolved"
    assert answered.confirmed_mappings[0].candidate_id == question.options[0]
    assert not [q for q in answered.questions if q.target == "revenue"]


def test_formula_without_cached_value_and_receipt_are_safe(tmp_path: Path) -> None:
    config = _config(tmp_path)
    workbook = config.exchange_root / "formula.csv"
    workbook.write_text(
        "Cuenta,2026-07,Moneda\nVentas,100,MXN\nUtilidad,=B2-B3,MXN\n",
        encoding="utf-8",
    )
    before = workbook.read_bytes()

    profile = profile_financial_workbook(config, workbook)
    receipt = render_profile_receipt_json(profile)

    assert "formula_without_cached_value" in profile.findings
    assert str(tmp_path) not in receipt
    assert "100" not in receipt
    assert workbook.read_bytes() == before


def test_reconstructs_statements_with_figure_provenance(tmp_path: Path) -> None:
    config = _config(tmp_path)
    workbook = config.exchange_root / "nopal-foods.csv"
    workbook.write_text(
        "Cuenta,2026-07,Moneda,Unidad\n"
        "Ventas netas,120000,MXN,pesos\n"
        "Costo de ventas,70000,MXN,pesos\n"
        "Gastos operativos,30000,MXN,pesos\n"
        "Utilidad neta,15000,MXN,pesos\n"
        "Caja,22000,MXN,pesos\n"
        "Cuentas por cobrar,18000,MXN,pesos\n"
        "Inventario,12000,MXN,pesos\n"
        "Cuentas por pagar,9000,MXN,pesos\n"
        "Flujo operativo,20000,MXN,pesos\n"
        "Flujo de inversion,-5000,MXN,pesos\n"
        "Flujo de financiamiento,-3000,MXN,pesos\n",
        encoding="utf-8",
    )

    profile = profile_financial_workbook(config, workbook)
    statements = reconstruct_statements(profile, as_of=date(2026, 7, 22))

    assert statements.status == "ready"
    assert statements.pnl.status == "ready"
    gross_profit = next(
        figure for figure in statements.pnl.figures if figure.account == "gross_profit"
    )
    assert gross_profit.value == 50000
    assert gross_profit.provenance.transformation == "revenue - cogs"
    assert gross_profit.provenance.relative_path == "nopal-foods.csv"
    assert gross_profit.provenance.sheet == "nopal-foods"
    assert gross_profit.provenance.cell_range == "nopal-foods!B2 - nopal-foods!B3"
    assert statements.balance.status == "ready"
    assert statements.cash_flow.status == "ready"
    net_change = next(
        figure
        for figure in statements.cash_flow.figures
        if figure.account == "net_cash_change"
    )
    assert net_change.value == 12000


def test_unresolved_mapping_blocks_statement_reconstruction(tmp_path: Path) -> None:
    config = _config(tmp_path)
    workbook = config.exchange_root / "ambiguous-statements.csv"
    workbook.write_text(
        "Cuenta,2026-07,Moneda\nVentas,100,MXN\nIngresos,100,MXN\n"
        "Costo de ventas,50,MXN\nGastos operativos,20,MXN\n",
        encoding="utf-8",
    )

    profile = profile_financial_workbook(config, workbook)
    statements = reconstruct_statements(profile, as_of=date(2026, 7, 22))

    assert statements.status == "blocked"
    assert "mapping_unresolved" in statements.findings
    assert statements.questions
    assert statements.pnl.status == "not_derivable"


def test_formula_without_cached_value_is_not_a_financial_fact(tmp_path: Path) -> None:
    config = _config(tmp_path)
    workbook = config.exchange_root / "missing-cached.csv"
    workbook.write_text(
        "Cuenta,2026-07,Moneda\nVentas netas,100,MXN\nCosto de ventas,50,MXN\n"
        "Gastos operativos,20,MXN\nUtilidad neta,=B2-B3,MXN\n",
        encoding="utf-8",
    )

    profile = profile_financial_workbook(config, workbook)
    statements = reconstruct_statements(profile, as_of=date(2026, 7, 22))

    assert statements.pnl.status == "partial"
    assert "net_profit" in statements.pnl.missing
    assert "formula_without_cached_value" in statements.findings
