"""S86.33 — El tablero viejo del poder del uno ya no está en el programa local.

El tablero `static/dashboards/cash/power-of-one.html` sumaba flujo + utilidad
por palanca (el error que S86.13 corrigió). El poder del uno vive en el
simulador del recorrido de cash (S86.22 + S86.26). Quien abre la ruta vieja ve
un aviso corto en español, sin números.
"""

from __future__ import annotations

import re
import subprocess
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "escala_server" / "static"
CASH_DASHBOARDS = STATIC / "dashboards" / "cash"
RUTA_VIEJA = "/dashboards/cash/power-of-one.html"


def _texto_visible(html: str) -> str:
    sin_estilo = re.sub(r"<style.*?</style>", "", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", sin_estilo)


def test_el_tablero_viejo_no_vuelve() -> None:
    assert not (CASH_DASHBOARDS / "power-of-one.html").exists()
    assert not list(STATIC.rglob("power-of-one*"))


def test_los_otros_tableros_de_cash_siguen() -> None:
    for nombre in ("cash-board", "ccc", "fundability", "recurring-revenue"):
        assert (CASH_DASHBOARDS / f"{nombre}.html").is_file()


def test_la_ruta_del_tablero_ya_no_existe() -> None:
    from escala_server.server import _build_router  # pyright: ignore[reportPrivateUsage]

    fn, _ = _build_router().dispatch("POST", "/api/cash/power-of-one")
    assert fn is None


def test_el_panel_de_control_no_ofrece_el_tablero() -> None:
    index = (STATIC / "index.html").read_text(encoding="utf-8")
    assert "'Power of One'" not in index
    assert "'Cash Board'" in index
    panel = (STATIC / "shared" / "js" / "context-panel.js").read_text(encoding="utf-8")
    assert "power-of-one" not in panel
    assert "'recurring-revenue': 'cash'" in panel


def test_el_aviso_manda_al_recorrido_de_cash_sin_numeros() -> None:
    from escala_server.retirados import pagina_retirada

    html = pagina_retirada(RUTA_VIEJA)
    assert html is not None
    texto = _texto_visible(html)
    assert "recorrido de cash" in texto
    assert "simulador" in texto
    assert "/escala-cash" in texto
    assert not re.search(r"\d", texto), texto
    assert "<script" not in html
    assert "/api/" not in html
    assert '<html lang="es">' in html


def test_otra_ruta_no_es_un_aviso() -> None:
    from escala_server.retirados import pagina_retirada

    assert pagina_retirada("/dashboards/cash/ccc.html") is None
    assert pagina_retirada("/index.html") is None


@pytest.fixture()
def servidor(tmp_path: Path) -> Iterator[str]:
    from escala_server.server import make_server

    server = make_server(
        host="127.0.0.1",
        port=0,
        static_root=str(STATIC),
        db_path=str(tmp_path / "escala.db"),
    )
    hilo = threading.Thread(target=server.serve_forever, daemon=True)
    hilo.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def test_abrir_la_ruta_vieja_da_el_aviso_y_no_un_404(servidor: str) -> None:
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(servidor + RUTA_VIEJA, timeout=5)
    respuesta = error.value
    assert respuesta.code == 410
    assert respuesta.headers["Content-Type"].startswith("text/html")
    assert "recorrido de cash" in respuesta.read().decode("utf-8")


def test_otro_tablero_de_cash_se_sirve_igual(servidor: str) -> None:
    with urllib.request.urlopen(
        servidor + "/dashboards/cash/ccc.html", timeout=5
    ) as respuesta:
        assert respuesta.status == 200


def test_nada_fuera_de_work_manda_al_tablero_ni_a_su_ruta() -> None:
    salida = subprocess.run(
        [
            "git",
            "grep",
            "-n",
            "-e",
            "dashboards/cash/power-of-one",
            "-e",
            "api/cash/power-of-one",
            "--",
            ".",
            ":!work",
            ":!escala_server/data",
            ":!tests/test_s86_33_sin_tablero_viejo.py",
            ":!escala_server/retirados.py",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert salida.stdout == ""


def test_los_procedimientos_mandan_al_simulador() -> None:
    skills = ROOT / "escala-skills"
    power1 = (skills / "escala-cash-power1" / "SKILL.md").read_text(encoding="utf-8")
    assert "panel-simulador-" in power1
    aceleracion = (skills / "escala-cash-acceleration" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "work/cash/power-of-one.md" not in aceleracion
    assert "panel-simulador-" in aceleracion
