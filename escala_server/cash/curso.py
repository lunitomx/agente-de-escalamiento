"""La calculadora del curso de cash (S86.16). Una sola, para todos los paquetes.

Toma los estados ya revisados (S86.15: cada cuenta en su caja, el periodo
confirmado) y devuelve cada número del curso con:

- su valor,
- su fórmula en palabras,
- de dónde sale, con las cifras («sale de: clientes 5,639,601.55 ÷ (ventas …)»),
- la lámina del curso.

Si un número no se puede calcular, lo dice con la razón (``no_calculable``) o
dice que no aplica a este negocio (``no_aplica``). Nunca pone 0 en su lugar.

Una sola definición de cada cosa:

- Las cajas (capital de trabajo, deuda neta, otras cuentas, capital) vienen de
  ``escala_server.financial.cajas``.
- El poder del uno lo calcula ``PowerOfOneEngine`` (S86.13).
- Los días usan los días reales del periodo revisado. Nunca ×12.

Entrada interna: ``python -m escala_server.cash.curso <estados-revisados.json>``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
import json
from pathlib import Path
import sys
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from escala_server.cash import (
    LEVER_META,
    FinancialInputs,
    LeverImpact,
    PowerOfOneEngine,
    lever_parts,
)
from escala_server.financial.cajas import Caja, CuentaEnCaja, TotalesPorCaja, con_signo
from escala_server.financial.formatos import fecha_corta, formato_monto
from escala_server.financial.lector import LecturaEstados
from escala_server.financial.revisiones import PeriodoDelEstado, RevisionDeEstados

CENTAVO = Decimal("0.01")
DIEZMILESIMO = Decimal("0.0001")
CERO = Decimal("0")
CIEN = Decimal("100")

Unidad = Literal["pesos", "días", "por cada 100 de ventas", "proporción", "%"]


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Calculado(_Modelo):
    clave: str
    nombre: str
    fecha: date
    valor: Decimal
    unidad: Unidad
    formula: str
    origen: str
    lamina: str


class NoCalculable(_Modelo):
    clave: str
    nombre: str
    fecha: date | None
    formula: str
    lamina: str
    no_calculable: str


class NoAplica(_Modelo):
    clave: str
    nombre: str
    fecha: date | None
    formula: str
    lamina: str
    no_aplica: str


Indicador = Calculado | NoCalculable | NoAplica


class Palanca(_Modelo):
    palanca: str
    nombre: str
    flujo: Indicador
    utilidad: Indicador


class Coeficiente(_Modelo):
    """Pesos que deja mover una palanca 1 punto (1% o 1 día), sin redondear (S86.22)."""

    clave: str
    nombre: str
    valor: Decimal
    formula: str
    origen: str
    lamina: str


ParteDelSimulador = Coeficiente | NoCalculable | NoAplica


class PalancaDelSimulador(_Modelo):
    """Los dos lados de una palanca para el simulador (S86.22).

    ``por_periodo`` es utilidad y se repite cada periodo; ``una_vez`` es lo que
    se queda o se libera una sola vez en clientes, inventario o proveedores.
    """

    palanca: str
    lever: str
    nombre: str
    unidad: Literal["%", "días"]
    mejora: str
    por_periodo: ParteDelSimulador
    una_vez: ParteDelSimulador


class DatosDelDueno(_Modelo):
    """Montos que sólo el dueño sabe (S86.24). ``None`` = todavía no lo dice.

    Todos son del mismo periodo que el estado de resultados. ESCALA no los supone.
    """

    salario_de_mercado: Decimal | None = Field(default=None, ge=0)
    sueldo_actual_del_dueno: Decimal | None = Field(default=None, ge=0)
    devoluciones: Decimal | None = Field(default=None, ge=0)


class PreguntaDelDueno(_Modelo):
    clave: Literal["salario_de_mercado", "sueldo_actual_del_dueno", "devoluciones"]
    pregunta: str
    para_que: str


class BloqueDelMargen(_Modelo):
    """Margen antes de impuestos, salario de mercado y devoluciones (S86.24, L75–L79).

    ``por_encima_de_la_linea`` compara el valor sin redondear contra la línea
    de referencia (10% o más = sí). ``None`` cuando el margen no se calcula.
    """

    fecha: date
    pretax: Indicador
    linea_de_referencia: Decimal
    por_encima_de_la_linea: bool | None
    sobre_utilidad_bruta: Indicador
    devoluciones: Indicador
    salario_de_mercado: Decimal | None
    sueldo_actual_del_dueno: Decimal | None
    utilidad_real: Indicador
    pretax_con_salario: Indicador
    por_encima_de_la_linea_con_salario: bool | None
    isr: Indicador
    nota_fiscal: str
    preguntas: tuple[PreguntaDelDueno, ...] = ()


class EstadosRevisados(_Modelo):
    """Lo que recibe la calculadora: la revisión de S86.15 y el estado de resultados."""

    revision: RevisionDeEstados
    resultados: LecturaEstados
    del_dueno: DatosDelDueno | None = None


class ResultadoDelCurso(_Modelo):
    no_calculable: str | None = None
    periodo: PeriodoDelEstado | None = None
    balance_inicial: date | None = None
    balance_final: date | None = None
    indicadores: tuple[Indicador, ...] = ()
    poder_del_uno: tuple[Palanca, ...] = ()
    poder_del_uno_flujo: Indicador | None = None
    poder_del_uno_utilidad: Indicador | None = None
    pendientes: tuple[str, ...] = ()
    simulador: tuple[PalancaDelSimulador, ...] = ()
    margen: BloqueDelMargen | None = None

    def del_simulador(self, clave: str) -> PalancaDelSimulador:
        for palanca in self.simulador:
            if palanca.palanca == clave:
                return palanca
        raise KeyError(clave)

    def indicador(self, clave: str, fecha: date) -> Indicador:
        for indicador in self.indicadores:
            if indicador.clave == clave and indicador.fecha == fecha:
                return indicador
        raise KeyError(f"{clave} al {fecha.isoformat()}")

    def palanca(self, clave: str) -> Palanca:
        for palanca in self.poder_del_uno:
            if palanca.palanca == clave:
                return palanca
        raise KeyError(clave)


# ---------------------------------------------------------------------------
# Definiciones: nombre, fórmula en palabras, lámina, unidad
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Definicion:
    clave: str
    nombre: str
    formula: str
    lamina: str
    unidad: Unidad


def _def(clave: str, nombre: str, formula: str, lamina: str, unidad: Unidad) -> _Definicion:
    return _Definicion(clave, nombre, formula, lamina, unidad)


UTILIDAD_BRUTA = _def("utilidad_bruta", "Utilidad bruta", "ventas − costo de ventas", "L11", "pesos")
UTILIDAD_DE_OPERACION = _def(
    "utilidad_de_operacion",
    "Utilidad de operación",
    "utilidad bruta − gastos de operación",
    "L11",
    "pesos",
)
CAPITAL_DE_TRABAJO = _def(
    "capital_de_trabajo",
    "Capital de trabajo",
    "clientes + inventario − proveedores (las cuentas de la caja de capital de trabajo)",
    "L18",
    "pesos",
)
DEUDA_NETA = _def(
    "deuda_neta",
    "Deuda neta",
    "préstamos que pagan interés − bancos",
    "L18",
    "pesos",
)
OTRAS_CUENTAS = _def(
    "otras_cuentas",
    "Otras cuentas",
    "lo que queda: deuda neta + capital − capital de trabajo",
    "L56",
    "pesos",
)
FINANCIAMIENTO = _def(
    "financiamiento",
    "Financiamiento",
    "deuda neta + capital (es igual a capital de trabajo + otras cuentas)",
    "L16 y L19",
    "pesos",
)
DIAS_CLIENTES = _def(
    "dias_clientes", "Días de clientes", "clientes ÷ (ventas ÷ días del periodo)", "L49", "días"
)
DIAS_INVENTARIO = _def(
    "dias_inventario",
    "Días de inventario",
    "inventario ÷ (costo de ventas ÷ días del periodo)",
    "L49",
    "días",
)
DIAS_PROVEEDORES = _def(
    "dias_proveedores",
    "Días de proveedores",
    "proveedores ÷ (costo de ventas ÷ días del periodo)",
    "L49",
    "días",
)
CICLO = _def(
    "ciclo",
    "Ciclo del efectivo",
    "días de clientes + días de inventario − días de proveedores",
    "L52",
    "días",
)
CAMBIO_CT = _def(
    "cambio_capital_de_trabajo",
    "Cambio en capital de trabajo",
    "capital de trabajo al final − capital de trabajo al inicio",
    "L46",
    "pesos",
)
FLUJO_NETO = _def(
    "flujo_neto",
    "Flujo neto",
    "−(deuda neta al final − deuda neta al inicio)",
    "L25 y L58",
    "pesos",
)
FLUJO_DE_OPERACION = _def(
    "flujo_de_operacion",
    "Flujo de operación",
    "utilidad de operación − cambio en capital de trabajo",
    "L61",
    "pesos",
)
MARGEN_BRUTO = _def(
    "margen_bruto", "Utilidad bruta por peso de venta", "utilidad bruta ÷ ventas", "L63", "proporción"
)
CT_POR_VENTAS = _def(
    "capital_de_trabajo_por_ventas",
    "Capital de trabajo por peso de venta",
    "capital de trabajo ÷ ventas",
    "L63",
    "proporción",
)
MARGINAL = _def(
    "marginal",
    "Flujo marginal",
    "utilidad bruta ÷ ventas − capital de trabajo ÷ ventas",
    "L63",
    "proporción",
)


def _por_cada_100(clave: str, nombre: str) -> _Definicion:
    return _def(
        f"{clave}_por_cada_100",
        f"{nombre} por cada 100 de ventas",
        f"100 × {nombre.lower()} ÷ ventas",
        "L54",
        "por cada 100 de ventas",
    )


POR_CADA_100 = (
    ("clientes", _por_cada_100("clientes", "Clientes")),
    ("inventario", _por_cada_100("inventario", "Inventario")),
    ("proveedores", _por_cada_100("proveedores", "Proveedores")),
)
CT_POR_CADA_100 = _por_cada_100("capital_de_trabajo", "Capital de trabajo")

LAMINA_PODER_DEL_UNO = "L36, L37 y L70"

# Palanca del motor (S86.13) → (clave, nombre, fórmula del flujo, fórmula de la utilidad)
PALANCAS: dict[str, tuple[str, str, str, str]] = {
    "price": ("precio", "Precio +1%", "1% × ventas − 1% × clientes", "1% × ventas"),
    "volume": (
        "volumen",
        "Volumen +1%",
        "1% × utilidad bruta − 1% × capital de trabajo",
        "1% × utilidad bruta",
    ),
    "cogs": (
        "costo",
        "Costo de ventas −1%",
        "1% × costo de ventas + 1% × (inventario − proveedores)",
        "1% × costo de ventas",
    ),
    "opex": ("gastos", "Gastos de operación −1%", "1% × gastos de operación", "1% × gastos de operación"),
    "ar_days": (
        "clientes",
        "Clientes −1 día",
        "1 día × ventas ÷ días del periodo",
        "mover días no cambia la utilidad",
    ),
    "inv_days": (
        "inventario",
        "Inventario −1 día",
        "1 día × costo de ventas ÷ días del periodo",
        "mover días no cambia la utilidad",
    ),
    "ap_days": (
        "proveedores",
        "Proveedores +1 día",
        "1 día × costo de ventas ÷ días del periodo",
        "mover días no cambia la utilidad",
    ),
}


# ---------------------------------------------------------------------------
# Cifras con su origen
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Cifra:
    """Un monto sin redondear y cómo se escribe en el origen."""

    valor: Decimal
    texto: str
    existe: bool = True


def _dinero(valor: Decimal) -> str:
    return formato_monto(valor.quantize(CENTAVO, rounding=ROUND_HALF_UP))


def _redondea(valor: Decimal, unidad: Unidad) -> Decimal:
    paso = DIEZMILESIMO if unidad == "proporción" else CENTAVO
    return valor.quantize(paso, rounding=ROUND_HALF_UP)


def _calculado(definicion: _Definicion, fecha: date, valor: Decimal, origen: str) -> Calculado:
    return Calculado(
        clave=definicion.clave,
        nombre=definicion.nombre,
        fecha=fecha,
        valor=_redondea(valor, definicion.unidad),
        unidad=definicion.unidad,
        formula=definicion.formula,
        origen=f"sale de: {origen}",
        lamina=definicion.lamina,
    )


def _no_calculable(definicion: _Definicion, fecha: date | None, razon: str) -> NoCalculable:
    return NoCalculable(
        clave=definicion.clave,
        nombre=definicion.nombre,
        fecha=fecha,
        formula=definicion.formula,
        lamina=definicion.lamina,
        no_calculable=razon,
    )


def _no_aplica(definicion: _Definicion, fecha: date | None, razon: str) -> NoAplica:
    return NoAplica(
        clave=definicion.clave,
        nombre=definicion.nombre,
        fecha=fecha,
        formula=definicion.formula,
        lamina=definicion.lamina,
        no_aplica=razon,
    )


_ETIQUETAS = {
    "ventas": "ventas",
    "costo_ventas": "costo de ventas",
    "gastos_operacion": "gastos de operación",
    "utilidad_antes_impuestos": "utilidad antes de impuestos",
    "isr": "ISR",
}


def _del_resultado(resultados: LecturaEstados, concepto: str, fecha: date) -> _Cifra | None:
    """Suma los renglones de un concepto en el estado de resultados a una fecha."""

    etiqueta = _ETIQUETAS[concepto]
    del_concepto = [
        c for c in resultados.cuentas if c.concepto == concepto and c.fecha == fecha
    ]
    renglones = [c for c in del_concepto if not c.es_total] or del_concepto[:1]
    if not renglones:
        return None
    total = sum((c.monto for c in renglones), CERO)
    texto = f"{etiqueta} {_dinero(total)}"
    if len(renglones) > 1:
        partes = " + ".join(f"{c.nombre} {_dinero(c.monto)}" for c in renglones)
        texto = f"{texto} ({partes})"
    return _Cifra(total, texto)


def _o_cero(cifra: _Cifra | None, concepto: str) -> _Cifra:
    if cifra is not None:
        return cifra
    etiqueta = _ETIQUETAS[concepto]
    return _Cifra(CERO, f"{etiqueta} 0.00 (tu estado no trae {etiqueta})", existe=False)


def _del_balance(cuentas: list[CuentaEnCaja], regla: str, etiqueta: str) -> _Cifra:
    de_la_regla = [c for c in cuentas if c.regla == regla and c.caja == "capital de trabajo"]
    total = sum((c.monto for c in de_la_regla), CERO)
    return _Cifra(total, f"{etiqueta} {_dinero(total)}", existe=bool(de_la_regla))


def _origen_de_caja(cuentas: list[CuentaEnCaja], caja: Caja) -> str:
    con_signo_por_cuenta = [
        (con_signo(cuenta.lado, caja, cuenta.monto), cuenta.nombre)
        for cuenta in cuentas
        if cuenta.caja == caja and cuenta.lado is not None
    ]
    # Primero lo que suma, luego lo que resta: «préstamos − bancos».
    con_signo_por_cuenta.sort(key=lambda par: par[0] < 0)
    partes = [
        f"{'−' if monto < 0 else '+'} {nombre} {_dinero(abs(monto))}"
        for monto, nombre in con_signo_por_cuenta
    ]
    if not partes:
        return "no hay cuentas en esta caja (0.00)"
    texto = " ".join(partes)
    return texto[2:] if texto.startswith("+ ") else texto


# ---------------------------------------------------------------------------
# Indicadores por fecha
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Fecha:
    fecha: date
    totales: TotalesPorCaja
    cuentas: list[CuentaEnCaja]
    ventas: _Cifra | None
    costo: _Cifra
    gastos: _Cifra
    clientes: _Cifra
    inventario: _Cifra
    proveedores: _Cifra


def _datos(revision: RevisionDeEstados, resultados: LecturaEstados, fecha: date) -> _Fecha | None:
    totales = revision.acomodo.en(fecha)
    if totales is None:
        return None
    cuentas = [c for c in revision.acomodo.cuentas if c.fecha == fecha]
    return _Fecha(
        fecha=fecha,
        totales=totales,
        cuentas=cuentas,
        ventas=_del_resultado(resultados, "ventas", fecha),
        costo=_o_cero(_del_resultado(resultados, "costo_ventas", fecha), "costo_ventas"),
        gastos=_o_cero(_del_resultado(resultados, "gastos_operacion", fecha), "gastos_operacion"),
        clientes=_del_balance(cuentas, "clientes", "clientes"),
        inventario=_del_balance(cuentas, "inventario", "inventario"),
        proveedores=_del_balance(cuentas, "proveedores", "proveedores"),
    )


def _falta_ventas(fecha: date) -> str:
    return f"falta el renglón de ventas del estado de resultados al {fecha_corta(fecha)}"


def _ventas_en_cero(fecha: date) -> str:
    return (
        f"las ventas al {fecha_corta(fecha)} son 0 o menos: "
        "no se puede dividir entre las ventas"
    )


def _cajas(d: _Fecha) -> list[Indicador]:
    t = d.totales
    otras = t.deuda_neta + t.capital - t.capital_de_trabajo
    return [
        _calculado(
            CAPITAL_DE_TRABAJO,
            d.fecha,
            t.capital_de_trabajo,
            _origen_de_caja(d.cuentas, "capital de trabajo"),
        ),
        _calculado(DEUDA_NETA, d.fecha, t.deuda_neta, _origen_de_caja(d.cuentas, "deuda neta")),
        _calculado(
            OTRAS_CUENTAS,
            d.fecha,
            otras,
            f"deuda neta {_dinero(t.deuda_neta)} + capital {_dinero(t.capital)}"
            f" − capital de trabajo {_dinero(t.capital_de_trabajo)}",
        ),
        _calculado(
            FINANCIAMIENTO,
            d.fecha,
            t.deuda_neta + t.capital,
            f"deuda neta {_dinero(t.deuda_neta)} + capital {_dinero(t.capital)}",
        ),
    ]


def _utilidad_bruta(d: _Fecha) -> _Cifra | None:
    if d.ventas is None:
        return None
    return _Cifra(d.ventas.valor - d.costo.valor, f"{d.ventas.texto} − {d.costo.texto}")


def _utilidades(d: _Fecha) -> list[Indicador]:
    ub = _utilidad_bruta(d)
    if ub is None:
        razon = _falta_ventas(d.fecha)
        return [
            _no_calculable(UTILIDAD_BRUTA, d.fecha, razon),
            _no_calculable(UTILIDAD_DE_OPERACION, d.fecha, razon),
        ]
    return [
        _calculado(UTILIDAD_BRUTA, d.fecha, ub.valor, ub.texto),
        _calculado(
            UTILIDAD_DE_OPERACION,
            d.fecha,
            ub.valor - d.gastos.valor,
            f"utilidad bruta {_dinero(ub.valor)} − {d.gastos.texto}",
        ),
    ]


def _dias(
    definicion: _Definicion,
    cuenta: _Cifra,
    base: _Cifra | None,
    fecha: date,
    dias: int | None,
    etiqueta: str,
) -> Indicador:
    nombre = cuenta.texto.split(" ")[0]
    if not cuenta.existe or cuenta.valor == 0:
        return _no_aplica(definicion, fecha, f"no tienes {nombre} en el balance al {fecha_corta(fecha)}")
    if dias is None:
        return _no_calculable(definicion, fecha, "falta confirmar qué periodo cubre tu estado de resultados")
    if base is None:
        return _no_calculable(definicion, fecha, _falta_ventas(fecha))
    if not base.existe:
        return _no_calculable(
            definicion,
            fecha,
            f"tienes {nombre} pero tu estado de resultados no trae {etiqueta}",
        )
    if base.valor <= 0:
        return _no_calculable(
            definicion,
            fecha,
            f"{etiqueta} al {fecha_corta(fecha)} es 0 o menos: no se puede dividir entre él",
        )
    valor = cuenta.valor / (base.valor / dias)
    return _calculado(definicion, fecha, valor, f"{cuenta.texto} ÷ ({base.texto} ÷ {dias})")


def _ciclo(partes: list[tuple[str, str, Indicador]], fecha: date) -> Indicador:
    for _, _, parte in partes:
        if isinstance(parte, NoCalculable):
            return _no_calculable(
                CICLO, fecha, f"no se pueden calcular los {parte.nombre.lower()}: {parte.no_calculable}"
            )
    if all(isinstance(parte, NoAplica) for _, _, parte in partes):
        return _no_aplica(CICLO, fecha, "no tienes clientes, inventario ni proveedores en el balance")
    total = CERO
    textos: list[str] = []
    for signo, nombre, parte in partes:
        prefijo = "" if not textos else f"{signo} "
        if isinstance(parte, Calculado):
            total += parte.valor if signo == "+" else -parte.valor
            textos.append(f"{prefijo}{nombre} {formato_monto(parte.valor)}")
        else:
            textos.append(f"{prefijo}{nombre} no aplica (cuenta 0)")
    return _calculado(CICLO, fecha, total, " ".join(textos))


def _dias_y_ciclo(d: _Fecha, dias: int | None) -> list[Indicador]:
    clientes = _dias(DIAS_CLIENTES, d.clientes, d.ventas, d.fecha, dias, "ventas")
    inventario = _dias(DIAS_INVENTARIO, d.inventario, d.costo, d.fecha, dias, "costo de ventas")
    proveedores = _dias(
        DIAS_PROVEEDORES, d.proveedores, d.costo, d.fecha, dias, "costo de ventas"
    )
    ciclo = _ciclo(
        [
            ("+", "días de clientes", clientes),
            ("+", "días de inventario", inventario),
            ("−", "días de proveedores", proveedores),
        ],
        d.fecha,
    )
    return [clientes, inventario, proveedores, ciclo]


def _sobre_ventas(d: _Fecha) -> list[Indicador]:
    definiciones = [definicion for _, definicion in POR_CADA_100]
    definiciones += [CT_POR_CADA_100, MARGEN_BRUTO, CT_POR_VENTAS, MARGINAL]
    if d.ventas is None or d.ventas.valor <= 0:
        razon = _falta_ventas(d.fecha) if d.ventas is None else _ventas_en_cero(d.fecha)
        return [_no_calculable(definicion, d.fecha, razon) for definicion in definiciones]
    ventas = d.ventas
    indicadores: list[Indicador] = []
    for cuenta, definicion in (
        (d.clientes, POR_CADA_100[0][1]),
        (d.inventario, POR_CADA_100[1][1]),
        (d.proveedores, POR_CADA_100[2][1]),
    ):
        if not cuenta.existe:
            indicadores.append(
                _no_aplica(definicion, d.fecha, f"no tienes {cuenta.texto.split(' ')[0]} en el balance")
            )
            continue
        indicadores.append(
            _calculado(
                definicion,
                d.fecha,
                CIEN * cuenta.valor / ventas.valor,
                f"100 × {cuenta.texto} ÷ {ventas.texto}",
            )
        )
    ct = d.totales.capital_de_trabajo
    indicadores.append(
        _calculado(
            CT_POR_CADA_100,
            d.fecha,
            CIEN * ct / ventas.valor,
            f"100 × capital de trabajo {_dinero(ct)} ÷ {ventas.texto}",
        )
    )
    ub = ventas.valor - d.costo.valor
    margen = ub / ventas.valor
    ct_ventas = ct / ventas.valor
    indicadores += [
        _calculado(MARGEN_BRUTO, d.fecha, margen, f"utilidad bruta {_dinero(ub)} ÷ {ventas.texto}"),
        _calculado(
            CT_POR_VENTAS,
            d.fecha,
            ct_ventas,
            f"capital de trabajo {_dinero(ct)} ÷ {ventas.texto}",
        ),
        _calculado(
            MARGINAL,
            d.fecha,
            margen - ct_ventas,
            f"utilidad bruta {_dinero(ub)} ÷ {ventas.texto}"
            f" − capital de trabajo {_dinero(ct)} ÷ {ventas.texto}",
        ),
    ]
    return indicadores


def _flujos(inicial: _Fecha | None, final: _Fecha) -> list[Indicador]:
    fecha = final.fecha
    if inicial is None:
        razon = "falta el balance al inicio del periodo"
        return [
            _no_calculable(CAMBIO_CT, fecha, razon),
            _no_calculable(FLUJO_NETO, fecha, razon),
            _no_calculable(FLUJO_DE_OPERACION, fecha, razon),
        ]
    ct_fin = final.totales.capital_de_trabajo
    ct_ini = inicial.totales.capital_de_trabajo
    cambio = ct_fin - ct_ini
    dn_fin = final.totales.deuda_neta
    dn_ini = inicial.totales.deuda_neta
    indicadores: list[Indicador] = [
        _calculado(
            CAMBIO_CT,
            fecha,
            cambio,
            f"capital de trabajo al {fecha_corta(fecha)} {_dinero(ct_fin)}"
            f" − capital de trabajo al {fecha_corta(inicial.fecha)} {_dinero(ct_ini)}",
        ),
        _calculado(
            FLUJO_NETO,
            fecha,
            -(dn_fin - dn_ini),
            f"−(deuda neta al {fecha_corta(fecha)} {_dinero(dn_fin)}"
            f" − deuda neta al {fecha_corta(inicial.fecha)} {_dinero(dn_ini)})",
        ),
    ]
    ub = _utilidad_bruta(final)
    if ub is None:
        indicadores.append(_no_calculable(FLUJO_DE_OPERACION, fecha, _falta_ventas(fecha)))
    else:
        uo = ub.valor - final.gastos.valor
        indicadores.append(
            _calculado(
                FLUJO_DE_OPERACION,
                fecha,
                uo - cambio,
                f"utilidad de operación {_dinero(uo)} − cambio en capital de trabajo {_dinero(cambio)}",
            )
        )
    return indicadores


# ---------------------------------------------------------------------------
# Poder del uno (motor de S86.13)
# ---------------------------------------------------------------------------


def _palanca_def(lever: str, flujo: bool) -> _Definicion:
    clave, nombre, formula_flujo, formula_utilidad = PALANCAS[lever]
    sufijo = "flujo" if flujo else "utilidad"
    return _def(
        f"poder_del_uno.{clave}.{sufijo}",
        f"{nombre}: {sufijo}",
        formula_flujo if flujo else formula_utilidad,
        LAMINA_PODER_DEL_UNO,
        "pesos",
    )


def _sin_palanca(lever: str, fecha: date, motivo: Indicador) -> Palanca:
    clave, nombre, _, _ = PALANCAS[lever]
    partes: list[Indicador] = []
    for flujo in (True, False):
        definicion = _palanca_def(lever, flujo)
        if isinstance(motivo, NoCalculable):
            partes.append(_no_calculable(definicion, fecha, motivo.no_calculable))
        elif isinstance(motivo, NoAplica):
            partes.append(_no_aplica(definicion, fecha, motivo.no_aplica))
    return Palanca(palanca=clave, nombre=nombre, flujo=partes[0], utilidad=partes[1])


def _con_impacto(lever: str, fecha: date, impacto: LeverImpact) -> Palanca:
    clave, nombre, _, _ = PALANCAS[lever]
    return Palanca(
        palanca=clave,
        nombre=nombre,
        flujo=_calculado(
            _palanca_def(lever, True), fecha, Decimal(str(impacto.cash_impact)), impacto.cash_formula
        ),
        utilidad=_calculado(
            _palanca_def(lever, False),
            fecha,
            Decimal(str(impacto.ebit_impact)),
            impacto.ebit_formula,
        ),
    )


TOTAL_FLUJO = _def(
    "poder_del_uno.total.flujo",
    "Poder del uno: flujo de todas las palancas",
    "suma del flujo de las palancas que aplican",
    LAMINA_PODER_DEL_UNO,
    "pesos",
)
TOTAL_UTILIDAD = _def(
    "poder_del_uno.total.utilidad",
    "Poder del uno: utilidad de todas las palancas",
    "suma de la utilidad de las palancas que aplican",
    LAMINA_PODER_DEL_UNO,
    "pesos",
)


def _entradas(d: _Fecha, utilidad_neta: Decimal) -> FinancialInputs:
    return FinancialInputs(
        net_sales=d.ventas.valor if d.ventas is not None else CERO,
        cost_of_goods_sold=d.costo.valor,
        total_opex=d.gastos.valor,
        accounts_receivable=d.clientes.valor,
        inventory=d.inventario.valor,
        accounts_payable=d.proveedores.valor,
        net_profit=utilidad_neta,
    )


def _poder_del_uno(
    d: _Fecha, dias: int | None, de_dias: dict[str, Indicador], utilidad_neta: Decimal
) -> tuple[tuple[Palanca, ...], Indicador, Indicador]:
    fecha = d.fecha
    if d.ventas is None or d.ventas.valor <= 0 or dias is None:
        if dias is None:
            razon = "falta confirmar qué periodo cubre tu estado de resultados"
        elif d.ventas is None:
            razon = _falta_ventas(fecha)
        else:
            razon = _ventas_en_cero(fecha) + "; sin ventas no hay palancas que medir"
        return (), _no_calculable(TOTAL_FLUJO, fecha, razon), _no_calculable(TOTAL_UTILIDAD, fecha, razon)

    fuera: dict[str, Indicador] = {}
    if not d.costo.existe or d.costo.valor <= 0:
        fuera["cogs"] = _no_aplica(
            _palanca_def("cogs", True), fecha, "tu estado de resultados no trae costo de ventas"
        )
    if not d.gastos.existe or d.gastos.valor <= 0:
        fuera["opex"] = _no_aplica(
            _palanca_def("opex", True), fecha, "tu estado de resultados no trae gastos de operación"
        )
    for lever, clave in (("ar_days", "dias_clientes"), ("inv_days", "dias_inventario"), ("ap_days", "dias_proveedores")):
        if not isinstance(de_dias[clave], Calculado):
            fuera[lever] = de_dias[clave]

    entradas = _entradas(d, utilidad_neta)
    resultado = PowerOfOneEngine(days_in_period=dias).calculate(
        entradas, {lever: 1 for lever in LEVER_META if lever not in fuera}
    )
    impactos = {impacto.lever: impacto for impacto in resultado.impacts}
    palancas = tuple(
        _sin_palanca(lever, fecha, fuera[lever]) if lever in fuera else _con_impacto(lever, fecha, impactos[lever])
        for lever in LEVER_META
    )
    con_valor = [p for p in palancas if isinstance(p.flujo, Calculado)]
    origen_flujo = " + ".join(
        f"{p.palanca} {formato_monto(p.flujo.valor)}" for p in con_valor if isinstance(p.flujo, Calculado)
    )
    origen_utilidad = " + ".join(
        f"{p.palanca} {formato_monto(p.utilidad.valor)}"
        for p in con_valor
        if isinstance(p.utilidad, Calculado)
    )
    if fuera:
        nota = " (no entran: " + ", ".join(PALANCAS[lever][0] for lever in fuera) + ")"
        origen_flujo += nota
        origen_utilidad += nota
    return (
        palancas,
        _calculado(TOTAL_FLUJO, fecha, Decimal(str(resultado.combined_cash_impact)), origen_flujo),
        _calculado(TOTAL_UTILIDAD, fecha, Decimal(str(resultado.combined_ebit_impact)), origen_utilidad),
    )


# ---------------------------------------------------------------------------
# Simulador de las 7 palancas (S86.22): dos coeficientes por palanca
# ---------------------------------------------------------------------------

SEIS_DECIMALES = Decimal("0.000001")

# Palanca del motor → (unidad, qué es mejorar, lado por periodo, lado de una vez)
PARTES: dict[str, tuple[Literal["%", "días"], str, str, str]] = {
    "price": ("%", "subir el precio", "1% × ventas", "−1% × clientes"),
    "volume": (
        "%",
        "vender más",
        "1% × utilidad bruta",
        "−1% × capital de trabajo (clientes + inventario − proveedores)",
    ),
    "cogs": ("%", "bajar el costo de ventas", "1% × costo de ventas", "1% × (inventario − proveedores)"),
    "opex": ("%", "bajar los gastos de operación", "1% × gastos de operación", "no deja nada en balance"),
    "ar_days": ("días", "cobrar antes", "mover días no cambia la utilidad", "1 día × ventas ÷ días del periodo"),
    "inv_days": (
        "días",
        "tener menos días de inventario",
        "mover días no cambia la utilidad",
        "1 día × costo de ventas ÷ días del periodo",
    ),
    "ap_days": (
        "días",
        "pagar a proveedores más tarde",
        "mover días no cambia la utilidad",
        "1 día × costo de ventas ÷ días del periodo",
    ),
}


def _parte(lever: str, una_vez: bool, valor: Decimal, origen: str) -> Coeficiente:
    clave, nombre, _, _ = PALANCAS[lever]
    _, _, formula_periodo, formula_una_vez = PARTES[lever]
    lado = "una_vez" if una_vez else "por_periodo"
    return Coeficiente(
        clave=f"simulador.{clave}.{lado}",
        nombre=f"{nombre}: {'una sola vez' if una_vez else 'cada periodo'}",
        valor=valor.quantize(SEIS_DECIMALES, rounding=ROUND_HALF_UP),
        formula=formula_una_vez if una_vez else formula_periodo,
        origen=f"sale de: {origen}",
        lamina=LAMINA_PODER_DEL_UNO,
    )


def _simulador(
    d: _Fecha, dias: int | None, palancas: tuple[Palanca, ...], utilidad_neta: Decimal
) -> tuple[PalancaDelSimulador, ...]:
    """Coeficientes por 1 punto de cada palanca, del mismo motor que el poder del uno."""
    if not palancas or dias is None:
        return ()
    entradas = _entradas(d, utilidad_neta)
    salida: list[PalancaDelSimulador] = []
    for lever, palanca in zip(LEVER_META, palancas, strict=True):
        unidad, mejora, _, _ = PARTES[lever]
        # «Costo de ventas −1%» → «Costo de ventas»; «Clientes −1 día» → «Clientes»
        nombre = palanca.nombre.rsplit(" ", 2 if unidad == "días" else 1)[0]
        flujo, utilidad = palanca.flujo, palanca.utilidad
        por_periodo: ParteDelSimulador
        una_vez: ParteDelSimulador
        if isinstance(flujo, Calculado) or isinstance(utilidad, Calculado):
            partes = lever_parts(lever, entradas, 1, dias)
            por_periodo = _parte(lever, False, partes.per_period, partes.per_period_formula)
            una_vez = _parte(lever, True, partes.one_time, partes.one_time_formula)
        else:
            # La palanca no entra al poder del uno: la misma razón, en gris.
            por_periodo, una_vez = utilidad, flujo
        salida.append(
            PalancaDelSimulador(
                palanca=palanca.palanca,
                lever=lever,
                nombre=nombre,
                unidad=unidad,
                mejora=mejora,
                por_periodo=por_periodo,
                una_vez=una_vez,
            )
        )
    return tuple(salida)


# ---------------------------------------------------------------------------
# Entrada pública
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Margen antes de impuestos, salario de mercado y devoluciones (S86.24)
# ---------------------------------------------------------------------------

LINEA_DEL_PRETAX = Decimal("10")
LIMITE_DE_LA_UB = Decimal("0.40")

MARGEN_PRETAX = _def(
    "margen_pretax",
    "Margen antes de impuestos",
    "100 × utilidad antes de impuestos ÷ ventas",
    "L77",
    "%",
)
MARGEN_SOBRE_UB = _def(
    "margen_sobre_utilidad_bruta",
    "Margen sobre la utilidad bruta",
    "si la utilidad bruta es menos del 40% de las ventas:"
    " 100 × utilidad antes de impuestos ÷ utilidad bruta",
    "L78",
    "%",
)
DEVOLUCIONES_SOBRE_UTILIDAD = _def(
    "devoluciones_sobre_utilidad",
    "Devoluciones sobre la utilidad",
    "100 × devoluciones, rebajas y bonificaciones ÷ utilidad antes de impuestos",
    "L79",
    "%",
)
UTILIDAD_REAL = _def(
    "utilidad_real",
    "Utilidad real con salario de mercado",
    "utilidad de operación − (salario de mercado − sueldo actual del dueño)",
    "L75 (cálculo de ESCALA)",
    "pesos",
)
PRETAX_CON_SALARIO = _def(
    "margen_pretax_con_salario",
    "Margen antes de impuestos con salario de mercado",
    "100 × (utilidad antes de impuestos − (salario de mercado − sueldo actual del dueño))"
    " ÷ ventas",
    "L75 y L77 (cálculo de ESCALA)",
    "%",
)
ISR = _def("isr", "ISR", "renglón de ISR del estado de resultados", "L11", "pesos")

NOTA_FISCAL = (
    "ESCALA sólo muestra el ISR de tu estado de resultados. "
    "Cualquier decisión de impuestos la ves con tu contador."
)

PREGUNTAS_DEL_DUENO: dict[str, PreguntaDelDueno] = {
    p.clave: p
    for p in (
        PreguntaDelDueno(
            clave="salario_de_mercado",
            pregunta=(
                "¿Cuánto le pagarías a una persona capacitada, que no sea dueña, por hacer "
                "lo que tú haces en la empresa? Dime el monto del mismo periodo que tu "
                "estado de resultados."
            ),
            para_que="Para ver tu margen como si la empresa te pagara un sueldo de mercado.",
        ),
        PreguntaDelDueno(
            clave="sueldo_actual_del_dueno",
            pregunta=(
                "¿Cuánto te pagas hoy en la nómina de la empresa en ese mismo periodo? "
                "Si no te pagas sueldo, dime 0."
            ),
            para_que="Para restar sólo la diferencia contra el salario de mercado.",
        ),
        PreguntaDelDueno(
            clave="devoluciones",
            pregunta=(
                "¿Cuánto sumaron las devoluciones, rebajas y bonificaciones del periodo? "
                "Si tu estado sólo trae ventas netas, tu contador tiene el dato."
            ),
            para_que="Para ver cuánta de tu utilidad se comen.",
        ),
    )
}


@dataclass(frozen=True)
class PretaxConLinea:
    """El margen pre-tax y si llega a la línea del 10% (con el valor sin redondear)."""

    indicador: Indicador
    por_encima_de_la_linea: bool | None


def _cifra(valor: Decimal, etiqueta: str) -> _Cifra:
    return _Cifra(valor, f"{etiqueta} {_dinero(valor)}")


def _sin_ventas(definicion: _Definicion, ventas: _Cifra | None, fecha: date) -> NoCalculable | None:
    if ventas is None:
        return _no_calculable(definicion, fecha, _falta_ventas(fecha))
    if ventas.valor <= 0:
        return _no_calculable(definicion, fecha, _ventas_en_cero(fecha))
    return None


def _falta_uai(definicion: _Definicion, fecha: date) -> NoCalculable:
    return _no_calculable(
        definicion,
        fecha,
        "tu estado de resultados no trae el renglón de utilidad antes de impuestos"
        f" al {fecha_corta(fecha)}",
    )


def _pretax(uai: _Cifra | None, ventas: _Cifra | None, fecha: date) -> PretaxConLinea:
    falta = _sin_ventas(MARGEN_PRETAX, ventas, fecha)
    if falta is not None:
        return PretaxConLinea(falta, None)
    if uai is None:
        return PretaxConLinea(_falta_uai(MARGEN_PRETAX, fecha), None)
    assert ventas is not None
    valor = CIEN * uai.valor / ventas.valor
    indicador = _calculado(MARGEN_PRETAX, fecha, valor, f"100 × {uai.texto} ÷ {ventas.texto}")
    return PretaxConLinea(indicador, valor >= LINEA_DEL_PRETAX)


def _sobre_ub(
    uai: _Cifra | None, ub: _Cifra | None, ventas: _Cifra | None, fecha: date
) -> Indicador:
    falta = _sin_ventas(MARGEN_SOBRE_UB, ventas, fecha)
    if falta is not None:
        return falta
    if uai is None:
        return _falta_uai(MARGEN_SOBRE_UB, fecha)
    assert ventas is not None and ub is not None
    if ub.valor <= 0:
        return _no_calculable(
            MARGEN_SOBRE_UB,
            fecha,
            f"la utilidad bruta es 0 o negativa ({_dinero(ub.valor)}):"
            " un porcentaje sobre ella no dice nada",
        )
    if uai.valor < 0:
        return _no_calculable(
            MARGEN_SOBRE_UB,
            fecha,
            f"la utilidad antes de impuestos es negativa ({_dinero(uai.valor)}): hay pérdida",
        )
    proporcion = ub.valor / ventas.valor
    if proporcion >= LIMITE_DE_LA_UB:
        porcentaje = formato_monto((CIEN * proporcion).quantize(CENTAVO, rounding=ROUND_HALF_UP))
        return _no_aplica(
            MARGEN_SOBRE_UB,
            fecha,
            f"tu utilidad bruta es {porcentaje}% de tus ventas (40% o más):"
            " el margen se mide contra las ventas",
        )
    return _calculado(
        MARGEN_SOBRE_UB, fecha, CIEN * uai.valor / ub.valor, f"100 × {uai.texto} ÷ {ub.texto}"
    )


def _devoluciones(devoluciones: _Cifra | None, uai: _Cifra | None, fecha: date) -> Indicador:
    if devoluciones is None:
        return _no_calculable(
            DEVOLUCIONES_SOBRE_UTILIDAD,
            fecha,
            "falta el monto de devoluciones, rebajas y bonificaciones: lo da el dueño",
        )
    if uai is None:
        return _falta_uai(DEVOLUCIONES_SOBRE_UTILIDAD, fecha)
    if uai.valor <= 0:
        return _no_calculable(
            DEVOLUCIONES_SOBRE_UTILIDAD,
            fecha,
            f"la utilidad antes de impuestos es 0 o negativa ({_dinero(uai.valor)}):"
            " no hay utilidad que se coman",
        )
    return _calculado(
        DEVOLUCIONES_SOBRE_UTILIDAD,
        fecha,
        CIEN * devoluciones.valor / uai.valor,
        f"100 × {devoluciones.texto} ÷ {uai.texto}",
    )


def margen_pretax(uai: Decimal, ventas: Decimal, fecha: date) -> PretaxConLinea:
    """F6.1 con montos sueltos: 100 × UAI ÷ ventas, y si llega a la línea del 10%."""

    return _pretax(_cifra(uai, "utilidad antes de impuestos"), _cifra(ventas, "ventas"), fecha)


def margen_sobre_utilidad_bruta(
    uai: Decimal, utilidad_bruta: Decimal, ventas: Decimal, fecha: date
) -> Indicador:
    """F6.2 con montos sueltos: sólo si la UB es menos del 40% de las ventas."""

    return _sobre_ub(
        _cifra(uai, "utilidad antes de impuestos"),
        _cifra(utilidad_bruta, "utilidad bruta"),
        _cifra(ventas, "ventas"),
        fecha,
    )


def devoluciones_sobre_utilidad(devoluciones: Decimal, uai: Decimal, fecha: date) -> Indicador:
    """F6.3 con montos sueltos: 100 × devoluciones ÷ UAI."""

    return _devoluciones(
        _cifra(devoluciones, "devoluciones, rebajas y bonificaciones"),
        _cifra(uai, "utilidad antes de impuestos"),
        fecha,
    )


def _falta_del_dueno(definicion: _Definicion, dueno: DatosDelDueno, fecha: date) -> NoCalculable | None:
    if dueno.salario_de_mercado is None:
        return _no_calculable(
            definicion, fecha, "falta el salario de mercado: lo da el dueño, ESCALA no lo supone"
        )
    if dueno.sueldo_actual_del_dueno is None:
        return _no_calculable(
            definicion, fecha, "falta cuánto se paga hoy el dueño en la nómina (0 si no se paga)"
        )
    return None


def _ajuste_de_salario(dueno: DatosDelDueno) -> tuple[Decimal, str]:
    assert dueno.salario_de_mercado is not None and dueno.sueldo_actual_del_dueno is not None
    ajuste = dueno.salario_de_mercado - dueno.sueldo_actual_del_dueno
    texto = (
        f"(salario de mercado {_dinero(dueno.salario_de_mercado)}"
        f" − sueldo actual del dueño {_dinero(dueno.sueldo_actual_del_dueno)})"
    )
    return ajuste, texto


def _utilidad_real(d: _Fecha, dueno: DatosDelDueno) -> Indicador:
    falta = _falta_del_dueno(UTILIDAD_REAL, dueno, d.fecha)
    if falta is not None:
        return falta
    ub = _utilidad_bruta(d)
    if ub is None:
        return _no_calculable(UTILIDAD_REAL, d.fecha, _falta_ventas(d.fecha))
    uo = ub.valor - d.gastos.valor
    ajuste, texto = _ajuste_de_salario(dueno)
    return _calculado(
        UTILIDAD_REAL, d.fecha, uo - ajuste, f"utilidad de operación {_dinero(uo)} − {texto}"
    )


def _pretax_con_salario(
    uai: _Cifra | None, ventas: _Cifra | None, dueno: DatosDelDueno, fecha: date
) -> PretaxConLinea:
    falta = _falta_del_dueno(PRETAX_CON_SALARIO, dueno, fecha) or _sin_ventas(
        PRETAX_CON_SALARIO, ventas, fecha
    )
    if falta is not None:
        return PretaxConLinea(falta, None)
    if uai is None:
        return PretaxConLinea(_falta_uai(PRETAX_CON_SALARIO, fecha), None)
    assert ventas is not None
    ajuste, texto = _ajuste_de_salario(dueno)
    valor = CIEN * (uai.valor - ajuste) / ventas.valor
    indicador = _calculado(
        PRETAX_CON_SALARIO, fecha, valor, f"100 × ({uai.texto} − {texto}) ÷ {ventas.texto}"
    )
    return PretaxConLinea(indicador, valor >= LINEA_DEL_PRETAX)


def _isr(resultados: LecturaEstados, fecha: date) -> Indicador:
    isr = _del_resultado(resultados, "isr", fecha)
    if isr is None:
        return _no_calculable(
            ISR, fecha, f"tu estado de resultados no trae el renglón de ISR al {fecha_corta(fecha)}"
        )
    return _calculado(ISR, fecha, isr.valor, isr.texto)


def _bloque_del_margen(d: _Fecha, resultados: LecturaEstados, dueno: DatosDelDueno) -> BloqueDelMargen:
    fecha = d.fecha
    uai = _del_resultado(resultados, "utilidad_antes_impuestos", fecha)
    ub = _utilidad_bruta(d)
    ub_cifra = None if ub is None else _cifra(ub.valor, "utilidad bruta")
    devoluciones = (
        None
        if dueno.devoluciones is None
        else _cifra(dueno.devoluciones, "devoluciones, rebajas y bonificaciones")
    )
    pretax = _pretax(uai, d.ventas, fecha)
    con_salario = _pretax_con_salario(uai, d.ventas, dueno, fecha)
    faltan = [
        clave
        for clave, valor in (
            ("salario_de_mercado", dueno.salario_de_mercado),
            ("sueldo_actual_del_dueno", dueno.sueldo_actual_del_dueno),
            ("devoluciones", dueno.devoluciones),
        )
        if valor is None
    ]
    return BloqueDelMargen(
        fecha=fecha,
        pretax=pretax.indicador,
        linea_de_referencia=LINEA_DEL_PRETAX,
        por_encima_de_la_linea=pretax.por_encima_de_la_linea,
        sobre_utilidad_bruta=_sobre_ub(uai, ub_cifra, d.ventas, fecha),
        devoluciones=_devoluciones(devoluciones, uai, fecha),
        salario_de_mercado=dueno.salario_de_mercado,
        sueldo_actual_del_dueno=dueno.sueldo_actual_del_dueno,
        utilidad_real=_utilidad_real(d, dueno),
        pretax_con_salario=con_salario.indicador,
        por_encima_de_la_linea_con_salario=con_salario.por_encima_de_la_linea,
        isr=_isr(resultados, fecha),
        nota_fiscal=NOTA_FISCAL,
        preguntas=tuple(PREGUNTAS_DEL_DUENO[clave] for clave in faltan),
    )


def _por_que_no(revision: RevisionDeEstados) -> str:
    razones = [h.mensaje for h in revision.hallazgos if h.bloquea]
    razones += [p.pregunta for p in revision.preguntas if p.bloquea]
    return "ESCALA no calcula todavía porque: " + " ".join(razones)


def calcular_curso(estados: EstadosRevisados) -> ResultadoDelCurso:
    """Calcula todos los números del curso de cash para los estados revisados."""

    revision = estados.revision
    resultados = estados.resultados
    base = {
        "periodo": revision.periodo,
        "balance_inicial": revision.balance_inicial,
        "balance_final": revision.balance_final,
    }
    if not revision.puede_calcular:
        return ResultadoDelCurso(no_calculable=_por_que_no(revision), **base)
    if revision.balance_final is None:
        return ResultadoDelCurso(no_calculable="falta el balance al final del periodo", **base)
    final = _datos(revision, resultados, revision.balance_final)
    if final is None:
        return ResultadoDelCurso(no_calculable="falta el balance al final del periodo", **base)
    inicial = (
        _datos(revision, resultados, revision.balance_inicial)
        if revision.balance_inicial is not None
        else None
    )
    dias = revision.periodo.dias if revision.periodo is not None else None

    indicadores: list[Indicador] = []
    de_dias_final: dict[str, Indicador] = {}
    for d in (inicial, final):
        if d is None:
            continue
        indicadores += _utilidades(d)
        indicadores += _cajas(d)
        dias_y_ciclo = _dias_y_ciclo(d, dias)
        indicadores += dias_y_ciclo
        if d is final:
            de_dias_final = {i.clave: i for i in dias_y_ciclo}
        indicadores += _sobre_ventas(d)
    indicadores += _flujos(inicial, final)

    neta = next(
        (
            c.monto
            for c in resultados.cuentas
            if c.concepto == "utilidad_neta" and c.fecha == final.fecha and not c.es_total
        ),
        CERO,
    )
    palancas, total_flujo, total_utilidad = _poder_del_uno(final, dias, de_dias_final, neta)
    pendientes = tuple(p.pregunta for p in revision.preguntas) + tuple(resultados.preguntas)
    return ResultadoDelCurso(
        indicadores=tuple(indicadores),
        poder_del_uno=palancas,
        poder_del_uno_flujo=total_flujo,
        poder_del_uno_utilidad=total_utilidad,
        pendientes=pendientes,
        simulador=_simulador(final, dias, palancas, neta),
        margen=_bloque_del_margen(final, resultados, estados.del_dueno or DatosDelDueno()),
        **base,
    )


def _imprime(texto: str) -> None:
    salida = sys.stdout
    reconfigurar = getattr(salida, "reconfigure", None)
    if callable(reconfigurar):
        reconfigurar(encoding="utf-8")
    salida.write(texto + "\n")


def _no(razon: str) -> int:
    _imprime(json.dumps({"no_calculable": razon}, ensure_ascii=False))
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    """``python -m escala_server.cash.curso <estados-revisados.json>`` → JSON."""

    argumentos = list(sys.argv[1:] if argv is None else argv)
    if len(argumentos) != 1:
        return _no("uso: python -m escala_server.cash.curso <estados-revisados.json>")
    try:
        texto = Path(argumentos[0]).read_text(encoding="utf-8")
    except OSError:
        return _no(f"no pude leer el archivo {argumentos[0]}")
    try:
        estados = EstadosRevisados.model_validate_json(texto)
    except ValidationError:
        return _no(
            "el archivo no trae estados revisados por ESCALA "
            "(la revisión del balance y el estado de resultados)"
        )
    _imprime(calcular_curso(estados).model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
