"""S86.22 — Simulador de las 7 palancas.

Según el curso de cash que vimos (F4.1, L70), mover una palanca tiene dos lados:

- **por periodo**: más venta, menos costo o gasto. Es utilidad y se repite cada periodo.
- **de una vez**: lo que se queda (o se libera) en clientes, inventario o
  proveedores. Es balance y pasa una sola vez.

El flujo del año es la suma de los dos. En vista mensual, sólo el lado por
periodo se reparte entre los meses; el de una vez va aparte (adversarial A6).

Valores de Mi Empresa (``verifica.py``). L38 muestra el flujo del precio
381,689.12 (errata); el correcto es 381,869.12. L54 trunca el capital de trabajo
por cada 100 a 14.09 (errata); bien redondeado es 14.10.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

import pytest

from escala_server.cash import LEVER_META, FinancialInputs, PowerOfOneEngine, lever_parts
from escala_server.cash import _lever_effect  # pyright: ignore[reportPrivateUsage]
from escala_server.cash.curso import (
    Coeficiente,
    EstadosRevisados,
    NoAplica,
    NoCalculable,
    ResultadoDelCurso,
    calcular_curso,
)
from escala_server.cash.simulador import (
    JS,
    Simulador,
    main,
    pagina,
    simulador_de,
)
from escala_server.financial.lector import CuentaLeida, LecturaEstados, leer_estados
from escala_server.financial.revisiones import Respuestas, revisar_estados

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
HOY = date(2026, 1, 31)
INI = date(2024, 12, 31)
FIN = date(2025, 12, 31)
ACUMULADO = Respuestas(periodo="acumulado del año")
CENTAVO = Decimal("0.01")
NODE = shutil.which("node")


def _cents(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def _mi_empresa_estados() -> EstadosRevisados:
    resultados = leer_estados(ESTADOS / "aspel_resultados.txt", hoy=HOY)
    revision = revisar_estados(
        [leer_estados(ESTADOS / "aspel_balance.txt", hoy=HOY)],
        resultados,
        respuestas=ACUMULADO,
        hoy=HOY,
    )
    return EstadosRevisados(revision=revision, resultados=resultados)


@pytest.fixture(scope="module")
def mi_empresa() -> ResultadoDelCurso:
    return calcular_curso(_mi_empresa_estados())


@pytest.fixture(scope="module")
def simulador(mi_empresa: ResultadoDelCurso) -> Simulador:
    return simulador_de(mi_empresa)


def _coeficiente(resultado: ResultadoDelCurso, palanca: str, lado: str) -> Coeficiente:
    parte = getattr(resultado.del_simulador(palanca), lado)
    assert isinstance(parte, Coeficiente), (palanca, lado, parte)
    return parte


# ---------------------------------------------------------------------------
# Motor: una sola definición, dos lados
# ---------------------------------------------------------------------------

# Mi Empresa al 31-dic-2025 (los mismos que lee la calculadora de los estados).
INPUTS = FinancialInputs(
    net_sales=Decimal("43826513.09"),
    cost_of_goods_sold=Decimal("22966464.00"),
    total_opex=Decimal("13421039.80"),
    accounts_receivable=Decimal("5639601.55"),
    inventory=Decimal("1771040.54"),
    accounts_payable=Decimal("1232468.24"),
    net_profit=Decimal("0"),
)


@pytest.mark.parametrize("lever", list(LEVER_META))
@pytest.mark.parametrize("units", [1, 5])
def test_el_flujo_del_motor_es_la_suma_de_sus_dos_lados(lever: str, units: int) -> None:
    partes = lever_parts(lever, INPUTS, units)
    flujo, utilidad, formula_flujo, formula_utilidad = _lever_effect(lever, INPUTS, units)
    assert partes.per_period + partes.one_time == flujo
    assert partes.per_period == utilidad
    assert partes.cash_formula == formula_flujo
    assert partes.per_period_formula == formula_utilidad


def test_lado_de_una_vez_del_precio_es_lo_que_se_queda_en_clientes() -> None:
    partes = lever_parts("price", INPUTS, 1)
    assert partes.one_time == -Decimal("0.01") * INPUTS.accounts_receivable
    assert "clientes 5,639,601.55" in partes.one_time_formula
    otro = FinancialInputs(**{**INPUTS.__dict__, "accounts_receivable": Decimal("1000000")})
    assert lever_parts("price", otro, 1).one_time == Decimal("-10000.00")


def test_lado_de_una_vez_de_los_dias_y_por_periodo_cero() -> None:
    partes = lever_parts("ar_days", INPUTS, 1)
    assert partes.per_period == 0
    assert _cents(partes.one_time) == Decimal("120072.64")
    gastos = lever_parts("opex", INPUTS, 1)
    assert gastos.one_time == 0
    assert _cents(gastos.per_period) == Decimal("134210.40")


# ---------------------------------------------------------------------------
# Calculadora: dos coeficientes por palanca, Mi Empresa
# ---------------------------------------------------------------------------

# (palanca, utilidad = por periodo, flujo = por periodo + una vez) — L70.
POR_PALANCA: list[tuple[str, str, str]] = [
    ("precio", "438265.13", "381869.12"),  # L38 dice 381,689.12 (errata)
    ("volumen", "208600.49", "146818.75"),
    ("costo", "229664.64", "235050.36"),
    ("gastos", "134210.40", "134210.40"),
    ("clientes", "0", "120072.64"),
    ("inventario", "0", "62921.82"),
    ("proveedores", "0", "62921.82"),
]


@pytest.mark.parametrize(("palanca", "utilidad", "flujo"), POR_PALANCA)
def test_coeficientes_de_mi_empresa(
    mi_empresa: ResultadoDelCurso, palanca: str, utilidad: str, flujo: str
) -> None:
    por_periodo = _coeficiente(mi_empresa, palanca, "por_periodo")
    una_vez = _coeficiente(mi_empresa, palanca, "una_vez")
    assert _cents(por_periodo.valor) == Decimal(utilidad)
    assert _cents(por_periodo.valor + una_vez.valor) == Decimal(flujo)
    for parte in (por_periodo, una_vez):
        assert parte.formula.strip()
        assert parte.origen.startswith("sale de: ")
        assert parte.lamina == "L36, L37 y L70"


def test_coeficientes_sin_redondear_a_centavos(mi_empresa: ResultadoDelCurso) -> None:
    # 1 día de clientes = 43,826,513.09 ÷ 365 = 120,072.638602…
    clientes = _coeficiente(mi_empresa, "clientes", "una_vez")
    assert clientes.valor == Decimal("120072.638603")


def test_los_coeficientes_salen_del_balance(mi_empresa: ResultadoDelCurso) -> None:
    una_vez = _coeficiente(mi_empresa, "precio", "una_vez")
    assert una_vez.valor < 0
    assert "clientes 5,639,601.55" in una_vez.origen
    assert _coeficiente(mi_empresa, "precio", "por_periodo").valor > 0


def test_la_calculadora_sigue_dando_flujo_y_utilidad(mi_empresa: ResultadoDelCurso) -> None:
    assert len(mi_empresa.poder_del_uno) == 7
    assert len(mi_empresa.simulador) == 7
    assert [p.unidad for p in mi_empresa.simulador] == ["%"] * 4 + ["días"] * 3


# ---------------------------------------------------------------------------
# Vistas y advertencias
# ---------------------------------------------------------------------------


def test_vistas_de_un_ano(simulador: Simulador) -> None:
    vistas = {v.clave: v.meses for v in simulador.vistas}
    assert vistas == {"anual": 1, "mensual": 12}
    assert simulador.rotulo == "antes de ISR"


def test_advertencias_del_curso(simulador: Simulador) -> None:
    textos = {a.palanca: a for a in simulador.advertencias}
    assert "fuera del mercado" in textos["precio"].texto
    volumen = textos["volumen"]
    assert "14.10 por cada 100" in volumen.texto
    assert volumen.origen.startswith("sale de: 100 × capital de trabajo")


def test_la_advertencia_de_volumen_se_calcula() -> None:
    # CT = clientes 400 + inventario 200 − proveedores 100 = 500 sobre ventas 1,000.
    resultado = _sinteticos(
        BALANCE_BASE,
        [
            ("Ventas", "ventas", "1000", "1000"),
            ("Costo de ventas", "costo_ventas", "600", "600"),
            ("Gastos generales", "gastos_operacion", "200", "200"),
            ("Utilidad neta", "utilidad_neta", "200", "200"),
        ],
    )
    texto = next(a.texto for a in simulador_de(resultado).advertencias if a.palanca == "volumen")
    assert "50.00 por cada 100" in texto
    assert "14.10" not in texto


# ---------------------------------------------------------------------------
# Estados sintéticos: un mes y empresa de servicios
# ---------------------------------------------------------------------------

Fila = tuple[str, str | None, str | None, str | None]


def _lectura(filas: list[Fila], inicial: date, final: date) -> LecturaEstados:
    cuentas: list[CuentaLeida] = []
    for renglon, (nombre, concepto, al_inicio, al_final) in enumerate(filas, start=1):
        for fecha, monto in ((inicial, al_inicio), (final, al_final)):
            if monto is not None:
                cuentas.append(
                    CuentaLeida(
                        nombre=nombre,
                        monto=Decimal(monto),
                        fecha=fecha,
                        renglon=renglon,
                        hoja="estado",
                        concepto=concepto,
                        es_total=False,
                    )
                )
    return LecturaEstados(cuentas=tuple(cuentas), fecha=final)


def _sinteticos(
    balance: list[Fila],
    resultados: list[Fila],
    *,
    respuestas: Respuestas = ACUMULADO,
    inicial: date = INI,
    final: date = FIN,
) -> ResultadoDelCurso:
    lectura = _lectura(resultados, inicial, final)
    revision = revisar_estados(
        [_lectura(balance, inicial, final)], lectura, respuestas=respuestas, hoy=HOY
    )
    return calcular_curso(EstadosRevisados(revision=revision, resultados=lectura))


BALANCE_BASE: list[Fila] = [
    ("Bancos", None, "100", "200"),
    ("Clientes", None, "300", "400"),
    ("Inventarios", None, "200", "200"),
    ("Proveedores", None, "100", "100"),
    ("Capital social", None, "500", "500"),
    ("Resultado del ejercicio", None, "0", "200"),
]


def _un_mes() -> ResultadoDelCurso:
    return _sinteticos(
        BALANCE_BASE,
        [
            ("Ventas", "ventas", None, "3100"),
            ("Costo de ventas", "costo_ventas", None, "1550"),
            ("Gastos generales", "gastos_operacion", None, "1350"),
            ("Utilidad neta", "utilidad_neta", None, "200"),
        ],
        respuestas=Respuestas(periodo="mes"),
        inicial=date(2025, 11, 30),
        final=FIN,
    )


def test_estados_de_un_mes_no_tienen_vista_anual() -> None:
    sim = simulador_de(_un_mes())
    assert [(v.clave, v.meses) for v in sim.vistas] == [("mensual", 1)]
    assert any("12" in razon for razon in sim.sin_vista)


def _servicios() -> ResultadoDelCurso:
    balance: list[Fila] = [
        ("Bancos", None, "500", "600"),
        ("Clientes", None, "100", "200"),
        ("Proveedores", None, "100", "100"),
        ("Capital social", None, "500", "500"),
        ("Resultado del ejercicio", None, "0", "200"),
    ]
    return _sinteticos(
        balance,
        [
            ("Ingresos por servicios", "ventas", "1000", "1000"),
            ("Gastos generales", "gastos_operacion", "800", "800"),
            ("Utilidad neta", "utilidad_neta", "200", "200"),
        ],
    )


def test_servicios_palancas_en_gris_con_razon() -> None:
    resultado = _servicios()
    for palanca in ("costo", "inventario", "proveedores"):
        encontrada = resultado.del_simulador(palanca)
        for parte in (encontrada.por_periodo, encontrada.una_vez):
            assert isinstance(parte, NoAplica | NoCalculable), (palanca, parte)
    assert isinstance(resultado.del_simulador("precio").por_periodo, Coeficiente)
    html = pagina(simulador_de(resultado))
    assert "costo de ventas" in html  # la razón viaja en los datos de la página


def test_sin_ventas_no_hay_simulador() -> None:
    resultado = _sinteticos(
        BALANCE_BASE,
        [
            ("Ventas", "ventas", "0", "0"),
            ("Costo de ventas", "costo_ventas", "0", "0"),
            ("Gastos generales", "gastos_operacion", "0", "0"),
            ("Utilidad neta", "utilidad_neta", "200", "200"),
        ],
    )
    sim = simulador_de(resultado)
    assert sim.palancas == ()
    assert sim.no_calculable is not None and "ventas" in sim.no_calculable


# ---------------------------------------------------------------------------
# La página: sólo multiplica (se prueba el JS con node)
# ---------------------------------------------------------------------------

_CORRE = """
const s = require(process.argv[1]);
let entrada = '';
process.stdin.on('data', (d) => { entrada += d; });
process.stdin.on('end', () => {
  const { datos, casos } = JSON.parse(entrada);
  console.log(JSON.stringify(casos.map((c) => s.simular(datos, c.movimientos, c.vista))));
});
"""


def _datos_de_la_pagina(html: str) -> dict[str, Any]:
    encontrado = re.search(
        r'<script id="datos-simulador" type="application/json">(.*?)</script>', html, re.S
    )
    assert encontrado, "la página no trae los coeficientes embebidos"
    datos: dict[str, Any] = json.loads(encontrado.group(1))
    return datos


def _simula(datos: dict[str, Any], casos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if NODE is None:
        pytest.skip("node no está instalado")
    salida = subprocess.run(
        [NODE, "-e", _CORRE, str(JS)],
        input=json.dumps({"datos": datos, "casos": casos}),
        capture_output=True,
        text=True,
        check=True,
    )
    resultado: list[dict[str, Any]] = json.loads(salida.stdout)
    return resultado


def _d(valor: float) -> Decimal:
    return _cents(Decimal(str(valor)))


TODAS_EN_1 = {p: 1 for p in ("precio", "volumen", "costo", "gastos", "clientes", "inventario", "proveedores")}


def test_las_7_en_1_anual(simulador: Simulador) -> None:
    datos = _datos_de_la_pagina(pagina(simulador))
    [anual] = _simula(datos, [{"movimientos": TODAS_EN_1, "vista": "anual"}])
    assert _d(anual["efectivo_total"]) == Decimal("1143864.91")
    assert _d(anual["utilidad"]) == Decimal("1010740.66")
    assert _d(anual["efectivo_cada_periodo"]) == Decimal("1010740.66")


def test_vista_mensual_subir_el_precio_nunca_resta_efectivo(simulador: Simulador) -> None:
    datos = _datos_de_la_pagina(pagina(simulador))
    casos = [{"movimientos": {"precio": n}, "vista": v} for n in range(1, 11) for v in ("mensual", "anual")]
    resultados = _simula(datos, casos)
    for caso, r in zip(casos, resultados):
        n = caso["movimientos"]["precio"]
        assert r["efectivo_cada_periodo"] > 0, caso
        # El efecto de una vez es el mismo en las dos vistas: no se reparte ni se repite.
        assert _d(r["una_vez"]) == _cents(Decimal(n) * Decimal("-56396.015500")), caso
        if caso["vista"] == "mensual":
            assert r["efectivo_total"] is None
            # Mezclarlos daría negativo: así se ve la trampa que la prueba evita.
            assert r["efectivo_cada_periodo"] + r["una_vez"] < 0
            assert _d(r["efectivo_cada_periodo"]) == _cents(Decimal(n) * Decimal("438265.1309") / 12)


def test_cobro_5_dias_antes_y_subo_2_por_ciento_igual_que_el_motor(
    simulador: Simulador,
) -> None:
    datos = _datos_de_la_pagina(pagina(simulador))
    [r] = _simula(datos, [{"movimientos": {"clientes": 5, "precio": 2}, "vista": "anual"}])
    motor = PowerOfOneEngine().calculate(INPUTS, {"ar_days": 5, "price": 2})
    assert _d(r["efectivo_total"]) == Decimal(str(motor.combined_cash_impact))
    assert _d(r["utilidad"]) == Decimal(str(motor.combined_ebit_impact))
    assert set(r["advertencias"]) == {"precio"}


def test_la_pagina_usa_los_coeficientes_embebidos(simulador: Simulador) -> None:
    datos = _datos_de_la_pagina(pagina(simulador))
    for palanca in datos["palancas"]:
        if palanca["palanca"] == "precio":
            palanca["por_periodo"]["valor"] = "1000"
            palanca["una_vez"]["valor"] = "0"
    [r] = _simula(datos, [{"movimientos": {"precio": 3}, "vista": "anual"}])
    assert r["efectivo_total"] == 3000


def test_palanca_que_no_aplica_no_se_mueve() -> None:
    datos = _datos_de_la_pagina(pagina(simulador_de(_servicios())))
    [r] = _simula(datos, [{"movimientos": {"costo": 5, "inventario": 3}, "vista": "anual"}])
    assert r["efectivo_total"] == 0 and r["utilidad"] == 0
    costo = next(p for p in r["palancas"] if p["palanca"] == "costo")
    assert costo["aplica"] is False and "costo de ventas" in costo["razon"]


def test_la_pagina_rotula_antes_de_isr_y_no_trae_formulas(simulador: Simulador) -> None:
    html = pagina(simulador)
    assert html.count("antes de ISR") >= 2
    assert JS.read_text(encoding="utf-8") in html
    js = JS.read_text(encoding="utf-8")
    # La página no conoce cuentas: sólo coeficientes × movimiento.
    for cuenta in ("ventas", "clientes", "inventario", "proveedores", "365"):
        assert cuenta not in js, cuenta


# ---------------------------------------------------------------------------
# Entrada: python -m escala_server.cash.simulador <estados> <salida.html>
# ---------------------------------------------------------------------------


def test_main_escribe_la_pagina(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    estados = tmp_path / "estados-revisados.json"
    estados.write_text(_mi_empresa_estados().model_dump_json(), encoding="utf-8")
    salida = tmp_path / "simulador.html"
    assert main([str(estados), str(salida)]) == 0
    assert "antes de ISR" in salida.read_text(encoding="utf-8")
    assert json.loads(capsys.readouterr().out)["pagina"] == str(salida)


def test_main_con_archivo_malo_no_calcula(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    malo = tmp_path / "malo.json"
    malo.write_text("{}", encoding="utf-8")
    salida = tmp_path / "simulador.html"
    assert main([str(malo), str(salida)]) != 0
    assert "no_calculable" in json.loads(capsys.readouterr().out)
    assert not salida.exists()


def test_modulo_se_corre_con_python_m(tmp_path: Path) -> None:
    estados = tmp_path / "estados-revisados.json"
    estados.write_text(_mi_empresa_estados().model_dump_json(), encoding="utf-8")
    salida = tmp_path / "simulador.html"
    corrida = subprocess.run(
        [sys.executable, "-m", "escala_server.cash.simulador", str(estados), str(salida)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert corrida.returncode == 0, corrida.stderr
    assert salida.exists()
