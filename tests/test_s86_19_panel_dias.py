"""S86.19 — Panel «Días y ciclo del dinero» (la página).

La página no calcula: pinta lo que dio ``dias_del_dinero`` (Python, con pruebas).
Cada número lleva su «sale de:»; la línea de tiempo va compra → pago → venta → cobro.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

from escala_server.cash.curso import (
    BaseDeDias,
    Calculado,
    DiasDelDinero,
    EstadosRevisados,
    dias_del_dinero,
)
from escala_server.cash.panel_dias import main, pagina
from escala_server.financial.lector import leer_estados
from escala_server.financial.revisiones import Respuestas, revisar_estados

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
HOY = date(2026, 1, 31)
FIN = date(2025, 12, 31)


def _mi_empresa(respuestas: Respuestas | None = None) -> EstadosRevisados:
    contestado = respuestas or Respuestas(periodo="acumulado del año")
    resultados = leer_estados(ESTADOS / "aspel_resultados.txt", hoy=HOY)
    revision = revisar_estados(
        [leer_estados(ESTADOS / "aspel_balance.txt", hoy=HOY)],
        resultados,
        respuestas=contestado,
        hoy=HOY,
    )
    return EstadosRevisados(
        revision=revision, resultados=resultados, respuestas=respuestas
    )


@pytest.fixture(scope="module")
def como_vienen() -> DiasDelDinero:
    return dias_del_dinero(_mi_empresa(), BaseDeDias())


@pytest.fixture(scope="module")
def html_como_vienen(como_vienen: DiasDelDinero) -> str:
    return pagina(como_vienen)


def _texto(html: str) -> str:
    """Lo que ve el dueño: sin etiquetas ni el bloque de datos."""
    sin_datos = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    sin_estilo = re.sub(r"<style.*?</style>", "", sin_datos, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", sin_estilo))


def test_pagina_trae_los_numeros_del_curso(html_como_vienen: str) -> None:
    texto = _texto(html_como_vienen)
    for numero in ("36.08", "46.97", "25.30", "28.15", "24.31", "19.59", "37.07", "55.53"):
        assert numero in texto, numero
    assert "Tu ciclo pasó de 37.07 a 55.53 días: empeoró" in texto
    # Proveedores bajó: pagas antes, y eso también empeora tu efectivo.
    assert "Tus días de proveedores pasaron de 24.31 a 19.59 días: empeoró" in texto


def test_cada_numero_dice_de_donde_sale(
    como_vienen: DiasDelDinero, html_como_vienen: str
) -> None:
    texto = _texto(html_como_vienen)
    for anio in como_vienen.anios:
        for clave in ("clientes", "inventario", "proveedores", "ciclo"):
            indicador = getattr(anio, clave)
            assert isinstance(indicador, Calculado)
            assert indicador.origen in texto, (clave, anio.fecha)
        assert anio.cronograma is not None
        assert anio.cronograma.origen in texto


def test_linea_de_tiempo_compra_pago_venta_cobro(html_como_vienen: str) -> None:
    texto = _texto(html_como_vienen)
    compra = texto.index("Compra")
    pago = texto.index("Pagas al proveedor")
    venta = texto.index("Vendes")
    cobro = texto.index("Cobras")
    assert compra < pago < venta < cobro
    assert "día 75.12" in texto  # cobro = 28.15 + 46.97
    assert "55.53 días que financias tú" in texto


def test_rotulo_avisos_y_preguntas(html_como_vienen: str) -> None:
    texto = _texto(html_como_vienen)
    assert "días de cobro calculados con los saldos como vienen" in texto
    assert "ventas totales" in texto
    assert "¿Tus saldos de clientes y proveedores incluyen IVA?" in texto
    assert "Según el curso de cash que vimos" in texto


def test_sin_iva_rotula_y_deja_la_nota_con_iva() -> None:
    dias = dias_del_dinero(
        _mi_empresa(), BaseDeDias(iva_incluido=True, tasa_iva=Decimal("16"))
    )
    texto = _texto(pagina(dias))
    assert "días de cobro calculados sin IVA" in texto
    assert "40.49" in texto
    assert "Con IVA, como los mide el curso: clientes 46.97" in texto


def test_pagina_de_un_archivo_sin_nada_de_fuera(html_como_vienen: str) -> None:
    assert html_como_vienen.startswith("<!doctype html>")
    assert "<script src" not in html_como_vienen
    assert "<link" not in html_como_vienen
    assert "prefers-color-scheme: dark" in html_como_vienen
    assert "<title>Días y ciclo del dinero</title>" in html_como_vienen


def test_la_pagina_no_calcula(html_como_vienen: str) -> None:
    """Sólo un bloque de datos; ningún script que haga cuentas."""
    scripts = re.findall(r"<script([^>]*)>", html_como_vienen)
    assert scripts == [' id="datos-dias" type="application/json"']


def test_no_calculable_se_dice_y_no_hay_ceros() -> None:
    dias = DiasDelDinero(no_calculable="tu balance no cuadra por 100.00")
    texto = _texto(pagina(dias))
    assert "No calculable: tu balance no cuadra por 100.00" in texto
    assert " 0.00" not in texto


def test_textos_se_escapan() -> None:
    dias = DiasDelDinero(no_calculable="<b>raro</b>")
    assert "<b>raro</b>" not in pagina(dias)


# ---------------------------------------------------------------------------
# Entrada: python -m escala_server.cash.panel_dias <estados> <salida.html> [...]
# ---------------------------------------------------------------------------


def _archivo(tmp_path: Path, estados: EstadosRevisados) -> Path:
    archivo = tmp_path / "estados-revisados.json"
    archivo.write_text(estados.model_dump_json(), encoding="utf-8")
    return archivo


def test_main_escribe_la_pagina(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    salida = tmp_path / "dias.html"
    assert main([str(_archivo(tmp_path, _mi_empresa())), str(salida)]) == 0
    assert json.loads(capsys.readouterr().out)["pagina"] == str(salida)
    assert "55.53" in salida.read_text(encoding="utf-8")


def test_main_toma_las_respuestas_guardadas_y_la_tasa(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    respuestas = Respuestas(
        periodo="acumulado del año", iva_incluido=True, ventas_a_credito=Decimal("100")
    )
    salida = tmp_path / "dias.html"
    archivo = _archivo(tmp_path, _mi_empresa(respuestas))
    assert main([str(archivo), str(salida), "--tasa-iva", "16"]) == 0
    capsys.readouterr()
    texto = _texto(salida.read_text(encoding="utf-8"))
    assert "días de cobro calculados sin IVA" in texto
    assert "40.49" in texto


def test_main_las_banderas_mandan_sobre_lo_guardado(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    salida = tmp_path / "dias.html"
    archivo = _archivo(tmp_path, _mi_empresa())
    assert main([str(archivo), str(salida), "--iva", "no", "--credito", "60"]) == 0
    capsys.readouterr()
    texto = _texto(salida.read_text(encoding="utf-8"))
    assert "días de cobro calculados sin IVA" in texto
    assert "78.28" in texto  # 46.97 ÷ 0.60


@pytest.mark.parametrize(
    "banderas",
    [["--tasa-iva", "dieciséis"], ["--credito", "150"], ["--iva", "quizá"], ["--otra"]],
)
def test_main_bandera_mala_no_calcula(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], banderas: list[str]
) -> None:
    salida = tmp_path / "dias.html"
    archivo = _archivo(tmp_path, _mi_empresa())
    assert main([str(archivo), str(salida), *banderas]) == 2
    assert "no_calculable" in json.loads(capsys.readouterr().out)
    assert not salida.exists()


def test_main_con_archivo_malo_no_calcula(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    malo = tmp_path / "malo.json"
    malo.write_text("{}", encoding="utf-8")
    salida = tmp_path / "dias.html"
    assert main([str(malo), str(salida)]) == 2
    assert "no_calculable" in json.loads(capsys.readouterr().out)
    assert not salida.exists()


def test_modulo_se_corre_con_python_m(tmp_path: Path) -> None:
    salida = tmp_path / "dias.html"
    corrida = subprocess.run(
        [
            sys.executable,
            "-m",
            "escala_server.cash.panel_dias",
            str(_archivo(tmp_path, _mi_empresa())),
            str(salida),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert corrida.returncode == 0, corrida.stderr
    assert salida.exists()
