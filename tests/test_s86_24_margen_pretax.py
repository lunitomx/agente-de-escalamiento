"""S86.24 — Margen antes de impuestos, salario de mercado y devoluciones.

Según el curso de cash que vimos (partes V y VI, láminas L75–L79):

- F6.1 margen pre-tax = UAI ÷ ventas; línea de referencia 10%.
- F6.2 si la UB es menor al 40% de ventas, el margen se mide contra la UB.
- F6.3 devoluciones, rebajas y bonificaciones ÷ UAI.
- El salario de mercado lo da el dueño; ESCALA no lo supone.

Caso 2 de L77/L78: el costo de ventas sube 4,000,000; la UB y la UAI bajan esos
mismos 4,000,000. Los valores salen de ``verifica.py`` del curso.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from escala_server.cash.curso import (
    BloqueDelMargen,
    Calculado,
    DatosDelDueno,
    EstadosRevisados,
    NoAplica,
    NoCalculable,
    ResultadoDelCurso,
    calcular_curso,
    devoluciones_sobre_utilidad,
    margen_pretax,
    margen_sobre_utilidad_bruta,
)
from escala_server.financial.lector import CuentaLeida, LecturaEstados, leer_estados, leer_texto
from escala_server.financial.revisiones import Respuestas, revisar_estados

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
HOY = date(2026, 1, 31)
INI = date(2024, 12, 31)
FIN = date(2025, 12, 31)
ACUMULADO = Respuestas(periodo="acumulado del año")
CUATRO_MILLONES = Decimal("4000000")


def _estados(texto_resultados: str | None = None, del_dueno: DatosDelDueno | None = None) -> EstadosRevisados:
    if texto_resultados is None:
        resultados = leer_estados(ESTADOS / "aspel_resultados.txt", hoy=HOY)
    else:
        resultados = leer_texto(texto_resultados, hoy=HOY, hoja="aspel_resultados")
    revision = revisar_estados(
        [leer_estados(ESTADOS / "aspel_balance.txt", hoy=HOY)],
        resultados,
        respuestas=ACUMULADO,
        hoy=HOY,
    )
    return EstadosRevisados(revision=revision, resultados=resultados, del_dueno=del_dueno)


def _caso_2() -> str:
    """Mi Empresa con el costo de ventas 4,000,000 más alto (lámina L77, caso 2)."""

    texto = (ESTADOS / "aspel_resultados.txt").read_text(encoding="utf-8")
    for antes, despues in (
        ("22966464.00", "26966464.00"),
        ("7439009.29", "3439009.29"),
        ("6781210.60", "2781210.60"),
    ):
        assert antes in texto
        texto = texto.replace(antes, despues)
    return texto


def _margen(resultado: ResultadoDelCurso) -> BloqueDelMargen:
    assert resultado.margen is not None, resultado.no_calculable
    return resultado.margen


@pytest.fixture(scope="module")
def mi_empresa() -> BloqueDelMargen:
    return _margen(calcular_curso(_estados()))


@pytest.fixture(scope="module")
def caso_2() -> BloqueDelMargen:
    return _margen(calcular_curso(_estados(_caso_2())))


def _valor(indicador: object) -> Decimal:
    assert isinstance(indicador, Calculado), indicador
    return indicador.valor


# ---------------------------------------------------------------------------
# F6.1 margen pre-tax (L77)
# ---------------------------------------------------------------------------


def test_pretax_mi_empresa(mi_empresa: BloqueDelMargen) -> None:
    pretax = mi_empresa.pretax
    assert _valor(pretax) == Decimal("15.47")
    assert isinstance(pretax, Calculado)
    assert pretax.unidad == "%"
    assert pretax.lamina == "L77"
    assert "6,781,210.60" in pretax.origen and "43,826,513.09" in pretax.origen
    assert mi_empresa.linea_de_referencia == Decimal("10")
    assert mi_empresa.por_encima_de_la_linea is True


def test_pretax_caso_2_costo_mas_4_millones(caso_2: BloqueDelMargen) -> None:
    assert _valor(caso_2.pretax) == Decimal("6.35")
    assert caso_2.por_encima_de_la_linea is False


def test_la_linea_usa_el_valor_sin_redondear() -> None:
    # 9.996% se escribe 10.00 pero está abajo de la línea del 10%.
    calculado = margen_pretax(Decimal("9996"), Decimal("100000"), FIN)
    assert _valor(calculado.indicador) == Decimal("10.00")
    assert calculado.por_encima_de_la_linea is False


def test_pretax_ventas_cero_no_calculable() -> None:
    resultado = margen_pretax(Decimal("100"), Decimal("0"), FIN)
    assert isinstance(resultado.indicador, NoCalculable)
    assert "ventas" in resultado.indicador.no_calculable
    assert resultado.por_encima_de_la_linea is None


def test_pretax_sin_renglon_de_uai_no_calculable() -> None:
    texto = (ESTADOS / "aspel_resultados.txt").read_text(encoding="utf-8")
    sin_uai = "\n".join(l for l in texto.splitlines() if "antes de impuestos" not in l)
    margen = _margen(calcular_curso(_estados(sin_uai)))
    assert isinstance(margen.pretax, NoCalculable)
    assert "utilidad antes de impuestos" in margen.pretax.no_calculable


# ---------------------------------------------------------------------------
# F6.2 margen sobre utilidad bruta (L78)
# ---------------------------------------------------------------------------


def test_sobre_ub_no_aplica_con_ub_de_40_o_mas(mi_empresa: BloqueDelMargen) -> None:
    sobre_ub = mi_empresa.sobre_utilidad_bruta
    assert isinstance(sobre_ub, NoAplica)
    assert "47.60" in sobre_ub.no_aplica


def test_sobre_ub_caso_2(caso_2: BloqueDelMargen) -> None:
    sobre_ub = caso_2.sobre_utilidad_bruta
    assert _valor(sobre_ub) == Decimal("16.50")
    assert isinstance(sobre_ub, Calculado)
    assert "2,781,210.60" in sobre_ub.origen and "16,860,049.09" in sobre_ub.origen
    assert sobre_ub.lamina == "L78"


@pytest.mark.parametrize(
    ("uai", "ub", "ventas", "palabra"),
    [
        ("-100", "-300", "1000", "utilidad bruta"),  # los dos negativos darían +33.33%
        ("100", "-300", "1000", "utilidad bruta"),
        ("-100", "300", "1000", "utilidad antes de impuestos"),
        ("100", "0", "1000", "utilidad bruta"),
        ("100", "300", "0", "ventas"),
    ],
)
def test_sobre_ub_negativas_no_calculable(uai: str, ub: str, ventas: str, palabra: str) -> None:
    indicador = margen_sobre_utilidad_bruta(Decimal(uai), Decimal(ub), Decimal(ventas), FIN)
    assert isinstance(indicador, NoCalculable), indicador
    assert palabra in indicador.no_calculable


def test_sobre_ub_justo_en_40_no_aplica() -> None:
    indicador = margen_sobre_utilidad_bruta(Decimal("100"), Decimal("400"), Decimal("1000"), FIN)
    assert isinstance(indicador, NoAplica)
    indicador = margen_sobre_utilidad_bruta(Decimal("100"), Decimal("399.99"), Decimal("1000"), FIN)
    assert _valor(indicador) == Decimal("25.00")


# ---------------------------------------------------------------------------
# F6.3 devoluciones sobre la utilidad (L79)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("devoluciones", "uai", "esperado"),
    [
        ("1253431", "7181210.60", "17.45"),  # caso 1 de L79
        ("2045326", "6781210.60", "30.16"),  # caso 2 de L79: UAI real de Mi Empresa
    ],
)
def test_devoluciones_casos_de_la_lamina(devoluciones: str, uai: str, esperado: str) -> None:
    indicador = devoluciones_sobre_utilidad(Decimal(devoluciones), Decimal(uai), FIN)
    assert _valor(indicador) == Decimal(esperado)
    assert isinstance(indicador, Calculado) and indicador.lamina == "L79"


def test_devoluciones_mi_empresa_con_dato_del_dueno() -> None:
    dueno = DatosDelDueno(devoluciones=Decimal("2045326"))
    margen = _margen(calcular_curso(_estados(del_dueno=dueno)))
    assert _valor(margen.devoluciones) == Decimal("30.16")


def test_devoluciones_sin_dato_pregunta(mi_empresa: BloqueDelMargen) -> None:
    assert isinstance(mi_empresa.devoluciones, NoCalculable)
    assert "devoluciones" in {p.clave for p in mi_empresa.preguntas}


def test_devoluciones_con_uai_negativa_no_calculable() -> None:
    indicador = devoluciones_sobre_utilidad(Decimal("100"), Decimal("-50"), FIN)
    assert isinstance(indicador, NoCalculable)


# ---------------------------------------------------------------------------
# Salario de mercado (L75) — el monto lo da el dueño
# ---------------------------------------------------------------------------


def test_sin_salario_pregunta_y_no_supone(mi_empresa: BloqueDelMargen) -> None:
    claves = {p.clave for p in mi_empresa.preguntas}
    assert {"salario_de_mercado", "sueldo_actual_del_dueno"} <= claves
    assert isinstance(mi_empresa.pretax_con_salario, NoCalculable)
    assert isinstance(mi_empresa.utilidad_real, NoCalculable)
    assert mi_empresa.salario_de_mercado is None


def test_salario_de_mercado_cambia_el_pretax() -> None:
    dueno = DatosDelDueno(
        salario_de_mercado=Decimal("1200000"), sueldo_actual_del_dueno=Decimal("0")
    )
    margen = _margen(calcular_curso(_estados(del_dueno=dueno)))
    # (6,781,210.60 − 1,200,000) ÷ 43,826,513.09 = 12.73%
    assert _valor(margen.pretax_con_salario) == Decimal("12.73")
    # 7,439,009.29 − (1,200,000 − 0)
    assert _valor(margen.utilidad_real) == Decimal("6239009.29")
    assert margen.salario_de_mercado == Decimal("1200000")
    assert "salario_de_mercado" not in {p.clave for p in margen.preguntas}
    assert _valor(margen.pretax) == Decimal("15.47")  # el pre-tax del estado no cambia


def test_si_ya_se_paga_de_mercado_no_cambia() -> None:
    dueno = DatosDelDueno(
        salario_de_mercado=Decimal("900000"), sueldo_actual_del_dueno=Decimal("900000")
    )
    margen = _margen(calcular_curso(_estados(del_dueno=dueno)))
    assert _valor(margen.pretax_con_salario) == Decimal("15.47")


def test_salario_sin_sueldo_actual_pregunta() -> None:
    dueno = DatosDelDueno(salario_de_mercado=Decimal("900000"))
    margen = _margen(calcular_curso(_estados(del_dueno=dueno)))
    assert isinstance(margen.pretax_con_salario, NoCalculable)
    assert "sueldo_actual_del_dueno" in {p.clave for p in margen.preguntas}


def test_montos_negativos_del_dueno_se_rechazan() -> None:
    with pytest.raises(ValidationError):
        DatosDelDueno(salario_de_mercado=Decimal("-1"))


# ---------------------------------------------------------------------------
# ISR: sólo se muestra
# ---------------------------------------------------------------------------


def test_isr_solo_se_muestra(mi_empresa: BloqueDelMargen) -> None:
    assert _valor(mi_empresa.isr) == Decimal("1763114.68")
    assert "contador" in mi_empresa.nota_fiscal
    texto = mi_empresa.model_dump_json().lower()
    for palabra in ("deduc", "te conviene", "recomiend", "ahorra impuestos"):
        assert palabra not in texto


# ---------------------------------------------------------------------------
# Lo que ya había no cambia; ventas 0 en estados completos
# ---------------------------------------------------------------------------


def test_lo_anterior_de_la_calculadora_sigue_igual() -> None:
    resultado = calcular_curso(_estados())
    utilidad_bruta = resultado.indicador("utilidad_bruta", FIN)
    assert _valor(utilidad_bruta) == Decimal("20860049.09")


def _lectura_sintetica(filas: list[tuple[str, str | None, str]]) -> LecturaEstados:
    cuentas = [
        CuentaLeida(
            nombre=nombre,
            monto=Decimal(monto),
            fecha=fecha,
            renglon=renglon,
            hoja="estado",
            concepto=concepto,
            es_total=False,
        )
        for renglon, (nombre, concepto, monto) in enumerate(filas, start=1)
        for fecha in (INI, FIN)
    ]
    return LecturaEstados(cuentas=tuple(cuentas), fecha=FIN)


def test_ventas_cero_en_estados_completos() -> None:
    balance = _lectura_sintetica(
        [
            ("Bancos", None, "100"),
            ("Clientes", None, "300"),
            ("Capital social", None, "400"),
        ]
    )
    resultados = _lectura_sintetica(
        [
            ("Ventas", "ventas", "0"),
            ("Costo de ventas", "costo_ventas", "0"),
            ("Utilidad antes de impuestos", "utilidad_antes_impuestos", "-50"),
            ("Utilidad neta", "utilidad_neta", "-50"),
        ]
    )
    revision = revisar_estados([balance], resultados, respuestas=ACUMULADO, hoy=HOY)
    margen = _margen(calcular_curso(EstadosRevisados(revision=revision, resultados=resultados)))
    assert isinstance(margen.pretax, NoCalculable)
    assert isinstance(margen.sobre_utilidad_bruta, NoCalculable)


@pytest.mark.parametrize(
    "nombre",
    [
        "Utilidad antes de impuestos",
        "Utilidad antes de ISR",
        "Utilidad antes de impuestos a la utilidad",
    ],
)
def test_el_lector_reconoce_la_uai(nombre: str) -> None:
    from escala_server.financial.formatos import concepto_de

    assert concepto_de(nombre) == "utilidad_antes_impuestos"
    assert concepto_de("ISR") == "isr"
    assert concepto_de("Impuestos a la utilidad") == "isr"
