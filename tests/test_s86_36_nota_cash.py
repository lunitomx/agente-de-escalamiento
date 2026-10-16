"""S86.36 — La nota de Cash del panel de control sale del recorrido de cash.

La nota ya no lee la hoja ``cash/power-of-one`` (sólo la llenaba el tablero que
se quitó en S86.33). Lee lo que el recorrido de cash guardó con «sí»:
``work/cash/<empresa>/estados-revisados-<fecha>.json`` y, si existe,
``perfil-ideal.json`` con los límites del dueño. Los números los vuelve a sacar
la calculadora; aquí no se inventa ningún límite.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import uuid

import pytest

from escala_server.cash.archivos import carpeta_de
from escala_server.cash.escenario import Conversacion, Paso, guardar
from escala_server.cash.nota import LineaDeLaNota, NotaDeCash, nota_de_cash
from escala_server.cash.perfil import ARCHIVO, Borde, Clave, Limites, PerfilGuardado
from escala_server.dashboard import DashboardHandler
from escala_server.handlers import WorksheetsHandler
from tests.test_s86_17_escenario import COMPLETA, EMPRESA, HOY, _platica

SIN_RECORRIDO = "Sin datos: corre el recorrido de cash (/escala-cash)"
SLUG = carpeta_de(EMPRESA)


def _b(valor: str, incluye: bool = False) -> Borde:
    return Borde(valor=Decimal(valor), incluye=incluye)


# Los límites de un dueño de ejemplo (los fija él; ESCALA no los supone).
# Mi Empresa: 47.60% bruta (amarillo), 30.62% gastos (amarillo), 16.97% operación
# (verde), 46.97 días clientes (verde), 28.15 inventario (verde), 19.59 proveedores
# (rojo con el valor sin redondear 19.587…). 3 de 6 en verde.
LIMITES: dict[Clave, Limites] = {
    "utilidad_bruta": Limites(ideal=Decimal("50"), verde=_b("50", True), rojo=_b("40")),
    "gastos": Limites(ideal=Decimal("30"), verde=_b("30"), rojo=_b("35")),
    "utilidad_de_operacion": Limites(
        ideal=Decimal("15"), verde=_b("15"), rojo=_b("10")
    ),
    "dias_clientes": Limites(ideal=Decimal("45"), verde=_b("50"), rojo=_b("60")),
    "dias_inventario": Limites(ideal=Decimal("25"), verde=_b("30"), rojo=_b("45")),
    "dias_proveedores": Limites(ideal=Decimal("30"), verde=_b("30"), rojo=_b("20")),
}


@pytest.fixture(scope="module")
def recorrido() -> tuple[Paso, Conversacion]:
    pasos, conversacion = _platica(COMPLETA)
    return pasos[-1], conversacion


def _guarda(carpeta: Path, recorrido: tuple[Paso, Conversacion]) -> None:
    paso, conversacion = recorrido
    guardar(paso, conversacion, carpeta=carpeta, hoy=HOY)


def _guarda_perfil(carpeta: Path) -> None:
    perfil = PerfilGuardado(empresa=EMPRESA, guardado=HOY, limites=LIMITES)
    (carpeta / SLUG / ARCHIVO).write_text(perfil.model_dump_json(), encoding="utf-8")


def _linea(nota: NotaDeCash, clave: str) -> LineaDeLaNota:
    return next(linea for linea in nota.lineas if linea.clave == clave)


def _balance_con_cambio(destino: Path) -> tuple[str, str]:
    """Mueve 1,000,000 de «otros activos circulantes» a clientes (Dic-2025).

    Los totales no cambian, así que la revisión sigue cuadrando.
    """
    original = Path(COMPLETA[0]).read_text(encoding="utf-8")
    cambiado = original.replace(
        "Clientes | 5639601.55 |", "Clientes | 6639601.55 |"
    ).replace(
        "Otros activos circulantes | 2527257.34 |",
        "Otros activos circulantes | 1527257.34 |",
    )
    assert cambiado != original
    balance = destino / "aspel_balance.txt"
    balance.write_text(cambiado, encoding="utf-8")
    return str(balance), COMPLETA[1]


# ---------------------------------------------------------------------------
# La nota
# ---------------------------------------------------------------------------


def test_sin_recorrido_dice_sin_datos(tmp_path: Path) -> None:
    nota = nota_de_cash(tmp_path)
    assert nota.estado == "sin_datos"
    assert nota.nota is None
    assert nota.texto == SIN_RECORRIDO
    assert nota.lineas == ()


def test_numeros_de_mi_empresa_con_su_origen(
    tmp_path: Path, recorrido: tuple[Paso, Conversacion]
) -> None:
    _guarda(tmp_path, recorrido)
    nota = nota_de_cash(tmp_path)
    esperado = {
        "ciclo": "55.53",
        "dias_clientes": "46.97",
        "dias_inventario": "28.15",
        "dias_proveedores": "19.59",
        "flujo_neto": "-3705245.84",
    }
    for clave, valor in esperado.items():
        linea = _linea(nota, clave)
        assert linea.valor == Decimal(valor), clave
        assert linea.sale_de.startswith("sale de: "), clave
    assert "-3,705,245.84" in _linea(nota, "flujo_neto").texto
    assert "5,639,601.55" in _linea(nota, "dias_clientes").sale_de
    for linea in nota.lineas:
        assert linea.sale_de.startswith("sale de: "), linea.clave
    assert nota.empresa == SLUG
    assert nota.archivo is not None and nota.archivo.endswith(
        "estados-revisados-2026-01-31.json"
    )


def test_sin_perfil_valores_sin_color_y_sin_nota(
    tmp_path: Path, recorrido: tuple[Paso, Conversacion]
) -> None:
    _guarda(tmp_path, recorrido)
    nota = nota_de_cash(tmp_path)
    assert nota.estado == "sin_perfil"
    assert nota.nota is None
    assert "falta tu perfil ideal" in nota.texto
    assert all(linea.color is None for linea in nota.lineas)


def test_con_perfil_la_nota_cuenta_tus_verdes(
    tmp_path: Path, recorrido: tuple[Paso, Conversacion]
) -> None:
    _guarda(tmp_path, recorrido)
    _guarda_perfil(tmp_path)
    nota = nota_de_cash(tmp_path)
    assert nota.estado == "con_perfil"
    assert (nota.verdes, nota.pintados) == (3, 6)
    assert nota.nota == 50
    assert nota.status == "critical"  # proveedores está en rojo
    assert nota.sale_de is not None and "3 de 6" in nota.sale_de
    colores = {linea.clave: linea.color for linea in nota.lineas}
    assert colores == {
        "ciclo": None,
        "dias_clientes": "verde",
        "dias_inventario": "verde",
        "dias_proveedores": "rojo",
        "flujo_neto": None,
        "utilidad_bruta": "amarillo",
        "gastos": "amarillo",
        "utilidad_de_operacion": "verde",
    }


def test_cambiar_una_cuenta_cambia_la_nota(
    tmp_path: Path, recorrido: tuple[Paso, Conversacion]
) -> None:
    _guarda(tmp_path, recorrido)
    _guarda_perfil(tmp_path)
    antes = nota_de_cash(tmp_path)

    archivos = _balance_con_cambio(tmp_path)
    pasos, conversacion = _platica(archivos)
    # Mismo día: el recorrido guarda «-2» sin sobrescribir; la nota toma el más nuevo.
    guardar(pasos[-1], conversacion, carpeta=tmp_path, hoy=HOY)
    despues = nota_de_cash(tmp_path)

    assert despues.archivo is not None and despues.archivo.endswith(
        "estados-revisados-2026-01-31-2.json"
    )
    assert _linea(despues, "dias_clientes").valor == Decimal("55.30")
    assert _linea(despues, "dias_clientes").color == "amarillo"
    assert _linea(despues, "ciclo").valor != _linea(antes, "ciclo").valor
    assert (despues.verdes, despues.nota) == (2, 33)
    assert despues.nota != antes.nota


# ---------------------------------------------------------------------------
# El panel de control
# ---------------------------------------------------------------------------


def _panel(carpeta: Path) -> DashboardHandler:
    db = f"file:test_s86_36_{uuid.uuid4().hex[:8]}?mode=memory&cache=shared"
    return DashboardHandler(db_path=db, carpeta_cash=carpeta)


def test_panel_ignora_la_hoja_vieja_y_no_la_borra(tmp_path: Path) -> None:
    panel = _panel(tmp_path)
    vieja = {"financials": {"net_sales": 12000000, "cogs": 7200000}}
    panel.worksheets.save_worksheet("cash", "power-of-one", {"data": vieja})

    resumen = panel.summary()["data"]
    cash = resumen["decisions"]["cash"]
    assert cash["score"] is None
    assert cash["label"] == SIN_RECORRIDO
    # La hoja del dueño sigue en la base.
    guardada = panel.worksheets.get_worksheets("cash", "power-of-one")
    assert guardada["data"]["data"] == vieja
    assert isinstance(panel.worksheets, WorksheetsHandler)


def test_panel_con_recorrido_y_perfil(
    tmp_path: Path, recorrido: tuple[Paso, Conversacion]
) -> None:
    _guarda(tmp_path, recorrido)
    _guarda_perfil(tmp_path)
    cash = _panel(tmp_path).summary()["data"]["decisions"]["cash"]
    assert cash["score"] == 50
    assert cash["status"] == "critical"
    assert "3 de 6" in cash["label"]
    ciclo = next(linea for linea in cash["lineas"] if linea["clave"] == "ciclo")
    assert "55.53" in ciclo["texto"] and ciclo["sale_de"].startswith("sale de: ")


def test_panel_sin_perfil_no_inventa_nota(
    tmp_path: Path, recorrido: tuple[Paso, Conversacion]
) -> None:
    _guarda(tmp_path, recorrido)
    panel = _panel(tmp_path)
    # Estrategia con datos: el foco cae en Cash (el primero sin nota).
    panel.worksheets.save_worksheet("strategy", "opsp", {"purpose": "Servir"})
    resumen = panel.summary()["data"]
    cash = resumen["decisions"]["cash"]
    assert cash["score"] is None
    assert "falta tu perfil ideal" in cash["label"]
    assert all(linea["color"] is None for linea in cash["lineas"])
    # Sin nota, el foco manda a lo que falta, no a «Empieza por su worksheet».
    assert resumen["focus"]["decision"] == "cash"
    assert "falta tu perfil ideal" in resumen["focus"]["message"]
