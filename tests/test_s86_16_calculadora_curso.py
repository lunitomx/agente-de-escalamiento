"""S86.16 — Una sola calculadora del curso de cash.

Según el curso de cash que vimos, cada número sale de los estados revisados
(S86.15) con su fórmula, de dónde sale y su lámina. Los valores de Mi Empresa
salen de ``verifica.py`` del curso. Donde una lámina tiene una errata, la prueba
usa el valor correcto y cita la errata:

- L54 trunca «por cada 100»: 12.86 y 14.09; el valor bien redondeado es 12.87 y 14.10.
- L64 muestra la deuda neta inicial 2,051,377.30 (bancos tecleado 121,000); la
  correcta es 2,051,839.39.
- L37/L40 muestran la utilidad bruta 20,860,019.09; la correcta es 20,860,049.09.
- L38 muestra el flujo del precio 381,689.12; el correcto es 381,869.12.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from escala_server.cash import FinancialInputs, PowerOfOneEngine
from escala_server.cash import curso
from escala_server.cash.curso import (
    Calculado,
    EstadosRevisados,
    NoAplica,
    NoCalculable,
    ResultadoDelCurso,
    calcular_curso,
    main,
)
from escala_server.financial.lector import CuentaLeida, LecturaEstados, leer_estados
from escala_server.financial.revisiones import Respuestas, revisar_estados

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
HOY = date(2026, 1, 31)
INI = date(2024, 12, 31)
FIN = date(2025, 12, 31)
ACUMULADO = Respuestas(periodo="acumulado del año")


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


def _calculado(resultado: ResultadoDelCurso, clave: str, fecha: date = FIN) -> Calculado:
    indicador = resultado.indicador(clave, fecha)
    assert isinstance(indicador, Calculado), (clave, fecha, indicador)
    return indicador


# ---------------------------------------------------------------------------
# Mi Empresa al centavo (verifica.py)
# ---------------------------------------------------------------------------

VALORES_MI_EMPRESA: list[tuple[str, date, str]] = [
    ("capital_de_trabajo", FIN, "6178173.85"),
    ("capital_de_trabajo", INI, "3574370.72"),
    ("dias_clientes", FIN, "46.97"),
    ("dias_inventario", FIN, "28.15"),
    ("dias_proveedores", FIN, "19.59"),
    ("dias_clientes", INI, "36.08"),
    ("dias_inventario", INI, "25.30"),
    ("dias_proveedores", INI, "24.31"),
    ("ciclo", FIN, "55.53"),
    ("ciclo", INI, "37.07"),
    ("flujo_neto", FIN, "-3705245.84"),
    ("flujo_de_operacion", FIN, "4835206.16"),
    ("marginal", FIN, "0.3350"),
    ("margen_bruto", FIN, "0.4760"),
    ("capital_de_trabajo_por_ventas", FIN, "0.1410"),
    ("financiamiento", FIN, "15014008.75"),
    ("financiamiento", INI, "9257195.26"),
    # L54 trunca a 14.09 y 12.86 (errata); bien redondeado es 14.10 y 12.87.
    ("capital_de_trabajo_por_cada_100", FIN, "14.10"),
    ("clientes_por_cada_100", FIN, "12.87"),
    ("inventario_por_cada_100", FIN, "4.04"),
    ("proveedores_por_cada_100", FIN, "2.81"),
    # L37/L40 muestran 20,860,019.09 (errata).
    ("utilidad_bruta", FIN, "20860049.09"),
    ("utilidad_bruta", INI, "18156894.44"),
    ("utilidad_de_operacion", FIN, "7439009.29"),
    # L64 muestra 2,051,377.30 (errata: bancos tecleado 121,000).
    ("deuda_neta", INI, "2051839.39"),
    ("deuda_neta", FIN, "5757085.23"),
    ("otras_cuentas", INI, "5682824.54"),
    ("otras_cuentas", FIN, "8835834.90"),
    ("cambio_capital_de_trabajo", FIN, "2603803.13"),
]


@pytest.mark.parametrize(("clave", "fecha", "esperado"), VALORES_MI_EMPRESA)
def test_mi_empresa_al_centavo(
    mi_empresa: ResultadoDelCurso, clave: str, fecha: date, esperado: str
) -> None:
    assert _calculado(mi_empresa, clave, fecha).valor == Decimal(esperado)


PODER_DEL_UNO: list[tuple[str, str, str]] = [
    # L38 muestra 381,689.12 en el precio (errata).
    ("precio", "381869.12", "438265.13"),
    ("volumen", "146818.75", "208600.49"),
    ("costo", "235050.36", "229664.64"),
    ("gastos", "134210.40", "134210.40"),
    ("proveedores", "62921.82", "0"),
    ("inventario", "62921.82", "0"),
    ("clientes", "120072.64", "0"),
]


@pytest.mark.parametrize(("palanca", "flujo", "utilidad"), PODER_DEL_UNO)
def test_poder_del_uno_mi_empresa(
    mi_empresa: ResultadoDelCurso, palanca: str, flujo: str, utilidad: str
) -> None:
    encontrada = mi_empresa.palanca(palanca)
    assert isinstance(encontrada.flujo, Calculado)
    assert isinstance(encontrada.utilidad, Calculado)
    assert encontrada.flujo.valor == Decimal(flujo)
    assert encontrada.utilidad.valor == Decimal(utilidad)
    assert encontrada.flujo.lamina == "L36, L37 y L70"


def test_poder_del_uno_totales(mi_empresa: ResultadoDelCurso) -> None:
    flujo = mi_empresa.poder_del_uno_flujo
    utilidad = mi_empresa.poder_del_uno_utilidad
    assert isinstance(flujo, Calculado) and isinstance(utilidad, Calculado)
    assert flujo.valor == Decimal("1143864.91")
    assert utilidad.valor == Decimal("1010740.66")


# ---------------------------------------------------------------------------
# Cada número con fórmula, origen y lámina
# ---------------------------------------------------------------------------


def test_origen_de_los_dias_de_clientes(mi_empresa: ResultadoDelCurso) -> None:
    dias = _calculado(mi_empresa, "dias_clientes")
    assert dias.origen == "sale de: clientes 5,639,601.55 ÷ (ventas 43,826,513.09 ÷ 365)"
    assert dias.formula == "clientes ÷ (ventas ÷ días del periodo)"
    assert dias.lamina == "L49"


@pytest.mark.parametrize(
    ("clave", "lamina"),
    [
        ("utilidad_bruta", "L11"),
        ("utilidad_de_operacion", "L11"),
        ("capital_de_trabajo", "L18"),
        ("deuda_neta", "L18"),
        ("otras_cuentas", "L56"),
        ("financiamiento", "L16 y L19"),
        ("dias_clientes", "L49"),
        ("ciclo", "L52"),
        ("clientes_por_cada_100", "L54"),
        ("cambio_capital_de_trabajo", "L46"),
        ("flujo_neto", "L25 y L58"),
        ("flujo_de_operacion", "L61"),
        ("marginal", "L63"),
    ],
)
def test_cada_numero_trae_su_lamina(
    mi_empresa: ResultadoDelCurso, clave: str, lamina: str
) -> None:
    assert _calculado(mi_empresa, clave).lamina == lamina


def test_todo_numero_trae_formula_y_origen(mi_empresa: ResultadoDelCurso) -> None:
    assert len(mi_empresa.indicadores) >= 30
    for indicador in mi_empresa.indicadores:
        assert isinstance(indicador, Calculado), indicador
        assert indicador.formula.strip()
        assert indicador.origen.startswith("sale de: ")
        assert indicador.lamina.startswith("L")
    for palanca in mi_empresa.poder_del_uno:
        for parte in (palanca.flujo, palanca.utilidad):
            assert isinstance(parte, Calculado)
            assert parte.origen.startswith("sale de: ")


def test_el_origen_muestra_las_cuentas_del_balance(mi_empresa: ResultadoDelCurso) -> None:
    ct = _calculado(mi_empresa, "capital_de_trabajo")
    assert "Clientes 5,639,601.55" in ct.origen
    assert "− Proveedores" in ct.origen
    flujo = _calculado(mi_empresa, "flujo_neto")
    assert "5,757,085.23" in flujo.origen and "2,051,839.39" in flujo.origen


def test_poder_del_uno_usa_el_motor_de_s86_13(monkeypatch: pytest.MonkeyPatch) -> None:
    llamadas: list[FinancialInputs] = []

    class Espia(PowerOfOneEngine):
        def calculate(self, inputs: FinancialInputs, adjustments: dict[str, int] | None = None):  # type: ignore[override]
            llamadas.append(inputs)
            return super().calculate(inputs, adjustments)

    monkeypatch.setattr(curso, "PowerOfOneEngine", Espia)
    calcular_curso(_mi_empresa_estados())
    assert len(llamadas) == 1
    assert llamadas[0].net_sales == Decimal("43826513.09")
    assert llamadas[0].total_opex == Decimal("13421039.80")


# ---------------------------------------------------------------------------
# Estados sintéticos: extremos
# ---------------------------------------------------------------------------

Fila = tuple[str, str | None, str | None, str | None]


def _lectura(filas: list[Fila], inicial: date = INI, final: date = FIN) -> LecturaEstados:
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


def test_ventas_cero_no_calculable_nunca_cero() -> None:
    resultado = _sinteticos(
        BALANCE_BASE,
        [
            ("Ventas", "ventas", "0", "0"),
            ("Costo de ventas", "costo_ventas", "0", "0"),
            ("Gastos generales", "gastos_operacion", "0", "0"),
            ("Utilidad neta", "utilidad_neta", "200", "200"),
        ],
    )
    for clave in (
        "dias_clientes",
        "clientes_por_cada_100",
        "capital_de_trabajo_por_cada_100",
        "marginal",
        "margen_bruto",
    ):
        indicador = resultado.indicador(clave, FIN)
        assert isinstance(indicador, NoCalculable), (clave, indicador)
        assert "ventas" in indicador.no_calculable
    assert isinstance(resultado.poder_del_uno_flujo, NoCalculable)
    assert resultado.poder_del_uno == ()
    texto = resultado.model_dump_json()
    assert '"no_calculable"' in texto


def test_utilidad_bruta_negativa_se_calcula_negativa() -> None:
    resultado = _sinteticos(
        BALANCE_BASE,
        [
            ("Ventas", "ventas", "1000", "1000"),
            ("Costo de ventas", "costo_ventas", "1200", "1300"),
            ("Gastos generales", "gastos_operacion", "100", "100"),
            ("Utilidad neta", "utilidad_neta", "200", "200"),
        ],
    )
    assert _calculado(resultado, "utilidad_bruta").valor == Decimal("-300.00")
    marginal = _calculado(resultado, "marginal")
    # UB/V − CT/V = −0.30 − 0.50
    assert marginal.valor == Decimal("-0.8000")


def test_sin_inventario_no_aplica_y_el_ciclo_lo_dice() -> None:
    balance: list[Fila] = [
        ("Bancos", None, "300", "400"),
        ("Clientes", None, "300", "400"),
        ("Proveedores", None, "100", "100"),
        ("Capital social", None, "500", "500"),
        ("Resultado del ejercicio", None, "0", "200"),
    ]
    resultado = _sinteticos(
        balance,
        [
            ("Ventas", "ventas", "1000", "1460"),
            ("Costo de ventas", "costo_ventas", "600", "730"),
            ("Gastos generales", "gastos_operacion", "200", "530"),
            ("Utilidad neta", "utilidad_neta", "200", "200"),
        ],
    )
    inventario = resultado.indicador("dias_inventario", FIN)
    assert isinstance(inventario, NoAplica)
    ciclo = _calculado(resultado, "ciclo")
    # clientes 400 ÷ (1,460 ÷ 365) = 100; proveedores 100 ÷ (730 ÷ 365) = 50
    assert ciclo.valor == Decimal("50.00")
    assert "inventario no aplica" in ciclo.origen
    assert isinstance(resultado.palanca("inventario").flujo, NoAplica)


def test_sin_costo_servicios() -> None:
    balance: list[Fila] = [
        ("Bancos", None, "500", "600"),
        ("Clientes", None, "100", "200"),
        ("Proveedores", None, "100", "100"),
        ("Capital social", None, "500", "500"),
        ("Resultado del ejercicio", None, "0", "200"),
    ]
    resultado = _sinteticos(
        balance,
        [
            ("Ingresos por servicios", "ventas", "1000", "1000"),
            ("Gastos generales", "gastos_operacion", "800", "800"),
            ("Utilidad neta", "utilidad_neta", "200", "200"),
        ],
    )
    assert isinstance(resultado.indicador("dias_inventario", FIN), NoAplica)
    proveedores = resultado.indicador("dias_proveedores", FIN)
    assert isinstance(proveedores, NoCalculable)
    assert "costo de ventas" in proveedores.no_calculable
    assert isinstance(resultado.indicador("ciclo", FIN), NoCalculable)
    assert _calculado(resultado, "utilidad_bruta").valor == Decimal("1000.00")
    assert isinstance(resultado.palanca("costo").flujo, NoAplica)
    assert isinstance(resultado.palanca("precio").flujo, Calculado)


def test_un_mes_usa_los_dias_del_mes_nunca_por_doce() -> None:
    inicial, final = date(2025, 11, 30), date(2025, 12, 31)
    resultado = _sinteticos(
        BALANCE_BASE,
        [
            ("Ventas", "ventas", None, "3100"),
            ("Costo de ventas", "costo_ventas", None, "1550"),
            ("Gastos generales", "gastos_operacion", None, "1350"),
            ("Utilidad neta", "utilidad_neta", None, "200"),
        ],
        respuestas=Respuestas(periodo="mes"),
        inicial=inicial,
        final=final,
    )
    dias = _calculado(resultado, "dias_clientes", final)
    # clientes 400 ÷ (3,100 ÷ 31) = 4
    assert dias.valor == Decimal("4.00")
    assert dias.origen.endswith("÷ 31)")
    clientes = resultado.palanca("clientes").flujo
    assert isinstance(clientes, Calculado)
    assert clientes.valor == Decimal("100.00")  # 3,100 ÷ 31, nunca 3,100 ÷ 365
    sin_anterior = resultado.indicador("dias_clientes", inicial)
    assert isinstance(sin_anterior, NoCalculable)


def test_revision_que_bloquea_no_calcula_nada() -> None:
    balance = [*BALANCE_BASE[:-1], ("Resultado del ejercicio", None, "0", "999")]
    resultado = _sinteticos(
        balance,
        [
            ("Ventas", "ventas", "1000", "1200"),
            ("Costo de ventas", "costo_ventas", "600", "700"),
            ("Gastos generales", "gastos_operacion", "200", "300"),
            ("Utilidad neta", "utilidad_neta", "200", "200"),
        ],
    )
    assert resultado.no_calculable is not None
    assert "no cuadra" in resultado.no_calculable
    assert resultado.indicadores == ()
    assert resultado.poder_del_uno == ()


# ---------------------------------------------------------------------------
# Entrada interna: python -m escala_server.cash.curso <archivo>
# ---------------------------------------------------------------------------


def _archivo(tmp_path: Path) -> Path:
    archivo = tmp_path / "estados-revisados.json"
    archivo.write_text(_mi_empresa_estados().model_dump_json(), encoding="utf-8")
    return archivo


def test_main_imprime_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(_archivo(tmp_path))]) == 0
    datos = json.loads(capsys.readouterr().out)
    dias = next(
        i for i in datos["indicadores"] if i["clave"] == "dias_clientes" and i["fecha"] == "2025-12-31"
    )
    assert Decimal(dias["valor"]) == Decimal("46.97")
    assert dias["origen"].startswith("sale de: clientes")


def test_main_con_archivo_malo_no_calcula(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    malo = tmp_path / "malo.json"
    malo.write_text("{}", encoding="utf-8")
    assert main([str(malo)]) != 0
    assert "no_calculable" in json.loads(capsys.readouterr().out)
    assert main([str(tmp_path / "no-existe.json")]) != 0
    assert "no_calculable" in json.loads(capsys.readouterr().out)


def test_modulo_se_corre_con_python_m(tmp_path: Path) -> None:
    salida = subprocess.run(
        [sys.executable, "-m", "escala_server.cash.curso", str(_archivo(tmp_path))],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    )
    datos = json.loads(salida.stdout)
    assert datos["no_calculable"] is None
    assert any(i["clave"] == "flujo_neto" for i in datos["indicadores"])
