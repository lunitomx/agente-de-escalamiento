"""S86.18 — Panel «Tu contabilidad real».

Según el curso de cash que vimos (F2.1, L16 y L18–L20), el balance se lee en dos
columnas que siempre igualan:

- financiamiento = deuda neta + capital;
- operación = capital de trabajo + otras cuentas (activo fijo incluido, L56).

«Otras cuentas» se suma por renglones y se compara contra el residuo
(financiamiento − capital de trabajo). Si un renglón quedó en otra caja sin que
cambien los totales, no igualan: el panel no sale y ESCALA pregunta
(adversarial A1).

F2.4 (L54): por cada 100 de ventas. L54 trunca a 12.86 y 14.09 (errata); bien
redondeado es 12.87 y 14.10.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from escala_server.cash.contabilidad import (
    BalanceSimplificado,
    PanelContabilidad,
    main,
    pagina,
    panel_de,
)
from escala_server.cash.curso import (
    Calculado,
    EstadosRevisados,
    NoCalculable,
    calcular_curso,
)
from escala_server.financial.cajas import Caja, CuentaEnCaja
from escala_server.financial.lector import leer_estados
from escala_server.financial.revisiones import Respuestas, revisar_estados

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
HOY = date(2026, 1, 31)
INI = date(2024, 12, 31)
FIN = date(2025, 12, 31)


def _estados(respuestas: Respuestas | None = None) -> EstadosRevisados:
    resultados = leer_estados(ESTADOS / "aspel_resultados.txt", hoy=HOY)
    revision = revisar_estados(
        [leer_estados(ESTADOS / "aspel_balance.txt", hoy=HOY)],
        resultados,
        respuestas=respuestas or Respuestas(periodo="acumulado del año"),
        hoy=HOY,
    )
    return EstadosRevisados(revision=revision, resultados=resultados)


def _cambia_renglon(
    estados: EstadosRevisados,
    nombre: str,
    fecha: date,
    *,
    caja: Caja | None = None,
    mas: Decimal = Decimal("0"),
) -> EstadosRevisados:
    """Cambia un renglón en el archivo sin recalcular los totales (archivo editado a mano)."""

    def cambia(cuenta: CuentaEnCaja) -> CuentaEnCaja:
        if cuenta.nombre != nombre or cuenta.fecha != fecha:
            return cuenta
        return cuenta.model_copy(
            update={"caja": caja or cuenta.caja, "monto": cuenta.monto + mas}
        )

    revision = estados.revision
    acomodo = revision.acomodo.model_copy(
        update={"cuentas": tuple(cambia(c) for c in revision.acomodo.cuentas)}
    )
    return estados.model_copy(
        update={"revision": revision.model_copy(update={"acomodo": acomodo})}
    )


@pytest.fixture(scope="module")
def mi_empresa() -> EstadosRevisados:
    return _estados()


@pytest.fixture(scope="module")
def panel(mi_empresa: EstadosRevisados) -> PanelContabilidad:
    return panel_de(mi_empresa)


def _balance(panel: PanelContabilidad, fecha: date) -> BalanceSimplificado:
    for balance in panel.balances:
        if balance.fecha == fecha:
            return balance
    raise KeyError(fecha)


def _valor(indicador: object) -> Decimal:
    assert isinstance(indicador, Calculado), indicador
    return indicador.valor


# ---------------------------------------------------------------------------
# La calculadora entrega el capital (cambio aditivo)
# ---------------------------------------------------------------------------


def test_la_calculadora_entrega_el_capital(mi_empresa: EstadosRevisados) -> None:
    resultado = calcular_curso(mi_empresa)
    capital = resultado.indicador("capital", FIN)
    assert _valor(capital) == Decimal("9256923.52")
    assert isinstance(capital, Calculado)
    assert capital.origen == "sale de: Capital contable 9,256,923.52"
    assert capital.lamina == "L18"
    assert _valor(resultado.indicador("capital", INI)) == Decimal("7205355.87")


# ---------------------------------------------------------------------------
# Mi Empresa: financiamiento = operación
# ---------------------------------------------------------------------------


def test_mi_empresa_financiamiento_igual_a_operacion(panel: PanelContabilidad) -> None:
    assert panel.no_calculable is None
    assert panel.preguntas == ()
    final = _balance(panel, FIN)
    assert final.financiamiento.valor == Decimal("15014008.75")
    assert final.operacion.valor == Decimal("15014008.75")
    assert final.deuda_neta.total.valor == Decimal("5757085.23")
    assert final.capital.total.valor == Decimal("9256923.52")
    assert final.capital_de_trabajo.total.valor == Decimal("6178173.85")
    assert final.activo_fijo.total.valor == Decimal("25318585.22")
    assert final.resto_de_otras.total.valor == Decimal("-16482750.32")
    assert final.otras_cuentas.total.valor == Decimal("8835834.90")
    assert final.residuo.valor == Decimal("8835834.90")
    assert final.cuadre == "cuadra"
    assert final.aviso is None


def test_mi_empresa_anio_anterior(panel: PanelContabilidad) -> None:
    inicial = _balance(panel, INI)
    assert inicial.financiamiento.valor == Decimal("9257195.26")
    assert inicial.operacion.valor == Decimal("9257195.26")
    assert inicial.otras_cuentas.total.valor == Decimal("5682824.54")
    # El final va primero: es el que el dueño quiere ver.
    assert [b.fecha for b in panel.balances] == [FIN, INI]


def test_otras_cuentas_se_suma_por_renglones(panel: PanelContabilidad) -> None:
    otras = _balance(panel, FIN).otras_cuentas
    montos = {r.nombre: r.monto for r in otras.renglones}
    # L56: 2,527,257.34 + 25,318,585.22 + 1,956,618.46 − 11,846,834.45 − 9,119,791.67
    assert montos == {
        "Otros activos circulantes": Decimal("2527257.34"),
        "Activo fijo neto": Decimal("25318585.22"),
        "Activo diferido": Decimal("1956618.46"),
        "Acreedores diversos": Decimal("-11846834.45"),
        "Documentos por pagar a largo plazo": Decimal("-9119791.67"),
    }
    assert sum(montos.values(), Decimal("0")) == otras.total.valor
    assert "Activo fijo neto 25,318,585.22" in otras.total.origen
    assert "− Acreedores diversos 11,846,834.45" in otras.total.origen


def test_por_cada_100_de_ventas(panel: PanelContabilidad) -> None:
    final = _balance(panel, FIN)
    por_cada_100 = {i.clave: _valor(i) for i in final.por_cada_100}
    # L54 trunca a 12.86 y 14.09 (errata); bien redondeado: 12.87 y 14.10.
    assert por_cada_100 == {
        "clientes_por_cada_100": Decimal("12.87"),
        "inventario_por_cada_100": Decimal("4.04"),
        "proveedores_por_cada_100": Decimal("2.81"),
        "capital_de_trabajo_por_cada_100": Decimal("14.10"),
    }
    assert final.frase == (
        "Por cada 100 pesos que vendes, 14.10 se quedan atrapados en capital de trabajo."
    )


def test_cada_numero_dice_de_donde_sale(panel: PanelContabilidad) -> None:
    for balance in panel.balances:
        totales = [balance.financiamiento, balance.operacion, balance.residuo]
        for grupo in balance.grupos:
            totales.append(grupo.total)
            for renglon in grupo.renglones:
                assert renglon.origen.startswith("sale de: tu balance al "), renglon
        for numero in totales:
            assert numero.origen.startswith("sale de: "), numero
            assert numero.formula.strip()
            assert numero.lamina.startswith("L")
        for indicador in balance.por_cada_100:
            assert isinstance(indicador, Calculado)
            assert indicador.origen.startswith("sale de: ")


# ---------------------------------------------------------------------------
# Otras cuentas por renglones contra el residuo: pruebas que pueden fallar
# ---------------------------------------------------------------------------


def test_renglon_de_otras_en_otra_caja_el_panel_no_sale(
    mi_empresa: EstadosRevisados,
) -> None:
    movido = _cambia_renglon(
        mi_empresa, "Activo fijo neto", FIN, caja="capital de trabajo"
    )
    panel = panel_de(movido)
    assert panel.balances == ()
    assert len(panel.preguntas) == 1
    pregunta = panel.preguntas[0]
    assert pregunta.bloquea
    assert pregunta.fecha == FIN
    assert pregunta.por_renglones == Decimal("-16482750.32")
    assert pregunta.contra == Decimal("8835834.90")
    assert pregunta.caja == "otras cuentas"
    assert pregunta.diferencia == Decimal("25318585.22")
    assert "25,318,585.22" in pregunta.pregunta
    assert pregunta.pregunta.endswith("?")


def test_pasivo_de_otras_a_deuda_neta_tambien_se_ve(
    mi_empresa: EstadosRevisados,
) -> None:
    movido = _cambia_renglon(mi_empresa, "Acreedores diversos", INI, caja="deuda neta")
    panel = panel_de(movido)
    assert panel.balances == ()
    assert [p.fecha for p in panel.preguntas] == [INI]
    assert panel.preguntas[0].diferencia == Decimal("13885547.68")


def test_clientes_a_deuda_neta_sin_recalcular_tampoco_sale(
    mi_empresa: EstadosRevisados,
) -> None:
    # Otras cuentas sí iguala (no se tocó), pero capital de trabajo por renglones no.
    movido = _cambia_renglon(mi_empresa, "Clientes", FIN, caja="deuda neta")
    panel = panel_de(movido)
    assert panel.balances == ()
    pregunta = panel.preguntas[0]
    assert pregunta.caja == "capital de trabajo"
    assert pregunta.por_renglones == Decimal("538572.30")
    assert pregunta.contra == Decimal("6178173.85")
    assert pregunta.diferencia == Decimal("5639601.55")


def test_centavos_sale_con_aviso(mi_empresa: EstadosRevisados) -> None:
    # Como la errata de L70 (0.31): ¿redondeo o falta una cuenta?
    casi = _cambia_renglon(mi_empresa, "Activo diferido", FIN, mas=Decimal("0.31"))
    panel = panel_de(casi)
    final = _balance(panel, FIN)
    assert final.cuadre == "aviso"
    assert final.aviso is not None
    assert "0.31" in final.aviso and "¿redondeo o falta una cuenta?" in final.aviso


def test_mas_de_un_peso_no_sale(mi_empresa: EstadosRevisados) -> None:
    lejos = _cambia_renglon(mi_empresa, "Activo diferido", FIN, mas=Decimal("1.01"))
    panel = panel_de(lejos)
    assert panel.balances == ()
    assert panel.preguntas[0].diferencia == Decimal("1.01")


def test_mover_con_escala_recalcula_y_el_panel_sale() -> None:
    # El dueño movió la cuenta con ESCALA: los totales se recalculan y cuadran.
    movido = _estados(
        Respuestas(
            periodo="acumulado del año",
            movimientos={"Documentos por pagar a largo plazo": "deuda neta"},
        )
    )
    panel = panel_de(movido)
    final = _balance(panel, FIN)
    assert final.deuda_neta.total.valor == Decimal("14876876.90")
    assert final.financiamiento.valor == final.operacion.valor == Decimal("24133800.42")
    assert final.cuadre == "cuadra"


# ---------------------------------------------------------------------------
# Lo que no se puede calcular
# ---------------------------------------------------------------------------


def test_sin_ventas_el_balance_sale_y_por_cada_100_no_calculable(
    mi_empresa: EstadosRevisados,
) -> None:
    resultados = mi_empresa.resultados
    sin_ventas = mi_empresa.model_copy(
        update={
            "resultados": resultados.model_copy(
                update={
                    "cuentas": tuple(
                        c for c in resultados.cuentas if c.concepto != "ventas"
                    )
                }
            )
        }
    )
    final = _balance(panel_de(sin_ventas), FIN)
    assert final.financiamiento.valor == Decimal("15014008.75")
    assert all(isinstance(i, NoCalculable) for i in final.por_cada_100)
    assert final.frase.startswith("Por cada 100 de ventas: no calculable: ")


def test_revision_que_bloquea_no_da_panel(mi_empresa: EstadosRevisados) -> None:
    sin_periodo = _estados(Respuestas())
    panel = panel_de(sin_periodo)
    assert panel.balances == ()
    assert panel.no_calculable is not None


# ---------------------------------------------------------------------------
# La página y la entrada
# ---------------------------------------------------------------------------


def test_la_pagina_tiene_dos_columnas_y_el_origen(panel: PanelContabilidad) -> None:
    texto = pagina(panel)
    assert "<title>Tu contabilidad real</title>" in texto
    assert "Financiamiento" in texto and "Operación" in texto
    assert texto.count("15,014,008.75") >= 2
    assert (
        "Por cada 100 pesos que vendes, 14.10 se quedan atrapados en capital de trabajo."
        in texto
    )
    assert "sale de:" in texto
    assert "Activo fijo neto" in texto
    assert "<script src" not in texto
    assert "Según el curso de cash que vimos" in texto


def test_la_pagina_de_un_panel_que_no_sale_trae_la_pregunta(
    mi_empresa: EstadosRevisados,
) -> None:
    movido = _cambia_renglon(
        mi_empresa, "Activo fijo neto", FIN, caja="capital de trabajo"
    )
    texto = pagina(panel_de(movido))
    assert "15,014,008.75" not in texto
    assert "25,318,585.22" in texto


def test_main_escribe_la_pagina(mi_empresa: EstadosRevisados, tmp_path: Path) -> None:
    archivo = tmp_path / "estados-revisados.json"
    archivo.write_text(mi_empresa.model_dump_json(), encoding="utf-8")
    salida = tmp_path / "contabilidad.html"
    proceso = subprocess.run(
        [
            sys.executable,
            "-m",
            "escala_server.cash.contabilidad",
            str(archivo),
            str(salida),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proceso.returncode == 0, proceso.stdout + proceso.stderr
    assert json.loads(proceso.stdout) == {"pagina": str(salida)}
    assert "15,014,008.75" in salida.read_text(encoding="utf-8")


def test_main_no_escribe_si_no_cuadra(
    mi_empresa: EstadosRevisados, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    movido = _cambia_renglon(
        mi_empresa, "Activo fijo neto", FIN, caja="capital de trabajo"
    )
    archivo = tmp_path / "estados-revisados.json"
    archivo.write_text(movido.model_dump_json(), encoding="utf-8")
    salida = tmp_path / "contabilidad.html"
    assert main([str(archivo), str(salida)]) == 2
    assert not salida.exists()
    respuesta = json.loads(capsys.readouterr().out)
    assert respuesta["preguntas"][0]["diferencia"] == "25318585.22"


def test_main_con_archivo_que_no_es_de_escala(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    archivo = tmp_path / "otro.json"
    archivo.write_text("{}", encoding="utf-8")
    assert main([str(archivo), str(tmp_path / "x.html")]) == 2
    assert "no_calculable" in json.loads(capsys.readouterr().out)
