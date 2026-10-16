"""S86.17 — Nada se guarda sin «sí», y el dueño puede seguir otro día.

La plática (rutas y respuestas, nunca cifras) vive en un archivo de trabajo
fuera de la carpeta del dueño. Sólo con «sí» se escribe en
``work/cash/<empresa>/``: la plática para seguir otro día y, si ya hay cálculo,
``estados-revisados-<fecha>.json``, que la calculadora lee igual.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from escala_server.cash import curso, escenario

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
EMPRESA = "Mi Empresa, S.A. de C.V."
SLUG = "mi-empresa-s-a-de-c-v"
HOY = "2026-01-31"
COMPLETA = (ESTADOS / "aspel_balance.txt", ESTADOS / "aspel_resultados.txt")
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


def _corre(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    *extra: str,
    archivos: tuple[Path, ...] = (),
    respuestas: tuple[str, ...] = (),
    conversacion: str = "platica.json",
) -> dict[str, Any]:
    argv = [
        "--empresa",
        EMPRESA,
        "--carpeta",
        str(tmp_path / "work" / "cash"),
        "--conversacion",
        str(tmp_path / "trabajo" / conversacion),
        "--hoy",
        HOY,
    ]
    for archivo in archivos:
        argv += ["--archivo", str(archivo)]
    for respuesta in respuestas:
        argv += ["--responde", respuesta]
    argv += list(extra)
    assert escenario.main(argv) == 0
    salida: dict[str, Any] = json.loads(capsys.readouterr().out)
    return salida


def _del_dueno(tmp_path: Path) -> list[str]:
    carpeta = tmp_path / "work" / "cash" / SLUG
    return sorted(p.name for p in carpeta.iterdir()) if carpeta.exists() else []


def test_sin_si_no_escribe_nada(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    salida = _corre(capsys, tmp_path, archivos=COMPLETA, respuestas=RESPUESTAS)
    assert salida["calculo"] is not None
    assert salida["guardado"] == []
    assert _del_dueno(tmp_path) == []


@pytest.mark.parametrize("respuesta", ["no", "ok", "luego", "si quieres"])
def test_otra_respuesta_no_escribe_nada(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, respuesta: str
) -> None:
    salida = _corre(
        capsys, tmp_path, "--guardar", respuesta, archivos=COMPLETA, respuestas=RESPUESTAS
    )
    assert salida["guardado"] == []
    assert _del_dueno(tmp_path) == []


def test_con_si_guarda_y_la_calculadora_lo_lee_igual(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    salida = _corre(capsys, tmp_path, "--guardar", "sí", archivos=COMPLETA, respuestas=RESPUESTAS)
    assert _del_dueno(tmp_path) == ["conversacion.json", "estados-revisados-2026-01-31.json"]
    assert len(salida["guardado"]) == 2
    assert "Guardé" in salida["mensaje"]
    assert "¿Guardo" not in salida["mensaje"]

    revisados = tmp_path / "work" / "cash" / SLUG / "estados-revisados-2026-01-31.json"
    assert curso.main([str(revisados)]) == 0
    calculo = json.loads(capsys.readouterr().out)
    assert calculo == salida["calculo"]
    capital = next(
        i for i in calculo["indicadores"] if i["clave"] == "capital_de_trabajo" and i["fecha"] == "2025-12-31"
    )
    assert Decimal(capital["valor"]) == Decimal("6178173.85")


def test_la_platica_guardada_no_trae_cifras(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    _corre(capsys, tmp_path, "--guardar", "sí", archivos=COMPLETA, respuestas=RESPUESTAS)
    platica = json.loads((tmp_path / "work" / "cash" / SLUG / "conversacion.json").read_text())
    assert set(platica) == {"empresa", "archivos", "respuestas"}
    assert "6178173.85" not in json.dumps(platica)


def test_nunca_sobrescribe(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    _corre(capsys, tmp_path, "--guardar", "sí", archivos=COMPLETA, respuestas=RESPUESTAS)
    _corre(capsys, tmp_path, "--guardar", "sí")
    assert "estados-revisados-2026-01-31-2.json" in _del_dueno(tmp_path)


def test_sin_calculo_el_si_solo_guarda_la_platica(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    salida = _corre(capsys, tmp_path, "--guardar", "sí", archivos=COMPLETA)
    assert salida["calculo"] is None
    assert _del_dueno(tmp_path) == ["conversacion.json"]


def test_seguir_otro_dia(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    """Otro día el archivo de trabajo ya no está; sigue desde lo que guardó con «sí»."""

    _corre(capsys, tmp_path, "--guardar", "sí", archivos=COMPLETA, respuestas=RESPUESTAS[:3])
    salida = _corre(capsys, tmp_path, conversacion="otro-dia.json")
    claves = [p["clave"] for p in salida["preguntas"]]
    assert "C10" not in claves
    assert claves[0] == "C11:Documentos por pagar a largo plazo"


def test_la_platica_sigue_entre_mensajes(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    _corre(capsys, tmp_path, archivos=COMPLETA, respuestas=RESPUESTAS[:5])
    salida = _corre(capsys, tmp_path, respuestas=RESPUESTAS[5:])
    assert salida["calculo"] is not None
    assert _del_dueno(tmp_path) == []
