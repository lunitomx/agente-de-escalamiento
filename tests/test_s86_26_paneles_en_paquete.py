"""S86.26 — Los paneles viajan en los paquetes y corren desde adentro.

Construye el Agent Plugin y el paquete de Codex y corre, con ``python -I``,
el escenario hasta la fase 7 de 8 y el guardado con «sí» (escribe las páginas
de los paneles), y la plática de los límites del perfil (``calcular.py perfil``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.test_s86_17_escenario_en_paquete import (
    ESTADOS,
    RESPUESTAS,
    _agent_plugin,
    _codex,
    _corre,
)
from validators.door_bundle import CALCULATOR_LAUNCHER, door_bundle

PANELES = (
    "escala_server/cash/archivos.py",
    "escala_server/cash/recorrido.py",
    "escala_server/cash/panel_decision.py",
    "escala_server/cash/contabilidad.py",
    "escala_server/cash/panel_dias.py",
    "escala_server/cash/flujo.py",
    "escala_server/cash/perfil.py",
    "escala_server/cash/panel_perfil.py",
    "escala_server/cash/simulador.py",
    "escala_server/cash/simulador.js",
)


def test_el_paquete_lleva_los_paneles() -> None:
    paquete = door_bundle()
    for modulo in PANELES:
        assert f"references/calculadora/{modulo}" in paquete, modulo


@pytest.mark.parametrize(
    "construir", [_agent_plugin, _codex], ids=["agent-plugin", "codex"]
)
def test_el_recorrido_corre_dentro_del_paquete(tmp_path: Path, construir: Any) -> None:
    puerta: Path = construir(tmp_path)
    lanzador = puerta / CALCULATOR_LAUNCHER
    afuera = tmp_path / "carpeta-del-negocio"
    afuera.mkdir()
    cash = afuera / "work" / "cash"

    argumentos = [
        "escenario",
        "--empresa",
        "Mi Empresa",
        "--archivo",
        str(ESTADOS / "aspel_balance.txt"),
        "--archivo",
        str(ESTADOS / "aspel_resultados.txt"),
        "--carpeta",
        str(cash),
        "--conversacion",
        str(afuera / "borrador.json"),
        "--hoy",
        "2026-01-31",
    ]
    for respuesta in (*RESPUESTAS, "C6=no", "tasa_iva=16"):
        argumentos += ["--responde", respuesta]

    corrida = _corre(lanzador, *argumentos, "--guardar", "sí", cwd=afuera)
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    datos: dict[str, Any] = json.loads(corrida.stdout)
    assert datos["fase"] == 7
    assert "Vamos en la fase 7 de 8" in datos["mensaje"]
    paneles = {p["clave"]: p for p in datos["paneles"]}
    assert "40.49" in paneles["dias"]["titular"]
    assert "26.60%" in paneles["precio_volumen"]["titular"]
    paginas = sorted(p.name for p in (cash / "mi-empresa").glob("panel-*.html"))
    assert paginas == [
        "panel-contabilidad-2026-01-31.html",
        "panel-dias-2026-01-31.html",
        "panel-flujo-2026-01-31.html",
        "panel-margen-2026-01-31.html",
        "panel-precio_volumen-2026-01-31.html",
        "panel-simulador-2026-01-31.html",
    ]

    # La plática de los límites, con los estados que el dueño guardó.
    estados = cash / "mi-empresa" / "estados-revisados-2026-01-31.json"
    perfil = _corre(
        lanzador,
        "perfil",
        "--empresa",
        "Mi Empresa",
        "--estados",
        str(estados),
        "--carpeta",
        str(cash),
        "--conversacion",
        str(afuera / "perfil.json"),
        cwd=afuera,
    )
    assert perfil.returncode == 0, perfil.stdout + perfil.stderr
    assert json.loads(perfil.stdout)["preguntas"]  # sin límites, primero pregunta

    verifica = _corre(lanzador, "--verifica", cwd=afuera)
    modulos: dict[str, str] = json.loads(verifica.stdout)["modulos"]
    assert "escala_server.cash.recorrido" in modulos
    for nombre, ruta in modulos.items():
        assert Path(ruta).resolve().is_relative_to(puerta.resolve()), (nombre, ruta)
