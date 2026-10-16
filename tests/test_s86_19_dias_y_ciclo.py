"""S86.19 — Días y ciclo del dinero (la calculadora).

Según el curso de cash que vimos (F2.2, L49; F2.3, L52–53):

    días de clientes   = clientes ÷ (ventas ÷ días del periodo)
    días de inventario = inventario ÷ (costo de ventas ÷ días del periodo)
    días de proveedores= proveedores ÷ (costo de ventas ÷ días del periodo)
    ciclo              = clientes + inventario − proveedores
    cronograma: compra día 0 → pago día DPO → venta día DIO → cobro día DIO + DSO

Mi Empresa (``verifica.py``): clientes 36.08 → 46.97, inventario 25.30 → 28.15,
proveedores 24.31 → 19.59, ciclo 37.07 → 55.53. El saldo de clientes trae IVA y
las ventas no (adversarial A3): sin IVA, clientes 46.97 ÷ 1.16 = 40.49.
Días de clientes sobre ventas a crédito: audio A1.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from escala_server.cash.curso import (
    BaseDeDias,
    Calculado,
    DiasDelDinero,
    EstadosRevisados,
    NoAplica,
    NoCalculable,
    calcular_curso,
    dias_del_dinero,
)
from escala_server.financial.lector import CuentaLeida, LecturaEstados, leer_estados
from escala_server.financial.revisiones import Respuestas, revisar_estados
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
HOY = date(2026, 1, 31)
INI = date(2024, 12, 31)
FIN = date(2025, 12, 31)
ACUMULADO = Respuestas(periodo="acumulado del año")


def _mi_empresa(respuestas: Respuestas = ACUMULADO) -> EstadosRevisados:
    resultados = leer_estados(ESTADOS / "aspel_resultados.txt", hoy=HOY)
    revision = revisar_estados(
        [leer_estados(ESTADOS / "aspel_balance.txt", hoy=HOY)],
        resultados,
        respuestas=respuestas,
        hoy=HOY,
    )
    return EstadosRevisados(
        revision=revision, resultados=resultados, respuestas=respuestas
    )


def _valor(dias: DiasDelDinero, clave: str, fecha: date) -> Decimal:
    indicador = getattr(dias.anio(fecha), clave)
    assert isinstance(indicador, Calculado), (clave, fecha, indicador)
    return indicador.valor


@pytest.fixture(scope="module")
def como_vienen() -> DiasDelDinero:
    return dias_del_dinero(_mi_empresa(), BaseDeDias())


@pytest.fixture(scope="module")
def sin_iva() -> DiasDelDinero:
    return dias_del_dinero(
        _mi_empresa(), BaseDeDias(iva_incluido=True, tasa_iva=Decimal("16"))
    )


# ---------------------------------------------------------------------------
# Mi Empresa al centavo
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("clave", "anterior", "actual"),
    [
        ("clientes", "36.08", "46.97"),
        ("inventario", "25.30", "28.15"),
        ("proveedores", "24.31", "19.59"),
        ("ciclo", "37.07", "55.53"),
    ],
)
def test_mi_empresa_dos_anios(
    como_vienen: DiasDelDinero, clave: str, anterior: str, actual: str
) -> None:
    assert _valor(como_vienen, clave, INI) == Decimal(anterior)
    assert _valor(como_vienen, clave, FIN) == Decimal(actual)


def test_mi_empresa_usa_365_en_los_dos_anios(como_vienen: DiasDelDinero) -> None:
    assert como_vienen.dias_del_periodo == 365
    clientes = como_vienen.anio(FIN).clientes
    assert isinstance(clientes, Calculado)
    assert clientes.origen == (
        "sale de: clientes 5,639,601.55 ÷ (ventas 43,826,513.09 ÷ 365)"
    )
    anterior = como_vienen.anio(INI).clientes
    assert isinstance(anterior, Calculado)
    assert anterior.origen.endswith("÷ 365)")


def test_mi_empresa_coincide_con_la_calculadora_del_curso(
    como_vienen: DiasDelDinero,
) -> None:
    """Una sola definición: con los saldos como vienen, los mismos días que S86.16."""
    curso = calcular_curso(_mi_empresa())
    for clave in ("clientes", "inventario", "proveedores", "ciclo"):
        for fecha in (INI, FIN):
            del_curso = curso.indicador(
                "ciclo" if clave == "ciclo" else f"dias_{clave}", fecha
            )
            assert isinstance(del_curso, Calculado)
            assert _valor(como_vienen, clave, fecha) == del_curso.valor


def test_sin_contestar_iva_lo_dice_y_pregunta(como_vienen: DiasDelDinero) -> None:
    assert como_vienen.iva == "como vienen"
    assert "como vienen" in como_vienen.rotulo
    assert any("IVA" in p for p in como_vienen.preguntas)


def test_ciclo_empeoro(como_vienen: DiasDelDinero) -> None:
    ciclo = como_vienen.cambio("ciclo")
    assert ciclo.anterior == Decimal("37.07")
    assert ciclo.actual == Decimal("55.53")
    assert ciclo.diferencia == Decimal("18.46")
    assert ciclo.veredicto == "empeoró"
    assert ciclo.texto.startswith("Tu ciclo pasó de 37.07 a 55.53 días")


@pytest.mark.parametrize(
    ("clave", "veredicto"),
    [
        ("clientes", "empeoró"),  # 36.08 → 46.97: tardan más en pagarte
        ("inventario", "empeoró"),  # 25.30 → 28.15
        ("proveedores", "empeoró"),  # 24.31 → 19.59: pagas antes
    ],
)
def test_veredicto_por_cuenta(
    como_vienen: DiasDelDinero, clave: str, veredicto: str
) -> None:
    assert como_vienen.cambio(clave).veredicto == veredicto


def test_proveedores_mejora_si_sube() -> None:
    """Pagar después es bueno para tu efectivo: el veredicto se invierte."""
    dias = dias_del_dinero(
        _sinteticos(
            [
                ("Bancos", None, "100", "300"),  # para que el balance cuadre
                *BALANCE[1:3],
                ("Proveedores", None, "100", "200"),
                *BALANCE[4:],
            ],
        ),
        BaseDeDias(),
    )
    assert dias.cambio("proveedores").veredicto == "mejoró"
    assert dias.cambio("ciclo").veredicto == "mejoró"


# ---------------------------------------------------------------------------
# IVA (C9)
# ---------------------------------------------------------------------------


def test_sin_iva_16(sin_iva: DiasDelDinero) -> None:
    assert sin_iva.iva == "sin IVA"
    assert sin_iva.rotulo == "días de cobro calculados sin IVA"
    # 46.97 ÷ 1.16 = 40.49; 36.08 ÷ 1.16 = 31.10
    assert _valor(sin_iva, "clientes", FIN) == Decimal("40.49")
    assert _valor(sin_iva, "clientes", INI) == Decimal("31.10")
    # Inventario no lleva IVA; proveedores sí.
    assert _valor(sin_iva, "inventario", FIN) == Decimal("28.15")
    assert _valor(sin_iva, "proveedores", FIN) == Decimal("16.89")
    assert _valor(sin_iva, "ciclo", FIN) == Decimal("51.75")
    clientes = sin_iva.anio(FIN).clientes
    assert isinstance(clientes, Calculado)
    assert "clientes 5,639,601.55 ÷ 1.16 = 4,861,725.47" in clientes.origen
    assert "sin IVA" in clientes.formula


def test_sin_iva_trae_la_cifra_con_iva_del_curso(sin_iva: DiasDelDinero) -> None:
    nota = sin_iva.anio(FIN).nota
    assert nota is not None
    assert "46.97" in nota and "55.53" in nota


def test_la_tasa_de_iva_cambia_el_resultado() -> None:
    """La tasa es dato: con 8% sale otro número."""
    ocho = dias_del_dinero(
        _mi_empresa(), BaseDeDias(iva_incluido=True, tasa_iva=Decimal("8"))
    )
    # 46.9682 ÷ 1.08 = 43.49
    assert _valor(ocho, "clientes", FIN) == Decimal("43.49")


def test_iva_si_sin_tasa_no_supone_16() -> None:
    dias = dias_del_dinero(_mi_empresa(), BaseDeDias(iva_incluido=True))
    assert dias.iva == "con IVA"
    assert dias.rotulo == "días de cobro calculados con IVA"
    assert _valor(dias, "clientes", FIN) == Decimal("46.97")
    nota = dias.anio(FIN).nota
    assert nota is not None and "no calculable" in nota and "tasa de IVA" in nota
    assert any("tasa de IVA" in p for p in dias.preguntas)
    assert dias.tasa_iva is None


def test_iva_no() -> None:
    dias = dias_del_dinero(_mi_empresa(), BaseDeDias(iva_incluido=False))
    assert dias.iva == "sin IVA"
    assert _valor(dias, "clientes", FIN) == Decimal("46.97")
    assert not any("IVA" in p for p in dias.preguntas)


def test_la_base_sale_de_las_respuestas_guardadas() -> None:
    respuestas = Respuestas(
        periodo="acumulado del año", iva_incluido=True, ventas_a_credito=Decimal("100")
    )
    base = BaseDeDias.de(respuestas, tasa_iva=Decimal("16"))
    assert base.iva_incluido is True and base.ventas_a_credito == Decimal("100")
    dias = dias_del_dinero(_mi_empresa(respuestas), base)
    assert _valor(dias, "clientes", FIN) == Decimal("40.49")
    assert BaseDeDias.de(None) == BaseDeDias()


def test_estados_revisados_sin_respuestas_siguen_leyendose() -> None:
    """Los archivos guardados antes de S86.19 no traen respuestas."""
    estados = _mi_empresa()
    viejo = estados.model_dump(mode="json")
    del viejo["respuestas"]
    assert EstadosRevisados.model_validate(viejo).respuestas is None


# ---------------------------------------------------------------------------
# Ventas a crédito (C1)
# ---------------------------------------------------------------------------


def test_sin_ventas_a_credito_usa_totales_con_aviso(como_vienen: DiasDelDinero) -> None:
    assert como_vienen.base_de_ventas == "ventas totales"
    assert any("ventas totales" in a for a in como_vienen.avisos)


def test_cero_por_ciento_a_credito_usa_totales_con_aviso() -> None:
    dias = dias_del_dinero(_mi_empresa(), BaseDeDias(ventas_a_credito=Decimal("0")))
    assert dias.base_de_ventas == "ventas totales"
    assert _valor(dias, "clientes", FIN) == Decimal("46.97")
    assert any("ventas totales" in a for a in dias.avisos)


def test_ventas_a_credito_cambia_los_dias_de_cobro() -> None:
    dias = dias_del_dinero(_mi_empresa(), BaseDeDias(ventas_a_credito=Decimal("60")))
    assert dias.base_de_ventas == "ventas a crédito"
    # 5,639,601.55 ÷ (60% × 43,826,513.09 ÷ 365) = 78.28
    assert _valor(dias, "clientes", FIN) == Decimal("78.28")
    assert _valor(dias, "inventario", FIN) == Decimal("28.15")
    clientes = dias.anio(FIN).clientes
    assert isinstance(clientes, Calculado)
    assert "ventas a crédito" in clientes.origen and "60%" in clientes.origen
    assert not any("ventas totales" in a for a in dias.avisos)


def test_cien_por_ciento_a_credito_no_avisa() -> None:
    dias = dias_del_dinero(_mi_empresa(), BaseDeDias(ventas_a_credito=Decimal("100")))
    assert _valor(dias, "clientes", FIN) == Decimal("46.97")
    assert dias.avisos == ()


# ---------------------------------------------------------------------------
# Cronograma (F2.3)
# ---------------------------------------------------------------------------


def test_cronograma_mi_empresa(como_vienen: DiasDelDinero) -> None:
    actual = como_vienen.anio(FIN).cronograma
    assert actual is not None
    assert actual.pago == Decimal("19.59")
    assert actual.venta == Decimal("28.15")
    assert actual.cobro == Decimal("75.12")
    assert actual.financiados == Decimal("55.53")
    assert actual.origen.startswith("sale de: ")
    anterior = como_vienen.anio(INI).cronograma
    assert anterior is not None
    assert (anterior.pago, anterior.venta, anterior.financiados) == (
        Decimal("24.31"),
        Decimal("25.30"),
        Decimal("37.07"),
    )


# ---------------------------------------------------------------------------
# Extremos sintéticos
# ---------------------------------------------------------------------------

Fila = tuple[str, str | None, str | None, str | None]

BALANCE: list[Fila] = [
    ("Bancos", None, "100", "200"),
    ("Clientes", None, "300", "400"),
    ("Inventarios", None, "200", "200"),
    ("Proveedores", None, "100", "100"),
    ("Capital social", None, "500", "500"),
    ("Resultado del ejercicio", None, "0", "200"),
]
RESULTADOS: list[Fila] = [
    ("Ventas", "ventas", "1460", "1460"),
    ("Costo de ventas", "costo_ventas", "730", "730"),
    ("Gastos generales", "gastos_operacion", "530", "530"),
    ("Utilidad neta", "utilidad_neta", "200", "200"),
]


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
    resultados: list[Fila] = RESULTADOS,
    *,
    inicial: date = INI,
    final: date = FIN,
    hoy: date = HOY,
) -> EstadosRevisados:
    lectura = _lectura(resultados, inicial, final)
    revision = revisar_estados(
        [_lectura(balance, inicial, final)], lectura, respuestas=ACUMULADO, hoy=hoy
    )
    return EstadosRevisados(revision=revision, resultados=lectura)


def test_sin_costo_inventario_y_proveedores_no_aplican() -> None:
    balance: list[Fila] = [
        ("Bancos", None, "500", "600"),
        ("Clientes", None, "100", "200"),
        ("Proveedores", None, "100", "100"),
        ("Capital social", None, "500", "500"),
        ("Resultado del ejercicio", None, "0", "200"),
    ]
    dias = dias_del_dinero(
        _sinteticos(
            balance,
            [
                ("Ingresos por servicios", "ventas", "1460", "1460"),
                ("Gastos generales", "gastos_operacion", "1260", "1260"),
                ("Utilidad neta", "utilidad_neta", "200", "200"),
            ],
        ),
        BaseDeDias(ventas_a_credito=Decimal("100")),
    )
    anio = dias.anio(FIN)
    assert isinstance(anio.inventario, NoAplica)
    assert isinstance(anio.proveedores, NoAplica)
    assert "costo de ventas" in anio.proveedores.no_aplica
    # El ciclo queda en los días de clientes: 200 ÷ (1,460 ÷ 365) = 50
    assert isinstance(anio.ciclo, Calculado)
    assert anio.ciclo.valor == Decimal("50.00")
    assert "no aplica" in anio.ciclo.origen
    assert anio.cronograma is not None and anio.cronograma.cobro == Decimal("50.00")


def test_con_costo_proveedores_si_aplica() -> None:
    """Contra-prueba del anterior: con costo, proveedores sí se calcula."""
    anio = dias_del_dinero(_sinteticos(BALANCE), BaseDeDias()).anio(FIN)
    assert isinstance(anio.proveedores, Calculado)
    # 100 ÷ (730 ÷ 365) = 50
    assert anio.proveedores.valor == Decimal("50.00")


def test_seis_meses_divide_entre_181() -> None:
    inicial, final = date(2025, 12, 31), date(2026, 6, 30)
    dias = dias_del_dinero(
        _sinteticos(
            BALANCE,
            [
                ("Ventas", "ventas", "1460", "724"),
                ("Costo de ventas", "costo_ventas", "730", "362"),
                ("Gastos generales", "gastos_operacion", "530", "162"),
                ("Utilidad neta", "utilidad_neta", "200", "200"),
            ],
            inicial=inicial,
            final=final,
            hoy=date(2026, 7, 15),
        ),
        BaseDeDias(),
    )
    assert dias.dias_del_periodo == 181
    clientes = dias.anio(final).clientes
    assert isinstance(clientes, Calculado)
    # 400 ÷ (724 ÷ 181) = 100, nunca 400 ÷ (724 ÷ 365)
    assert clientes.valor == Decimal("100.00")
    assert clientes.origen.endswith("÷ 181)")


def test_falta_un_dato_dice_no_calculable_nunca_cero() -> None:
    dias = dias_del_dinero(
        _sinteticos(
            BALANCE,
            [
                ("Ventas", "ventas", None, "1460"),
                ("Costo de ventas", "costo_ventas", None, "730"),
                ("Gastos generales", "gastos_operacion", None, "530"),
                ("Utilidad neta", "utilidad_neta", None, "200"),
            ],
        ),
        BaseDeDias(),
    )
    anterior = dias.anio(INI)
    assert isinstance(anterior.clientes, NoCalculable)
    assert isinstance(anterior.ciclo, NoCalculable)
    assert anterior.cronograma is None and anterior.sin_cronograma
    cambio = dias.cambio("ciclo")
    assert cambio.veredicto == "no comparable"
    assert cambio.diferencia is None


def test_revision_que_bloquea_no_calcula() -> None:
    balance = [*BALANCE[:-1], ("Resultado del ejercicio", None, "0", "999")]
    dias = dias_del_dinero(_sinteticos(balance), BaseDeDias())
    assert dias.no_calculable is not None
    assert dias.anios == ()


def test_el_escenario_guarda_las_respuestas_c1_y_c9(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """Las respuestas del dueño viajan con los estados revisados (S86.17 → S86.19)."""
    from escala_server.cash import escenario

    argv = [
        "--empresa",
        "Mi Empresa, S.A. de C.V.",
        "--carpeta",
        str(tmp_path / "work" / "cash"),
        "--conversacion",
        str(tmp_path / "trabajo" / "platica.json"),
        "--hoy",
        "2026-01-31",
        "--archivo",
        str(ESTADOS / "aspel_balance.txt"),
        "--archivo",
        str(ESTADOS / "aspel_resultados.txt"),
        "--guardar",
        "sí",
    ]
    for respuesta in (
        "C10=acumulado del año",
        "suma:gastos_operacion:2025-12-31=sí",
        "suma:gastos_operacion:2024-12-31=sí",
        "C11:Documentos por pagar a largo plazo=no",
        "C9=sí",
        "C1=80",
        "C4=2,966,528.27",
        "C3=no sé",
        "C2=todas",
    ):
        argv += ["--responde", respuesta]
    assert escenario.main(argv) == 0
    capsys.readouterr()
    guardado = (
        tmp_path
        / "work"
        / "cash"
        / "mi-empresa-s-a-de-c-v"
        / "estados-revisados-2026-01-31.json"
    )
    estados = EstadosRevisados.model_validate_json(guardado.read_text(encoding="utf-8"))
    assert estados.respuestas is not None
    assert estados.respuestas.iva_incluido is True
    assert estados.respuestas.ventas_a_credito == Decimal("80")
