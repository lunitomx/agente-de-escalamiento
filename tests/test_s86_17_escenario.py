"""S86.17 — El escenario «analiza mi balance general y mi estado de resultados».

Según el curso de cash que vimos, ESCALA lee lo que llegó, muestra la lista
✔ lo tengo · ? no me queda claro · ✘ me falta, pregunta (máximo 3 por mensaje,
de la más importante a la menos importante), revisa R1–R11, anuncia qué va a
calcular y qué no, y calcula con la calculadora de Python (S86.16).

Tres entradas de punta a punta:

- Mi Empresa completa (balance de dos fechas) → calcula todo.
- Mi Empresa sin el balance anterior → calcula lo estático y dice qué falta.
- Un estado sucio de prueba → pregunta antes de calcular.

Valores de Mi Empresa: los mismos de ``verifica.py`` del curso (ver S86.16).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from escala_server.cash.curso import Calculado, NoCalculable
from escala_server.cash.escenario import Conversacion, Paso, atender

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
HOY = date(2026, 1, 31)
FIN = date(2025, 12, 31)
EMPRESA = "Mi Empresa, S.A. de C.V."

COMPLETA = (str(ESTADOS / "aspel_balance.txt"), str(ESTADOS / "aspel_resultados.txt"))
SIN_ANTERIOR = (
    str(ESTADOS / "contpaqi_balance.txt"),
    str(ESTADOS / "contpaqi_resultados.txt"),
)
SUCIA = (str(ESTADOS / "sucio_balance.txt"), str(ESTADOS / "aspel_resultados.txt"))

# Lo que contesta el dueño de Mi Empresa, por clave de pregunta.
DUENO: dict[str, str] = {
    "C10": "acumulado del año",
    "unidad": "pesos",
    "suma:gastos_operacion:2025-12-31": "sí",
    "suma:gastos_operacion:2024-12-31": "sí",
    "C11:Documentos por pagar a largo plazo": "no",
    "C9": "sí",
    "C1": "no sé",
    "C4": "2,966,528.27",
    "C3": "no sé",
    "C2": "todas",
    "R7:Cuenta puente": "otra cuenta a mi favor",
}

RESUMEN_COMPLETA: dict[str, str] = {
    "capital_de_trabajo": "6178173.85",
    "dias_clientes": "46.97",
    "dias_inventario": "28.15",
    "dias_proveedores": "19.59",
    "ciclo": "55.53",
    "flujo_neto": "-3705245.84",
    "flujo_de_operacion": "4835206.16",
    "marginal": "0.3350",
}


def _platica(archivos: tuple[str, ...]) -> tuple[list[Paso], Conversacion]:
    """Contesta lo que ESCALA pregunte hasta que ya no pregunte nada contestable."""

    conversacion = Conversacion(empresa=EMPRESA, archivos=archivos)
    pasos = [atender(conversacion, hoy=HOY)]
    for _ in range(8):
        claves = [p.clave for p in pasos[-1].preguntas if p.clave is not None]
        if not claves:
            break
        respuestas = dict(conversacion.respuestas)
        for clave in claves:
            respuestas[clave] = DUENO[clave]
        conversacion = conversacion.model_copy(update={"respuestas": respuestas})
        pasos.append(atender(conversacion, hoy=HOY))
    return pasos, conversacion


def _marca(paso: Paso, texto: str) -> str:
    renglones = [r for r in paso.lista if texto in r.nombre]
    assert renglones, f"no hay renglón «{texto}» en la lista"
    return renglones[0].marca


# ---------------------------------------------------------------------------
# Mi Empresa completa → calcula todo
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def completa() -> list[Paso]:
    return _platica(COMPLETA)[0]


def test_primero_lista_y_pregunta_sin_calcular(completa: list[Paso]) -> None:
    primero = completa[0]
    assert primero.calculo is None
    assert primero.anuncio is None
    assert _marca(primero, "Bancos") == "✔"
    assert _marca(primero, "Clientes") == "✔"
    assert _marca(primero, "Periodo") == "?"
    assert "✔ lo tengo" in primero.mensaje and "✘ me falta" in primero.mensaje
    assert "5,639,601.55" in primero.mensaje  # Clientes, tal como viene en el archivo


def test_maximo_tres_preguntas_por_mensaje(completa: list[Paso]) -> None:
    assert all(len(paso.preguntas) <= 3 for paso in completa)
    assert len(completa[0].preguntas) == 3
    assert len(completa) >= 3  # 9 preguntas → al menos 3 mensajes


def test_de_la_mas_importante_a_la_menos_importante(completa: list[Paso]) -> None:
    claves = [p.clave for paso in completa for p in paso.preguntas]
    assert claves == [
        "C10",
        "suma:gastos_operacion:2025-12-31",
        "suma:gastos_operacion:2024-12-31",
        "C11:Documentos por pagar a largo plazo",
        "C9",
        "C1",
        "C4",
        "C3",
        "C2",
    ]


def test_las_preguntas_salen_tal_cual_en_el_mensaje(completa: list[Paso]) -> None:
    for paso in completa:
        for pregunta in paso.preguntas:
            assert pregunta.pregunta in paso.mensaje


def test_completa_anuncia_y_calcula_todo(completa: list[Paso]) -> None:
    ultimo = completa[-1]
    assert ultimo.calculo is not None and ultimo.calculo.no_calculable is None
    assert ultimo.anuncio is not None
    assert ultimo.anuncio.startswith("Con esto voy a calcular")
    assert "Flujo neto" in ultimo.anuncio
    assert "No puedo calcular" not in ultimo.anuncio
    assert ultimo.anuncio in ultimo.mensaje
    assert not ultimo.preguntas


def test_completa_resumen_con_origen(completa: list[Paso]) -> None:
    ultimo = completa[-1]
    resumen = {linea.clave: linea for linea in ultimo.resumen}
    assert list(resumen) == list(RESUMEN_COMPLETA)
    for clave, valor in RESUMEN_COMPLETA.items():
        linea = resumen[clave]
        assert linea.valor == Decimal(valor), clave
        assert linea.origen is not None and linea.origen.startswith("sale de:")
        assert linea.lamina
        assert linea.origen in ultimo.mensaje
    assert "6,178,173.85" in ultimo.mensaje
    assert "-3,705,245.84" in ultimo.mensaje


def test_al_final_pregunta_si_guarda(completa: list[Paso]) -> None:
    assert "«sí»" in completa[-1].mensaje
    assert "work/cash/mi-empresa-s-a-de-c-v/" in completa[-1].mensaje


# ---------------------------------------------------------------------------
# Sin el balance anterior → calcula lo estático y dice qué falta
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sin_anterior() -> list[Paso]:
    return _platica(SIN_ANTERIOR)[0]


def test_sin_anterior_pregunta_la_unidad(sin_anterior: list[Paso]) -> None:
    claves = [p.clave for paso in sin_anterior for p in paso.preguntas]
    assert claves[:2] == ["C10", "unidad"]


def test_sin_anterior_marca_lo_que_falta(sin_anterior: list[Paso]) -> None:
    ultimo = sin_anterior[-1]
    assert _marca(ultimo, "Balance al inicio") == "✘"
    assert _marca(ultimo, "Balance al cierre") == "✔"


def test_sin_anterior_calcula_lo_estatico(sin_anterior: list[Paso]) -> None:
    ultimo = sin_anterior[-1]
    assert ultimo.calculo is not None
    resumen = {linea.clave: linea for linea in ultimo.resumen}
    for clave in ("capital_de_trabajo", "dias_clientes", "ciclo", "marginal"):
        assert resumen[clave].valor == Decimal(RESUMEN_COMPLETA[clave]), clave
    for clave in ("flujo_neto", "flujo_de_operacion"):
        assert resumen[clave].valor is None
        assert resumen[clave].no_calculable == "falta el balance al inicio del periodo"
    assert isinstance(ultimo.calculo.indicador("flujo_neto", FIN), NoCalculable)
    assert isinstance(ultimo.calculo.indicador("capital_de_trabajo", FIN), Calculado)


def test_sin_anterior_dice_que_no_puede_y_por_que(sin_anterior: list[Paso]) -> None:
    anuncio = sin_anterior[-1].anuncio
    assert anuncio is not None
    assert anuncio.startswith("Con esto voy a calcular")
    assert "No puedo calcular" in anuncio
    assert "Flujo neto" in anuncio and "Flujo de operación" in anuncio
    assert "porque falta el balance al inicio del periodo" in anuncio
    assert (
        "no calculable: falta el balance al inicio del periodo"
        in sin_anterior[-1].mensaje
    )


# ---------------------------------------------------------------------------
# Un estado sucio → pregunta antes de calcular
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sucia() -> tuple[list[Paso], Conversacion]:
    return _platica(SUCIA)


def test_sucia_no_calcula_y_dice_el_numero(
    sucia: tuple[list[Paso], Conversacion],
) -> None:
    pasos, _ = sucia
    primero = pasos[0]
    assert primero.calculo is None and primero.anuncio is None
    assert len(primero.preguntas) == 3
    # Lo más importante primero: los signos, que explican por qué no cuadra.
    assert primero.preguntas[0].clave is None
    assert "-1,232,468.24" in primero.preguntas[0].pregunta
    assert "No calculo" in primero.mensaje
    assert _marca(primero, "Proveedores") == "✘"
    assert _marca(primero, "Cuenta puente") == "?"


def test_sucia_aunque_conteste_todo_no_calcula() -> None:
    conversacion = Conversacion(empresa=EMPRESA, archivos=SUCIA, respuestas=DUENO)
    paso = atender(conversacion, hoy=HOY)
    assert paso.calculo is None and paso.anuncio is None
    assert _marca(paso, "Cuenta puente") == "✔"  # ya dijo qué es
    assert paso.preguntas  # quedan los problemas: piden el archivo corregido
    assert all(p.clave is None for p in paso.preguntas)
    assert "corregido" in paso.mensaje


def test_sucia_con_el_archivo_corregido_calcula() -> None:
    corregida = Conversacion(empresa=EMPRESA, archivos=COMPLETA, respuestas=DUENO)
    paso = atender(corregida, hoy=HOY)
    assert paso.calculo is not None and paso.calculo.no_calculable is None
    resumen = {linea.clave: linea.valor for linea in paso.resumen}
    assert resumen["capital_de_trabajo"] == Decimal("6178173.85")


def test_cuenta_puente_contestada_cambia_las_cajas() -> None:
    """Prueba que puede fallar: decir qué es «Cuenta puente» la saca de ?."""

    conversacion = Conversacion(
        empresa=EMPRESA, archivos=SUCIA, respuestas={"R7:Cuenta puente": "clientes"}
    )
    assert _marca(atender(conversacion, hoy=HOY), "Cuenta puente") == "✔"


# ---------------------------------------------------------------------------
# Respuestas que no se entienden
# ---------------------------------------------------------------------------


def test_respuesta_que_no_entiende_se_vuelve_a_preguntar() -> None:
    conversacion = Conversacion(
        empresa=EMPRESA, archivos=COMPLETA, respuestas={"C10": "el trimestre"}
    )
    paso = atender(conversacion, hoy=HOY)
    assert paso.preguntas[0].clave == "C10"
    assert any("el trimestre" in error for error in paso.errores)
    assert paso.calculo is None


def test_no_se_no_sirve_para_lo_que_bloquea() -> None:
    conversacion = Conversacion(
        empresa=EMPRESA, archivos=COMPLETA, respuestas={"C10": "no sé"}
    )
    paso = atender(conversacion, hoy=HOY)
    assert paso.preguntas[0].clave == "C10"
    assert paso.errores


def test_sin_estado_de_resultados_lo_pide() -> None:
    conversacion = Conversacion(empresa=EMPRESA, archivos=COMPLETA[:1])
    paso = atender(conversacion, hoy=HOY)
    assert paso.calculo is None
    assert _marca(paso, "Estado de resultados") == "✘"
    assert paso.preguntas[0].clave is None
