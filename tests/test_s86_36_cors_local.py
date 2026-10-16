"""S86.36 — Seguridad: sólo el propio servidor local lee el panel.

El panel ya devuelve los números reales del dueño (``/api/dashboard/summary``).
Con ``Access-Control-Allow-Origin: *``, cualquier página que el dueño abra en
su navegador podía leerlos desde ``localhost:8080``. Ahora la cabecera sólo se
manda a ``http://localhost:<puerto>`` y ``http://127.0.0.1:<puerto>``.
Ejemplo: una petición con ``Origin: https://ejemplo-malo.com`` no la recibe.

Quitar «*» no basta contra el «DNS rebinding»: una página de ataque hace que su
propio dominio apunte a 127.0.0.1 y, para el navegador, es el mismo origen.
Por eso el servidor también revisa la cabecera ``Host`` en toda petición:
``Host: malo.ejemplo.com`` recibe 403 sin datos. Y un POST/PATCH/DELETE con un
``Origin`` que no es el propio servidor local también recibe 403.
"""

from __future__ import annotations

from collections.abc import Iterator
from http.server import HTTPServer
from pathlib import Path
import json
import threading
import urllib.error
import urllib.request

import pytest

from escala_server.cors import CORSHandler, anfitrion_local
from escala_server.server import make_server

STATIC = Path(__file__).resolve().parents[1] / "escala_server" / "static"
MALO = "https://ejemplo-malo.com"


@pytest.fixture()
def servidor(tmp_path: Path) -> Iterator[int]:
    # Los manejadores de SQLite sólo sirven en el hilo que los creó:
    # el servidor se arma en el mismo hilo que atiende, como en ``escala start``.
    listo = threading.Event()
    servidores: list[HTTPServer] = []

    def atiende() -> None:
        server = make_server(
            host="127.0.0.1",
            port=0,
            static_root=str(STATIC),
            db_path=str(tmp_path / "escala.db"),
        )
        servidores.append(server)
        listo.set()
        server.serve_forever()

    hilo = threading.Thread(target=atiende, daemon=True)
    hilo.start()
    assert listo.wait(10)
    server = servidores[0]
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()


def _pide(puerto: int, ruta: str, origen: str | None, metodo: str = "GET"):
    peticion = urllib.request.Request(f"http://127.0.0.1:{puerto}{ruta}", method=metodo)
    if origen is not None:
        peticion.add_header("Origin", origen)
    return urllib.request.urlopen(peticion, timeout=5)


def test_pagina_ajena_no_lee_el_panel(servidor: int) -> None:
    with _pide(servidor, "/api/dashboard/summary", MALO) as respuesta:
        assert respuesta.status == 200
        assert respuesta.headers["Access-Control-Allow-Origin"] is None


def test_preflight_ajeno_no_recibe_permiso(servidor: int) -> None:
    with _pide(servidor, "/api/dashboard/summary", MALO, "OPTIONS") as respuesta:
        assert respuesta.headers["Access-Control-Allow-Origin"] is None


@pytest.mark.parametrize("anfitrion", ["localhost", "127.0.0.1"])
def test_el_propio_servidor_local_si(servidor: int, anfitrion: str) -> None:
    origen = f"http://{anfitrion}:{servidor}"
    with _pide(servidor, "/api/dashboard/summary", origen) as respuesta:
        assert respuesta.headers["Access-Control-Allow-Origin"] == origen
        assert "Origin" in (respuesta.headers["Vary"] or "")


def test_otro_puerto_local_tampoco(servidor: int) -> None:
    origen = f"http://localhost:{servidor + 1}"
    with _pide(servidor, "/api/dashboard/summary", origen) as respuesta:
        assert respuesta.headers["Access-Control-Allow-Origin"] is None


def test_mismo_origen_sin_cabecera_funciona(servidor: int) -> None:
    with _pide(servidor, "/api/dashboard/summary", None) as respuesta:
        assert respuesta.status == 200
        assert respuesta.headers["Access-Control-Allow-Origin"] is None
    with _pide(servidor, "/index.html", None) as respuesta:
        assert respuesta.status == 200


@pytest.mark.parametrize(
    "origen", [None, "", "null", "*", MALO, "http://localhost", "http://127.0.0.1"]
)
def test_nunca_comodin_ni_origen_ajeno(origen: str | None) -> None:
    cabeceras = CORSHandler.get_headers(origen, 8080)
    assert cabeceras.get("Access-Control-Allow-Origin") is None
    assert "*" not in cabeceras.values()


def test_el_servidor_escucha_solo_en_la_maquina(tmp_path: Path) -> None:
    server = make_server(port=0, db_path=str(tmp_path / "escala.db"))
    try:
        assert server.server_address[0] == "127.0.0.1"
    finally:
        server.server_close()


# ---------------------------------------------------------------------------
# DNS rebinding: la cabecera Host y el Origin de los cambios
# ---------------------------------------------------------------------------


def _con_host(
    puerto: int,
    ruta: str,
    host: str,
    metodo: str = "GET",
    origen: str | None = None,
    cuerpo: bytes | None = None,
):
    peticion = urllib.request.Request(
        f"http://127.0.0.1:{puerto}{ruta}", data=cuerpo, method=metodo
    )
    peticion.add_header("Host", host)
    if origen is not None:
        peticion.add_header("Origin", origen)
    if cuerpo is not None:
        peticion.add_header("Content-Type", "application/json")
    return urllib.request.urlopen(peticion, timeout=5)


def _rechazo(error: urllib.error.HTTPError) -> str:
    assert error.code == 403
    texto = error.read().decode("utf-8")
    assert "dashboard" not in texto and "decisions" not in texto
    return texto


@pytest.mark.parametrize("ruta", ["/api/dashboard/summary", "/index.html"])
def test_host_ajeno_recibe_403_sin_datos(servidor: int, ruta: str) -> None:
    with pytest.raises(urllib.error.HTTPError) as error:
        _con_host(servidor, ruta, "malo.ejemplo.com")
    assert "local" in _rechazo(error.value)


def test_host_ajeno_con_puerto_tambien(servidor: int) -> None:
    with pytest.raises(urllib.error.HTTPError) as error:
        _con_host(servidor, "/api/dashboard/summary", f"malo.ejemplo.com:{servidor}")
    _rechazo(error.value)


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "[::1]"])
def test_host_local_con_y_sin_puerto(servidor: int, host: str) -> None:
    for valor in (host, f"{host}:{servidor}"):
        with _con_host(servidor, "/api/dashboard/summary", valor) as respuesta:
            assert respuesta.status == 200
        with _con_host(servidor, "/index.html", valor) as respuesta:
            assert respuesta.status == 200


def test_post_con_origin_ajeno_recibe_403(servidor: int) -> None:
    cuerpo = json.dumps({"name": "Ataque"}).encode("utf-8")
    with pytest.raises(urllib.error.HTTPError) as error:
        _con_host(
            servidor,
            "/api/companies",
            f"localhost:{servidor}",
            metodo="POST",
            origen=MALO,
            cuerpo=cuerpo,
        )
    _rechazo(error.value)


def test_post_con_origin_local_si_pasa(servidor: int) -> None:
    cuerpo = json.dumps({"name": "Mi Empresa"}).encode("utf-8")
    with _con_host(
        servidor,
        "/api/companies",
        f"localhost:{servidor}",
        metodo="POST",
        origen=f"http://localhost:{servidor}",
        cuerpo=cuerpo,
    ) as respuesta:
        assert respuesta.status == 200


@pytest.mark.parametrize(
    ("host", "local"),
    [
        ("localhost", True),
        ("localhost:8080", True),
        ("127.0.0.1:8080", True),
        ("[::1]", True),
        ("[::1]:8080", True),
        ("LOCALHOST:8080", True),
        (None, False),
        ("", False),
        ("malo.ejemplo.com", False),
        ("localhost.malo.ejemplo.com", False),
        ("127.0.0.1.nip.io", False),
        ("malo@localhost", False),
        ("localhost:80:80", False),
        ("localhost:abc", False),
        ("::1", False),
    ],
)
def test_anfitrion_local(host: str | None, local: bool) -> None:
    assert anfitrion_local(host) is local
