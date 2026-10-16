"""S86.17 — Ningún número del modelo.

Cada número del resumen sale del JSON de la calculadora, y cada monto de la
lista sale tal cual de los archivos del dueño. La prueba saca los números del
texto y los busca en esas dos fuentes. Incluye un caso que la rompe: un número
inventado se detecta.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re

import pytest

from escala_server.cash.escenario import Conversacion, Paso, atender
from escala_server.financial.lector import leer_estados

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
HOY = date(2026, 1, 31)
EMPRESA = "Mi Empresa"
NUMERO = re.compile(r"\d[\d,]*(?:\.\d+)?")
RESPUESTAS = {
    "C10": "acumulado del año",
    "unidad": "pesos",
    "suma:gastos_operacion:2025-12-31": "sí",
    "suma:gastos_operacion:2024-12-31": "sí",
    "C11:Documentos por pagar a largo plazo": "no",
    "C9": "sí",
    "C1": "no sé",
    "C4": "2,966,528.27",
    "C3": "no sé",
    "C2": "todas",
}
ENTRADAS = {
    "completa": ("aspel_balance.txt", "aspel_resultados.txt"),
    "sin_anterior": ("contpaqi_balance.txt", "contpaqi_resultados.txt"),
}


def _numeros(texto: str) -> set[str]:
    return {n.replace(",", "") for n in NUMERO.findall(texto)}


def _paso(entrada: str) -> Paso:
    archivos = tuple(str(ESTADOS / nombre) for nombre in ENTRADAS[entrada])
    paso = atender(Conversacion(empresa=EMPRESA, archivos=archivos, respuestas=RESPUESTAS), hoy=HOY)
    assert paso.calculo is not None and paso.resumen
    return paso


def _resumen(mensaje: str) -> str:
    inicio = mensaje.index("Resumen al")
    fin = mensaje.index("¿Guardo")
    return mensaje[inicio:fin]


def _sin_origen(texto: str, paso: Paso) -> set[str]:
    assert paso.calculo is not None
    return _numeros(texto) - _numeros(paso.calculo.model_dump_json())


def _lista(mensaje: str) -> str:
    return mensaje[mensaje.index("Balance general") : mensaje.index("Lo que te pregunto")]


def _montos_leidos(entrada: str) -> set[str]:
    montos: set[str] = set()
    for nombre in ENTRADAS[entrada]:
        for cuenta in leer_estados(ESTADOS / nombre, hoy=HOY).cuentas:
            montos.add(f"{abs(cuenta.monto):.2f}")
    return montos


@pytest.mark.parametrize("entrada", list(ENTRADAS))
def test_cada_numero_del_resumen_sale_de_la_calculadora(entrada: str) -> None:
    paso = _paso(entrada)
    resumen = _resumen(paso.mensaje)
    assert _numeros(resumen)  # hay números que revisar
    assert _sin_origen(resumen, paso) == set()


@pytest.mark.parametrize("entrada", list(ENTRADAS))
def test_el_anuncio_solo_trae_nombres_de_la_calculadora(entrada: str) -> None:
    # «por cada 100 de ventas» es parte del nombre que da la calculadora.
    paso = _paso(entrada)
    assert paso.anuncio is not None
    assert _sin_origen(paso.anuncio, paso) == set()


@pytest.mark.parametrize("entrada", list(ENTRADAS))
def test_cada_monto_de_la_lista_sale_de_los_archivos(entrada: str) -> None:
    lista = _lista(_paso(entrada).mensaje)
    montos = {n for n in _numeros(lista) if "." in n}
    assert montos
    assert montos - _montos_leidos(entrada) == set()


def test_un_numero_inventado_se_detecta() -> None:
    """La prueba puede fallar: un número que no está en la calculadora sale."""

    paso = _paso("completa")
    inventado = _resumen(paso.mensaje).replace("6,178,173.85", "6,178,174.00")
    assert _sin_origen(inventado, paso) == {"6178174.00"}
    lista = _lista(paso.mensaje).replace("5,639,601.55", "5,639,601.56")
    montos = {n for n in _numeros(lista) if "." in n}
    assert montos - _montos_leidos("completa") == {"5639601.56"}
