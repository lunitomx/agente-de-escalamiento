"""S86.23 — Precio contra volumen y el costo de un descuento.

Según el curso de cash que vimos (F3b.2, L36–L38): subir el precio 1% deja más
utilidad y más efectivo que vender 1% más. Y (F3b.3, L39–L43): dar 10% de
descuento para vender 15% más pierde utilidad y efectivo.

Valores de Mi Empresa (``verifica.py``). Erratas que la prueba no copia:

- L37/L40 muestran la utilidad bruta 20,860,019.09; la correcta es 20,860,049.09.
- L38 muestra el flujo del precio 381,689.12; el correcto es 381,869.12 (la razón
  2.60 sí usa el correcto).
- L43 muestra el neto −1,616,414.36 / −1,253,644.31; arrastra la errata de L37.
  El correcto es −1,616,409.87 / −1,253,643.95.

Lo que no está en el curso lo calcula ESCALA y lo rotula «cálculo de ESCALA»:

- Volumen de equilibrio: UB ÷ (ventas × (1 − d) − costo) − 1 = 26.60% con 10%.
  La fórmula vieja del conocimiento (d × ventas ÷ UB = 21.01%) olvidaba que el
  volumen extra también va con descuento.
- Combinado de 10% de descuento y 15% más de volumen:
  (1 + v) × (ventas × (1 − d) − costo) − UB = −1,911,041.64.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from escala_server.cash.curso import (
    CifraDePrecioVolumen,
    EstadosRevisados,
    NoCalculable,
    PrecioContraVolumen,
    calcular_curso,
    precio_contra_volumen,
)
from escala_server.financial.lector import CuentaLeida, LecturaEstados, leer_estados
from escala_server.financial.revisiones import Respuestas, revisar_estados

ROOT = Path(__file__).resolve().parents[1]
ESTADOS = ROOT / "tests" / "fixtures" / "cash" / "estados"
HOY = date(2026, 1, 31)
INI = date(2024, 12, 31)
FIN = date(2025, 12, 31)
ACUMULADO = Respuestas(periodo="acumulado del año")
ESCALA = "cálculo de ESCALA"


def _mi_empresa_estados() -> EstadosRevisados:
    resultados = leer_estados(ESTADOS / "aspel_resultados.txt", hoy=HOY)
    revision = revisar_estados(
        [leer_estados(ESTADOS / "aspel_balance.txt", hoy=HOY)],
        resultados,
        respuestas=ACUMULADO,
        hoy=HOY,
    )
    return EstadosRevisados(revision=revision, resultados=resultados)


@pytest.fixture(scope="module")
def mi_empresa() -> PrecioContraVolumen:
    return precio_contra_volumen(_mi_empresa_estados(), descuento=10, volumen=15)


def _cifra(resultado: PrecioContraVolumen, clave: str) -> CifraDePrecioVolumen:
    cifra = resultado.cifra(clave)
    assert isinstance(cifra, CifraDePrecioVolumen), (clave, cifra)
    return cifra


def _no_calculable(resultado: PrecioContraVolumen, clave: str) -> NoCalculable:
    cifra = resultado.cifra(clave)
    assert isinstance(cifra, NoCalculable), (clave, cifra)
    return cifra


# ---------------------------------------------------------------------------
# Mi Empresa al centavo
# ---------------------------------------------------------------------------

VALORES: list[tuple[str, str, str, str]] = [
    # clave, valor, fuente, lámina
    ("razon.utilidad", "2.10", "curso", "L38"),
    ("razon.flujo", "2.60", "curso", "L38"),
    ("precio.utilidad", "438265.13", "curso", "L36"),
    ("precio.flujo", "381869.12", "curso", "L36"),  # L38 dice 381,689.12 (errata)
    ("volumen_1.utilidad", "208600.49", "curso", "L37"),  # L37 dice 208,600.19 (errata)
    ("volumen_1.flujo", "146818.75", "curso", "L37"),
    ("descuento.utilidad", "-4382651.31", "curso", "L41"),
    ("descuento.flujo", "-3818691.15", "curso", "L41"),
    ("volumen.utilidad", "3129007.36", "curso", "L40"),  # L40 dice 3,129,002.86 (errata)
    # 3,129,007.3635 − 926,726.0775 = 2,202,281.286 → .29 (L40 lo trae .29)
    ("volumen.flujo", "2202281.29", "curso", "L40"),
    ("neto_del_curso.utilidad", "-1253643.95", "curso", "L43"),  # L43: −1,253,644.31
    ("neto_del_curso.flujo", "-1616409.87", "curso", "L43"),  # L43: −1,616,414.36
    ("combinado.utilidad", "-1911041.64", ESCALA, "L43"),
    ("equilibrio.volumen", "26.60", ESCALA, "L43"),
]


@pytest.mark.parametrize(("clave", "valor", "fuente", "lamina"), VALORES)
def test_mi_empresa(
    mi_empresa: PrecioContraVolumen, clave: str, valor: str, fuente: str, lamina: str
) -> None:
    cifra = _cifra(mi_empresa, clave)
    assert cifra.valor == Decimal(valor)
    assert cifra.fuente == fuente
    assert lamina in cifra.lamina
    assert cifra.formula
    assert cifra.origen.startswith("sale de: ")


def test_cada_cifra_dice_de_donde_sale(mi_empresa: PrecioContraVolumen) -> None:
    combinado = _cifra(mi_empresa, "combinado.utilidad")
    assert "43,826,513.09" in combinado.origen  # ventas
    assert "22,966,464.00" in combinado.origen  # costo de ventas
    assert "20,860,049.09" in combinado.origen  # utilidad bruta correcta (no la de L37)
    razon = _cifra(mi_empresa, "razon.flujo")
    assert "381,869.12" in razon.origen and "146,818.75" in razon.origen


def test_lo_que_no_es_del_curso_lleva_la_etiqueta(mi_empresa: PrecioContraVolumen) -> None:
    for cifra in mi_empresa.cifras:
        assert isinstance(cifra, CifraDePrecioVolumen)
        es_de_escala = cifra.clave in {"combinado.utilidad", "equilibrio.volumen"}
        assert (cifra.fuente == ESCALA) is es_de_escala, cifra.clave
        if es_de_escala:
            assert ESCALA in cifra.nombre


def test_lo_que_ve_el_dueno(mi_empresa: PrecioContraVolumen) -> None:
    texto = "\n".join(mi_empresa.mensajes)
    assert (
        "Si das 10% de descuento, necesitas vender 26.60% más solo para quedar igual"
        " (cálculo de ESCALA)."
    ) in texto
    assert "−1,911,041.64" in texto
    assert "el curso lo simplifica sumando los dos efectos, y da −1,253,643.95" in texto
    assert "2.10" in texto and "2.60" in texto


def test_la_formula_vieja_ya_no_esta(mi_empresa: PrecioContraVolumen) -> None:
    # d × ventas ÷ UB = 21.01%: olvidaba que el volumen extra también va con descuento.
    assert _cifra(mi_empresa, "equilibrio.volumen").valor != Decimal("21.01")
    assert "21.01" not in "\n".join(mi_empresa.mensajes)


def test_la_calculadora_trae_el_ejemplo_del_curso() -> None:
    resultado = calcular_curso(_mi_empresa_estados())
    bloque = resultado.precio_contra_volumen
    assert bloque is not None
    assert (bloque.descuento, bloque.volumen) == (10, 15)
    assert _cifra(bloque, "equilibrio.volumen").valor == Decimal("26.60")


def test_otro_descuento_da_otro_equilibrio() -> None:
    cinco = precio_contra_volumen(_mi_empresa_estados(), descuento=5, volumen=15)
    # UB ÷ (0.95 × ventas − costo) − 1 = 20,860,049.09 ÷ 18,668,723.4355 − 1
    assert _cifra(cinco, "equilibrio.volumen").valor == Decimal("11.74")
    assert "Si das 5% de descuento, necesitas vender 11.74% más" in "\n".join(cinco.mensajes)


# ---------------------------------------------------------------------------
# Estados sintéticos: una cuenta cambia el resultado; «no calculable» con razón
# ---------------------------------------------------------------------------

Fila = tuple[str, str | None, str | None, str | None]


def _lectura(filas: list[Fila]) -> LecturaEstados:
    cuentas: list[CuentaLeida] = []
    for renglon, (nombre, concepto, al_inicio, al_final) in enumerate(filas, start=1):
        for fecha, monto in ((INI, al_inicio), (FIN, al_final)):
            if monto is not None:
                cuentas.append(
                    CuentaLeida(
                        nombre=nombre,
                        monto=Decimal(monto),
                        fecha=fecha,
                        renglon=renglon,
                        hoja="estado",
                        concepto=concepto,
                        es_total=False,
                    )
                )
    return LecturaEstados(cuentas=tuple(cuentas), fecha=FIN)


def _balance(clientes: str = "400") -> list[Fila]:
    return [
        ("Bancos", None, "100", "200"),
        ("Clientes", None, "300", clientes),
        ("Inventarios", None, "200", "200"),
        ("Proveedores", None, "100", "100"),
        ("Capital social", None, "500", "500"),
        ("Resultado del ejercicio", None, "0", str(200 + int(clientes) - 400)),
    ]


def _sintetico(
    *, costo: str = "500", clientes: str = "400", descuento: int = 10, volumen: int = 15
) -> PrecioContraVolumen:
    resultados = _lectura(
        [
            ("Ventas", "ventas", "1000", "1000"),
            ("Costo de ventas", "costo_ventas", costo, costo),
            ("Gastos generales", "gastos_operacion", "300", "300"),
            ("Utilidad neta", "utilidad_neta", "200", "200"),
        ]
    )
    revision = revisar_estados([_lectura(_balance(clientes))], resultados, respuestas=ACUMULADO, hoy=HOY)
    return precio_contra_volumen(
        EstadosRevisados(revision=revision, resultados=resultados),
        descuento=descuento,
        volumen=volumen,
    )


def test_sintetico_a_mano() -> None:
    # ventas 1000, costo 500 → UB 500; CT 400 + 200 − 100 = 500
    r = _sintetico()
    assert _cifra(r, "razon.utilidad").valor == Decimal("2.00")  # 10 ÷ 5
    assert _cifra(r, "equilibrio.volumen").valor == Decimal("25.00")  # 500 ÷ 400 − 1
    assert _cifra(r, "combinado.utilidad").valor == Decimal("-40.00")  # 1.15 × 400 − 500
    assert _cifra(r, "neto_del_curso.utilidad").valor == Decimal("-25.00")  # −100 + 75


def test_mover_clientes_cambia_el_flujo_pero_no_la_utilidad() -> None:
    base, mas_clientes = _sintetico(), _sintetico(clientes="450")
    assert _cifra(base, "razon.utilidad").valor == _cifra(mas_clientes, "razon.utilidad").valor
    assert _cifra(base, "razon.flujo").valor != _cifra(mas_clientes, "razon.flujo").valor
    assert _cifra(base, "descuento.flujo").valor != _cifra(mas_clientes, "descuento.flujo").valor


def test_mover_el_costo_cambia_el_equilibrio() -> None:
    assert _cifra(_sintetico(costo="600"), "equilibrio.volumen").valor == Decimal("33.33")  # 400 ÷ 300 − 1


def test_descuento_igual_al_margen_no_es_calculable() -> None:
    r = _sintetico(descuento=50)  # margen bruto 50%
    razon = _no_calculable(r, "equilibrio.volumen").no_calculable
    assert "margen" in razon
    assert not any("necesitas vender" in m for m in r.mensajes)
    assert any("no calculable" in m for m in r.mensajes)


def test_utilidad_bruta_cero_no_es_calculable() -> None:
    r = _sintetico(costo="1000")
    for clave in ("razon.utilidad", "razon.flujo", "equilibrio.volumen"):
        assert "utilidad bruta" in _no_calculable(r, clave).no_calculable, clave


def test_volumen_que_no_deja_efectivo_no_da_razon_de_flujo() -> None:
    # UB 100 < CT 500: vender 1% más pide más capital de trabajo del que deja.
    r = _sintetico(costo="900")
    assert isinstance(r.cifra("razon.utilidad"), CifraDePrecioVolumen)
    assert "capital de trabajo" in _no_calculable(r, "razon.flujo").no_calculable


@pytest.mark.parametrize(("descuento", "volumen"), [(0, 15), (100, 15), (10, -1)])
def test_entradas_fuera_de_rango(descuento: int, volumen: int) -> None:
    r = _sintetico(descuento=descuento, volumen=volumen)
    assert r.no_calculable is not None
    assert r.cifras == ()


def test_sin_ventas_no_es_calculable() -> None:
    resultados = _lectura([("Utilidad neta", "utilidad_neta", "200", "200")])
    revision = revisar_estados([_lectura(_balance())], resultados, respuestas=ACUMULADO, hoy=HOY)
    r = precio_contra_volumen(EstadosRevisados(revision=revision, resultados=resultados))
    assert r.no_calculable is not None
    assert r.cifras == ()
