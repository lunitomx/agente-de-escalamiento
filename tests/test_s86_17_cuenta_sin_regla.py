"""S86.17 — Una cuenta que ninguna regla reconoce se acomoda con la respuesta del dueño (R7)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from escala_server.financial.cajas import acomodar
from escala_server.financial.lector import leer_texto
from escala_server.financial.revisiones import Respuestas, revisar_estados

HOY = date(2026, 1, 31)
BALANCE = """Balance General
(Cifras en pesos)
Nombre | Dic-2025
Bancos | 100.00
Clientes | 400.00
Cuenta puente | 300.00
Total ACTIVO | 800.00
Proveedores | 200.00
Capital social | 600.00
Total PASIVO Y CAPITAL | 800.00
"""
RESULTADOS = """Estado de Resultados del 1/Ene/2025 al 31/Dic/2025
(Cifras en pesos)
Concepto | Acumulado
Ventas netas | 1,000.00
Costo de ventas | 600.00
Gastos de operación | 300.00
Utilidad neta | 100.00
"""


def _revisar(que_es: dict[str, str] | None = None):
    respuestas = Respuestas(periodo="acumulado del año", que_es=que_es or {})
    return revisar_estados(
        [leer_texto(BALANCE, hoy=HOY)],
        leer_texto(RESULTADOS, hoy=HOY),
        respuestas=respuestas,
        hoy=HOY,
    )


def test_sin_respuesta_la_cuenta_sin_regla_bloquea() -> None:
    revision = _revisar()
    r7 = [p for p in revision.preguntas if p.codigo == "R7"]
    assert [p.cuenta for p in r7] == ["Cuenta puente"]
    assert not revision.puede_calcular


def test_con_respuesta_va_a_su_caja_y_deja_de_bloquear() -> None:
    revision = _revisar({"Cuenta puente": "deudores"})
    assert not [p for p in revision.preguntas if p.codigo == "R7"]
    cuenta = next(c for c in revision.acomodo.cuentas if c.nombre == "Cuenta puente")
    assert (cuenta.regla, cuenta.lado, cuenta.caja) == ("deudores", "activo", "otras cuentas")
    assert "Me dijiste" in cuenta.porque
    assert revision.puede_calcular


def test_la_respuesta_cambia_las_cajas() -> None:
    como_cliente = acomodar(
        leer_texto(BALANCE, hoy=HOY).cuentas, que_es={"Cuenta puente": "clientes"}
    ).totales[0]
    como_deudor = acomodar(
        leer_texto(BALANCE, hoy=HOY).cuentas, que_es={"Cuenta puente": "deudores"}
    ).totales[0]
    assert como_cliente.capital_de_trabajo == Decimal("500.00")
    assert como_deudor.capital_de_trabajo == Decimal("200.00")
    assert como_deudor.otras_cuentas == Decimal("300.00")


def test_una_regla_que_no_existe_se_rechaza() -> None:
    with pytest.raises(ValidationError):
        Respuestas(que_es={"Cuenta puente": "lo que sea"})
