"""S86.26 — El recorrido con paneles y decisión.

Mi Empresa, de los estados a todos los paneles: el escenario de S86.17 sigue
hasta la fase 7 de 8 (mostrar) y deja listos los paneles de la fase 8 (decidir).
Cada titular sale de Python; la prueba busca cada número del titular en los
datos del panel y en la calculadora, y tiene un caso que la rompe.

Números de Mi Empresa (validados en S86.16–S86.25):

- contabilidad real: deuda neta 2,051,839.39 → 5,757,085.23; por cada 100, 14.10
- días y ciclo: ciclo 37.07 → 55.53; sin IVA (tasa 16) clientes 40.49
- tres medidas: flujo neto −3,705,245.84
- simulador (todas las palancas en 1): efectivo 1,143,864.91, utilidad 1,010,740.66
- precio contra volumen: 26.60% de equilibrio; combinado −1,911,041.64 y el curso −1,253,643.95
- margen: pre-tax 15.47%; con salario 1,200,000 y sueldo 0, 12.73%; devoluciones 2,045,326 → 30.16%
"""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import re
from typing import Any

import pytest

from escala_server.cash import escenario
from escala_server.cash.escenario import Conversacion, Paso, atender, guardar
from escala_server.cash.perfil import (
    VERSION_B,
    Borde,
    Limites,
    PerfilGuardado,
    ruta_del_perfil,
)
from tests.test_s86_17_escenario import COMPLETA, EMPRESA, HOY, _platica

NUMERO = re.compile(r"\d[\d,]*(?:\.\d+)?")
FASE_7 = ("contabilidad", "dias", "flujo")
FASE_8 = ("perfil", "simulador", "precio_volumen", "margen")
SLUG = "mi-empresa-s-a-de-c-v"


@pytest.fixture(scope="module")
def platica() -> tuple[list[Paso], Conversacion]:
    return _platica(COMPLETA)


def _con(conversacion: Conversacion, **respuestas: str) -> Conversacion:
    todas = dict(conversacion.respuestas)
    todas.update(respuestas)
    return conversacion.model_copy(update={"respuestas": todas})


def _paso(
    conversacion: Conversacion, carpeta: Path | None = None, **respuestas: str
) -> Paso:
    conversacion = _con(conversacion, **respuestas)
    if carpeta is None:
        return atender(conversacion, hoy=HOY)
    return atender(conversacion, hoy=HOY, carpeta=carpeta)


def _panel(paso: Paso, clave: str) -> Any:
    return next(p for p in paso.paneles if p.clave == clave)


def _numeros(texto: str) -> set[str]:
    return {n.replace(",", "").rstrip(".") for n in NUMERO.findall(texto)}


# ---------------------------------------------------------------------------
# Las fases
# ---------------------------------------------------------------------------


def test_cada_mensaje_dice_en_que_fase_vamos(
    platica: tuple[list[Paso], Conversacion],
) -> None:
    pasos, _ = platica
    for paso in pasos[:-1]:
        assert paso.fase == 3
        assert "Vamos en la fase 3 de 8" in paso.mensaje
    assert pasos[-1].fase == 7
    assert "Vamos en la fase 7 de 8" in pasos[-1].mensaje


def test_sin_archivos_vamos_en_la_fase_1() -> None:
    paso = atender(Conversacion(empresa=EMPRESA), hoy=HOY)
    assert paso.fase == 1
    assert "Vamos en la fase 1 de 8" in paso.mensaje
    assert paso.paneles == ()


def test_sin_calcular_no_hay_paneles(platica: tuple[list[Paso], Conversacion]) -> None:
    pasos, _ = platica
    assert all(paso.paneles == () for paso in pasos[:-1])


# ---------------------------------------------------------------------------
# Mi Empresa, de los estados a todos los paneles
# ---------------------------------------------------------------------------


def test_al_calcular_arma_todos_los_paneles(
    platica: tuple[list[Paso], Conversacion],
) -> None:
    ultimo = platica[0][-1]
    assert tuple(p.clave for p in ultimo.paneles) == FASE_7 + FASE_8
    assert {p.clave for p in ultimo.paneles if p.fase == 7} == set(FASE_7)
    assert {p.clave for p in ultimo.paneles if p.fase == 8} == set(FASE_8)
    for panel in ultimo.paneles:
        assert panel.titular in ultimo.mensaje
        assert panel.nombre in ultimo.mensaje


def test_contabilidad_real(platica: tuple[list[Paso], Conversacion]) -> None:
    panel = _panel(platica[0][-1], "contabilidad")
    assert panel.estado == "listo"
    assert "14.10" in panel.titular
    assert "2,051,839.39" in panel.titular and "5,757,085.23" in panel.titular


def test_dias_y_ciclo_sin_tasa_quedan_con_iva(
    platica: tuple[list[Paso], Conversacion],
) -> None:
    panel = _panel(platica[0][-1], "dias")
    assert panel.estado == "listo"
    assert "37.07" in panel.titular and "55.53" in panel.titular
    assert "46.97" in panel.titular
    assert "con IVA" in panel.titular


def test_tres_medidas(platica: tuple[list[Paso], Conversacion]) -> None:
    panel = _panel(platica[0][-1], "flujo")
    assert panel.estado == "listo"
    assert "3,705,245.84" in panel.titular


def test_simulador(platica: tuple[list[Paso], Conversacion]) -> None:
    panel = _panel(platica[0][-1], "simulador")
    assert panel.estado == "listo"
    assert "1,143,864.91" in panel.titular and "1,010,740.66" in panel.titular
    assert "antes de ISR" in panel.titular


def test_precio_contra_volumen_y_descuento(
    platica: tuple[list[Paso], Conversacion],
) -> None:
    panel = _panel(platica[0][-1], "precio_volumen")
    assert panel.estado == "listo"
    assert "26.60%" in panel.titular
    # La decisión del plan: el combinado, y la nota de lo que da el curso.
    assert "−1,911,041.64" in panel.titular
    assert "−1,253,643.95" in panel.titular


def test_margen_sin_datos_del_dueno(platica: tuple[list[Paso], Conversacion]) -> None:
    panel = _panel(platica[0][-1], "margen")
    assert panel.estado == "listo"
    assert "15.47%" in panel.titular and "10%" in panel.titular
    assert "12.73" not in panel.titular


def test_sin_limites_el_perfil_primero_pregunta(
    platica: tuple[list[Paso], Conversacion], tmp_path: Path
) -> None:
    paso = _paso(platica[1], carpeta=tmp_path)
    panel = _panel(paso, "perfil")
    assert panel.estado == "falta tu respuesta"
    assert "límites" in panel.titular
    assert panel.pagina is None


def _limites_guardados(carpeta: Path) -> None:
    limites = {c: lim for c, lim in VERSION_B.items() if lim is not None}
    limites["gastos"] = Limites(
        ideal=Decimal("30"),
        verde=Borde(valor=Decimal("30"), incluye=False),
        rojo=Borde(valor=Decimal("35"), incluye=False),
    )
    ruta = ruta_del_perfil(EMPRESA, carpeta=carpeta)
    ruta.parent.mkdir(parents=True)
    ruta.write_text(
        PerfilGuardado(empresa=EMPRESA, guardado=HOY, limites=limites).model_dump_json(),
        encoding="utf-8",
    )


def test_con_limites_guardados_el_perfil_pinta(
    platica: tuple[list[Paso], Conversacion], tmp_path: Path
) -> None:
    _limites_guardados(tmp_path)
    paso = _paso(platica[1], carpeta=tmp_path)
    panel = _panel(paso, "perfil")
    assert panel.estado == "listo"
    assert "verde" in panel.titular or "rojo" in panel.titular
    assert panel.pagina is not None and "<html" in panel.pagina


def test_cada_numero_de_un_titular_sale_de_python(
    platica: tuple[list[Paso], Conversacion],
) -> None:
    for panel in platica[0][-1].paneles:
        assert _numeros(panel.titular) <= _numeros(panel.fuente), panel.clave


def test_un_numero_inventado_se_detecta(
    platica: tuple[list[Paso], Conversacion],
) -> None:
    panel = _panel(platica[0][-1], "margen")
    inventado = panel.titular + " Tu margen ideal es 23.45%."
    assert not _numeros(inventado) <= _numeros(panel.fuente)


def test_los_paneles_salen_en_el_mensaje_antes_de_guardar(
    platica: tuple[list[Paso], Conversacion],
) -> None:
    mensaje = platica[0][-1].mensaje
    assert mensaje.index("Resumen al") < mensaje.index("Tus paneles")
    assert mensaje.split("\n\n")[-1].startswith("¿Guardo ")


# ---------------------------------------------------------------------------
# Las preguntas del recorrido: tasa de IVA, salario y devoluciones
# ---------------------------------------------------------------------------


def test_pregunta_tasa_y_salario_sin_pasar_de_tres(
    platica: tuple[list[Paso], Conversacion],
) -> None:
    ultimo = platica[0][-1]
    assert ultimo.preguntas == ()  # lo que bloquea ya se contestó
    assert ultimo.pregunta_travesuras is not None  # C6 va primero (S86.25)
    claves = [p.clave for p in ultimo.preguntas_del_recorrido]
    assert claves == ["tasa_iva", "salario_de_mercado"]
    for pregunta in ultimo.preguntas_del_recorrido:
        assert pregunta.pregunta in ultimo.mensaje

    sin_travesuras = _paso(platica[1], C6="no")
    claves = [p.clave for p in sin_travesuras.preguntas_del_recorrido]
    assert claves == ["tasa_iva", "salario_de_mercado", "sueldo_actual_del_dueno"]


def test_sin_iva_en_los_saldos_no_pregunta_la_tasa(
    platica: tuple[list[Paso], Conversacion],
) -> None:
    paso = _paso(platica[1], C9="no", C6="no")
    claves = [p.clave for p in paso.preguntas_del_recorrido]
    assert "tasa_iva" not in claves
    assert claves == ["salario_de_mercado", "sueldo_actual_del_dueno", "devoluciones"]


def test_con_tasa_16_los_dias_salen_sin_iva(
    platica: tuple[list[Paso], Conversacion],
) -> None:
    paso = _paso(platica[1], C6="no", tasa_iva="16%")
    panel = _panel(paso, "dias")
    assert "40.49" in panel.titular and "sin IVA" in panel.titular
    assert "46.97" not in panel.titular
    assert paso.estados is not None and paso.estados.respuestas is not None
    assert paso.estados.respuestas.tasa_iva == Decimal("16")
    assert "tasa_iva" not in [p.clave for p in paso.preguntas_del_recorrido]
    # El resumen de la fase 6 no cambia: la calculadora mide como vienen los saldos.
    assert "46.97" in paso.mensaje


def test_con_salario_el_margen_baja(platica: tuple[list[Paso], Conversacion]) -> None:
    paso = _paso(
        platica[1],
        C6="no",
        salario_de_mercado="1,200,000",
        sueldo_actual_del_dueno="0",
    )
    panel = _panel(paso, "margen")
    assert "12.73%" in panel.titular
    assert paso.estados is not None and paso.estados.del_dueno is not None
    assert paso.estados.del_dueno.salario_de_mercado == Decimal("1200000")
    assert paso.estados.del_dueno.sueldo_actual_del_dueno == Decimal("0")


def test_con_devoluciones(platica: tuple[list[Paso], Conversacion]) -> None:
    paso = _paso(platica[1], C6="no", devoluciones="2,045,326")
    panel = _panel(paso, "margen")
    assert "30.16%" in panel.titular


def test_no_se_no_vuelve_a_preguntar(platica: tuple[list[Paso], Conversacion]) -> None:
    paso = _paso(
        platica[1],
        C6="no",
        tasa_iva="no sé",
        salario_de_mercado="no sé",
        devoluciones="no sé",
    )
    assert paso.preguntas_del_recorrido == ()
    assert paso.errores == ()
    assert "12.73" not in _panel(paso, "margen").titular


@pytest.mark.parametrize(
    ("clave", "valor"),
    [("tasa_iva", "0"), ("tasa_iva", "200"), ("salario_de_mercado", "-5")],
)
def test_una_respuesta_que_no_se_entiende_se_dice(
    platica: tuple[list[Paso], Conversacion], clave: str, valor: str
) -> None:
    paso = _paso(platica[1], C6="no", **{clave: valor})
    assert any(valor in error for error in paso.errores)
    assert clave in [p.clave for p in paso.preguntas_del_recorrido]


# ---------------------------------------------------------------------------
# Las páginas y el guardado
# ---------------------------------------------------------------------------


def test_cada_pagina_dice_de_donde_sale(
    platica: tuple[list[Paso], Conversacion],
) -> None:
    for panel in platica[0][-1].paneles:
        if panel.pagina is None:
            continue
        assert panel.pagina.startswith("<!doctype html>"), panel.clave
        assert "sale de" in panel.pagina, panel.clave
        if panel.clave != "simulador":
            assert "<script" not in panel.pagina, panel.clave


def test_pagina_de_precio_contra_volumen(
    platica: tuple[list[Paso], Conversacion],
) -> None:
    pagina = _panel(platica[0][-1], "precio_volumen").pagina
    assert pagina is not None
    assert "cálculo de ESCALA" in pagina
    assert "26.60" in pagina and "1,911,041.64" in pagina and "1,253,643.95" in pagina


def test_pagina_del_margen_con_la_linea_del_10(
    platica: tuple[list[Paso], Conversacion],
) -> None:
    pagina = _panel(platica[0][-1], "margen").pagina
    assert pagina is not None
    assert "15.47" in pagina
    assert "línea de referencia" in pagina and "10%" in pagina
    assert "contador" in pagina  # lo fiscal sólo se muestra


def test_con_si_guarda_las_paginas(
    platica: tuple[list[Paso], Conversacion], tmp_path: Path
) -> None:
    conversacion = _con(platica[1], C6="no")
    paso = atender(conversacion, hoy=HOY, carpeta=tmp_path)
    guardados = guardar(paso, conversacion, carpeta=tmp_path, hoy=HOY)
    nombres = sorted(p.name for p in (tmp_path / SLUG).iterdir())
    assert nombres == sorted(
        [
            "conversacion.json",
            "estados-revisados-2026-01-31.json",
            "panel-contabilidad-2026-01-31.html",
            "panel-dias-2026-01-31.html",
            "panel-flujo-2026-01-31.html",
            "panel-simulador-2026-01-31.html",
            "panel-precio_volumen-2026-01-31.html",
            "panel-margen-2026-01-31.html",
        ]
    )
    assert len(guardados) == 8
    # Guardar otra vez no sobrescribe.
    guardar(paso, conversacion, carpeta=tmp_path, hoy=HOY)
    assert (tmp_path / SLUG / "panel-margen-2026-01-31-2.html").exists()


def test_sin_si_no_escribe_paneles(
    capsys: pytest.CaptureFixture[str],
    platica: tuple[list[Paso], Conversacion],
    tmp_path: Path,
) -> None:
    argv = ["--empresa", EMPRESA, "--carpeta", str(tmp_path / "cash")]
    argv += ["--conversacion", str(tmp_path / "borrador.json"), "--hoy", HOY.isoformat()]
    for archivo in COMPLETA:
        argv += ["--archivo", archivo]
    for clave, valor in platica[1].respuestas.items():
        argv += ["--responde", f"{clave}={valor}"]
    assert escenario.main(argv) == 0
    salida: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert salida["fase"] == 7
    assert [p["clave"] for p in salida["paneles"]] == list(FASE_7 + FASE_8)
    assert "pagina" not in salida["paneles"][0]
    assert not (tmp_path / "cash").exists()

    assert escenario.main([*argv, "--guardar", "sí"]) == 0
    salida = json.loads(capsys.readouterr().out)
    paginas = [r for r in salida["guardado"] if r.endswith(".html")]
    assert len(paginas) == 6  # sin límites guardados, el perfil no se pinta
    assert "¿Guardo" not in salida["mensaje"]
