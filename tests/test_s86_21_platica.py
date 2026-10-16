"""S86.21 — La plática del perfil: ESCALA pregunta antes de pintar y guarda sólo con «sí»."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from escala_server.cash.curso import BaseDeDias, EstadosRevisados
from escala_server.cash.perfil import (
    CONTRADICCION_GASTOS_B,
    INDICADORES,
    DeUnPeso,
    PerfilGuardado,
    PlaticaDelPerfil,
    ValorOSin,
    atender,
    guardar_perfil,
    leer_guardado,
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
def valores(mi_empresa: EstadosRevisados) -> tuple[ValorOSin, ...]:
    return valores_del_perfil(mi_empresa, BaseDeDias())


@pytest.fixture(scope="module")
def peso(mi_empresa: EstadosRevisados) -> DeUnPeso:
    return porcentajes_de_un_peso(mi_empresa)


def _platica(**respuestas: str) -> PlaticaDelPerfil:
    return PlaticaDelPerfil(empresa=EMPRESA, respuestas=respuestas)


def test_sin_limites_pregunta_antes_de_pintar(
    valores: tuple[ValorOSin, ...], peso: DeUnPeso
) -> None:
    paso = atender(_platica(), valores, peso, guardado=None)
    assert not paso.pintar
    assert paso.tarjetas == ()
    assert 1 <= len(paso.preguntas) <= 3
    # La primera ofrece el ejemplo del curso, dicho como ejemplo.
    primera = paso.preguntas[0]
    assert primera.clave == "curso"
    assert "Según el curso de cash que vimos, un ejemplo es" in primera.pregunta
    assert "más de 50%" in primera.pregunta
    # No hay semáforo por defecto: ningún indicador sale con color.
    assert "(regular)" not in paso.mensaje and "(malo)" not in paso.mensaje
    assert "antes de pintar" in paso.mensaje.lower()


def test_con_el_ejemplo_del_curso_gastos_queda_pendiente(
    valores: tuple[ValorOSin, ...], peso: DeUnPeso
) -> None:
    paso = atender(_platica(curso="sí"), valores, peso, guardado=None)
    assert not paso.pintar
    assert [p.clave for p in paso.preguntas] == ["gastos"]
    assert CONTRADICCION_GASTOS_B in paso.preguntas[0].pregunta
    assert set(paso.limites) == set(INDICADORES) - {"gastos"}


def test_con_el_ejemplo_y_gastos_resueltos_pinta(
    valores: tuple[ValorOSin, ...], peso: DeUnPeso
) -> None:
    paso = atender(_platica(curso="sí", gastos=GASTOS), valores, peso, guardado=None)
    assert paso.pintar
    colores = {t.clave: t.color for t in paso.tarjetas}
    assert colores == {
        "utilidad_bruta": "amarillo",
        "gastos": "amarillo",  # 30.62: de 30% a 33% (lo decidió el dueño)
        "utilidad_de_operacion": "rojo",
        "dias_clientes": "rojo",
        "dias_inventario": "verde",
        "dias_proveedores": "rojo",
    }
    assert "responde «sí»" in paso.mensaje
    assert paso.pide_guardar


def test_una_respuesta_que_no_se_entiende_se_vuelve_a_preguntar(
    valores: tuple[ValorOSin, ...], peso: DeUnPeso
) -> None:
    paso = atender(
        _platica(curso="sí", gastos="ideal 33, verde menos de 33, rojo más de 30"),
        valores,
        peso,
        guardado=None,
    )
    assert not paso.pintar
    assert paso.preguntas[0].clave == "gastos"
    assert "verde y rojo a la vez" in paso.preguntas[0].pregunta


def test_sin_el_curso_pregunta_los_seis_de_tres_en_tres(
    valores: tuple[ValorOSin, ...], peso: DeUnPeso
) -> None:
    paso = atender(_platica(curso="no"), valores, peso, guardado=None)
    assert [p.clave for p in paso.preguntas] == [
        "utilidad_bruta",
        "gastos",
        "utilidad_de_operacion",
    ]
    assert "6 de 6" in paso.mensaje or "Me faltan 6" in paso.mensaje


def test_con_limites_guardados_pinta_sin_preguntar(
    valores: tuple[ValorOSin, ...], peso: DeUnPeso, tmp_path: Path
) -> None:
    completo = atender(
        _platica(curso="sí", gastos=GASTOS), valores, peso, guardado=None
    )
    ruta = guardar_perfil(completo, EMPRESA, carpeta=tmp_path, hoy=HOY)
    assert ruta is not None
    guardado = leer_guardado(EMPRESA, carpeta=tmp_path)
    assert isinstance(guardado, PerfilGuardado)
    paso = atender(_platica(), valores, peso, guardado=guardado)
    assert paso.pintar and paso.preguntas == ()
    assert not paso.pide_guardar


def test_guardar_escribe_en_la_carpeta_de_la_empresa(
    valores: tuple[ValorOSin, ...], peso: DeUnPeso, tmp_path: Path
) -> None:
    paso = atender(_platica(curso="sí", gastos=GASTOS), valores, peso, guardado=None)
    ruta = guardar_perfil(paso, EMPRESA, carpeta=tmp_path, hoy=HOY)
    assert ruta == tmp_path / "mi-empresa-s-a-de-c-v" / "perfil-ideal.json"
    assert ruta is not None
    assert ruta.stat().st_mode & 0o777 == 0o600


def test_sin_limites_no_hay_nada_que_guardar(
    valores: tuple[ValorOSin, ...], peso: DeUnPeso, tmp_path: Path
) -> None:
    paso = atender(_platica(), valores, peso, guardado=None)
    assert guardar_perfil(paso, EMPRESA, carpeta=tmp_path, hoy=HOY) is None
    assert not any(tmp_path.iterdir())
