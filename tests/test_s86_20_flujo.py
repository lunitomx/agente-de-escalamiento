"""S86.20 — Panel «Las tres medidas de tu flujo» y los 4 capítulos.

Según el curso de cash que vimos (Parte III, L25, L58–L64):

- flujo neto = −(deuda neta al final − deuda neta al inicio);
- flujo de operación = utilidad de operación − cambio en capital de trabajo;
- flujo marginal = utilidad bruta ÷ ventas − capital de trabajo ÷ ventas.

Los 4 capítulos (L59) no suman sin una 5ª fila, «salidas de capital»
(Δ capital − utilidad neta):

    5,018,095.92 − 2,603,803.13 − 3,153,010.36 − 2,966,528.27 = −3,705,245.84

Errata L59: la lámina imprime financiamiento −3,705,843 y rentabilidad
5,018,095.82 (captura, sin causa reproducible). Las pruebas usan −3,705,245.84
y 5,018,095.92, que salen de los estados.

Flujo neto ajustado del poder del uno (L70): −3,705,245.84 + 1,143,864.91 = −2,561,380.93.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from escala_server.cash.curso import Calculado, EstadosRevisados, NoCalculable
from escala_server.cash.flujo import Capitulo, PanelDelFlujo, main, pagina, panel_de
from escala_server.financial.cajas import CuentaEnCaja
from escala_server.financial.lector import leer_estados
from escala_server.financial.revisiones import Respuestas, revisar_estados

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
HOY = date(2026, 1, 31)
INI = date(2024, 12, 31)
FIN = date(2025, 12, 31)
FLUJO_NETO = Decimal("-3705245.84")


def _estados(respuestas: Respuestas | None = None) -> EstadosRevisados:
    respuestas = respuestas or Respuestas(periodo="acumulado del año")
    resultados = leer_estados(ESTADOS / "aspel_resultados.txt", hoy=HOY)
    revision = revisar_estados(
        [leer_estados(ESTADOS / "aspel_balance.txt", hoy=HOY)],
        resultados,
        respuestas=respuestas,
        hoy=HOY,
    )
    return EstadosRevisados(revision=revision, resultados=resultados, respuestas=respuestas)


def _con_retiros(del_dueno: str | None, de_capital: str | None) -> EstadosRevisados:
    return _estados(
        Respuestas(
            periodo="acumulado del año",
            retiros_del_dueno=None if del_dueno is None else Decimal(del_dueno),
            retiros_de_capital=None if de_capital is None else Decimal(de_capital),
        )
    )


@pytest.fixture(scope="module")
def mi_empresa() -> EstadosRevisados:
    return _estados()


@pytest.fixture(scope="module")
def panel(mi_empresa: EstadosRevisados) -> PanelDelFlujo:
    return panel_de(mi_empresa)


def _valor(indicador: object) -> Decimal:
    assert isinstance(indicador, Calculado), indicador
    return indicador.valor


def _cambios(capitulo: Capitulo) -> dict[str, Decimal]:
    return {r.nombre: r.cambio for r in capitulo.desglose}


# ---------------------------------------------------------------------------
# Las tres medidas
# ---------------------------------------------------------------------------


def test_las_tres_medidas_de_mi_empresa(panel: PanelDelFlujo) -> None:
    assert _valor(panel.medida("flujo_neto")) == FLUJO_NETO
    assert _valor(panel.medida("flujo_de_operacion")) == Decimal("4835206.16")
    assert _valor(panel.medida("marginal")) == Decimal("0.3350")


def test_cada_medida_dice_formula_origen_y_para_quien(panel: PanelDelFlujo) -> None:
    for medida in panel.medidas:
        assert isinstance(medida.indicador, Calculado)
        assert medida.indicador.origen.startswith("sale de: ")
        assert medida.indicador.formula
        assert medida.para_quien
    assert "deuda neta" in panel.medida("flujo_neto").formula


def test_bancos_final_menos_inicial_se_muestra_como_lo_que_engana(panel: PanelDelFlujo) -> None:
    assert panel.engana is not None
    assert panel.engana.valor == Decimal("89753.25")
    assert "210,291.16" in panel.engana.origen and "120,537.91" in panel.engana.origen


# ---------------------------------------------------------------------------
# Los 4 capítulos y la 5ª fila
# ---------------------------------------------------------------------------


def test_la_cascada_de_mi_empresa_suma_al_centavo(panel: PanelDelFlujo) -> None:
    valores = [c.valor for c in panel.capitulos]
    assert [c.clave for c in panel.capitulos] == [
        "rentabilidad",
        "capital_de_trabajo",
        "otras_cuentas",
        "salidas_de_capital",
    ]
    # Errata L59: la lámina dice 5,018,095.82 y −3,705,843.
    assert valores == [
        Decimal("5018095.92"),
        Decimal("-2603803.13"),
        Decimal("-3153010.36"),
        Decimal("-2966528.27"),
    ]
    assert panel.flujo_neto is not None and panel.flujo_neto.valor == FLUJO_NETO
    assert sum(valores, Decimal("0")) == FLUJO_NETO
    assert panel.suma_de_capitulos == FLUJO_NETO
    assert panel.cuadre == "cuadra" and panel.aviso is None


def test_otras_cuentas_abre_su_desglose_por_renglon(panel: PanelDelFlujo) -> None:
    otras = panel.capitulo("otras_cuentas")
    assert _cambios(otras) == {
        "Otros activos circulantes": Decimal("128515.05"),
        "Activo fijo neto": Decimal("320732.86"),
        "Activo diferido": Decimal("202666.76"),
        "Acreedores diversos": Decimal("2038713.23"),
        "Documentos por pagar a largo plazo": Decimal("462382.46"),
    }
    assert sum((r.efecto for r in otras.desglose), Decimal("0")) == otras.valor
    acreedores = next(r for r in otras.desglose if r.nombre == "Acreedores diversos")
    assert acreedores.al_inicio == Decimal("-13885547.68")
    assert acreedores.al_final == Decimal("-11846834.45")
    assert "pagaste" in acreedores.origen and "13,885,547.68" in acreedores.origen


def test_capital_de_trabajo_abre_su_desglose(panel: PanelDelFlujo) -> None:
    assert _cambios(panel.capitulo("capital_de_trabajo")) == {
        "Clientes": Decimal("2112721.58"),
        "Inventarios": Decimal("556158.24"),
        "Proveedores": Decimal("-65076.69"),
    }


def test_cada_capitulo_dice_de_donde_sale(panel: PanelDelFlujo) -> None:
    for capitulo in panel.capitulos:
        assert capitulo.origen.startswith("sale de: "), capitulo
        assert capitulo.formula and capitulo.lamina
    salidas = panel.capitulo("salidas_de_capital")
    assert "9,256,923.52" in salidas.origen and "7,205,355.87" in salidas.origen
    assert "5,018,095.92" in salidas.origen


def test_mover_una_cuenta_con_escala_cambia_el_capitulo_y_la_cascada_sigue_sumando() -> None:
    movido = panel_de(
        _estados(
            Respuestas(
                periodo="acumulado del año",
                movimientos={"Otros activos circulantes": "capital de trabajo"},
            )
        )
    )
    assert movido.capitulo("capital_de_trabajo").valor == Decimal("-2732318.18")
    assert movido.capitulo("otras_cuentas").valor == Decimal("-3024495.31")
    assert sum((c.valor for c in movido.capitulos), Decimal("0")) == FLUJO_NETO
    assert movido.cuadre == "cuadra"


def test_un_renglon_cambiado_a_mano_no_da_panel(mi_empresa: EstadosRevisados) -> None:
    def cambia(cuenta: CuentaEnCaja) -> CuentaEnCaja:
        if cuenta.nombre == "Activo fijo neto" and cuenta.fecha == FIN:
            return cuenta.model_copy(update={"caja": "capital de trabajo"})
        return cuenta

    revision = mi_empresa.revision
    acomodo = revision.acomodo.model_copy(
        update={"cuentas": tuple(cambia(c) for c in revision.acomodo.cuentas)}
    )
    editado = mi_empresa.model_copy(
        update={"revision": revision.model_copy(update={"acomodo": acomodo})}
    )
    resultado = panel_de(editado)
    assert resultado.capitulos == ()
    assert resultado.preguntas and resultado.preguntas[0].diferencia == Decimal("25318585.22")


# ---------------------------------------------------------------------------
# La 5ª fila contra lo que dijo el dueño (C3/C4)
# ---------------------------------------------------------------------------


def test_sin_respuesta_pregunta_c3_y_c4_con_el_numero(panel: PanelDelFlujo) -> None:
    retiros = panel.retiros
    assert retiros is not None
    assert retiros.estado == "sin respuesta"
    assert retiros.sin_explicar is None
    assert {p.codigo for p in retiros.preguntas} == {"C3", "C4"}
    assert any("2,966,528.27" in p.pregunta for p in retiros.preguntas)


def test_retiros_que_cuadran() -> None:
    retiros = panel_de(_con_retiros("966528.27", "2000000")).retiros
    assert retiros is not None
    assert retiros.estado == "cuadra"
    assert retiros.dijo == Decimal("2966528.27")
    assert retiros.preguntas == ()


def test_retiros_distintos_de_la_quinta_fila_dejan_algo_sin_explicar() -> None:
    retiros = panel_de(_con_retiros("1000000", "1000000")).retiros
    assert retiros is not None
    assert retiros.estado == "sin explicar"
    assert retiros.sin_explicar == Decimal("966528.27")
    assert "sin explicar: 966,528.27" in retiros.mensaje


def test_solo_contesto_uno_compara_y_pregunta_el_otro() -> None:
    retiros = panel_de(_con_retiros(None, "2966528.27")).retiros
    assert retiros is not None
    assert retiros.estado == "cuadra"
    assert [p.codigo for p in retiros.preguntas] == ["C3"]


def test_hasta_un_peso_de_diferencia_cuadra_como_r9() -> None:
    cerca = panel_de(_con_retiros("0", "2966527.50")).retiros
    lejos = panel_de(_con_retiros("0", "2966527.26")).retiros
    assert cerca is not None and cerca.estado == "cuadra"
    assert lejos is not None and lejos.estado == "sin explicar"


# ---------------------------------------------------------------------------
# Flujo neto ajustado del poder del uno
# ---------------------------------------------------------------------------


def test_flujo_neto_ajustado_del_poder_del_uno(panel: PanelDelFlujo) -> None:
    ajustado = panel.flujo_ajustado
    assert isinstance(ajustado, Calculado)
    assert ajustado.valor == Decimal("-2561380.93")
    assert "1,143,864.91" in ajustado.origen and "3,705,245.84" in ajustado.origen


# ---------------------------------------------------------------------------
# Cuando no se puede
# ---------------------------------------------------------------------------


def test_sin_balance_inicial_no_calculable(mi_empresa: EstadosRevisados) -> None:
    revision = mi_empresa.revision.model_copy(update={"balance_inicial": None})
    resultado = panel_de(mi_empresa.model_copy(update={"revision": revision}))
    assert resultado.capitulos == ()
    assert resultado.no_calculable is not None
    assert "inicio" in resultado.no_calculable


def test_sin_utilidad_neta_los_capitulos_no_se_calculan(mi_empresa: EstadosRevisados) -> None:
    lectura = mi_empresa.resultados
    sin_neta = lectura.model_copy(
        update={"cuentas": tuple(c for c in lectura.cuentas if c.concepto != "utilidad_neta")}
    )
    resultado = panel_de(mi_empresa.model_copy(update={"resultados": sin_neta}))
    assert resultado.capitulos == ()
    assert resultado.capitulos_no_calculable is not None
    assert "utilidad neta" in resultado.capitulos_no_calculable
    assert _valor(resultado.medida("flujo_neto")) == FLUJO_NETO


def test_frase_por_que_ganaste_y_tienes_menos(panel: PanelDelFlujo) -> None:
    assert "5,018,095.92" in panel.frase
    assert "3,705,245.84" in panel.frase


# ---------------------------------------------------------------------------
# Página y entrada
# ---------------------------------------------------------------------------


def test_la_pagina_trae_la_cascada_y_el_origen(panel: PanelDelFlujo) -> None:
    texto = pagina(panel)
    assert texto.startswith("<!doctype html>")
    assert "<script" not in texto
    assert texto.count('class="barra') == 5
    for cifra in ("5,018,095.92", "2,603,803.13", "3,153,010.36", "2,966,528.27", "3,705,245.84"):
        assert cifra in texto
    assert "2,038,713.23" in texto and "sale de:" in texto
    assert "2,561,380.93" in texto and "0.3350" in texto
    assert "89,753.25" in texto


def test_la_pagina_de_un_panel_que_no_sale_trae_la_pregunta() -> None:
    sin = PanelDelFlujo(no_calculable="falta el balance al inicio del periodo")
    assert "falta el balance al inicio" in pagina(sin)


def test_main_escribe_la_pagina(mi_empresa: EstadosRevisados, tmp_path: Path) -> None:
    archivo = tmp_path / "estados-revisados.json"
    archivo.write_text(mi_empresa.model_dump_json(), encoding="utf-8")
    salida = tmp_path / "flujo.html"
    proceso = subprocess.run(
        [sys.executable, "-m", "escala_server.cash.flujo", str(archivo), str(salida)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proceso.returncode == 0, proceso.stdout + proceso.stderr
    assert json.loads(proceso.stdout) == {"pagina": str(salida)}
    assert "3,705,245.84" in salida.read_text(encoding="utf-8")


def test_main_con_archivo_que_no_es_de_escala(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    archivo = tmp_path / "otro.json"
    archivo.write_text("{}", encoding="utf-8")
    assert main([str(archivo), str(tmp_path / "x.html")]) == 2
    assert "no_calculable" in json.loads(capsys.readouterr().out)


def test_no_calculable_no_pone_cero(mi_empresa: EstadosRevisados) -> None:
    revision = mi_empresa.revision.model_copy(update={"balance_inicial": None})
    resultado = panel_de(mi_empresa.model_copy(update={"revision": revision}))
    assert isinstance(resultado.medida("flujo_neto"), NoCalculable)
