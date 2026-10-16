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

from dataclasses import dataclass, replace
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
import json
from pathlib import Path
import sys
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

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
from escala_server.financial.revisiones import PeriodoDelEstado, Respuestas, RevisionDeEstados

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


FuenteDeCifra = Literal["curso", "cálculo de ESCALA"]


class CifraDePrecioVolumen(_Modelo):
    """Un número de precio contra volumen o del descuento (S86.23).

    ``fuente`` dice si el número está en el curso o si lo calcula ESCALA.
    """

    clave: str
    nombre: str
    valor: Decimal
    unidad: Literal["pesos", "veces", "%"]
    formula: str
    origen: str
    lamina: str
    fuente: FuenteDeCifra


ParteDePrecioVolumen = CifraDePrecioVolumen | NoCalculable


class PrecioContraVolumen(_Modelo):
    """Precio contra volumen (F3b.2) y el costo de un descuento (F3b.3), S86.23."""

    descuento: int
    volumen: int
    no_calculable: str | None = None
    cifras: tuple[ParteDePrecioVolumen, ...] = ()
    mensajes: tuple[str, ...] = ()

    def cifra(self, clave: str) -> ParteDePrecioVolumen:
        for cifra in self.cifras:
            if cifra.clave == clave:
                return cifra
        raise KeyError(clave)


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
    # Lo que contestó el dueño (C1, C9…). Opcional: los archivos de antes no lo traen (S86.19).
    respuestas: Respuestas | None = None


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
    precio_contra_volumen: PrecioContraVolumen | None = None
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
# Días y ciclo del dinero (S86.19): dos años, con o sin IVA, ventas a crédito
# ---------------------------------------------------------------------------

Iva = Literal["con IVA", "sin IVA", "como vienen"]
Veredicto = Literal["mejoró", "empeoró", "igual", "no comparable"]
LAMINA_CRONOGRAMA = "L52 y L53"
UNO = Decimal("1")


class BaseDeDias(_Modelo):
    """En qué base se miden los días: IVA en los saldos (C9), su tasa y ventas a crédito (C1).

    La tasa de IVA es dato del dueño: ESCALA no supone 16%.
    """

    iva_incluido: bool | None = None
    tasa_iva: Decimal | None = Field(default=None, gt=0, le=100)  # en %
    ventas_a_credito: Decimal | None = Field(default=None, ge=0, le=100)  # en %

    @classmethod
    def de(cls, respuestas: Respuestas | None, *, tasa_iva: Decimal | None = None) -> BaseDeDias:
        """La base con lo que el dueño ya contestó en la revisión (C1 y C9)."""
        if respuestas is None:
            return cls(tasa_iva=tasa_iva)
        return cls(
            iva_incluido=respuestas.iva_incluido,
            tasa_iva=tasa_iva,
            ventas_a_credito=respuestas.ventas_a_credito,
        )


class Cronograma(_Modelo):
    """Compra día 0 → pago al proveedor → venta → cobro (F2.3)."""

    fecha: date
    pago: Decimal
    venta: Decimal
    cobro: Decimal
    financiados: Decimal
    origen: str
    lamina: str = LAMINA_CRONOGRAMA


class DiasDelAnio(_Modelo):
    fecha: date
    clientes: Indicador
    inventario: Indicador
    proveedores: Indicador
    ciclo: Indicador
    cronograma: Cronograma | None = None
    sin_cronograma: str | None = None
    nota: str | None = None


class Cambio(_Modelo):
    """Año anterior contra año actual. El veredicto usa los valores sin redondear."""

    clave: str
    nombre: str
    anterior: Decimal | None = None
    actual: Decimal | None = None
    diferencia: Decimal | None = None
    veredicto: Veredicto
    texto: str


class DiasDelDinero(_Modelo):
    no_calculable: str | None = None
    periodo: PeriodoDelEstado | None = None
    dias_del_periodo: int | None = None
    iva: Iva = "como vienen"
    rotulo: str = ""
    tasa_iva: Decimal | None = None
    base_de_ventas: Literal["ventas a crédito", "ventas totales"] = "ventas totales"
    avisos: tuple[str, ...] = ()
    preguntas: tuple[str, ...] = ()
    anios: tuple[DiasDelAnio, ...] = ()
    cambios: tuple[Cambio, ...] = ()

    def anio(self, fecha: date) -> DiasDelAnio:
        for anio in self.anios:
            if anio.fecha == fecha:
                return anio
        raise KeyError(fecha.isoformat())

    def cambio(self, clave: str) -> Cambio:
        for cambio in self.cambios:
            if cambio.clave == clave:
                return cambio
        raise KeyError(clave)


ROTULOS: dict[Iva, str] = {
    "con IVA": "días de cobro calculados con IVA",
    "sin IVA": "días de cobro calculados sin IVA",
    "como vienen": (
        "días de cobro calculados con los saldos como vienen "
        "(no me has dicho si clientes y proveedores traen IVA)"
    ),
}
PREGUNTA_IVA = (
    "¿Tus saldos de clientes y proveedores incluyen IVA? Tus ventas y tu costo no lo "
    "traen; si los saldos sí, tus días de cobro y de pago salen de más."
)
PREGUNTA_TASA = (
    "¿Qué tasa de IVA traen tus saldos de clientes y proveedores (por ejemplo, 16%)? "
    "No la supongo: con tu tasa calculo los días sin IVA."
)
AVISO_SIN_CREDITO = (
    "Calculé los días de cobro sobre tus ventas totales: no sé qué parte vendes a "
    "crédito. Si una parte es de contado, tus clientes tardan más en pagarte de lo "
    "que dice aquí."
)
AVISO_CERO_CREDITO = (
    "Me dijiste que no vendes a crédito, pero tu balance trae clientes. Calculé los "
    "días de cobro sobre tus ventas totales."
)
SIN_COSTO = (
    "tu estado de resultados no trae costo de ventas (por ejemplo, un negocio de "
    "servicios): los días de inventario y de proveedores se miden contra el costo"
)

# clave → (nombre, sujeto del cambio, ¿mejora si sube?)
_CAMBIOS: tuple[tuple[str, str, str, bool], ...] = (
    ("clientes", "Días de clientes", "Tus días de clientes pasaron", False),
    ("inventario", "Días de inventario", "Tus días de inventario pasaron", False),
    ("proveedores", "Días de proveedores", "Tus días de proveedores pasaron", True),
    ("ciclo", "Ciclo del efectivo", "Tu ciclo pasó", False),
)


def _numero(valor: Decimal) -> str:
    """60 → «60»; 1.16 → «1.16»; 100 → «100» (sin notación científica)."""
    return format(valor.normalize(), "f")


def _sin_iva(cifra: _Cifra, divisor: Decimal) -> _Cifra:
    if not cifra.existe or cifra.valor == 0:
        return cifra
    etiqueta = cifra.texto.split(" ")[0]
    valor = cifra.valor / divisor
    return _Cifra(
        valor,
        f"{etiqueta} sin IVA ({cifra.texto} ÷ {_numero(divisor)} = {_dinero(valor)})",
    )


def _a_credito(ventas: _Cifra | None, porcentaje: Decimal | None) -> _Cifra | None:
    if ventas is None or porcentaje is None or porcentaje in (CERO, CIEN):
        return ventas
    valor = ventas.valor * porcentaje / CIEN
    return _Cifra(
        valor, f"ventas a crédito {_dinero(valor)} ({_numero(porcentaje)}% de {ventas.texto})"
    )


def _con_crudo(
    definicion: _Definicion,
    cuenta: _Cifra,
    base: _Cifra | None,
    fecha: date,
    dias: int | None,
    etiqueta: str,
) -> tuple[Indicador, Decimal | None]:
    indicador = _dias(definicion, cuenta, base, fecha, dias, etiqueta)
    if isinstance(indicador, Calculado) and base is not None and dias is not None:
        return indicador, cuenta.valor / (base.valor / dias)
    return indicador, None


def _ciclo_del_dinero(
    fecha: date, partes: list[tuple[str, str, Indicador, Decimal | None]]
) -> tuple[Indicador, Decimal | None]:
    for _, _, parte, _ in partes:
        if isinstance(parte, NoCalculable):
            razon = f"no se pueden calcular los {parte.nombre.lower()}: {parte.no_calculable}"
            return _no_calculable(CICLO, fecha, razon), None
    if all(isinstance(parte, NoAplica) for _, _, parte, _ in partes):
        return _no_aplica(CICLO, fecha, "no tienes clientes, inventario ni proveedores en el balance"), None
    # Como la calculadora del curso: la suma de los días ya redondeados (se lee y cuadra).
    total = CERO
    crudo = CERO
    textos: list[str] = []
    for signo, nombre, parte, sin_redondear in partes:
        prefijo = "" if not textos else f"{signo} "
        if isinstance(parte, Calculado):
            total += parte.valor if signo == "+" else -parte.valor
            de_la_parte = sin_redondear if sin_redondear is not None else parte.valor
            crudo += de_la_parte if signo == "+" else -de_la_parte
            textos.append(f"{prefijo}{nombre} {formato_monto(parte.valor)}")
        else:
            textos.append(f"{prefijo}{nombre} no aplica")
    return _calculado(CICLO, fecha, total, " ".join(textos)), crudo


def _dia(indicador: Indicador) -> Decimal:
    return indicador.valor if isinstance(indicador, Calculado) else CERO


def _cronograma(anio: DiasDelAnio) -> tuple[Cronograma | None, str | None]:
    partes = (anio.clientes, anio.inventario, anio.proveedores)
    for parte in partes:
        if isinstance(parte, NoCalculable):
            return None, f"no calculable: {parte.no_calculable}"
    if not isinstance(anio.ciclo, Calculado):
        return None, "no aplica: no tienes clientes, inventario ni proveedores en el balance"
    pago, venta = _dia(anio.proveedores), _dia(anio.inventario)
    cobro = venta + _dia(anio.clientes)

    def de(parte: Indicador, nombre: str) -> str:
        valor = f"{nombre} {formato_monto(parte.valor)}" if isinstance(parte, Calculado) else f"{nombre} no aplica"
        return valor

    origen = (
        f"sale de: pago día {formato_monto(pago)} ({de(anio.proveedores, 'días de proveedores')}); "
        f"venta día {formato_monto(venta)} ({de(anio.inventario, 'días de inventario')}); "
        f"cobro día {formato_monto(cobro)} (venta {formato_monto(venta)} + "
        f"{de(anio.clientes, 'días de clientes')}); "
        f"financiados {formato_monto(cobro - pago)} (cobro − pago)"
    )
    return (
        Cronograma(
            fecha=anio.fecha,
            pago=pago,
            venta=venta,
            cobro=cobro,
            financiados=cobro - pago,
            origen=origen,
        ),
        None,
    )


@dataclass(frozen=True)
class _DelAnio:
    anio: DiasDelAnio
    crudos: dict[str, Decimal | None]


def _dias_del_anio(
    d: _Fecha, dias: int | None, divisor: Decimal | None, credito: Decimal | None
) -> _DelAnio:
    fecha = d.fecha
    clientes = _sin_iva(d.clientes, divisor) if divisor is not None else d.clientes
    proveedores = _sin_iva(d.proveedores, divisor) if divisor is not None else d.proveedores
    ventas = _a_credito(d.ventas, credito)
    sufijo = " sin IVA" if divisor is not None else ""
    def_clientes = replace(
        DIAS_CLIENTES,
        formula=(
            f"clientes{sufijo} ÷ "
            f"({'ventas a crédito' if ventas is not d.ventas else 'ventas'} ÷ días del periodo)"
        ),
    )
    def_proveedores = replace(
        DIAS_PROVEEDORES, formula=f"proveedores{sufijo} ÷ (costo de ventas ÷ días del periodo)"
    )
    de_clientes = _con_crudo(def_clientes, clientes, ventas, fecha, dias, "ventas")
    if d.ventas is not None and (not d.costo.existe or d.costo.valor <= 0):
        de_inventario: tuple[Indicador, Decimal | None] = (
            _no_aplica(DIAS_INVENTARIO, fecha, SIN_COSTO),
            None,
        )
        de_proveedores: tuple[Indicador, Decimal | None] = (
            _no_aplica(def_proveedores, fecha, SIN_COSTO),
            None,
        )
    else:
        de_inventario = _con_crudo(DIAS_INVENTARIO, d.inventario, d.costo, fecha, dias, "costo de ventas")
        de_proveedores = _con_crudo(def_proveedores, proveedores, d.costo, fecha, dias, "costo de ventas")
    ciclo, ciclo_crudo = _ciclo_del_dinero(
        fecha,
        [
            ("+", "días de clientes", de_clientes[0], de_clientes[1]),
            ("+", "días de inventario", de_inventario[0], de_inventario[1]),
            ("−", "días de proveedores", de_proveedores[0], de_proveedores[1]),
        ],
    )
    anio = DiasDelAnio(
        fecha=fecha,
        clientes=de_clientes[0],
        inventario=de_inventario[0],
        proveedores=de_proveedores[0],
        ciclo=ciclo,
    )
    cronograma, sin_cronograma = _cronograma(anio)
    return _DelAnio(
        anio.model_copy(update={"cronograma": cronograma, "sin_cronograma": sin_cronograma}),
        {
            "clientes": de_clientes[1],
            "inventario": de_inventario[1],
            "proveedores": de_proveedores[1],
            "ciclo": ciclo_crudo,
        },
    )


def _nota_con_iva(con_iva: DiasDelAnio) -> str | None:
    partes = [
        f"{nombre} {formato_monto(indicador.valor)}"
        for nombre, indicador in (
            ("clientes", con_iva.clientes),
            ("proveedores", con_iva.proveedores),
            ("ciclo", con_iva.ciclo),
        )
        if isinstance(indicador, Calculado)
    ]
    if not partes:
        return None
    return "Con IVA, como los mide el curso: " + ", ".join(partes) + " días."


def _cambio(
    clave: str,
    nombre: str,
    sujeto: str,
    mejora_si_sube: bool,
    anterior: _DelAnio | None,
    actual: _DelAnio,
) -> Cambio:
    if anterior is None:
        return Cambio(
            clave=clave,
            nombre=nombre,
            veredicto="no comparable",
            texto="no comparable: falta el balance del año anterior",
        )
    antes = getattr(anterior.anio, clave)
    ahora = getattr(actual.anio, clave)
    crudo_antes, crudo_ahora = anterior.crudos[clave], actual.crudos[clave]
    if (
        not isinstance(antes, Calculado)
        or not isinstance(ahora, Calculado)
        or crudo_antes is None
        or crudo_ahora is None
    ):
        razones = [
            f"{'año anterior' if parte is antes else 'año actual'}: "
            f"{parte.no_calculable if isinstance(parte, NoCalculable) else parte.no_aplica}"
            for parte in (antes, ahora)
            if isinstance(parte, NoCalculable | NoAplica)
        ]
        return Cambio(
            clave=clave,
            nombre=nombre,
            veredicto="no comparable",
            texto="no comparable: " + "; ".join(razones),
        )
    diferencia = ahora.valor - antes.valor
    cambio_crudo = crudo_ahora - crudo_antes
    veredicto: Veredicto
    if cambio_crudo == 0:
        veredicto = "igual"
    elif (cambio_crudo > 0) == mejora_si_sube:
        veredicto = "mejoró"
    else:
        veredicto = "empeoró"
    cuanto = (
        ""
        if diferencia == 0
        else f" ({formato_monto(abs(diferencia))} días {'más' if diferencia > 0 else 'menos'})"
    )
    return Cambio(
        clave=clave,
        nombre=nombre,
        anterior=antes.valor,
        actual=ahora.valor,
        diferencia=diferencia,
        veredicto=veredicto,
        texto=(
            f"{sujeto} de {formato_monto(antes.valor)} a {formato_monto(ahora.valor)} días: "
            f"{veredicto}{cuanto}."
        ),
    )


def dias_del_dinero(estados: EstadosRevisados, base: BaseDeDias) -> DiasDelDinero:
    """Días de clientes, inventario y proveedores, ciclo y cronograma, para los dos años.

    Según el curso de cash que vimos (F2.2, F2.3). Los días son los del periodo
    revisado; el año anterior usa los mismos, como el curso.
    """
    revision = estados.revision
    resultados = estados.resultados
    if not revision.puede_calcular:
        return DiasDelDinero(no_calculable=_por_que_no(revision), periodo=revision.periodo)
    final = (
        _datos(revision, resultados, revision.balance_final)
        if revision.balance_final is not None
        else None
    )
    if final is None:
        return DiasDelDinero(no_calculable="falta el balance al final del periodo", periodo=revision.periodo)
    inicial = (
        _datos(revision, resultados, revision.balance_inicial)
        if revision.balance_inicial is not None
        else None
    )
    dias = revision.periodo.dias if revision.periodo is not None else None

    iva: Iva
    divisor: Decimal | None = None
    preguntas: list[str] = []
    if base.iva_incluido is None:
        iva = "como vienen"
        preguntas.append(PREGUNTA_IVA)
    elif not base.iva_incluido:
        iva = "sin IVA"
    elif base.tasa_iva is None:
        iva = "con IVA"
        preguntas.append(PREGUNTA_TASA)
    else:
        iva = "sin IVA"
        divisor = UNO + base.tasa_iva / CIEN

    credito = base.ventas_a_credito
    avisos: list[str] = []
    if credito is None:
        avisos.append(AVISO_SIN_CREDITO)
    elif credito == 0:
        avisos.append(AVISO_CERO_CREDITO)
    a_credito = credito if credito is not None and credito > 0 else None

    por_anio: list[_DelAnio] = []
    for d in (inicial, final):
        if d is None:
            continue
        del_anio = _dias_del_anio(d, dias, divisor, a_credito)
        nota: str | None = None
        if divisor is not None:
            nota = _nota_con_iva(_dias_del_anio(d, dias, None, a_credito).anio)
        elif iva == "con IVA":
            nota = "Sin IVA: no calculable: falta confirmar tu tasa de IVA."
        if nota is not None:
            del_anio = _DelAnio(del_anio.anio.model_copy(update={"nota": nota}), del_anio.crudos)
        por_anio.append(del_anio)

    anterior = por_anio[0] if inicial is not None else None
    actual = por_anio[-1]
    return DiasDelDinero(
        periodo=revision.periodo,
        dias_del_periodo=dias,
        iva=iva,
        rotulo=ROTULOS[iva],
        tasa_iva=base.tasa_iva if divisor is not None else None,
        base_de_ventas="ventas a crédito" if a_credito is not None else "ventas totales",
        avisos=tuple(avisos),
        preguntas=tuple(preguntas),
        anios=tuple(a.anio for a in por_anio),
        cambios=tuple(
            _cambio(clave, nombre, sujeto, sube, anterior, actual)
            for clave, nombre, sujeto, sube in _CAMBIOS
        ),
    )


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
# Precio contra volumen y el costo de un descuento (S86.23)
# ---------------------------------------------------------------------------

# El ejemplo del curso (L39): «10% de descuento para vender 15% más».
DESCUENTO_DEL_CURSO = 10
VOLUMEN_DEL_CURSO = 15
CALCULO_DE_ESCALA: FuenteDeCifra = "cálculo de ESCALA"


def _signo(valor: Decimal) -> str:
    """Monto a centavos con el signo menos tipográfico, para lo que lee el dueño."""
    texto = _dinero(valor)
    return "−" + texto[1:] if texto.startswith("-") else texto


def _cifra_pv(
    clave: str,
    nombre: str,
    valor: Decimal,
    unidad: Literal["pesos", "veces", "%"],
    formula: str,
    origen: str,
    lamina: str,
    fuente: FuenteDeCifra = "curso",
) -> CifraDePrecioVolumen:
    if fuente == CALCULO_DE_ESCALA:
        nombre = f"{nombre} ({CALCULO_DE_ESCALA})"
    return CifraDePrecioVolumen(
        clave=clave,
        nombre=nombre,
        valor=valor.quantize(CENTAVO, rounding=ROUND_HALF_UP),
        unidad=unidad,
        formula=formula,
        origen=f"sale de: {origen}",
        lamina=lamina,
        fuente=fuente,
    )


def _no_calculable_pv(clave: str, nombre: str, formula: str, lamina: str, razon: str) -> NoCalculable:
    return NoCalculable(
        clave=clave, nombre=nombre, fecha=None, formula=formula, lamina=lamina, no_calculable=razon
    )


def _precio_contra_volumen(d: _Fecha, descuento: int, volumen: int) -> PrecioContraVolumen:
    """F3b.2 y F3b.3 con los estados al cierre. Precio y volumen salen del motor."""
    if d.ventas is None or d.ventas.valor <= 0:
        razon = _falta_ventas(d.fecha) if d.ventas is None else _ventas_en_cero(d.fecha)
        return PrecioContraVolumen(no_calculable=razon, descuento=descuento, volumen=volumen)

    entradas = _entradas(d, CERO)
    ventas, costo = d.ventas.valor, d.costo.valor
    ub = ventas - costo
    precio = lever_parts("price", entradas, 1)
    vol_1 = lever_parts("volume", entradas, 1)
    precio_d = lever_parts("price", entradas, descuento)
    vol_v = lever_parts("volume", entradas, volumen)
    precio_flujo = precio.per_period + precio.one_time
    vol_1_flujo = vol_1.per_period + vol_1.one_time

    cifras: list[ParteDePrecioVolumen] = [
        _cifra_pv("precio.utilidad", "Subir el precio 1%: utilidad", precio.per_period, "pesos",
                  "1% × ventas", precio.per_period_formula, "L36"),
        _cifra_pv("precio.flujo", "Subir el precio 1%: flujo", precio_flujo, "pesos",
                  "1% × ventas − 1% × clientes", precio.cash_formula, "L36"),
        _cifra_pv("volumen_1.utilidad", "Vender 1% más: utilidad", vol_1.per_period, "pesos",
                  "1% × utilidad bruta", vol_1.per_period_formula, "L37"),
        _cifra_pv("volumen_1.flujo", "Vender 1% más: flujo", vol_1_flujo, "pesos",
                  "1% × utilidad bruta − 1% × capital de trabajo", vol_1.cash_formula, "L37"),
    ]

    # Razones (L38): cuántas veces rinde subir el precio contra vender más.
    sin_ub = "la utilidad bruta es 0 o menos: vender más no deja utilidad con qué comparar"
    formula_ru = "utilidad por subir el precio 1% ÷ utilidad por vender 1% más"
    formula_rf = "flujo por subir el precio 1% ÷ flujo por vender 1% más"
    razon_u: ParteDePrecioVolumen
    razon_f: ParteDePrecioVolumen
    if ub <= 0:
        razon_u = _no_calculable_pv("razon.utilidad", "Precio contra volumen: utilidad", formula_ru, "L38", sin_ub)
    else:
        razon_u = _cifra_pv(
            "razon.utilidad", "Precio contra volumen: utilidad", precio.per_period / vol_1.per_period,
            "veces", formula_ru,
            f"precio {_dinero(precio.per_period)} ÷ volumen {_dinero(vol_1.per_period)}", "L38",
        )
    if ub <= 0 or vol_1_flujo <= 0:
        razon = sin_ub if ub <= 0 else (
            "vender 1% más pide más capital de trabajo del que deja: "
            f"su flujo es {_dinero(vol_1_flujo)}"
        )
        razon_f = _no_calculable_pv("razon.flujo", "Precio contra volumen: flujo", formula_rf, "L38", razon)
    else:
        razon_f = _cifra_pv(
            "razon.flujo", "Precio contra volumen: flujo", precio_flujo / vol_1_flujo, "veces", formula_rf,
            f"precio {_dinero(precio_flujo)} ÷ volumen {_dinero(vol_1_flujo)}", "L38",
        )
    cifras += [razon_u, razon_f]

    # El descuento y el volumen como los suma el curso (L40, L41, L43).
    desc_u = -precio_d.per_period
    desc_f = -(precio_d.per_period + precio_d.one_time)
    vol_u = vol_v.per_period
    vol_f = vol_v.per_period + vol_v.one_time
    d_ = f"{descuento}%"
    v_ = f"{volumen}%"
    cifras += [
        _cifra_pv("descuento.utilidad", f"Descuento de {d_}: utilidad", desc_u, "pesos",
                  f"−{d_} × ventas", f"−{precio_d.per_period_formula}", "L41"),
        _cifra_pv("descuento.flujo", f"Descuento de {d_}: flujo", desc_f, "pesos",
                  f"−{d_} × ventas + {d_} × clientes", f"−({precio_d.cash_formula})", "L41"),
        _cifra_pv("volumen.utilidad", f"Vender {v_} más: utilidad", vol_u, "pesos",
                  f"{v_} × utilidad bruta", vol_v.per_period_formula, "L40"),
        _cifra_pv("volumen.flujo", f"Vender {v_} más: flujo", vol_f, "pesos",
                  f"{v_} × utilidad bruta − {v_} × capital de trabajo", vol_v.cash_formula, "L40"),
        _cifra_pv("neto_del_curso.utilidad", "Descuento y volumen, sumados como el curso: utilidad",
                  desc_u + vol_u, "pesos", "efecto del descuento + efecto del volumen",
                  f"descuento {_dinero(desc_u)} + volumen {_dinero(vol_u)}", "L43"),
        _cifra_pv("neto_del_curso.flujo", "Descuento y volumen, sumados como el curso: flujo",
                  desc_f + vol_f, "pesos", "efecto del descuento + efecto del volumen",
                  f"descuento {_dinero(desc_f)} + volumen {_dinero(vol_f)}", "L43"),
    ]

    # Cálculo de ESCALA: el volumen extra también va con descuento.
    factor_d = 1 - Decimal(descuento) / CIEN
    factor_v = 1 + Decimal(volumen) / CIEN
    ub_con_descuento = ventas * factor_d - costo
    texto_ub_d = f"{d.ventas.texto} × {factor_d} − {d.costo.texto}"
    combinado = factor_v * ub_con_descuento - ub
    cifras.append(
        _cifra_pv(
            "combinado.utilidad", f"{d_} de descuento y {v_} más de volumen, juntos: utilidad", combinado,
            "pesos",
            "(1 + volumen) × (ventas × (1 − descuento) − costo de ventas) − utilidad bruta",
            f"{factor_v} × ({texto_ub_d}) − utilidad bruta {_dinero(ub)}",
            "L43 (el curso suma los dos efectos; aquí se calculan juntos)", CALCULO_DE_ESCALA,
        )
    )
    formula_eq = "utilidad bruta ÷ (ventas × (1 − descuento) − costo de ventas) − 1"
    nombre_eq = f"Volumen extra para que {d_} de descuento no pierda utilidad ({CALCULO_DE_ESCALA})"
    equilibrio: ParteDePrecioVolumen
    if ub <= 0:
        equilibrio = _no_calculable_pv(
            "equilibrio.volumen", nombre_eq, formula_eq, "L43",
            "la utilidad bruta es 0 o menos: no hay utilidad que cuidar",
        )
    elif ub_con_descuento <= 0:
        margen = (CIEN * ub / ventas).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        equilibrio = _no_calculable_pv(
            "equilibrio.volumen", nombre_eq, formula_eq, "L43",
            f"el descuento de {d_} es igual o mayor que tu margen bruto ({margen}%): "
            "cada venta con descuento deja 0 o pierde, y ningún volumen lo compensa",
        )
    else:
        equilibrio = _cifra_pv(
            "equilibrio.volumen", "Volumen extra para que el descuento no pierda utilidad",
            CIEN * (ub / ub_con_descuento - 1), "%", formula_eq,
            f"utilidad bruta {_dinero(ub)} ÷ ({texto_ub_d}) − 1", "L43", CALCULO_DE_ESCALA,
        )
    cifras.append(equilibrio)

    mensajes: list[str] = []
    if isinstance(razon_u, CifraDePrecioVolumen):
        mensajes.append(
            f"Subir el precio 1% te deja {razon_u.valor} veces la utilidad que te deja vender 1% más (L38)."
        )
    else:
        mensajes.append(f"Precio contra volumen, utilidad: no calculable: {razon_u.no_calculable}.")
    if isinstance(razon_f, CifraDePrecioVolumen):
        mensajes.append(f"En efectivo, {razon_f.valor} veces (L38).")
    else:
        mensajes.append(f"Precio contra volumen, efectivo: no calculable: {razon_f.no_calculable}.")
    if isinstance(equilibrio, CifraDePrecioVolumen):
        mensajes.append(
            f"Si das {d_} de descuento, necesitas vender {equilibrio.valor}% más solo para quedar igual"
            f" ({CALCULO_DE_ESCALA})."
        )
    else:
        mensajes.append(
            f"Si das {d_} de descuento, el volumen para quedar igual es no calculable: "
            f"{equilibrio.no_calculable}."
        )
    mensajes.append(
        f"Con {d_} de descuento y {v_} más de volumen, tu utilidad cambia {_signo(combinado)}"
        f" ({CALCULO_DE_ESCALA}: el volumen extra también va con descuento);"
        f" el curso lo simplifica sumando los dos efectos, y da {_signo(desc_u + vol_u)}."
    )
    return PrecioContraVolumen(cifras=tuple(cifras), mensajes=tuple(mensajes), descuento=descuento, volumen=volumen)


def precio_contra_volumen(
    estados: EstadosRevisados,
    descuento: int = DESCUENTO_DEL_CURSO,
    volumen: int = VOLUMEN_DEL_CURSO,
) -> PrecioContraVolumen:
    """Precio contra volumen y el costo de dar ``descuento``% para vender ``volumen``% más.

    Los dos van en puntos enteros de %, como las palancas del motor.
    """
    if not 0 < descuento < 100:
        return PrecioContraVolumen(
            no_calculable="el descuento tiene que ser mayor que 0% y menor que 100%",
            descuento=descuento,
            volumen=volumen,
        )
    if volumen < 0:
        return PrecioContraVolumen(no_calculable="el volumen extra no puede ser negativo", descuento=descuento, volumen=volumen)
    revision = estados.revision
    if not revision.puede_calcular:
        return PrecioContraVolumen(no_calculable=_por_que_no(revision), descuento=descuento, volumen=volumen)
    final = (
        _datos(revision, estados.resultados, revision.balance_final)
        if revision.balance_final is not None
        else None
    )
    if final is None:
        return PrecioContraVolumen(no_calculable="falta el balance al final del periodo", descuento=descuento, volumen=volumen)
    return _precio_contra_volumen(final, descuento, volumen)


# ---------------------------------------------------------------------------
# Las travesuras: ajustes que confiesa el dueño (S86.25)
# ---------------------------------------------------------------------------
#
# Según el curso de cash que vimos (F1.4, lámina 12): para ver la utilidad «sin
# travesuras», el dueño suma los gastos personales que pagó la empresa y las
# ventas que no quedaron registradas.
#
# Sobre qué utilidad se suma: la lámina 12 suma los ajustes directo a la
# UTILIDAD NETA (el resultado del ejercicio), sin recalcular el ISR:
#
#   5,018,095.92 + 445,164.11 = 5,463,260.03   (lámina, con la errata 97,492)
#
# Errata L12: el ajuste de gastos es 55,820 + 41,875 + 247 = 97,942, no 97,492.
# Con el correcto, los ajustes suman 445,614.11 y la utilidad ajustada es
# 5,463,710.03. Ojo: 5,463,710.03 − 97,942 = 5,365,768.03 NO es un renglón del
# estado de resultados; es la utilidad neta 5,018,095.92 + la venta sin factura
# 123,250 + el ajuste de intereses 224,422.11 (los otros dos ajustes de la
# lámina). La base es siempre el renglón «Utilidad neta».
#
# ESCALA solo suma los montos que dio el dueño: nunca estima ni sugiere uno.
# No recalcula impuestos ni recomienda nada fiscal.

AVISO_FISCAL = "Lo fiscal lo ve tu contador."

# Los ejemplos del curso, sin montos: el dueño pone los suyos.
EJEMPLOS_DE_TRAVESURAS: tuple[str, ...] = (
    "un viaje familiar",
    "la camioneta que usa un familiar",
    "la computadora de un hijo",
    "una venta que no quedó registrada",
)

UTILIDAD_CONTABLE = _def(
    "utilidad_contable",
    "Utilidad contable",
    "la utilidad neta de tu estado de resultados",
    "L11",
    "pesos",
)
AJUSTES_DEL_DUENO = _def(
    "ajustes_del_dueno",
    "Ajustes que me dijiste",
    "suma de los montos que me dijiste",
    "L12",
    "pesos",
)
UTILIDAD_AJUSTADA = _def(
    "utilidad_ajustada",
    "Utilidad ajustada",
    "utilidad contable + ajustes que me dijiste",
    "L12",
    "pesos",
)


class AjusteDelDueno(_Modelo):
    """Un gasto personal que pagó la empresa (o una venta no registrada), en palabras del dueño."""

    concepto: str = Field(min_length=1)
    monto: Decimal = Field(gt=0)

    @field_validator("concepto")
    @classmethod
    def _con_texto(cls, concepto: str) -> str:
        limpio = concepto.strip()
        if not limpio:
            raise ValueError("el ajuste necesita un concepto")
        return limpio


ParteDeUtilidadAjustada = Calculado | NoCalculable


class UtilidadAjustada(_Modelo):
    """Utilidad contable, los ajustes que dijo el dueño y la utilidad ajustada (F1.4)."""

    ajustes: tuple[AjusteDelDueno, ...] = ()
    utilidad_contable: ParteDeUtilidadAjustada
    total_de_ajustes: ParteDeUtilidadAjustada
    utilidad_ajustada: ParteDeUtilidadAjustada
    aviso: str = AVISO_FISCAL


def _utilidad_neta(resultados: LecturaEstados, fecha: date) -> _Cifra | None:
    renglones = [
        c
        for c in resultados.cuentas
        if c.concepto == "utilidad_neta" and c.fecha == fecha and not c.es_total
    ]
    if not renglones:
        return None
    return _Cifra(renglones[0].monto, f"utilidad neta {_dinero(renglones[0].monto)}")


def utilidad_ajustada(
    estados: EstadosRevisados, ajustes: Sequence[AjusteDelDueno]
) -> UtilidadAjustada:
    """Utilidad ajustada = utilidad neta al cierre + suma de los ajustes del dueño.

    Sin ajustes, la utilidad ajustada es la contable. Nunca inventa un ajuste.
    """
    revision = estados.revision
    fecha = revision.balance_final
    ajustes_ = tuple(ajustes)
    if not revision.puede_calcular or fecha is None:
        razon = _por_que_no(revision) if not revision.puede_calcular else "falta el balance al final del periodo"
        return UtilidadAjustada(
            ajustes=ajustes_,
            utilidad_contable=_no_calculable(UTILIDAD_CONTABLE, fecha, razon),
            total_de_ajustes=_no_calculable(AJUSTES_DEL_DUENO, fecha, razon),
            utilidad_ajustada=_no_calculable(UTILIDAD_AJUSTADA, fecha, razon),
        )

    suma = sum((a.monto for a in ajustes_), CERO)
    detalle = " + ".join(f"{a.concepto} {_dinero(a.monto)}" for a in ajustes_)
    total = _calculado(
        AJUSTES_DEL_DUENO,
        fecha,
        suma,
        detalle if ajustes_ else "no me dijiste ningún ajuste",
    )
    neta = _utilidad_neta(estados.resultados, fecha)
    if neta is None:
        razon = f"tu estado de resultados al {fecha_corta(fecha)} no trae la utilidad neta"
        return UtilidadAjustada(
            ajustes=ajustes_,
            utilidad_contable=_no_calculable(UTILIDAD_CONTABLE, fecha, razon),
            total_de_ajustes=total,
            utilidad_ajustada=_no_calculable(UTILIDAD_AJUSTADA, fecha, razon),
        )
    contable = _calculado(
        UTILIDAD_CONTABLE,
        fecha,
        neta.valor,
        f"{neta.texto} (renglón «Utilidad neta» de tu estado de resultados al {fecha_corta(fecha)})",
    )
    origen = (
        f"{neta.texto} + {detalle}"
        if ajustes_
        else f"{neta.texto} (no me dijiste ningún ajuste)"
    )
    return UtilidadAjustada(
        ajustes=ajustes_,
        utilidad_contable=contable,
        total_de_ajustes=total,
        utilidad_ajustada=_calculado(UTILIDAD_AJUSTADA, fecha, neta.valor + suma, origen),
    )


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
        precio_contra_volumen=_precio_contra_volumen(final, DESCUENTO_DEL_CURSO, VOLUMEN_DEL_CURSO),
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
