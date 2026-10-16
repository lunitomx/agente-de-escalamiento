"""S86.21 — Panel «Tu perfil ideal»: 6 tarjetas verde / amarillo / rojo y la entrada.

La página no calcula ni decide colores: pinta lo que dio ``perfil.atender``.
"""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re

import pytest

from escala_server.cash.curso import BaseDeDias, EstadosRevisados
from escala_server.cash.panel_perfil import main, pagina
from escala_server.cash.perfil import (
    PasoDelPerfil,
    PlaticaDelPerfil,
    atender,
    porcentajes_de_un_peso,
    valores_del_perfil,
)
from escala_server.financial.lector import leer_estados
from escala_server.financial.revisiones import Respuestas, revisar_estados

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
HOY = date(2026, 1, 31)
EMPRESA = "Mi Empresa, S.A. de C.V."
GASTOS = "ideal 30, verde menos de 30, rojo más de 33"


@pytest.fixture(scope="module")
def mi_empresa() -> EstadosRevisados:
    resultados = leer_estados(ESTADOS / "aspel_resultados.txt", hoy=HOY)
    revision = revisar_estados(
        [leer_estados(ESTADOS / "aspel_balance.txt", hoy=HOY)],
        resultados,
        respuestas=Respuestas(periodo="acumulado del año"),
        hoy=HOY,
    )
    return EstadosRevisados(revision=revision, resultados=resultados)


@pytest.fixture(scope="module")
def paso(mi_empresa: EstadosRevisados) -> PasoDelPerfil:
    return atender(
        PlaticaDelPerfil(empresa=EMPRESA, respuestas={"curso": "sí", "gastos": GASTOS}),
        valores_del_perfil(mi_empresa, BaseDeDias()),
        porcentajes_de_un_peso(mi_empresa),
        guardado=None,
    )


def _tarjetas(html: str) -> dict[str, str]:
    return dict(
        re.findall(
            r'<section class="tarjeta [^"]*" id="([a-z_]+)">(.*?)</section>',
            html,
            flags=re.S,
        )
    )


def test_seis_tarjetas_con_su_color(paso: PasoDelPerfil) -> None:
    html = pagina(paso)
    encontrados = re.findall(r'<section class="tarjeta ([a-z]+)" id="([a-z_]+)">', html)
    colores = {clave: color for color, clave in encontrados}
    assert colores == {
        "utilidad_bruta": "amarillo",
        "gastos": "amarillo",
        "utilidad_de_operacion": "rojo",
        "dias_clientes": "rojo",
        "dias_inventario": "verde",
        "dias_proveedores": "rojo",
    }
    # El nivel va en texto, no sólo en color.
    assert (
        "amarillo · regular" in html
        and "rojo · malo" in html
        and "verde · óptimo" in html
    )


def test_cada_tarjeta_trae_valor_meta_distancia_y_origen(paso: PasoDelPerfil) -> None:
    tarjetas = _tarjetas(pagina(paso))
    assert len(tarjetas) == 6
    for clave, cuerpo in tarjetas.items():
        assert cuerpo.count("sale de:") >= 3, clave  # valor, meta y distancia
        assert "Tu ideal" in cuerpo, clave
        assert "verde:" in cuerpo and "rojo:" in cuerpo, clave
    proveedores = tarjetas["dias_proveedores"]
    assert "19.59 días" in proveedores
    assert "19.587" in proveedores  # el valor sin redondear que decide el color
    assert "malo" in proveedores
    assert "ejemplo del curso" in proveedores
    assert "47.60%" in tarjetas["utilidad_bruta"]
    assert "2.40 puntos debajo de tu ideal de 50%" in tarjetas["utilidad_bruta"]


def test_de_cada_peso_en_la_pagina(paso: PasoDelPerfil) -> None:
    html = pagina(paso)
    assert "De cada peso que vendes" in html
    for numero in ("52.40", "47.60", "30.62", "16.97", "11.45"):
        assert numero in html, numero
    assert "Lo fiscal lo ve tu contador." in html


def test_la_pagina_no_trae_scripts_que_calculen(paso: PasoDelPerfil) -> None:
    html = pagina(paso)
    for script in re.findall(r"<script[^>]*>", html):
        assert 'type="application/json"' in script


def test_sin_limites_no_hay_pagina(mi_empresa: EstadosRevisados) -> None:
    sin = atender(
        PlaticaDelPerfil(empresa=EMPRESA),
        valores_del_perfil(mi_empresa, BaseDeDias()),
        porcentajes_de_un_peso(mi_empresa),
        guardado=None,
    )
    with pytest.raises(ValueError):
        pagina(sin)


# ---------------------------------------------------------------------------
# La entrada: python -m escala_server.cash.panel_perfil
# ---------------------------------------------------------------------------


@pytest.fixture()
def estados_json(mi_empresa: EstadosRevisados, tmp_path: Path) -> Path:
    ruta = tmp_path / "estados-revisados.json"
    ruta.write_text(mi_empresa.model_dump_json(), encoding="utf-8")
    return ruta


def _corre(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, estados: Path, *extra: str
) -> tuple[int, dict[str, object]]:
    codigo = main(
        [
            "--empresa",
            EMPRESA,
            "--estados",
            str(estados),
            "--carpeta",
            str(tmp_path / "work" / "cash"),
            "--conversacion",
            str(tmp_path / "borrador.json"),
            "--hoy",
            HOY.isoformat(),
            *extra,
        ]
    )
    salida = json.loads(capsys.readouterr().out)
    assert isinstance(salida, dict)
    return codigo, salida  # type: ignore[return-value]


def test_entrada_sin_limites_pregunta_y_no_escribe_pagina(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, estados_json: Path
) -> None:
    html = tmp_path / "perfil.html"
    codigo, salida = _corre(capsys, tmp_path, estados_json, "--html", str(html))
    assert codigo == 0
    assert salida["pintar"] is False
    assert salida["preguntas"]
    assert not html.exists()
    assert not (tmp_path / "work").exists()


def test_entrada_sigue_la_platica_y_guarda_solo_con_si(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, estados_json: Path
) -> None:
    html = tmp_path / "perfil.html"
    _corre(capsys, tmp_path, estados_json, "--responde", "curso=sí")
    # Segundo mensaje: sólo gastos; lo demás viene del borrador.
    codigo, salida = _corre(
        capsys,
        tmp_path,
        estados_json,
        "--responde",
        f"gastos={GASTOS}",
        "--html",
        str(html),
        "--guardar",
        "no",
    )
    assert codigo == 0 and salida["pintar"] is True
    assert html.exists()
    assert salida["guardado"] is None
    assert not (tmp_path / "work").exists()
    codigo, salida = _corre(capsys, tmp_path, estados_json, "--guardar", "sí")
    guardado = (
        tmp_path / "work" / "cash" / "mi-empresa-s-a-de-c-v" / "perfil-ideal.json"
    )
    assert salida["guardado"] == guardado.as_posix()
    assert guardado.exists()
    assert "Guardé tus límites" in str(salida["mensaje"])
    # Otro día, sin borrador: pinta con lo guardado y no vuelve a preguntar.
    (tmp_path / "borrador.json").unlink()
    codigo, salida = _corre(capsys, tmp_path, estados_json)
    assert salida["pintar"] is True and salida["preguntas"] == []


def test_entrada_con_un_archivo_que_no_es_de_estados(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    malo = tmp_path / "otro.json"
    malo.write_text("{}", encoding="utf-8")
    codigo, salida = _corre(capsys, tmp_path, malo)
    assert codigo == 2
    assert "no_calculable" in salida
