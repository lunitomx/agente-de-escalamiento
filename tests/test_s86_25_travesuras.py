"""S86.25 — Las travesuras: ajustes que confiesa el dueño.

Según el curso de cash que vimos (F1.4, lámina 12), el dueño suma a su utilidad
los gastos personales que pagó la empresa (y las ventas que no quedaron
registradas), para ver su utilidad «como si no estuvieran».

Sobre qué utilidad se suma: la lámina 12 suma los ajustes directo a la utilidad
neta (resultado del ejercicio) 5,018,095.92, sin recalcular ISR.

- Ajustes de la lámina: venta sin factura 123,250 · viaje familiar 55,820 ·
  depreciación de la camioneta 41,875 · depreciación de la computadora 247 ·
  ajuste de intereses 224,422.11.
- Errata de la lámina 12: teclea el ajuste de gastos como 97,492; el correcto es
  55,820 + 41,875 + 247 = 97,942. Por eso la lámina dice 5,463,260.03 y la
  prueba usa el correcto: 5,463,710.03.
- 5,463,710.03 − 97,942 = 5,365,768.03 no es un renglón del estado: es la
  utilidad neta 5,018,095.92 + 123,250 + 224,422.11 (los otros dos ajustes).

ESCALA solo suma los montos que dio el dueño. Nunca estima ni sugiere uno.
Lo fiscal lo ve el contador.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from escala_server.cash import escenario
from escala_server.cash.curso import (
    AVISO_FISCAL,
    AjusteDelDueno,
    Calculado,
    EstadosRevisados,
    NoCalculable,
    UtilidadAjustada,
    utilidad_ajustada,
)
from escala_server.cash.escenario import Conversacion, Paso, atender
from escala_server.financial.lector import LecturaEstados, leer_estados
from escala_server.financial.revisiones import Respuestas, revisar_estados

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
HOY = date(2026, 1, 31)
EMPRESA = "Mi Empresa, S.A. de C.V."
SLUG = "mi-empresa-s-a-de-c-v"
COMPLETA = (ESTADOS / "aspel_balance.txt", ESTADOS / "aspel_resultados.txt")

# Los ajustes de la lámina 12, con el de gastos ya corregido (97,942 en tres partes).
LAMINA_12: tuple[tuple[str, str], ...] = (
    ("venta de desperdicio sin factura", "123250"),
    ("viaje familiar", "55820"),
    ("depreciación de la camioneta de un familiar", "41875"),
    ("depreciación de la computadora de un hijo", "247"),
    ("ajuste de intereses", "224422.11"),
)

# Lo que contesta el dueño de Mi Empresa hasta llegar al resumen (igual que S86.17).
RESPUESTAS: dict[str, str] = {
    "C10": "acumulado del año",
    "suma:gastos_operacion:2025-12-31": "sí",
    "suma:gastos_operacion:2024-12-31": "sí",
    "C11:Documentos por pagar a largo plazo": "no",
    "C9": "sí",
    "C1": "no sé",
    "C4": "2,966,528.27",
    "C3": "no sé",
    "C2": "todas",
}


def _estados(resultados: LecturaEstados | None = None) -> EstadosRevisados:
    leidos = resultados or leer_estados(ESTADOS / "aspel_resultados.txt", hoy=HOY)
    revision = revisar_estados(
        [leer_estados(ESTADOS / "aspel_balance.txt", hoy=HOY)],
        leidos,
        respuestas=Respuestas(periodo="acumulado del año"),
        hoy=HOY,
    )
    return EstadosRevisados(revision=revision, resultados=leidos)


def _ajustes(*pares: tuple[str, str]) -> list[AjusteDelDueno]:
    return [AjusteDelDueno(concepto=c, monto=Decimal(m)) for c, m in pares]


def _calculado(cifra: Calculado | NoCalculable) -> Calculado:
    assert isinstance(cifra, Calculado), cifra
    return cifra


@pytest.fixture(scope="module")
def mi_empresa() -> EstadosRevisados:
    return _estados()


# ---------------------------------------------------------------------------
# La cuenta: utilidad contable + ajustes del dueño
# ---------------------------------------------------------------------------


def test_lamina_12_utilidad_ajustada_con_el_ajuste_correcto(
    mi_empresa: EstadosRevisados,
) -> None:
    # Errata L12: la lámina teclea 97,492 y da 5,463,260.03. El correcto es 97,942.
    resultado = utilidad_ajustada(mi_empresa, _ajustes(*LAMINA_12))

    contable = _calculado(resultado.utilidad_contable)
    assert contable.valor == Decimal("5018095.92")
    assert "utilidad neta 5,018,095.92" in contable.origen

    ajustes = _calculado(resultado.total_de_ajustes)
    assert ajustes.valor == Decimal("445614.11")

    ajustada = _calculado(resultado.utilidad_ajustada)
    assert ajustada.valor == Decimal("5463710.03")
    assert ajustada.lamina == "L12"
    assert ajustada.formula == "utilidad contable + ajustes que me dijiste"
    assert ajustada.origen.startswith("sale de: utilidad neta 5,018,095.92 + ")
    assert "viaje familiar 55,820.00" in ajustada.origen
    assert "ajuste de intereses 224,422.11" in ajustada.origen


def test_sin_los_gastos_personales_queda_la_utilidad_neta_mas_los_otros_dos(
    mi_empresa: EstadosRevisados,
) -> None:
    # 5,463,710.03 − 97,942 = 5,365,768.03 = utilidad neta + 123,250 + 224,422.11.
    sin_gastos = [LAMINA_12[0], LAMINA_12[4]]
    resultado = utilidad_ajustada(mi_empresa, _ajustes(*sin_gastos))
    assert _calculado(resultado.utilidad_ajustada).valor == Decimal("5365768.03")


def test_cambiar_un_monto_del_dueno_cambia_la_utilidad_ajustada(
    mi_empresa: EstadosRevisados,
) -> None:
    # Con el monto de la errata (97,492 en lugar de 97,942) sale el número de la lámina.
    con_errata = [
        LAMINA_12[0],
        ("gastos personales (como los tecleó la lámina)", "97492"),
        LAMINA_12[4],
    ]
    resultado = utilidad_ajustada(mi_empresa, _ajustes(*con_errata))
    assert _calculado(resultado.utilidad_ajustada).valor == Decimal("5463260.03")


def test_solo_suma_lo_que_dijo_el_dueno(mi_empresa: EstadosRevisados) -> None:
    resultado = utilidad_ajustada(mi_empresa, _ajustes(("viaje familiar", "55820")))
    assert resultado.ajustes == tuple(_ajustes(("viaje familiar", "55820")))
    assert _calculado(resultado.utilidad_ajustada).valor == Decimal("5073915.92")


def test_sin_ajustes_la_ajustada_es_la_contable(mi_empresa: EstadosRevisados) -> None:
    resultado = utilidad_ajustada(mi_empresa, [])
    ajustada = _calculado(resultado.utilidad_ajustada)
    assert ajustada.valor == Decimal("5018095.92")
    assert "no me dijiste ningún ajuste" in ajustada.origen


@pytest.mark.parametrize("monto", ["0", "-55820"])
def test_un_ajuste_sin_monto_positivo_no_se_acepta(monto: str) -> None:
    with pytest.raises(ValidationError):
        AjusteDelDueno(concepto="viaje familiar", monto=Decimal(monto))


def test_un_ajuste_sin_concepto_no_se_acepta() -> None:
    with pytest.raises(ValidationError):
        AjusteDelDueno(concepto="  ", monto=Decimal("1"))


def test_sin_utilidad_neta_no_calcula_y_no_pone_cero() -> None:
    leidos = leer_estados(ESTADOS / "aspel_resultados.txt", hoy=HOY)
    sin_neta = leidos.model_copy(
        update={"cuentas": [c for c in leidos.cuentas if c.concepto != "utilidad_neta"]}
    )
    resultado = utilidad_ajustada(
        _estados(sin_neta), _ajustes(("viaje familiar", "55820"))
    )
    assert isinstance(resultado.utilidad_contable, NoCalculable)
    assert isinstance(resultado.utilidad_ajustada, NoCalculable)
    assert "utilidad neta" in resultado.utilidad_ajustada.no_calculable


def test_lo_fiscal_lo_ve_el_contador(mi_empresa: EstadosRevisados) -> None:
    resultado = utilidad_ajustada(mi_empresa, _ajustes(*LAMINA_12))
    assert AVISO_FISCAL == "Lo fiscal lo ve tu contador."
    assert resultado.aviso == AVISO_FISCAL
    texto = resultado.model_dump_json().lower()
    assert "deduc" not in texto


def test_el_resultado_es_un_modelo_pydantic(mi_empresa: EstadosRevisados) -> None:
    resultado = utilidad_ajustada(mi_empresa, _ajustes(*LAMINA_12))
    assert (
        UtilidadAjustada.model_validate_json(resultado.model_dump_json()) == resultado
    )


# ---------------------------------------------------------------------------
# El escenario: pregunta estructurada, sin juicio, después del resumen
# ---------------------------------------------------------------------------


def _paso(**extra: str) -> Paso:
    respuestas = {**RESPUESTAS, **extra}
    conversacion = Conversacion(
        empresa=EMPRESA, archivos=tuple(str(a) for a in COMPLETA), respuestas=respuestas
    )
    return atender(conversacion, hoy=HOY)


def test_tras_el_resumen_pregunta_por_gastos_personales_sin_juicio() -> None:
    paso = _paso()
    assert paso.resumen, paso.mensaje
    assert paso.travesuras is None
    pregunta = paso.pregunta_travesuras
    assert pregunta is not None and pregunta.clave == "C6"
    assert not pregunta.bloquea
    for ejemplo in ("viaje familiar", "camioneta", "computadora"):
        assert ejemplo in pregunta.pregunta
    assert "Opcional" in paso.mensaje
    # La pregunta no trae ningún monto sugerido: ni un solo número.
    assert not any(
        ch.isdigit() for ch in pregunta.pregunta + " ".join(pregunta.opciones)
    )
    # El «¿Guardo …?» sigue al final.
    assert paso.mensaje.split("\n\n")[-1].startswith("¿Guardo ")


def test_el_dueno_da_concepto_y_monto_y_ve_la_utilidad_ajustada() -> None:
    paso = _paso(**{f"C6:{c}": m for c, m in LAMINA_12})
    assert paso.pregunta_travesuras is None
    assert paso.travesuras is not None
    ajustada = _calculado(paso.travesuras.utilidad_ajustada)
    assert ajustada.valor == Decimal("5463710.03")
    assert "Utilidad contable: 5,018,095.92" in paso.mensaje
    assert "- viaje familiar: 55,820.00" in paso.mensaje
    assert "Utilidad ajustada: 5,463,710.03" in paso.mensaje
    assert "Lo fiscal lo ve tu contador." in paso.mensaje
    assert "deduc" not in paso.mensaje.lower()
    assert paso.mensaje.split("\n\n")[-1].startswith("¿Guardo ")


def test_el_dueno_dice_que_no_hay_travesuras() -> None:
    paso = _paso(C6="no")
    assert paso.pregunta_travesuras is None
    assert paso.travesuras is not None
    assert _calculado(paso.travesuras.utilidad_ajustada).valor == Decimal("5018095.92")


def test_sin_monto_no_lo_suma_ni_lo_estima() -> None:
    paso = _paso(**{"C6:viaje familiar": "55,820", "C6:camioneta": "no sé"})
    assert paso.travesuras is not None
    assert _calculado(paso.travesuras.utilidad_ajustada).valor == Decimal("5073915.92")
    assert "«camioneta»: sin monto no lo sumo" in paso.mensaje


@pytest.mark.parametrize("valor", ["cero", "-5", "0", "mucho"])
def test_un_monto_que_no_se_entiende_se_dice(valor: str) -> None:
    paso = _paso(**{"C6:viaje familiar": valor})
    assert any(valor in error for error in paso.errores), paso.errores
    assert paso.travesuras is None


# ---------------------------------------------------------------------------
# Nada se guarda sin «sí» (el mecanismo de S86.17)
# ---------------------------------------------------------------------------


def _corre(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, *extra: str
) -> dict[str, Any]:
    argv = [
        "--empresa",
        EMPRESA,
        "--carpeta",
        str(tmp_path / "work" / "cash"),
        "--conversacion",
        str(tmp_path / "trabajo" / "platica.json"),
        "--hoy",
        HOY.isoformat(),
    ]
    for archivo in COMPLETA:
        argv += ["--archivo", str(archivo)]
    for clave, valor in RESPUESTAS.items():
        argv += ["--responde", f"{clave}={valor}"]
    for clave, valor in LAMINA_12:
        argv += ["--responde", f"C6:{clave}={valor}"]
    assert escenario.main([*argv, *extra]) == 0
    return json.loads(capsys.readouterr().out)


def test_sin_si_no_se_guardan_los_ajustes(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    salida = _corre(capsys, tmp_path)
    assert salida["guardado"] == []
    assert Decimal(salida["travesuras"]["utilidad_ajustada"]["valor"]) == Decimal(
        "5463710.03"
    )
    assert not (tmp_path / "work" / "cash" / SLUG).exists()


def test_con_si_los_ajustes_quedan_en_la_platica(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    salida = _corre(capsys, tmp_path, "--guardar", "sí")
    assert salida["guardado"]
    guardada = json.loads(
        (tmp_path / "work" / "cash" / SLUG / "conversacion.json").read_text("utf-8")
    )
    assert guardada["respuestas"]["C6:viaje familiar"] == "55820"
