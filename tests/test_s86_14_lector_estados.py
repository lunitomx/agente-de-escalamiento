"""S86.14 — ESCALA lee los estados como vienen.

Una prueba por cada falla de la revisión adversarial A4 del lector de E38:

1. coincidía por pedazo de palabra («ventas» encontraba «Costo de ventas»);
2. tomaba una sola fila por concepto;
3. sólo entendía fechas «2025-12»;
4. bloqueaba si no decía «pesos»;
5. bloqueaba todo dato con más de 90 días;
6. descartaba negativos entre paréntesis.

Datos: «Mi Empresa, S.A. de C.V.» (sintéticos, diccionarios A = 2024 y
B = 2025 del curso de cash) en archivos con forma de CONTPAQi y de Aspel.
"""

from __future__ import annotations

import filecmp
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from escala_server.financial import profile_financial_workbook, reconstruct_statements
from escala_server.financial.formatos import (
    buscar_fechas,
    concepto_de,
    leer_monto,
    posible_digito_invertido,
)
from escala_server.financial.lector import (
    LecturaEstados,
    leer_estados,
    leer_texto,
    render_asi_lei,
)
from escala_server.financial.profiling import read_raw_sheets
from escala_server.workspace.authority import WorkspaceConfig

ESTADOS = Path(__file__).parent / "fixtures" / "cash" / "estados"
HOY = date(2026, 10, 16)
REPORTES = (
    "contpaqi_balance",
    "contpaqi_resultados",
    "aspel_balance",
    "aspel_resultados",
)
FIN_2025 = date(2025, 12, 31)
FIN_2024 = date(2024, 12, 31)


def _montos(lectura: LecturaEstados, fecha: date) -> dict[str, Decimal]:
    return {
        cuenta.nombre: cuenta.monto
        for cuenta in lectura.cuentas
        if cuenta.fecha == fecha and not cuenta.es_total
    }


# ---------------------------------------------------------------------------
# A4-1 · palabra completa con lista de exclusiones
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nombre", "concepto"),
    [
        ("Ventas netas", "ventas"),
        ("VENTAS", "ventas"),
        ("Costo de ventas", "costo_ventas"),
        ("Devoluciones sobre ventas", None),
        ("Otros ingresos (venta de activos)", None),
        ("Clientes", "clientes"),
        ("Anticipo de clientes", None),
        ("Anticipos de clientes", None),
        ("Proveedores", "proveedores"),
        ("Anticipo a proveedores", None),
        ("Caja y bancos", "bancos"),
        ("Gastos de venta", "gastos_operacion"),
        ("Gastos de administración", "gastos_operacion"),
        ("Gastos financieros", "intereses"),
        ("Inventarios", "inventario"),
        ("Total gastos de operación", "gastos_operacion"),
    ],
)
def test_a4_1_concepto_por_palabra_completa_con_exclusiones(
    nombre: str, concepto: str | None
) -> None:
    assert concepto_de(nombre) == concepto


def test_a4_1_costo_de_ventas_no_es_ventas_en_la_lectura() -> None:
    lectura = leer_texto(
        "Estado de resultados al 31/12/2025\n"
        "Cifras en pesos\n"
        "Ventas netas  1,000.00\n"
        "Costo de ventas  600.00\n"
        "Anticipo de clientes  50.00\n"
        "Clientes  300.00\n",
        hoy=HOY,
    )
    conceptos = {cuenta.nombre: cuenta.concepto for cuenta in lectura.cuentas}
    assert conceptos == {
        "Ventas netas": "ventas",
        "Costo de ventas": "costo_ventas",
        "Anticipo de clientes": None,
        "Clientes": "clientes",
    }
    # Sólo una fila es «ventas»: no hay suma que confirmar.
    assert lectura.sumas_por_confirmar == ()


def test_a4_1_el_lector_de_e38_no_toma_costo_de_ventas_como_ventas(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    source = config.exchange_root / "estado.csv"
    source.write_text(
        "Cuenta,2026-07,Moneda\nCosto de ventas,50,MXN\nAnticipo de clientes,7,MXN\n",
        encoding="utf-8",
    )
    profile = profile_financial_workbook(config, source)
    targets = {
        (candidate.label, candidate.target) for candidate in profile.mapping_candidates
    }
    assert ("Costo de ventas", "revenue") not in targets
    assert ("Costo de ventas", "cogs") in targets
    assert ("Anticipo de clientes", "accounts_receivable") not in targets


# ---------------------------------------------------------------------------
# A4-2 · varias filas del mismo concepto: se listan todas y la suma pide «sí»
# ---------------------------------------------------------------------------


def test_a4_2_varias_filas_del_mismo_concepto_piden_confirmacion() -> None:
    lectura = leer_estados(ESTADOS / "aspel_resultados.csv", hoy=HOY)
    nombres = [cuenta.nombre for cuenta in lectura.cuentas if cuenta.fecha == FIN_2025]
    assert "Gastos de venta" in nombres
    assert "Gastos de administración" in nombres

    sumas = {(suma.concepto, suma.fecha): suma for suma in lectura.sumas_por_confirmar}
    assert set(sumas) == {
        ("gastos_operacion", FIN_2025),
        ("gastos_operacion", FIN_2024),
    }
    actual = sumas[("gastos_operacion", FIN_2025)]
    assert actual.estado == "pide confirmación"
    assert actual.nombres == ("Gastos de venta", "Gastos de administración")
    assert actual.renglones == (7, 8)
    # 5,368,415.92 + 8,052,623.88 = 13,421,039.80 (gastos de Mi Empresa 2025)
    assert actual.suma == Decimal("13421039.80")
    assert sumas[("gastos_operacion", FIN_2024)].suma == Decimal("11791007.37")
    assert "¿" in actual.pregunta and "13,421,039.80" in actual.pregunta


def test_a4_2_mover_una_fila_cambia_la_suma() -> None:
    base = (
        "Resultados al 31/12/2025\nCifras en pesos\n"
        "Gastos de venta  100.00\nGastos de administración  50.00\n"
    )
    lectura = leer_texto(base, hoy=HOY)
    assert lectura.sumas_por_confirmar[0].suma == Decimal("150.00")
    otra = leer_texto(base.replace("50.00", "51.00"), hoy=HOY)
    assert otra.sumas_por_confirmar[0].suma == Decimal("151.00")
    sola = leer_texto("Resultados al 31/12/2025\nGastos de venta  100.00\n", hoy=HOY)
    assert sola.sumas_por_confirmar == ()


# ---------------------------------------------------------------------------
# A4-3 · fechas como vienen
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "esperada"),
    [
        ("2025-12", FIN_2025),
        ("Dic-2025", FIN_2025),
        ("dic 2025", FIN_2025),
        ("Diciembre 2025", FIN_2025),
        ("31/12/2025", FIN_2025),
        ("31/Dic/2025", FIN_2025),
        ("al 31 de diciembre de 2025", FIN_2025),
        ("Estado de Posición Financiera al 31/Dic/2025", FIN_2025),
        ("Del 1/Ene/2025 al 31/Dic/2025", FIN_2025),
        ("Feb-2024", date(2024, 2, 29)),
        ("15/06/2025", date(2025, 6, 15)),
    ],
)
def test_a4_3_fechas_en_las_formas_de_los_contadores(
    texto: str, esperada: date
) -> None:
    assert max(buscar_fechas(texto)) == esperada


@pytest.mark.parametrize("titulo", ["Al 31/12/2025", "31/12/2025"])
def test_a4_3_fecha_sola_en_un_titulo_no_es_columna(titulo: str) -> None:
    lectura = leer_texto(f"Mi Empresa\n{titulo}\nBancos  210.29\n", hoy=HOY)
    assert [(c.nombre, c.monto, c.fecha) for c in lectura.cuentas] == [
        ("Bancos", Decimal("210.29"), FIN_2025)
    ]


def test_a4_3_columnas_dic_2025_y_dic_2024() -> None:
    lectura = leer_estados(ESTADOS / "aspel_balance.csv", hoy=HOY)
    assert {cuenta.fecha for cuenta in lectura.cuentas} == {FIN_2025, FIN_2024}
    assert _montos(lectura, FIN_2024)["Clientes"] == Decimal("3526879.97")
    assert _montos(lectura, FIN_2025)["Clientes"] == Decimal("5639601.55")


def test_a4_3_el_lector_de_e38_entiende_dic_2025(tmp_path: Path) -> None:
    config = _config(tmp_path)
    source = config.exchange_root / "estado.csv"
    source.write_text(
        "Cuenta,Dic-2025,Moneda,Unidad\nVentas netas,120000,MXN,pesos\n",
        encoding="utf-8",
    )
    profile = profile_financial_workbook(config, source)
    statements = reconstruct_statements(profile, as_of=date(2026, 1, 15))
    periods = {figure.period for figure in statements.pnl.figures}
    assert periods == {"2025-12"}


# ---------------------------------------------------------------------------
# A4-4 · sin unidad: pregunta, no bloquea
# ---------------------------------------------------------------------------


def test_a4_4_sin_unidad_pregunta_pesos_o_miles() -> None:
    lectura = leer_estados(ESTADOS / "contpaqi_balance.csv", hoy=HOY)
    assert lectura.unidad is None
    assert any("¿pesos o miles de pesos?" in pregunta for pregunta in lectura.preguntas)
    # No bloquea: las cuentas están completas.
    assert _montos(lectura, FIN_2025)["Bancos"] == Decimal("210291.16")


@pytest.mark.parametrize(
    ("leyenda", "unidad"),
    [
        ("(Cifras en pesos)", "pesos"),
        ("Cifras en miles de pesos", "miles de pesos"),
        ("Cifras en millones de pesos", "millones de pesos"),
    ],
)
def test_a4_4_con_unidad_no_pregunta_y_no_escala_montos(
    leyenda: str, unidad: str
) -> None:
    lectura = leer_texto(f"Balance al 31/12/2025\n{leyenda}\nBancos  210.29\n", hoy=HOY)
    assert lectura.unidad == unidad
    assert not any("pesos o miles" in pregunta for pregunta in lectura.preguntas)
    assert lectura.cuentas[0].monto == Decimal("210.29")


# ---------------------------------------------------------------------------
# A4-5 · más de 90 días: avisa con la fecha, no bloquea
# ---------------------------------------------------------------------------


def test_a4_5_estado_viejo_avisa_con_fecha_y_no_bloquea() -> None:
    lectura = leer_estados(ESTADOS / "contpaqi_resultados.csv", hoy=HOY)
    viejos = [aviso for aviso in lectura.avisos if aviso.codigo == "estado_viejo"]
    assert len(viejos) == 1
    assert "31 de diciembre de 2025" in viejos[0].mensaje
    assert "más reciente" in viejos[0].mensaje
    assert _montos(lectura, FIN_2025)["Ventas netas"] == Decimal("43826513.09")


def test_a4_5_estado_reciente_no_avisa() -> None:
    lectura = leer_estados(ESTADOS / "contpaqi_resultados.csv", hoy=date(2026, 1, 15))
    assert not [aviso for aviso in lectura.avisos if aviso.codigo == "estado_viejo"]


def test_a4_5_sin_fecha_pregunta_la_fecha() -> None:
    lectura = leer_texto("Bancos  210.29\n", hoy=HOY)
    assert lectura.cuentas[0].fecha is None
    assert any("¿De qué fecha" in pregunta for pregunta in lectura.preguntas)


# ---------------------------------------------------------------------------
# A4-6 · negativos entre paréntesis
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "monto"),
    [
        ("(1,234.50)", Decimal("-1234.50")),
        ("(797,135.85)", Decimal("-797135.85")),
        ("$ (1,234.50)", Decimal("-1234.50")),
        ("-1,234.50", Decimal("-1234.50")),
        ("$43,826,513.09", Decimal("43826513.09")),
        ("43826513.09", Decimal("43826513.09")),
        ("13421039.800000001", Decimal("13421039.8")),
        ("1101-000-000", None),
        ("100.00%", None),
        ("Bancos", None),
        ("(1,234.50", None),
    ],
)
def test_a4_6_montos_con_parentesis(texto: str, monto: Decimal | None) -> None:
    assert leer_monto(texto) == monto


def test_a4_6_venta_de_activos_negativa_en_aspel() -> None:
    for archivo in (
        "aspel_resultados.csv",
        "aspel_resultados.xlsx",
        "aspel_resultados.txt",
    ):
        lectura = leer_estados(ESTADOS / archivo, hoy=HOY)
        assert _montos(lectura, FIN_2024)[
            "Otros ingresos (venta de activos)"
        ] == Decimal("-797135.85"), archivo


def test_a4_6_el_lector_de_e38_lee_parentesis(tmp_path: Path) -> None:
    config = _config(tmp_path)
    source = config.exchange_root / "flujo.csv"
    source.write_text(
        "Cuenta,2026-07,Moneda,Unidad\n"
        "Flujo operativo,20000,MXN,pesos\n"
        'Flujo de inversion,"(5,000)",MXN,pesos\n'
        "Flujo de financiamiento,(3000),MXN,pesos\n",
        encoding="utf-8",
    )
    profile = profile_financial_workbook(config, source)
    statements = reconstruct_statements(profile, as_of=date(2026, 8, 1))
    values = {figure.account: figure.value for figure in statements.cash_flow.figures}
    assert values["investing_cash_flow"] == Decimal("-5000")
    assert values["financing_cash_flow"] == Decimal("-3000")
    assert values["net_cash_change"] == Decimal("12000")


# ---------------------------------------------------------------------------
# Dígito invertido: total − suma múltiplo de 9 con los mismos dígitos
# ---------------------------------------------------------------------------


def test_digito_invertido_funcion_pura() -> None:
    # Errata de la lámina 12 del curso: dice 97,492; el valor correcto es 97,942.
    # Diferencia 450 = 9 × 50.
    assert posible_digito_invertido(Decimal("97942"), Decimal("97492"))
    assert posible_digito_invertido(Decimal("97492"), Decimal("97942"))
    assert posible_digito_invertido(Decimal("10148109.59"), Decimal("10148190.59"))
    assert not posible_digito_invertido(Decimal("97942"), Decimal("97942"))
    assert not posible_digito_invertido(Decimal("97942"), Decimal("97500"))
    # 900 sí es múltiplo de 9, pero cambió un dígito: no es una inversión.
    assert not posible_digito_invertido(Decimal("97942"), Decimal("97042"))


def test_digito_invertido_en_un_total_de_seccion() -> None:
    texto = (ESTADOS / "contpaqi_balance.txt").read_text(encoding="utf-8")
    sana = leer_texto(texto, hoy=HOY)
    assert not [a for a in sana.avisos if a.codigo == "posible_digito_invertido"]

    mal = leer_texto(texto.replace("10,148,190.59", "10,148,109.59"), hoy=HOY)
    avisos = [a for a in mal.avisos if a.codigo == "posible_digito_invertido"]
    assert len(avisos) == 1
    assert "Total ACTIVO CIRCULANTE" in avisos[0].mensaje
    assert "10,148,109.59" in avisos[0].mensaje
    assert "10,148,190.59" in avisos[0].mensaje


# ---------------------------------------------------------------------------
# CONTPAQi y Aspel completos; Mi Empresa igual en Excel, CSV y texto
# ---------------------------------------------------------------------------

_BALANCE_2025 = {
    "bancos": Decimal("210291.16"),
    "clientes": Decimal("5639601.55"),
    "inventario": Decimal("1771040.54"),
    "proveedores": Decimal("1232468.24"),
    "acreedores": Decimal("11846834.45"),
    "prestamos_cp": Decimal("148811.41"),
    "documentos_lp": Decimal("9119791.67"),
    "prestamos_lp": Decimal("5818564.98"),
}
_RESULTADOS_2025 = {
    "ventas": Decimal("43826513.09"),
    "costo_ventas": Decimal("22966464.00"),
    "intereses": Decimal("1339211.23"),
    "isr": Decimal("1763114.68"),
    "utilidad_neta": Decimal("5018095.92"),
}


def _por_concepto(lectura: LecturaEstados, fecha: date) -> dict[str, Decimal]:
    resultado: dict[str, Decimal] = {}
    for cuenta in lectura.cuentas:
        if cuenta.fecha == fecha and not cuenta.es_total and cuenta.concepto:
            resultado.setdefault(cuenta.concepto, cuenta.monto)
    return resultado


def test_contpaqi_balance_completo() -> None:
    lectura = leer_estados(ESTADOS / "contpaqi_balance.xlsx", hoy=HOY)
    assert len(lectura.cuentas) == 24
    assert {c.hoja for c in lectura.cuentas} == {"Balance"}
    conceptos = _por_concepto(lectura, FIN_2025)
    for concepto, monto in _BALANCE_2025.items():
        assert conceptos[concepto] == monto, concepto
    totales = {c.nombre: c.monto for c in lectura.cuentas if c.es_total}
    assert totales["Total ACTIVO"] == Decimal("37423394.27")
    assert totales["Total PASIVO"] == Decimal("28166470.75")
    assert totales["Total CAPITAL CONTABLE"] == Decimal("9256923.52")
    bancos = next(c for c in lectura.cuentas if c.nombre == "Bancos")
    assert bancos.renglon == 6  # la fila vacía 3 cuenta en Excel


def test_contpaqi_resultados_completo() -> None:
    lectura = leer_estados(ESTADOS / "contpaqi_resultados.xlsx", hoy=HOY)
    assert len(lectura.cuentas) == 10
    conceptos = _por_concepto(lectura, FIN_2025)
    for concepto, monto in _RESULTADOS_2025.items():
        assert conceptos[concepto] == monto, concepto
    assert conceptos["gastos_operacion"] == Decimal("13421039.80")


def test_aspel_balance_completo() -> None:
    lectura = leer_estados(ESTADOS / "aspel_balance.xlsx", hoy=HOY)
    assert lectura.unidad == "pesos"
    assert len(lectura.cuentas) == 2 * 16
    for concepto, monto in _BALANCE_2025.items():
        assert _por_concepto(lectura, FIN_2025)[concepto] == monto, concepto
    anterior = _por_concepto(lectura, FIN_2024)
    assert anterior["bancos"] == Decimal("120537.91")
    assert anterior["prestamos_lp"] == Decimal("2073621.05")


def test_aspel_resultados_completo() -> None:
    lectura = leer_estados(ESTADOS / "aspel_resultados.xlsx", hoy=HOY)
    assert len(lectura.cuentas) == 2 * 11
    for concepto, monto in _RESULTADOS_2025.items():
        assert _por_concepto(lectura, FIN_2025)[concepto] == monto, concepto
    anterior = _por_concepto(lectura, FIN_2024)
    assert anterior["ventas"] == Decimal("35681743.00")
    assert anterior["utilidad_neta"] == Decimal("3566527.96")


@pytest.mark.parametrize("reporte", REPORTES)
def test_mi_empresa_igual_en_excel_csv_y_texto(reporte: str) -> None:
    def lista(sufijo: str) -> list[tuple[str, Decimal, date | None, int]]:
        lectura = leer_estados(ESTADOS / f"{reporte}{sufijo}", hoy=HOY)
        return [(c.nombre, c.monto, c.fecha, c.renglon) for c in lectura.cuentas]

    excel = lista(".xlsx")
    assert excel
    assert excel == lista(".csv")
    assert excel == lista(".txt")


def test_los_archivos_salen_del_generador(tmp_path: Path) -> None:
    subprocess.run(
        [sys.executable, str(ESTADOS / "generar.py"), str(tmp_path)], check=True
    )
    for reporte in REPORTES:
        for sufijo in (".xlsx", ".csv", ".txt"):
            nombre = f"{reporte}{sufijo}"
            assert filecmp.cmp(tmp_path / nombre, ESTADOS / nombre, shallow=False), (
                nombre
            )


def test_excel_conserva_el_numero_de_renglon_con_filas_vacias() -> None:
    hojas = read_raw_sheets(ESTADOS / "contpaqi_balance.xlsx")
    fila = hojas[0].rows[5]
    assert fila[0].value == "Bancos"
    assert fila[0].address == "A6"


# ---------------------------------------------------------------------------
# «Así leí tus cuentas»
# ---------------------------------------------------------------------------


def test_asi_lei_tus_cuentas_muestra_nombre_monto_fecha_y_renglon() -> None:
    lectura = leer_estados(ESTADOS / "aspel_resultados.csv", hoy=HOY)
    texto = render_asi_lei(lectura)
    assert texto.startswith("Así leí tus cuentas")
    assert (
        "| Otros ingresos (venta de activos) | -797,135.85 | 31-dic-2024 | 12 |"
        in texto
    )
    assert "| Ventas netas | 43,826,513.09 | 31-dic-2025 | 5 |" in texto
    assert "pide confirmación" in texto


def _config(tmp_path: Path) -> WorkspaceConfig:
    exchange = tmp_path / "exchange"
    exchange.mkdir()
    return WorkspaceConfig(
        platform="macos",
        data_root=tmp_path / "data",
        database_path=tmp_path / "data" / "escala.sqlite",
        exchange_root=exchange,
    )
