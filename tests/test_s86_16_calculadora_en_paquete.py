"""S86.16 — La calculadora viaja con ESCALA y se corre desde adentro del paquete.

La prueba de aceptación construye el Agent Plugin y el adaptador de Codex en una
carpeta temporal y corre la calculadora desde ahí, con ``python -I`` para que no
use la copia del repositorio. Si falta Python o pydantic, la calculadora lo dice
y no calcula.
"""

from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from adapters.agent_plugins.build_plugin import build_agent_plugin
from adapters.codex.build_adapter import build_codex_adapter
from escala_server.cash import calcular
from escala_server.cash.curso import EstadosRevisados
from escala_server.financial.lector import leer_estados
from escala_server.financial.revisiones import Respuestas, revisar_estados
from validators.door_bundle import (
    CALCULATOR_LAUNCHER,
    DoorBundleError,
    door_bundle,
    door_bundle_paths,
    validate_door_bundle,
)

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
CATALOG = ROOT / "capabilities" / "mvp" / "catalog.json"


def _estados(tmp_path: Path) -> Path:
    from datetime import date

    hoy = date(2026, 1, 31)
    resultados = leer_estados(ESTADOS / "aspel_resultados.txt", hoy=hoy)
    revision = revisar_estados(
        [leer_estados(ESTADOS / "aspel_balance.txt", hoy=hoy)],
        resultados,
        respuestas=Respuestas(periodo="acumulado del año"),
        hoy=hoy,
    )
    archivo = tmp_path / "estados-revisados.json"
    archivo.write_text(
        EstadosRevisados(revision=revision, resultados=resultados).model_dump_json(),
        encoding="utf-8",
    )
    return archivo


def _agent_plugin(tmp_path: Path) -> Path:
    raiz = tmp_path / "artifacts"
    raiz.mkdir()
    paquete = build_agent_plugin(output=raiz / "escala-agent-plugin", allowed_root=raiz)
    return paquete / "skills" / "escala"


def _codex(tmp_path: Path) -> Path:
    raiz = tmp_path / "codex-install"
    raiz.mkdir()
    paquete = build_codex_adapter(
        catalog_path=CATALOG, output=raiz / "codex", allowed_root=raiz
    )
    return paquete / "skills" / "escala"


def _corre(
    lanzador: Path, *argumentos: str, cwd: Path, extra: tuple[str, ...] = ()
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", *extra, str(lanzador), *argumentos],
        capture_output=True,
        text=True,
        cwd=cwd,
        check=False,
    )


def _indicador(
    datos: dict[str, Any], clave: str, fecha: str = "2025-12-31"
) -> dict[str, Any]:
    return next(
        i for i in datos["indicadores"] if i["clave"] == clave and i["fecha"] == fecha
    )


@pytest.mark.parametrize(
    "construir", [_agent_plugin, _codex], ids=["agent-plugin", "codex"]
)
def test_la_calculadora_corre_dentro_del_paquete(
    tmp_path: Path, construir: Any
) -> None:
    puerta: Path = construir(tmp_path)
    lanzador = puerta / CALCULATOR_LAUNCHER
    assert lanzador.is_file()
    archivo = _estados(tmp_path)
    afuera = tmp_path / "carpeta-del-negocio"
    afuera.mkdir()

    verifica = _corre(lanzador, "--verifica", cwd=afuera)
    assert verifica.returncode == 0, verifica.stdout + verifica.stderr
    info = json.loads(verifica.stdout)
    # Todo módulo de ESCALA cargado viene del paquete, no de la copia del repo.
    assert info["modulos"]
    for nombre, ruta in info["modulos"].items():
        assert Path(ruta).resolve().is_relative_to(puerta.resolve()), (nombre, ruta)

    salida = _corre(lanzador, str(archivo), cwd=afuera)
    assert salida.returncode == 0, salida.stdout + salida.stderr
    datos = json.loads(salida.stdout)
    assert Decimal(_indicador(datos, "dias_clientes")["valor"]) == Decimal("46.97")
    assert Decimal(_indicador(datos, "flujo_neto")["valor"]) == Decimal("-3705245.84")
    assert Decimal(_indicador(datos, "flujo_de_operacion")["valor"]) == Decimal(
        "4835206.16"
    )
    assert Decimal(datos["poder_del_uno_flujo"]["valor"]) == Decimal("1143864.91")


def test_sin_pydantic_no_calcula_y_lo_dice(tmp_path: Path) -> None:
    puerta = _agent_plugin(tmp_path)
    # -S: sin site-packages, como una computadora con Python pero sin pydantic.
    salida = _corre(
        puerta / CALCULATOR_LAUNCHER,
        str(_estados(tmp_path)),
        cwd=tmp_path,
        extra=("-S",),
    )
    assert salida.returncode != 0
    datos = json.loads(salida.stdout)
    assert set(datos) == {"no_calculable"}
    assert "No voy a hacer las cuentas de memoria" in datos["no_calculable"]


def test_python_viejo_no_calcula() -> None:
    falta = calcular.revisar_python((3, 9, 1))
    assert falta is not None and "Python 3.9" in falta
    assert calcular.revisar_python((3, 10, 0)) is None


def test_en_la_copia_del_repo_tambien_corre(tmp_path: Path) -> None:
    salida = _corre(
        ROOT / "escala_server" / "cash" / "calcular.py",
        str(_estados(tmp_path)),
        cwd=tmp_path,
    )
    assert salida.returncode == 0, salida.stderr
    assert Decimal(_indicador(json.loads(salida.stdout), "ciclo")["valor"]) == Decimal(
        "55.53"
    )


def test_el_paquete_lleva_la_calculadora_byte_a_byte(tmp_path: Path) -> None:
    bundle = door_bundle()
    assert CALCULATOR_LAUNCHER in bundle
    assert "references/calculadora/escala_server/cash/curso.py" in bundle
    assert "references/calculadora/escala_server/financial/revisiones.py" in bundle
    assert {
        "references/calculadora",
        "references/calculadora/escala_server",
        "references/calculadora/escala_server/cash",
    } <= door_bundle_paths()
    puerta = _agent_plugin(tmp_path)
    validate_door_bundle(puerta)
    curso = puerta / "references/calculadora/escala_server/cash/curso.py"
    curso.write_text(
        curso.read_text(encoding="utf-8") + "\n# cambio\n", encoding="utf-8"
    )
    with pytest.raises(DoorBundleError, match="door_bundle_drift"):
        validate_door_bundle(puerta)
