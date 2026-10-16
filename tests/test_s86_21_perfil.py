"""S86.21 — Tu perfil ideal, con tus límites (la calculadora y el semáforo).

Según el curso de cash que vimos (F3b.1, L33, L71): de cada peso que vendes,
cuánto es costo, utilidad bruta, gastos y utilidad de operación; y un semáforo
con los límites que fija el dueño. Los del curso son sólo ejemplo.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from escala_server.cash.curso import BaseDeDias, Calculado, EstadosRevisados, dias_del_dinero
from escala_server.cash.perfil import (
    CONTRADICCION_GASTOS_B,
    Clave,
    INDICADORES,
    VERSION_B,
    Borde,
    Limites,
    ParteDeUnPeso,
    SinValor,
    ValorDelPerfil,
    color,
    entender_limites,
    porcentajes_de_un_peso,
    revisar_limites,
    semaforo,
    valores_del_perfil,
)
from escala_server.financial.lector import leer_estados
from escala_server.financial.revisiones import Respuestas, revisar_estados

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
HOY = date(2026, 1, 31)
FIN = date(2025, 12, 31)


def _mi_empresa(resultados_txt: str | None = None) -> EstadosRevisados:
    ruta = ESTADOS / "aspel_resultados.txt"
    if resultados_txt is not None:
        ruta = Path(resultados_txt)
    resultados = leer_estados(ruta, hoy=HOY)
    revision = revisar_estados(
        [leer_estados(ESTADOS / "aspel_balance.txt", hoy=HOY)],
        resultados,
        respuestas=Respuestas(periodo="acumulado del año"),
        hoy=HOY,
    )
    return EstadosRevisados(revision=revision, resultados=resultados)


@pytest.fixture(scope="module")
def mi_empresa() -> EstadosRevisados:
    return _mi_empresa()


# ---------------------------------------------------------------------------
# T1 — F3b.1 de cada peso, y los días sin redondear
# ---------------------------------------------------------------------------


def _parte(partes: tuple[ParteDeUnPeso, ...], clave: str) -> ParteDeUnPeso:
    return next(p for p in partes if p.clave == clave)


def test_de_cada_peso_mi_empresa(mi_empresa: EstadosRevisados) -> None:
    peso = porcentajes_de_un_peso(mi_empresa)
    assert peso.no_calculable is None
    assert peso.fecha == FIN
    esperado = {
        "costo": "52.40",
        "utilidad_bruta": "47.60",
        "gastos": "30.62",
        "utilidad_de_operacion": "16.97",
    }
    for clave, valor in esperado.items():
        assert _parte(peso.partes, clave).mostrado == Decimal(valor), clave
    # Sin redondear: 47.5968714…
    ub = _parte(peso.partes, "utilidad_bruta")
    assert Decimal("47.5968") < ub.valor < Decimal("47.5969")
    assert ub.origen.startswith("sale de: ")
    assert "43,826,513.09" in ub.origen and "20,860,049.09" in ub.origen


def test_de_cada_peso_trae_los_renglones_de_abajo(mi_empresa: EstadosRevisados) -> None:
    peso = porcentajes_de_un_peso(mi_empresa)
    claves = [p.clave for p in peso.partes]
    for clave in ("gastos_financieros", "utilidad_antes_impuestos", "isr", "utilidad_neta"):
        assert clave in claves
    # 5,018,095.92 ÷ 43,826,513.09 = 11.45%
    assert _parte(peso.partes, "utilidad_neta").mostrado == Decimal("11.45")
    # Lo fiscal sólo se muestra.
    assert peso.nota_fiscal is not None and "contador" in peso.nota_fiscal


def test_mover_el_costo_cambia_el_peso(tmp_path: Path) -> None:
    texto = (ESTADOS / "aspel_resultados.txt").read_text(encoding="utf-8")
    otro = tmp_path / "resultados.txt"
    otro.write_text(texto.replace("22966464.00", "21966464.00"), encoding="utf-8")
    peso = porcentajes_de_un_peso(_mi_empresa(str(otro)))
    assert _parte(peso.partes, "utilidad_bruta").mostrado != Decimal("47.60")


def test_dias_sin_redondear(mi_empresa: EstadosRevisados) -> None:
    dias = dias_del_dinero(mi_empresa, BaseDeDias())
    anio = dias.anio(FIN)
    assert isinstance(anio.proveedores, Calculado)
    assert anio.proveedores.valor == Decimal("19.59")
    crudo = anio.sin_redondear["proveedores"]
    assert crudo is not None and Decimal("19.587") < crudo < Decimal("19.588")
    # No viaja en el JSON del panel de días.
    assert "sin_redondear" not in dias.model_dump_json()


def test_valores_del_perfil(mi_empresa: EstadosRevisados) -> None:
    valores = {v.clave: v for v in valores_del_perfil(mi_empresa, BaseDeDias())}
    assert tuple(valores) == INDICADORES
    mostrados = {
        "utilidad_bruta": "47.60",
        "gastos": "30.62",
        "utilidad_de_operacion": "16.97",
        "dias_clientes": "46.97",
        "dias_inventario": "28.15",
        "dias_proveedores": "19.59",
    }
    for clave, valor in mostrados.items():
        v = valores[clave]
        assert isinstance(v, ValorDelPerfil), clave
        assert v.mostrado == Decimal(valor), clave
        assert v.origen.startswith("sale de: "), clave
    proveedores = valores["dias_proveedores"]
    assert isinstance(proveedores, ValorDelPerfil)
    assert proveedores.valor != proveedores.mostrado


# ---------------------------------------------------------------------------
# T2 — límites, borde y color
# ---------------------------------------------------------------------------


def _b(clave: Clave) -> Limites:
    limites = VERSION_B[clave]
    assert limites is not None
    return limites


def test_validacion_con_la_version_b(mi_empresa: EstadosRevisados) -> None:
    valores = {v.clave: v for v in valores_del_perfil(mi_empresa, BaseDeDias())}
    esperado: dict[Clave, str] = {
        "utilidad_bruta": "amarillo",  # 47.60 regular
        "utilidad_de_operacion": "rojo",  # 16.97 malo
        "dias_clientes": "rojo",  # 46.97 malo
        "dias_inventario": "verde",  # 28.15 óptimo
        "dias_proveedores": "rojo",  # 19.59 malo (19.587… < 20)
    }
    for clave, esperado_color in esperado.items():
        v = valores[clave]
        assert isinstance(v, ValorDelPerfil)
        assert color(clave, v.valor, _b(clave)) == esperado_color, clave


def test_proveedores_mi_empresa_la_lamina_redondea_a_20() -> None:
    # La lámina L71 redondea 19.587… a 20 y dice «regular». Sin redondear es rojo.
    limites = _b("dias_proveedores")
    assert color("dias_proveedores", Decimal("19.587"), limites) == "rojo"
    assert color("dias_proveedores", Decimal("20"), limites) == "amarillo"


def test_el_color_usa_el_valor_sin_redondear() -> None:
    # 19.996 días se ve «20.00»; con el valor redondeado saldría amarillo.
    limites = _b("dias_proveedores")
    sin_redondear = Decimal("19.996")
    mostrado = sin_redondear.quantize(Decimal("0.01"))
    assert mostrado == Decimal("20.00")
    assert color("dias_proveedores", mostrado, limites) == "amarillo"
    assert color("dias_proveedores", sin_redondear, limites) == "rojo"


def test_el_semaforo_usa_el_valor_sin_redondear() -> None:
    valor = ValorDelPerfil(
        clave="dias_proveedores",
        nombre="Días de proveedores",
        unidad="días",
        fecha=FIN,
        valor=Decimal("19.996"),
        mostrado=Decimal("20.00"),
        origen="sale de: prueba",
        lamina="L71",
    )
    tarjeta = semaforo(valor, _b("dias_proveedores"))
    assert tarjeta.color == "rojo"
    assert tarjeta.nivel == "malo"


def test_el_borde_dice_si_se_incluye() -> None:
    excluye = Limites(ideal=Decimal(50), verde=Borde(valor=Decimal(50), incluye=False), rojo=Borde(valor=Decimal(47), incluye=False))
    incluye = Limites(ideal=Decimal(50), verde=Borde(valor=Decimal(50), incluye=True), rojo=Borde(valor=Decimal(47), incluye=True))
    assert color("utilidad_bruta", Decimal(50), excluye) == "amarillo"
    assert color("utilidad_bruta", Decimal(50), incluye) == "verde"
    assert color("utilidad_bruta", Decimal(47), excluye) == "amarillo"
    assert color("utilidad_bruta", Decimal(47), incluye) == "rojo"
    # Menos es mejor (gastos): verde «menos de 30».
    gastos = Limites(ideal=Decimal(30), verde=Borde(valor=Decimal(30), incluye=False), rojo=Borde(valor=Decimal(33), incluye=False))
    assert color("gastos", Decimal("29.99"), gastos) == "verde"
    assert color("gastos", Decimal(30), gastos) == "amarillo"
    assert color("gastos", Decimal("33.01"), gastos) == "rojo"


def test_gastos_de_la_version_b_queda_sin_resolver() -> None:
    assert VERSION_B["gastos"] is None
    assert "31" in CONTRADICCION_GASTOS_B
    assert "33" in CONTRADICCION_GASTOS_B and "30" in CONTRADICCION_GASTOS_B


def test_entender_limites() -> None:
    limites = entender_limites("utilidad_bruta", "ideal 50, verde más de 50, rojo menos de 47")
    assert isinstance(limites, Limites)
    assert limites.verde == Borde(valor=Decimal(50), incluye=False)
    assert limites.rojo == Borde(valor=Decimal(47), incluye=False)
    otra = entender_limites("dias_clientes", "ideal 40; verde 40 o menos; rojo más de 45")
    assert isinstance(otra, Limites)
    assert otra.verde == Borde(valor=Decimal(40), incluye=True)
    con_signos = entender_limites("gastos", "ideal 30% verde <30 rojo >=33.5")
    assert isinstance(con_signos, Limites)
    assert con_signos.rojo == Borde(valor=Decimal("33.5"), incluye=True)


def test_entender_limites_sin_ideal_o_al_reves() -> None:
    falta = entender_limites("utilidad_bruta", "verde más de 50, rojo menos de 47")
    assert isinstance(falta, str) and "ideal" in falta
    al_reves = entender_limites("utilidad_bruta", "ideal 50, verde menos de 50, rojo más de 47")
    assert isinstance(al_reves, str) and "más es mejor" in al_reves


def test_limites_que_se_pisan() -> None:
    # Gastos como la lámina L71: verde menos de 33, rojo más de 30.
    pisan = Limites(ideal=Decimal(33), verde=Borde(valor=Decimal(33), incluye=False), rojo=Borde(valor=Decimal(30), incluye=False))
    razon = revisar_limites("gastos", pisan)
    assert razon is not None and "verde y rojo a la vez" in razon
    mismo_borde = Limites(ideal=Decimal(50), verde=Borde(valor=Decimal(50), incluye=True), rojo=Borde(valor=Decimal(50), incluye=True))
    assert revisar_limites("utilidad_bruta", mismo_borde) is not None
    assert revisar_limites("utilidad_bruta", _b("utilidad_bruta")) is None


def test_semaforo_trae_meta_y_distancia(mi_empresa: EstadosRevisados) -> None:
    valores = {v.clave: v for v in valores_del_perfil(mi_empresa, BaseDeDias())}
    ub = valores["utilidad_bruta"]
    assert isinstance(ub, ValorDelPerfil)
    tarjeta = semaforo(ub, _b("utilidad_bruta"))
    assert tarjeta.color == "amarillo" and tarjeta.nivel == "regular"
    assert tarjeta.meta == Decimal(50)
    assert tarjeta.distancia == Decimal("-2.40")
    assert "2.40" in tarjeta.texto_distancia and "50" in tarjeta.texto_distancia
    assert tarjeta.origen_distancia.startswith("sale de: ")
    assert "de 47% a 50%" in tarjeta.texto_limites


def test_sin_valor_no_pinta() -> None:
    sin = SinValor(clave="dias_inventario", nombre="Días de inventario", unidad="días", razon="no aplica: no tienes inventario")
    tarjeta = semaforo(sin, _b("dias_inventario"))
    assert tarjeta.color is None
    assert tarjeta.razon is not None and "inventario" in tarjeta.razon
