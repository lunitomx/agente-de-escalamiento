"""ESCALA pone cada cuenta del balance en su caja (S86.15).

Según el curso de cash que vimos, el balance se lee en 4 cajas:

- **Capital de trabajo** = clientes + inventario − proveedores.
- **Deuda neta** = préstamos que pagan interés (bancos, sobregiro) − bancos.
- **Otras cuentas** = todo lo demás (deudores, anticipos, impuestos, activo
  fijo, diferidos, acreedores, documentos que no pagan interés).
- **Capital** = capital social, reservas y resultados.

Las cajas de uso (capital de trabajo, otras cuentas) suman el activo y restan
el pasivo. Las cajas de fuente (deuda neta, capital) suman el pasivo y el
capital y restan el activo. Si el balance cuadra:
capital de trabajo + otras cuentas = deuda neta + capital.

Cada cuenta se acomoda por una regla escrita, con su porqué. Aquí no se calcula
ningún indicador: sólo se acomoda y se suma por caja.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .formatos import coincide
from .lector import CuentaLeida

Caja = Literal["capital de trabajo", "deuda neta", "otras cuentas", "capital"]
Lado = Literal["activo", "pasivo", "capital"]
CAJAS: tuple[Caja, ...] = ("capital de trabajo", "deuda neta", "otras cuentas", "capital")
_CAJAS_DE_USO: frozenset[Caja] = frozenset({"capital de trabajo", "otras cuentas"})


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


@dataclass(frozen=True)
class Regla:
    """Cómo se reconoce una cuenta y en qué caja va."""

    clave: str
    frases: tuple[str, ...]
    lado: Lado
    caja: Caja
    porque: str
    exclusiones: tuple[str, ...] = ()
    # Si es True, ESCALA pregunta (C11) si la cuenta paga interés.
    pregunta_interes: bool = False


_ANTICIPOS = ("anticipo", "anticipos")

REGLAS: tuple[Regla, ...] = (
    Regla(
        "bancos",
        ("bancos", "banco", "caja", "caja y bancos", "efectivo", "efectivo y equivalentes"),
        "activo",
        "deuda neta",
        "El efectivo resta a la deuda: es dinero con el que podrías pagarla.",
        exclusiones=("sobregiro", "prestamo", "prestamos"),
    ),
    Regla(
        "clientes",
        ("clientes", "cuentas por cobrar", "cuentas por cobrar a clientes"),
        "activo",
        "capital de trabajo",
        "Es lo que tus clientes te deben por ventas: dinero de la operación.",
        exclusiones=_ANTICIPOS,
    ),
    Regla(
        "inventario",
        ("inventario", "inventarios", "almacen", "mercancias"),
        "activo",
        "capital de trabajo",
        "Es mercancía que compraste para vender: dinero de la operación.",
    ),
    Regla(
        "proveedores",
        ("proveedores", "cuentas por pagar"),
        "pasivo",
        "capital de trabajo",
        "Es lo que debes a tus proveedores por compras: financia la operación sin interés.",
        exclusiones=_ANTICIPOS,
    ),
    Regla(
        "prestamos",
        (
            "prestamo",
            "prestamos",
            "prestamo bancario",
            "prestamos bancarios",
            "credito bancario",
            "creditos bancarios",
        ),
        "pasivo",
        "deuda neta",
        "Es un préstamo que paga interés: es deuda.",
    ),
    Regla(
        "sobregiro",
        ("sobregiro", "sobregiros", "sobregiro bancario"),
        "pasivo",
        "deuda neta",
        "Un sobregiro es un préstamo del banco: paga interés y es deuda.",
    ),
    Regla(
        "documentos_por_pagar",
        ("documentos por pagar",),
        "pasivo",
        "otras cuentas",
        "Va en otras cuentas, como en el curso. Si paga interés, es deuda: por eso te pregunto.",
        pregunta_interes=True,
    ),
    Regla(
        "anticipo_de_clientes",
        ("anticipo de clientes", "anticipos de clientes"),
        "pasivo",
        "otras cuentas",
        "Es dinero que tus clientes ya te pagaron por algo que no has entregado; no es deuda con el banco.",
    ),
    Regla(
        "anticipo_a_proveedores",
        ("anticipo a proveedores", "anticipos a proveedores"),
        "activo",
        "otras cuentas",
        "Es dinero que ya pagaste por algo que todavía no recibes.",
    ),
    Regla(
        "acreedores",
        ("acreedores", "acreedores diversos", "otras cuentas por pagar"),
        "pasivo",
        "otras cuentas",
        "Es una deuda que no es con proveedores ni con el banco.",
    ),
    Regla(
        "impuestos_por_pagar",
        (
            "impuestos por pagar",
            "contribuciones por pagar",
            "iva por pagar",
            "isr por pagar",
            "ptu por pagar",
        ),
        "pasivo",
        "otras cuentas",
        "Son impuestos que vas a pagar; no son operación ni deuda con el banco.",
    ),
    Regla(
        "deudores",
        (
            "deudores",
            "deudores diversos",
            "otras cuentas por cobrar",
            "iva por acreditar",
            "impuestos a favor",
            "pagos anticipados",
        ),
        "activo",
        "otras cuentas",
        "Es dinero que te deben y no viene de ventas a clientes.",
    ),
    Regla(
        "otros_activos",
        ("otros activos", "otros activos circulantes"),
        "activo",
        "otras cuentas",
        "No es clientes, inventario ni bancos: va en otras cuentas.",
    ),
    Regla(
        "activo_fijo",
        (
            "activo fijo",
            "propiedades",
            "inmuebles",
            "maquinaria",
            "equipo",
            "terrenos",
            "edificios",
        ),
        "activo",
        "otras cuentas",
        "Es lo que usas para trabajar (maquinaria, edificios): no es operación del día a día.",
    ),
    Regla(
        "activo_diferido",
        ("activo diferido", "cargos diferidos", "gastos anticipados", "depositos en garantia"),
        "activo",
        "otras cuentas",
        "Son pagos hechos por adelantado: van en otras cuentas.",
    ),
    Regla(
        "capital",
        (
            "capital",
            "capital social",
            "capital contable",
            "reserva",
            "reservas",
            "reserva legal",
            "aportaciones",
            "resultados de ejercicios anteriores",
            "utilidades acumuladas",
            "otras cuentas de capital",
        ),
        "capital",
        "capital",
        "Es el dinero que los socios pusieron o dejaron en la empresa.",
    ),
    Regla(
        "resultado_del_ejercicio",
        (
            "utilidad del ejercicio",
            "resultado del ejercicio",
            "perdida del ejercicio",
        ),
        "capital",
        "capital",
        "Es la utilidad del año que se queda en la empresa: es capital.",
    ),
)

_POR_CLAVE = {regla.clave: regla for regla in REGLAS}


def regla_de(nombre: str) -> Regla | None:
    """La regla con la frase más larga que coincide (palabra completa); ``None`` si ninguna."""

    mejor: tuple[int, Regla] | None = None
    for regla in REGLAS:
        largo = coincide(nombre, regla.frases, regla.exclusiones)
        if largo and (mejor is None or largo > mejor[0]):
            mejor = (largo, regla)
    return mejor[1] if mejor else None


def regla_por_clave(clave: str) -> Regla:
    return _POR_CLAVE[clave]


class CuentaEnCaja(_Modelo):
    nombre: str
    monto: Decimal
    fecha: date | None
    renglon: int
    hoja: str
    regla: str | None
    lado: Lado | None
    caja: Caja | None
    # La caja que dice la regla; distinta de ``caja`` si el dueño la movió.
    caja_por_regla: Caja | None
    movida: bool = False
    pregunta_interes: bool = False
    porque: str


class TotalesPorCaja(_Modelo):
    """Suma por caja a una fecha. Fórmula de cada caja en el docstring del módulo."""

    fecha: date
    capital_de_trabajo: Decimal
    deuda_neta: Decimal
    otras_cuentas: Decimal
    capital: Decimal
    activo: Decimal
    pasivo: Decimal
    capital_contable: Decimal

    def de(self, caja: Caja) -> Decimal:
        return {
            "capital de trabajo": self.capital_de_trabajo,
            "deuda neta": self.deuda_neta,
            "otras cuentas": self.otras_cuentas,
            "capital": self.capital,
        }[caja]


class Acomodo(_Modelo):
    cuentas: tuple[CuentaEnCaja, ...]
    totales_del_documento: tuple[CuentaLeida, ...]
    totales: tuple[TotalesPorCaja, ...]

    def en(self, fecha: date) -> TotalesPorCaja | None:
        return next((total for total in self.totales if total.fecha == fecha), None)

    @property
    def fechas(self) -> tuple[date, ...]:
        return tuple(total.fecha for total in self.totales)


def con_signo(lado: Lado, caja: Caja, monto: Decimal) -> Decimal:
    if caja in _CAJAS_DE_USO:
        return monto if lado == "activo" else -monto
    return -monto if lado == "activo" else monto


def _acomodar_una(
    cuenta: CuentaLeida,
    movimientos: dict[str, Caja],
    con_interes: dict[str, bool],
) -> CuentaEnCaja:
    regla = regla_de(cuenta.nombre)
    if regla is None:
        return CuentaEnCaja(
            nombre=cuenta.nombre,
            monto=cuenta.monto,
            fecha=cuenta.fecha,
            renglon=cuenta.renglon,
            hoja=cuenta.hoja,
            regla=None,
            lado=None,
            caja=None,
            caja_por_regla=None,
            porque="Ninguna regla la reconoce: necesito que me digas qué es.",
        )
    caja: Caja = regla.caja
    porque = regla.porque
    movida = False
    if cuenta.nombre in movimientos and movimientos[cuenta.nombre] != regla.caja:
        caja = movimientos[cuenta.nombre]
        movida = True
        porque = f"La moviste tú a {caja}. Por regla iba en {regla.caja}: {regla.porque}"
    elif regla.pregunta_interes and con_interes.get(cuenta.nombre) is True:
        caja = "deuda neta"
        porque = "Me dijiste que paga interés: es deuda, va en deuda neta."
    elif regla.pregunta_interes and con_interes.get(cuenta.nombre) is False:
        porque = "Me dijiste que no paga interés: se queda en otras cuentas."
    return CuentaEnCaja(
        nombre=cuenta.nombre,
        monto=cuenta.monto,
        fecha=cuenta.fecha,
        renglon=cuenta.renglon,
        hoja=cuenta.hoja,
        regla=regla.clave,
        lado=regla.lado,
        caja=caja,
        caja_por_regla=regla.caja,
        movida=movida,
        pregunta_interes=regla.pregunta_interes,
        porque=porque,
    )


def _totales(fecha: date, cuentas: list[CuentaEnCaja]) -> TotalesPorCaja:
    por_caja: dict[Caja, Decimal] = {caja: Decimal("0") for caja in CAJAS}
    por_lado: dict[Lado, Decimal] = {
        "activo": Decimal("0"),
        "pasivo": Decimal("0"),
        "capital": Decimal("0"),
    }
    for cuenta in cuentas:
        if cuenta.lado is None or cuenta.caja is None:
            continue
        por_caja[cuenta.caja] += con_signo(cuenta.lado, cuenta.caja, cuenta.monto)
        por_lado[cuenta.lado] += cuenta.monto
    return TotalesPorCaja(
        fecha=fecha,
        capital_de_trabajo=por_caja["capital de trabajo"],
        deuda_neta=por_caja["deuda neta"],
        otras_cuentas=por_caja["otras cuentas"],
        capital=por_caja["capital"],
        activo=por_lado["activo"],
        pasivo=por_lado["pasivo"],
        capital_contable=por_lado["capital"],
    )


def acomodar(
    cuentas: tuple[CuentaLeida, ...] | list[CuentaLeida],
    *,
    movimientos: dict[str, Caja] | None = None,
    con_interes: dict[str, bool] | None = None,
) -> Acomodo:
    """Acomoda cada cuenta del balance en su caja y suma cada caja por fecha.

    ``movimientos``: cuentas que el dueño movió de caja (nombre → caja).
    ``con_interes``: respuesta C11 por cuenta (nombre → ¿paga interés?).
    Los totales del documento no se acomodan: se guardan para revisar (R3).
    """

    movidas = movimientos or {}
    interes = con_interes or {}
    acomodadas = [
        _acomodar_una(cuenta, movidas, interes) for cuenta in cuentas if not cuenta.es_total
    ]
    fechas = sorted({cuenta.fecha for cuenta in acomodadas if cuenta.fecha is not None})
    return Acomodo(
        cuentas=tuple(acomodadas),
        totales_del_documento=tuple(cuenta for cuenta in cuentas if cuenta.es_total),
        totales=tuple(
            _totales(fecha, [c for c in acomodadas if c.fecha == fecha]) for fecha in fechas
        ),
    )
