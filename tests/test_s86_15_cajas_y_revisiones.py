"""S86.15 — ESCALA pone cada cuenta en su caja y revisa que cuadre.

ESCALA toma la lista del lector (S86.14), acomoda cada cuenta del balance en
una de 4 cajas (capital de trabajo, deuda neta, otras cuentas, capital), corre
las revisiones R1–R11 y arma las preguntas de la primera vuelta. No calcula
indicadores (S86.16) ni conversa (S86.17).

Datos: «Mi Empresa, S.A. de C.V.» (sintéticos, A = 2024 y B = 2025, números
del curso de cash que vimos) en los archivos de ``tests/fixtures/cash/estados``.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from escala_server.financial import (
    profile_financial_workbook,
    reconstruct_statements,
)
from escala_server.financial.cajas import Acomodo, acomodar, regla_de
from escala_server.financial.cash_decision import (
    annualization_factor,
    build_cash_decision,
)
from escala_server.financial.lector import LecturaEstados, leer_estados, leer_texto
from escala_server.financial.revisiones import (
    Respuestas,
    RevisionDeEstados,
    render_asi_acomode,
    revisar_estados,
)
from escala_server.workspace.authority import WorkspaceConfig

ESTADOS = Path(__file__).parent / "fixtures" / "cash" / "estados"
DIC_2024 = date(2024, 12, 31)
DIC_2025 = date(2025, 12, 31)
# Antes de 90 días del cierre: R11 no avisa.
HOY = date(2026, 1, 31)
ACUMULADO = Respuestas(periodo="acumulado del año")
DOCUMENTOS = "Documentos por pagar a largo plazo"


def _texto(nombre: str) -> str:
    return (ESTADOS / nombre).read_text(encoding="utf-8")


def _lee(texto: str, hoja: str = "texto") -> LecturaEstados:
    return leer_texto(texto, hoy=HOY, hoja=hoja)


def _aspel_balance() -> LecturaEstados:
    return leer_estados(ESTADOS / "aspel_balance.txt", hoy=HOY)


def _aspel_resultados() -> LecturaEstados:
    return leer_estados(ESTADOS / "aspel_resultados.txt", hoy=HOY)


def _contpaqi_balance(texto: str | None = None) -> LecturaEstados:
    return _lee(texto or _texto("contpaqi_balance.txt"), "contpaqi_balance")


def _contpaqi_resultados() -> LecturaEstados:
    return _lee(_texto("contpaqi_resultados.txt"), "contpaqi_resultados")


def _mi_empresa(respuestas: Respuestas = ACUMULADO) -> RevisionDeEstados:
    return revisar_estados(
        [_aspel_balance()], _aspel_resultados(), respuestas=respuestas, hoy=HOY
    )


def _codigos(revision: RevisionDeEstados) -> list[str]:
    return [pregunta.codigo for pregunta in revision.preguntas]


def _hallazgos(revision: RevisionDeEstados, codigo: str):
    return [hallazgo for hallazgo in revision.hallazgos if hallazgo.revision == codigo]


# ---------------------------------------------------------------------------
# Las 4 cajas
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nombre", "lado", "caja"),
    [
        ("Bancos", "activo", "deuda neta"),
        ("Caja y bancos", "activo", "deuda neta"),
        ("Clientes", "activo", "capital de trabajo"),
        ("Inventarios", "activo", "capital de trabajo"),
        ("Proveedores", "pasivo", "capital de trabajo"),
        ("Acreedores diversos", "pasivo", "otras cuentas"),
        ("Préstamos bancarios a corto plazo", "pasivo", "deuda neta"),
        ("Préstamos bancarios a largo plazo", "pasivo", "deuda neta"),
        # Regla: un sobregiro es un préstamo del banco.
        ("Sobregiro bancario", "pasivo", "deuda neta"),
        # Regla: el anticipo de clientes es dinero que ya te pagaron; no es deuda.
        ("Anticipo de clientes", "pasivo", "otras cuentas"),
        ("Anticipo a proveedores", "activo", "otras cuentas"),
        ("Otras cuentas por pagar", "pasivo", "otras cuentas"),
        ("Impuestos por pagar", "pasivo", "otras cuentas"),
        ("Deudores diversos", "activo", "otras cuentas"),
        ("Otros activos circulantes", "activo", "otras cuentas"),
        ("Activo fijo neto", "activo", "otras cuentas"),
        ("Activo diferido", "activo", "otras cuentas"),
        # Como el curso: documentos por pagar LP en otras cuentas (y se pregunta C11).
        (DOCUMENTOS, "pasivo", "otras cuentas"),
        ("Capital social", "capital", "capital"),
        ("Reserva legal", "capital", "capital"),
        ("Resultados de ejercicios anteriores", "capital", "capital"),
        ("Utilidad del ejercicio", "capital", "capital"),
        ("Capital contable", "capital", "capital"),
    ],
)
def test_cada_cuenta_tiene_su_caja_por_regla_escrita(nombre: str, lado: str, caja: str) -> None:
    regla = regla_de(nombre)

    assert regla is not None
    assert regla.lado == lado
    assert regla.caja == caja
    assert regla.porque  # cada regla dice por qué


def test_una_cuenta_que_ninguna_regla_conoce_no_tiene_caja() -> None:
    assert regla_de("Inversión en criptomonedas") is None
    assert regla_de("Costo de ventas") is None  # no es cuenta del balance


def test_los_documentos_por_pagar_piden_saber_si_pagan_interes() -> None:
    regla = regla_de(DOCUMENTOS)
    assert regla is not None and regla.pregunta_interes
    bancaria = regla_de("Préstamos bancarios a largo plazo")
    assert bancaria is not None and not bancaria.pregunta_interes


def _acomodo_aspel() -> Acomodo:
    return acomodar(_aspel_balance().cuentas)


def test_mi_empresa_deuda_neta_inicial_y_final_al_centavo() -> None:
    acomodo = _acomodo_aspel()
    inicial = acomodo.en(DIC_2024)
    final = acomodo.en(DIC_2025)
    assert inicial is not None and final is not None

    # 98,756.25 + 2,073,621.05 − 120,537.91. La lámina 64 dice 2,051,377.30
    # porque bancos se tecleó 121,000 (errata L64); la prueba usa el valor correcto.
    assert inicial.deuda_neta == Decimal("2051839.39")
    # 148,811.41 + 5,818,564.98 − 210,291.16
    assert final.deuda_neta == Decimal("5757085.23")


def test_mi_empresa_las_otras_cajas_como_el_curso() -> None:
    acomodo = _acomodo_aspel()
    inicial = acomodo.en(DIC_2024)
    final = acomodo.en(DIC_2025)
    assert inicial is not None and final is not None

    assert inicial.capital_de_trabajo == Decimal("3574370.72")
    assert final.capital_de_trabajo == Decimal("6178173.85")
    assert inicial.otras_cuentas == Decimal("5682824.54")
    assert final.otras_cuentas == Decimal("8835834.90")  # L19, L56
    assert inicial.capital == Decimal("7205355.87")
    assert final.capital == Decimal("9256923.52")
    assert final.activo == Decimal("37423394.27")
    assert final.pasivo + final.capital_contable == Decimal("37423394.27")


def test_cada_cuenta_del_balance_dice_su_caja_y_por_que() -> None:
    acomodo = acomodar(_contpaqi_balance().cuentas)

    assert acomodo.cuentas
    assert all(cuenta.caja is not None and cuenta.porque for cuenta in acomodo.cuentas)
    # Los totales del documento no se acomodan: se usan para revisar (R3).
    assert all(not cuenta.nombre.lower().startswith("total") for cuenta in acomodo.cuentas)
    assert {total.nombre for total in acomodo.totales_del_documento} >= {
        "Total ACTIVO",
        "Total PASIVO",
        "Total CAPITAL CONTABLE",
        "Total PASIVO Y CAPITAL",
    }


# ---------------------------------------------------------------------------
# Criterio: mover una cuenta de caja cambia el resultado y dispara una pregunta
# ---------------------------------------------------------------------------


def test_mover_una_cuenta_de_caja_cambia_el_resultado_y_dispara_una_pregunta() -> None:
    quieta = _mi_empresa()
    movida = _mi_empresa(
        Respuestas(periodo="acumulado del año", movimientos={DOCUMENTOS: "deuda neta"})
    )

    antes = quieta.acomodo.en(DIC_2025)
    despues = movida.acomodo.en(DIC_2025)
    assert antes is not None and despues is not None
    assert antes.deuda_neta == Decimal("5757085.23")
    # 5,757,085.23 + 9,119,791.67
    assert despues.deuda_neta == Decimal("14876876.90")
    assert despues.otras_cuentas == antes.otras_cuentas + Decimal("9119791.67")

    assert "movida" not in _codigos(quieta)
    pregunta = next(p for p in movida.preguntas if p.codigo == "movida")
    assert pregunta.cuenta == DOCUMENTOS
    assert "5,757,085.23" in pregunta.pregunta
    assert "14,876,876.90" in pregunta.pregunta
    # El balance sigue cuadrando: sólo cambió de caja.
    assert all(h.resultado == "cuadra" for h in _hallazgos(movida, "R1"))


def test_si_el_dueno_dice_que_paga_interes_la_cuenta_pasa_a_deuda_neta() -> None:
    revision = _mi_empresa(
        Respuestas(periodo="acumulado del año", pagan_interes={DOCUMENTOS: True})
    )

    final = revision.acomodo.en(DIC_2025)
    assert final is not None
    assert final.deuda_neta == Decimal("14876876.90")
    cuenta = next(c for c in revision.acomodo.cuentas if c.nombre == DOCUMENTOS)
    assert cuenta.caja == "deuda neta"
    assert "interés" in cuenta.porque
    # Ya contestó: ni pregunta C11 por esa cuenta ni pide confirmar el movimiento.
    assert not [p for p in revision.preguntas if p.codigo in {"C11", "movida"}]


def test_si_el_dueno_dice_que_no_paga_interes_se_queda_en_otras_cuentas() -> None:
    revision = _mi_empresa(
        Respuestas(periodo="acumulado del año", pagan_interes={DOCUMENTOS: False})
    )

    final = revision.acomodo.en(DIC_2025)
    assert final is not None and final.deuda_neta == Decimal("5757085.23")
    assert not [p for p in revision.preguntas if p.cuenta == DOCUMENTOS]


# ---------------------------------------------------------------------------
# R1 — el balance cuadra; la errata de 0.31; el que no cuadra no calcula
# ---------------------------------------------------------------------------


def test_mi_empresa_cuadra_en_las_dos_fechas() -> None:
    revision = _mi_empresa()

    r1 = _hallazgos(revision, "R1")
    assert {h.fecha for h in r1} == {DIC_2024, DIC_2025}
    assert all(h.resultado == "cuadra" and not h.bloquea for h in r1)
    assert all(h.resultado == "cuadra" for h in _hallazgos(revision, "R10"))
    assert all(h.resultado == "cuadra" for h in _hallazgos(revision, "R3"))
    assert revision.puede_calcular
    assert "Tu balance cuadra" in render_asi_acomode(revision)


def _con_errata_l70() -> LecturaEstados:
    # Errata L13/L70: otras cuentas de capital 1,838,827.91 en vez de 1,838,827.60 (L11).
    texto = _texto("contpaqi_balance.txt").replace("1,838,827.60", "1,838,827.91")
    return _contpaqi_balance(texto)


def test_la_errata_de_031_de_la_lamina_70_produce_el_aviso() -> None:
    revision = revisar_estados(
        [_con_errata_l70()], _contpaqi_resultados(), respuestas=ACUMULADO, hoy=HOY
    )

    r1 = _hallazgos(revision, "R1")
    assert len(r1) == 1
    aviso = r1[0]
    assert aviso.resultado == "aviso"
    assert aviso.diferencia == Decimal("0.31")
    assert "37,423,394.27" in aviso.mensaje  # activo
    assert "37,423,394.58" in aviso.mensaje  # pasivo más capital
    assert "no cuadra por 0.31: ¿redondeo o falta una cuenta?" in aviso.mensaje
    # Dentro de la tolerancia de 1 peso: avisa y pregunta, no bloquea.
    assert not aviso.bloquea
    assert "no cuadra por 0.31: ¿redondeo o falta una cuenta?" in render_asi_acomode(revision)
    # El documento dice capital 9,256,923.52 y sus cuentas suman 9,256,923.83 (R3).
    r3 = [h for h in _hallazgos(revision, "R3") if h.resultado != "cuadra"]
    assert any("9,256,923.83" in h.mensaje for h in r3)
    assert [h.resultado for h in _hallazgos(revision, "R10")] == ["aviso"]


def test_un_balance_que_no_cuadra_no_calcula_y_dice_la_diferencia() -> None:
    texto = _texto("contpaqi_balance.txt").replace("5,639,601.55", "5,640,601.55")
    revision = revisar_estados(
        [_contpaqi_balance(texto)], _contpaqi_resultados(), respuestas=ACUMULADO, hoy=HOY
    )

    r1 = _hallazgos(revision, "R1")[0]
    assert r1.resultado == "no cuadra"
    assert r1.bloquea
    assert r1.diferencia == Decimal("1000.00")
    assert "1,000.00" in r1.mensaje
    assert not revision.puede_calcular
    assert "no cuadra por 1,000.00" in render_asi_acomode(revision)


# ---------------------------------------------------------------------------
# R2 — utilidad del estado contra resultado del ejercicio del balance
# ---------------------------------------------------------------------------


def test_r2_mi_empresa_utilidad_igual_al_resultado_del_ejercicio() -> None:
    revision = revisar_estados(
        [_contpaqi_balance()], _contpaqi_resultados(), respuestas=ACUMULADO, hoy=HOY
    )

    [r2] = _hallazgos(revision, "R2")
    assert r2.resultado == "cuadra"


def test_r2_avisa_si_la_utilidad_no_es_el_resultado_del_ejercicio() -> None:
    texto = _texto("contpaqi_balance.txt").replace("5,018,095.92", "5,018,095.61")
    revision = revisar_estados(
        [_contpaqi_balance(texto)], _contpaqi_resultados(), respuestas=ACUMULADO, hoy=HOY
    )

    [r2] = _hallazgos(revision, "R2")
    assert r2.resultado == "aviso"
    assert r2.diferencia == Decimal("0.31")
    assert "5,018,095.92" in r2.mensaje and "5,018,095.61" in r2.mensaje


def test_r2_sin_resultado_del_ejercicio_en_el_balance_no_es_revisable() -> None:
    # El balance de Aspel trae «Capital contable» en un solo renglón.
    [r2] = _hallazgos(_mi_empresa(), "R2")
    assert r2.resultado == "no revisable"
    assert not r2.bloquea


# ---------------------------------------------------------------------------
# Periodo: emparejar balances; un acumulado nunca se multiplica
# ---------------------------------------------------------------------------


def test_mi_empresa_empareja_el_balance_inicial_y_el_final_con_el_estado() -> None:
    revision = _mi_empresa()

    assert revision.periodo is not None
    assert revision.periodo.desde == DIC_2024
    assert revision.periodo.hasta == DIC_2025
    assert revision.periodo.dias == 365
    assert revision.balance_inicial == DIC_2024
    assert revision.balance_final == DIC_2025
    assert [h.resultado for h in _hallazgos(revision, "R4")] == ["cuadra"]


_BALANCE_JUNIO = """Mi Empresa, S.A. de C.V.
Balance General comparativo
(Cifras en pesos)
Cuenta | 30/Jun/2026 | 31/Dic/2025
Bancos | 300,000.00 | 210,291.16
Clientes | 1,000,000.00 | 5,639,601.55
Proveedores | 400,000.00 | 1,232,468.24
Capital social | 900,000.00 | 4,617,424.47
"""

_RESULTADOS_JUNIO = """Mi Empresa, S.A. de C.V.
Estado de resultados al 30/Jun/2026
(Cifras en pesos)
Ventas netas | 21,000,000.00
Costo de ventas | 11,000,000.00
Utilidad neta | 2,400,000.00
"""


def test_un_acumulado_de_6_meses_cubre_181_dias_y_no_se_anualiza() -> None:
    revision = revisar_estados(
        [_lee(_BALANCE_JUNIO)],
        _lee(_RESULTADOS_JUNIO),
        respuestas=ACUMULADO,
        hoy=date(2026, 7, 15),
    )

    assert revision.periodo is not None
    assert revision.periodo.tipo == "acumulado del año"
    assert revision.periodo.desde == DIC_2025
    assert revision.periodo.hasta == date(2026, 6, 30)
    assert revision.periodo.dias == 181
    assert revision.balance_inicial == DIC_2025


def test_un_estado_del_mes_empieza_al_cierre_del_mes_anterior() -> None:
    revision = revisar_estados(
        [_lee(_BALANCE_JUNIO)],
        _lee(_RESULTADOS_JUNIO),
        respuestas=Respuestas(periodo="mes"),
        hoy=date(2026, 7, 15),
    )

    assert revision.periodo is not None
    assert revision.periodo.desde == date(2026, 5, 31)
    assert revision.periodo.dias == 30
    # No hay balance al 31 de mayo: sólo se calcula lo que no mide cambio.
    assert revision.balance_inicial is None
    [r4] = _hallazgos(revision, "R4")
    assert r4.resultado == "aviso" and not r4.bloquea
    assert "31-may-2026" in r4.mensaje


def test_sin_saber_si_es_del_mes_o_acumulado_no_calcula_y_pregunta() -> None:
    revision = _mi_empresa(Respuestas())

    assert revision.periodo is None
    c10 = next(p for p in revision.preguntas if p.codigo == "C10")
    assert c10.bloquea
    assert "mes" in c10.pregunta and "acumulado" in c10.pregunta
    assert not revision.puede_calcular


def test_r4_el_estado_no_coincide_con_los_balances() -> None:
    balance = _lee(_texto("contpaqi_balance.txt").replace("31/Dic/2025", "30/Jun/2025"))
    revision = revisar_estados(
        [balance], _contpaqi_resultados(), respuestas=ACUMULADO, hoy=HOY
    )

    [r4] = _hallazgos(revision, "R4")
    assert r4.resultado == "no cuadra" and r4.bloquea
    assert "31-dic-2025" in r4.mensaje and "30-jun-2025" in r4.mensaje
    assert not revision.puede_calcular


@pytest.mark.parametrize(
    ("period", "months", "factor"),
    [
        ("2026-07", 1, 12),  # el dueño dijo que es del mes
        ("2025-12", 12, 1),  # comparativo anual de Aspel («Dic-2025»)
        ("2026-06", 6, None),  # acumulado de 6 meses: nunca ×12
        ("2026-06", None, None),  # sin saber: no supone
        ("2025", None, 1),  # periodo de un año, sin mes
    ],
)
def test_el_factor_anual_solo_multiplica_un_mes_confirmado(
    period: str, months: int | None, factor: int | None
) -> None:
    assert annualization_factor(period, months) == factor


def _config(tmp_path: Path) -> WorkspaceConfig:
    exchange = tmp_path / "exchange"
    exchange.mkdir()
    return WorkspaceConfig(
        platform="macos",
        data_root=tmp_path / "data",
        database_path=tmp_path / "data" / "escala.sqlite",
        exchange_root=exchange,
    )


def _decision(tmp_path: Path, months: int | None):
    config = _config(tmp_path)
    workbook = config.exchange_root / "junio.csv"
    workbook.write_text(
        "Cuenta,2026-06,Moneda,Unidad\n"
        "Ventas netas,600000,MXN,pesos\n"
        "Costo de ventas,350000,MXN,pesos\n"
        "Gastos operativos,150000,MXN,pesos\n"
        "Utilidad neta,75000,MXN,pesos\n"
        "Caja,22000,MXN,pesos\n"
        "Cuentas por cobrar,18000,MXN,pesos\n"
        "Inventario,12000,MXN,pesos\n"
        "Cuentas por pagar,9000,MXN,pesos\n"
        "Flujo operativo,20000,MXN,pesos\n"
        "Flujo de inversion,-5000,MXN,pesos\n"
        "Flujo de financiamiento,-3000,MXN,pesos\n",
        encoding="utf-8",
    )
    statements = reconstruct_statements(
        profile_financial_workbook(config, workbook), as_of=date(2026, 7, 10)
    )
    return build_cash_decision(statements, as_of=date(2026, 7, 10), statement_months=months)


def test_la_decision_de_cash_nunca_multiplica_un_acumulado_de_6_meses(tmp_path: Path) -> None:
    decision = _decision(tmp_path, 6)

    assert decision.status == "blocked"
    assert "accumulated_statement_not_annualized" in decision.findings
    assert decision.validated_inputs is None  # 600,000 nunca se vuelve 7,200,000


def test_la_decision_de_cash_no_supone_que_el_estado_es_del_mes(tmp_path: Path) -> None:
    decision = _decision(tmp_path, None)

    assert decision.status == "blocked"
    assert "statement_months_unknown" in decision.findings


def test_la_decision_de_cash_anualiza_solo_un_mes_confirmado(tmp_path: Path) -> None:
    decision = _decision(tmp_path, 1)

    assert decision.status == "ready"
    assert decision.validated_inputs is not None
    assert decision.validated_inputs.net_sales == Decimal("7200000")


# ---------------------------------------------------------------------------
# Preguntas de la primera vuelta y C11 con la tasa
# ---------------------------------------------------------------------------


def test_la_primera_vuelta_pregunta_c1_c2_c3_c4_c9_c11() -> None:
    codigos = _codigos(_mi_empresa())

    for codigo in ("C1", "C2", "C3", "C4", "C9", "C11"):
        assert codigo in codigos
    assert "C10" not in codigos  # ya contestó


def test_lo_que_el_dueno_ya_contesto_no_se_vuelve_a_preguntar() -> None:
    revision = _mi_empresa(
        Respuestas(
            periodo="acumulado del año",
            ventas_a_credito=Decimal("80"),
            ventas_completas="todas",
            retiros_del_dueno=Decimal("0"),
            retiros_de_capital=Decimal("2966528.27"),
            iva_incluido=True,
            pagan_interes={DOCUMENTOS: False},
        )
    )

    assert not [c for c in _codigos(revision) if c.startswith("C")]


def test_cada_pregunta_dice_para_que_sirve_y_las_que_bloquean_van_primero() -> None:
    revision = _mi_empresa(Respuestas())

    assert all(p.pregunta and p.para_que for p in revision.preguntas)
    bloquean = [p.bloquea for p in revision.preguntas]
    assert bloquean == sorted(bloquean, reverse=True)


def test_c11_avisa_la_tasa_anormal_como_pregunta() -> None:
    revision = _mi_empresa()

    # 1,339,211.23 ÷ ((98,756.25 + 2,073,621.05 + 148,811.41 + 5,818,564.98) ÷ 2)
    assert revision.tasa_deuda_bancaria is not None
    assert round(revision.tasa_deuda_bancaria, 2) == Decimal("32.91")
    # Sumando documentos por pagar LP (9,582,174.13 y 9,119,791.67)
    assert revision.tasa_con_documentos is not None
    assert round(revision.tasa_con_documentos, 2) == Decimal("9.98")
    c11 = next(p for p in revision.preguntas if p.codigo == "C11")
    assert c11.cuenta == DOCUMENTOS
    assert "32.91%" in c11.pregunta and "9.98%" in c11.pregunta
    assert c11.pregunta.rstrip().endswith("?")


def test_con_un_umbral_mas_alto_la_tasa_no_se_menciona() -> None:
    revision = revisar_estados(
        [_aspel_balance()],
        _aspel_resultados(),
        respuestas=ACUMULADO,
        hoy=HOY,
        umbral_tasa=Decimal("0.40"),
    )

    c11 = next(p for p in revision.preguntas if p.codigo == "C11")
    assert "32.91%" not in c11.pregunta


# ---------------------------------------------------------------------------
# R5–R11
# ---------------------------------------------------------------------------


def test_r5_balance_en_pesos_y_estado_en_miles_no_calcula() -> None:
    resultados = _lee(
        _texto("aspel_resultados.txt").replace("(Cifras en pesos)", "(Cifras en miles de pesos)")
    )
    revision = revisar_estados(
        [_aspel_balance()], resultados, respuestas=ACUMULADO, hoy=HOY
    )

    [r5] = _hallazgos(revision, "R5")
    assert r5.resultado == "no cuadra" and r5.bloquea
    assert not revision.puede_calcular


def test_r6_proveedores_negativos_no_calcula_y_pregunta() -> None:
    texto = _texto("contpaqi_balance.txt").replace(
        "Proveedores | 1,232,468.24", "Proveedores | (1,232,468.24)"
    )
    revision = revisar_estados(
        [_contpaqi_balance(texto)], _contpaqi_resultados(), respuestas=ACUMULADO, hoy=HOY
    )

    r6 = [h for h in _hallazgos(revision, "R6") if h.resultado == "no cuadra"]
    assert r6 and r6[0].bloquea
    assert "Proveedores" in r6[0].mensaje and "-1,232,468.24" in r6[0].mensaje
    assert not revision.puede_calcular


def test_r7_una_cuenta_sin_caja_no_calcula_y_pregunta() -> None:
    texto = _texto("contpaqi_balance.txt").replace(
        "Activo diferido | 1,956,618.46 |", "Inversión en criptomonedas | 1,956,618.46 |"
    )
    revision = revisar_estados(
        [_contpaqi_balance(texto)], _contpaqi_resultados(), respuestas=ACUMULADO, hoy=HOY
    )

    r7 = next(p for p in revision.preguntas if p.codigo == "R7")
    assert r7.cuenta == "Inversión en criptomonedas" and r7.bloquea
    assert not revision.puede_calcular
    # R1 no cuadra por 1,956,618.46 y dice por qué: esa cuenta no entra en ninguna caja.
    [r1] = _hallazgos(revision, "R1")
    assert r1.diferencia == Decimal("1956618.46")
    assert "1 cuenta(s) sin caja" in r1.mensaje


def test_r7_el_anticipo_de_clientes_va_a_otras_cuentas_sin_preguntar() -> None:
    texto = _texto("contpaqi_balance.txt").replace(
        "Acreedores diversos | 11,846,834.45", "Anticipo de clientes | 11,846,834.45"
    )
    revision = revisar_estados(
        [_contpaqi_balance(texto)], _contpaqi_resultados(), respuestas=ACUMULADO, hoy=HOY
    )

    cuenta = next(c for c in revision.acomodo.cuentas if c.nombre == "Anticipo de clientes")
    assert cuenta.caja == "otras cuentas"
    assert "R7" not in _codigos(revision)


def test_r8_pasa_el_aviso_de_digito_invertido_del_lector() -> None:
    texto = _texto("contpaqi_balance.txt").replace("1,956,618.46 | ", "1,965,618.46 | ", 1)
    revision = revisar_estados(
        [_contpaqi_balance(texto)], _contpaqi_resultados(), respuestas=ACUMULADO, hoy=HOY
    )

    assert [h.resultado for h in _hallazgos(revision, "R8")] == ["aviso"]


def test_r9_el_capital_bajo_mas_de_lo_que_explica_la_utilidad() -> None:
    sin_respuesta = _mi_empresa()
    c4 = next(p for p in sin_respuesta.preguntas if p.codigo == "C4")
    # Δ capital − utilidad = 2,051,567.65 − 5,018,095.92
    assert "2,966,528.27" in c4.pregunta

    dijo_cero = _mi_empresa(
        Respuestas(periodo="acumulado del año", retiros_de_capital=Decimal("0"))
    )
    [r9] = _hallazgos(dijo_cero, "R9")
    assert r9.resultado == "aviso" and not r9.bloquea
    assert "2,966,528.27" in r9.mensaje and "0.00" in r9.mensaje

    dijo_bien = _mi_empresa(
        Respuestas(periodo="acumulado del año", retiros_de_capital=Decimal("2966528.27"))
    )
    assert [h.resultado for h in _hallazgos(dijo_bien, "R9")] == ["cuadra"]


def test_r11_un_balance_viejo_avisa_pero_no_bloquea() -> None:
    revision = revisar_estados(
        [_aspel_balance()], _aspel_resultados(), respuestas=ACUMULADO, hoy=date(2026, 10, 16)
    )

    [r11] = _hallazgos(revision, "R11")
    assert r11.resultado == "aviso" and not r11.bloquea
    assert "289 días" in r11.mensaje
    assert revision.puede_calcular


def test_asi_acomode_tus_cuentas_muestra_caja_y_por_que() -> None:
    texto = render_asi_acomode(_mi_empresa())

    assert texto.startswith("Así acomodé tus cuentas")
    assert "| Cuenta | Monto | Fecha | Caja | Por qué |" in texto
    assert "| Préstamos bancarios a largo plazo | 5,818,564.98 | 31-dic-2025 | deuda neta |" in texto
    assert "Deuda neta" in texto and "5,757,085.23" in texto
