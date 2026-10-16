"""S86.17 — El borrador de la plática es privado del usuario.

Entre mensajes, la plática (rutas y respuestas del dueño, que pueden traer
cantidades como sus retiros) vive en ``~/.escala/borradores/``: carpeta 0o700,
archivo 0o600, escrito de forma atómica y sin seguir enlaces simbólicos. No vive
en la carpeta temporal compartida, que además se borra al reiniciar.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import tempfile

import pytest

from escala_server.cash import escenario

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
EMPRESA = "Mi Empresa, S.A. de C.V."
SLUG = "mi-empresa-s-a-de-c-v"


def _corre(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, *extra: str
) -> tuple[int, dict[str, object]]:
    argv = [
        "--empresa",
        EMPRESA,
        "--carpeta",
        str(tmp_path / "work" / "cash"),
        "--hoy",
        "2026-01-31",
        *extra,
    ]
    codigo = escenario.main(argv)
    salida: dict[str, object] = json.loads(capsys.readouterr().out)
    return codigo, salida


@pytest.fixture
def casa(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    casa = tmp_path / "casa"
    casa.mkdir()
    monkeypatch.setenv("HOME", str(casa))
    return casa


def test_la_ruta_no_esta_en_el_tmp_compartido() -> None:
    ruta = escenario.ruta_del_borrador(EMPRESA)
    assert ruta == Path.home() / ".escala" / "borradores" / f"{SLUG}.json"
    assert not ruta.is_relative_to(Path(tempfile.gettempdir()))
    assert not ruta.is_relative_to(Path("/tmp"))


def test_permisos_del_borrador(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, casa: Path
) -> None:
    codigo, _ = _corre(capsys, tmp_path, "--archivo", str(ESTADOS / "aspel_balance.txt"))
    assert codigo == 0
    borrador = casa / ".escala" / "borradores" / f"{SLUG}.json"
    assert stat.S_IMODE(borrador.stat().st_mode) == 0o600
    assert stat.S_IMODE(borrador.parent.stat().st_mode) == 0o700
    assert [p.name for p in borrador.parent.iterdir()] == [borrador.name]  # sin temporales


def test_la_platica_sigue_en_el_borrador(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, casa: Path
) -> None:
    _corre(capsys, tmp_path, "--archivo", str(ESTADOS / "aspel_balance.txt"), "--responde", "C9=sí")
    _, salida = _corre(capsys, tmp_path)
    assert all(p["clave"] != "C9" for p in salida["preguntas"])  # type: ignore[index, union-attr]
    assert not (tmp_path / "work" / "cash" / SLUG).exists()  # sin «sí», nada en work/cash


def test_no_sigue_enlaces_simbolicos(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, casa: Path
) -> None:
    carpeta = casa / ".escala" / "borradores"
    carpeta.mkdir(parents=True)
    victima = tmp_path / "victima.txt"
    victima.write_text("no me toques", encoding="utf-8")
    os.symlink(victima, carpeta / f"{SLUG}.json")
    codigo, salida = _corre(capsys, tmp_path, "--archivo", str(ESTADOS / "aspel_balance.txt"))
    assert codigo != 0
    assert "enlace" in str(salida["no_calculable"])
    assert victima.read_text(encoding="utf-8") == "no me toques"


def test_corrige_permisos_de_una_carpeta_abierta(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, casa: Path
) -> None:
    carpeta = casa / ".escala" / "borradores"
    carpeta.mkdir(parents=True, mode=0o777)
    carpeta.chmod(0o777)
    _corre(capsys, tmp_path, "--archivo", str(ESTADOS / "aspel_balance.txt"))
    assert stat.S_IMODE(carpeta.stat().st_mode) == 0o700
