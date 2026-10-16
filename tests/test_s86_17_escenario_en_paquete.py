"""S86.17 — El escenario viaja en los paquetes y corre desde adentro.

Construye el Agent Plugin y el adaptador de Codex en una carpeta temporal y
corre ``calcular.py escenario`` desde ahí, con ``python -I``, como lo hará el
procedimiento de la puerta.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from adapters.agent_plugins.build_plugin import build_agent_plugin
from adapters.codex.build_adapter import build_codex_adapter
from validators.door_bundle import CALCULATOR_LAUNCHER, door_bundle

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
CATALOG = ROOT / "capabilities" / "mvp" / "catalog.json"
RESPUESTAS = (
    "C10=acumulado del año",
    "suma:gastos_operacion:2025-12-31=sí",
    "suma:gastos_operacion:2024-12-31=sí",
    "C11:Documentos por pagar a largo plazo=no",
    "C9=sí",
    "C1=no sé",
    "C4=2,966,528.27",
    "C3=no sé",
    "C2=todas",
)


def _agent_plugin(tmp_path: Path) -> Path:
    raiz = tmp_path / "artifacts"
    raiz.mkdir()
    return build_agent_plugin(output=raiz / "escala-agent-plugin", allowed_root=raiz) / "skills" / "escala"


def _codex(tmp_path: Path) -> Path:
    raiz = tmp_path / "codex-install"
    raiz.mkdir()
    paquete = build_codex_adapter(catalog_path=CATALOG, output=raiz / "codex", allowed_root=raiz)
    return paquete / "skills" / "escala"


def _corre(lanzador: Path, *argumentos: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(lanzador), *argumentos],
        capture_output=True,
        text=True,
        cwd=cwd,
        check=False,
    )


def test_el_paquete_lleva_el_escenario() -> None:
    assert "references/calculadora/escala_server/cash/escenario.py" in door_bundle()


@pytest.mark.parametrize("construir", [_agent_plugin, _codex], ids=["agent-plugin", "codex"])
def test_el_escenario_corre_dentro_del_paquete(tmp_path: Path, construir: Any) -> None:
    puerta: Path = construir(tmp_path)
    lanzador = puerta / CALCULATOR_LAUNCHER
    afuera = tmp_path / "carpeta-del-negocio"
    afuera.mkdir()

    verifica = _corre(lanzador, "--verifica", cwd=afuera)
    assert verifica.returncode == 0, verifica.stdout + verifica.stderr
    modulos: dict[str, str] = json.loads(verifica.stdout)["modulos"]
    assert "escala_server.cash.escenario" in modulos
    for nombre, ruta in modulos.items():
        assert Path(ruta).resolve().is_relative_to(puerta.resolve()), (nombre, ruta)

    argumentos = [
        "escenario",
        "--empresa",
        "Mi Empresa",
        "--archivo",
        str(ESTADOS / "aspel_balance.txt"),
        "--archivo",
        str(ESTADOS / "aspel_resultados.txt"),
        "--carpeta",
        str(afuera / "work" / "cash"),
        "--conversacion",
        str(afuera / "borrador.json"),
        "--hoy",
        "2026-01-31",
    ]
    for respuesta in RESPUESTAS:
        argumentos += ["--responde", respuesta]

    primero = _corre(lanzador, *argumentos, cwd=afuera)
    assert primero.returncode == 0, primero.stdout + primero.stderr
    datos: dict[str, Any] = json.loads(primero.stdout)
    assert datos["anuncio"].startswith("Con esto voy a calcular")
    resumen = {linea["clave"]: linea for linea in datos["resumen"]}
    assert Decimal(resumen["capital_de_trabajo"]["valor"]) == Decimal("6178173.85")
    assert Decimal(resumen["flujo_neto"]["valor"]) == Decimal("-3705245.84")
    assert not (afuera / "work").exists()  # sin «sí», nada

    texto = _corre(lanzador, *argumentos[:13], "--formato", "texto", "--guardar", "sí", cwd=afuera)
    assert texto.returncode == 0, texto.stdout + texto.stderr
    assert "6,178,173.85" in texto.stdout
    guardados = sorted(p.name for p in (afuera / "work" / "cash" / "mi-empresa").iterdir())
    assert guardados == ["conversacion.json", "estados-revisados-2026-01-31.json"]
