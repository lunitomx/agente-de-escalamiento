"""El escenario «analiza mi balance general y mi estado de resultados» (S86.17).

Según el curso de cash que vimos, ESCALA hace esto, en orden:

1. Lee lo que llegó (``financial.lector``), sin calcular.
2. Muestra la lista de lo que necesita: ✔ lo tengo · ? no me queda claro · ✘ me falta.
3. Pregunta lo pendiente: máximo 3 preguntas por mensaje, de la más importante a
   la menos importante.
4. Revisa que todo cuadre (R1–R11, ``financial.revisiones``). Si algo no cuadra,
   lo dice con el número y no calcula.
5. Dice qué va a calcular y qué no puede calcular, y por qué.
6. Calcula con la calculadora (``cash.curso``) y muestra un resumen: capital de
   trabajo, días, ciclo y las tres medidas del flujo, cada uno con su origen.

Aquí no se calcula ningún indicador: los números del resumen salen tal cual de
la calculadora y los de la lista salen tal cual de los archivos.

Cada llamada vuelve a leer los archivos y aplica todas las respuestas: con las
mismas entradas, el mismo resultado. Nada se guarda sin un «sí» del dueño.

Entrada interna::

    python -m escala_server.cash.escenario --empresa "Mi Empresa" \\
        --archivo balance.xlsx --archivo resultados.txt \\
        [--responde CLAVE=VALOR ...] [--guardar sí]
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from escala_server.cash.curso import (
    EJEMPLOS_DE_TRAVESURAS,
    AjusteDelDueno,
    Calculado,
    EstadosRevisados,
    Indicador,
    NoAplica,
    NoCalculable,
    ResultadoDelCurso,
    UtilidadAjustada,
    calcular_curso,
    utilidad_ajustada,
)
from escala_server.financial.cajas import CuentaEnCaja
from escala_server.financial.formatos import fecha_corta, formato_monto, leer_monto, normalizar
from escala_server.financial.lector import LecturaEstados, Unidad, leer_estados
from escala_server.financial.revisiones import (
    Hallazgo,
    Periodo,
    Respuestas,
    RevisionDeEstados,
    revisar_estados,
)

Marca = Literal["✔", "?", "✘"]
CARPETA = Path("work/cash")

# Lo que sale en el resumen, en este orden: capital de trabajo, días, ciclo y
# las tres medidas del flujo.
RESUMEN: tuple[str, ...] = (
    "capital_de_trabajo",
    "dias_clientes",
    "dias_inventario",
    "dias_proveedores",
    "ciclo",
    "flujo_neto",
    "flujo_de_operacion",
    "marginal",
)

# R7: lo que el dueño puede contestar, en sus palabras → regla de ``cajas``.
QUE_ES: dict[str, str] = {
    "clientes": "clientes",
    "inventario": "inventario",
    "proveedores": "proveedores",
    "préstamo que paga interés": "prestamos",
    "capital de los socios": "capital",
    "otra cuenta a mi favor": "deudores",
    "otra cuenta que debo": "acreedores",
}

_SI_NO = ("sí", "no")
_SI_NO_NOSE = ("sí", "no", "no sé")
OPCIONES: dict[str, tuple[str, ...]] = {
    "C10": ("mes", "acumulado del año"),
    "R7": tuple(QUE_ES),
    "unidad": ("pesos", "miles de pesos", "millones de pesos"),
    "R8": _SI_NO,
    "suma": _SI_NO,
    "C11": _SI_NO_NOSE,
    "C9": _SI_NO_NOSE,
    "C1": ("un porcentaje de 0 a 100", "no sé"),
    "C4": ("una cantidad en pesos", "no", "no sé"),
    "C3": ("una cantidad en pesos", "no sé"),
    "C2": ("todas", "solo lo facturado", "no sé"),
    # S86.25: «C6=no» o un gasto por respuesta: «C6:<concepto>=<monto en pesos>».
    "C6": ("no", "cada gasto con su monto en pesos"),
}
# De la más importante a la menos importante (después de los problemas).
_IMPORTANCIA: tuple[str, ...] = (
    "C10",
    "R7",
    "unidad",
    "R8",
    "suma",
    "C11",
    "C9",
    "C1",
    "C4",
    "C3",
    "C2",
)
# Entre los problemas: la unidad y los signos suelen explicar por qué no cuadra.
_PROBLEMAS: tuple[str, ...] = ("archivo", "R5", "R6", "R1", "R3", "R4", "R2", "R8", "R9", "R10")
_BLOQUEAN_SIN_NO_SE = frozenset({"C10", "R7", "unidad", "R8", "suma"})
_POR_CORREGIR = "Mándame el archivo corregido (si hace falta, pídeselo a tu contador); con eso sigo."


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Conversacion(_Modelo):
    """La plática: archivos y respuestas del dueño. Nunca cifras calculadas."""

    empresa: str
    archivos: tuple[str, ...] = ()
    respuestas: dict[str, str] = Field(default_factory=dict[str, str])


class Renglon(_Modelo):
    seccion: str
    marca: Marca
    nombre: str
    detalle: str


class Pregunta(_Modelo):
    # ``None``: un problema que no se contesta con palabras; pide el archivo corregido.
    clave: str | None
    pregunta: str
    para_que: str
    opciones: tuple[str, ...] = ()
    bloquea: bool = False


class LineaDeResumen(_Modelo):
    clave: str
    nombre: str
    fecha: date | None
    valor: Decimal | None = None
    unidad: str | None = None
    formula: str
    origen: str | None = None
    lamina: str
    no_calculable: str | None = None
    no_aplica: str | None = None


class Paso(_Modelo):
    empresa: str
    carpeta: str
    lista: tuple[Renglon, ...] = ()
    preguntas: tuple[Pregunta, ...] = ()
    pendientes: int = 0
    errores: tuple[str, ...] = ()
    anuncio: str | None = None
    calculo: ResultadoDelCurso | None = None
    resumen: tuple[LineaDeResumen, ...] = ()
    # S86.25: la pregunta opcional por gastos personales, o la utilidad ajustada.
    pregunta_travesuras: Pregunta | None = None
    travesuras: UtilidadAjustada | None = None
    sin_monto: tuple[str, ...] = ()
    mensaje: str = ""
    # Lo que se guarda con «sí». No va en la salida para el modelo.
    estados: EstadosRevisados | None = Field(default=None, exclude=True)


def carpeta_de(empresa: str) -> str:
    """«Mi Empresa, S.A. de C.V.» → «mi-empresa-s-a-de-c-v»."""

    return re.sub(r"[^a-z0-9]+", "-", normalizar(empresa)).strip("-") or "empresa"


# ---------------------------------------------------------------------------
# Respuestas del dueño
# ---------------------------------------------------------------------------


class _NoSe:
    pass


NO_SE = _NoSe()
Entendido = str | bool | Decimal | _NoSe


def _tipo(clave: str) -> str:
    return clave.split(":", 1)[0]


def _limpia(valor: str) -> str:
    return normalizar(valor).strip(" .¡!¿?«»\"'")


def _si_no(texto: str) -> bool | None:
    if texto in {"si", "s", "si, sumalas", "sumalas"}:
        return True
    if texto in {"no", "n"}:
        return False
    return None


def entender(clave: str, valor: str) -> Entendido | None:
    """La respuesta en forma que ESCALA usa; ``None`` si no se entiende."""

    tipo = _tipo(clave)
    texto = _limpia(valor)
    if texto in {"no se", "nose", "no lo se"}:
        return None if tipo in _BLOQUEAN_SIN_NO_SE else NO_SE
    if tipo == "C10":
        if texto in {"mes", "del mes", "solo del mes", "mensual"}:
            return "mes"
        if texto in {"acumulado", "acumulado del ano", "del ano", "ano", "anual", "desde enero"}:
            return "acumulado del año"
        return None
    if tipo == "R7":
        return next((QUE_ES[o] for o in QUE_ES if normalizar(o) == texto), None)
    if tipo == "unidad":
        return next((u for u in OPCIONES["unidad"] if normalizar(u) == texto), None)
    if tipo in {"R8", "suma", "C11", "C9"}:
        return _si_no(texto)
    if tipo == "C2":
        if texto in {"todas", "todas mis ventas", "todo"}:
            return "todas"
        if texto in {"solo lo facturado", "lo facturado", "facturado", "solo facturado"}:
            return "solo lo facturado"
        return None
    if tipo == "C1":
        try:
            porcentaje = Decimal(texto.replace("%", "").replace(",", "").strip())
        except InvalidOperation:
            return None
        return porcentaje if Decimal("0") <= porcentaje <= Decimal("100") else None
    if tipo == "C6":
        return _travesura(clave, texto)
    if tipo in {"C3", "C4"}:
        if tipo == "C4" and texto in {"no", "ninguno", "ninguna", "cero"}:
            return Decimal("0")
        monto = leer_monto(texto)
        return monto if monto is not None and monto >= 0 else None
    return None


def _travesura(clave: str, texto: str) -> Entendido | None:
    """S86.25: «C6» acepta «no»; «C6:<concepto>» acepta un monto mayor que 0.

    ESCALA no estima: un monto que no entiende no se suma, se dice.
    """
    if clave == "C6":
        return False if texto in {"no", "n", "ninguno", "ninguna", "nada"} else None
    if not clave.split(":", 1)[1].strip():
        return None
    monto = leer_monto(texto)
    return monto if monto is not None and monto > 0 else None


@dataclass(frozen=True)
class _Aplicadas:
    respuestas: Respuestas
    entendidas: dict[str, Entendido]
    errores: tuple[str, ...]


def _aplicar(conversacion: Conversacion) -> _Aplicadas:
    entendidas: dict[str, Entendido] = {}
    errores: list[str] = []
    for clave, valor in conversacion.respuestas.items():
        if _tipo(clave) not in OPCIONES:
            errores.append(f"No conozco la pregunta «{clave}»; no usé esa respuesta.")
            continue
        entendido = entender(clave, valor)
        if entendido is None:
            opciones = " · ".join(OPCIONES[_tipo(clave)])
            errores.append(
                f"No entendí tu respuesta «{valor}». Puedes contestar: {opciones}."
            )
            continue
        entendidas[clave] = entendido

    def dicho(clave: str) -> Entendido | None:
        return entendidas.get(clave)

    periodo = dicho("C10")
    credito, completas = dicho("C1"), dicho("C2")
    del_dueno, de_capital, iva = dicho("C3"), dicho("C4"), dicho("C9")
    respuestas = Respuestas(
        periodo=_periodo(periodo),
        ventas_a_credito=credito if isinstance(credito, Decimal) else None,
        ventas_completas=(
            "todas"
            if completas == "todas"
            else "solo lo facturado"
            if completas == "solo lo facturado"
            else None
        ),
        retiros_del_dueno=del_dueno if isinstance(del_dueno, Decimal) else None,
        retiros_de_capital=de_capital if isinstance(de_capital, Decimal) else None,
        iva_incluido=iva if isinstance(iva, bool) else None,
        pagan_interes={
            clave.split(":", 1)[1]: valor
            for clave, valor in entendidas.items()
            if _tipo(clave) == "C11" and isinstance(valor, bool)
        },
        que_es={
            clave.split(":", 1)[1]: valor
            for clave, valor in entendidas.items()
            if _tipo(clave) == "R7" and isinstance(valor, str)
        },
    )
    return _Aplicadas(respuestas, entendidas, tuple(errores))


def _periodo(valor: Entendido | None) -> Periodo | None:
    if valor == "mes":
        return "mes"
    if valor == "acumulado del año":
        return "acumulado del año"
    return None


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Leido:
    balances: list[LecturaEstados]
    resultados: LecturaEstados | None
    problemas: list[Pregunta]
    unidad: Unidad | None


def _es_resultados(lectura: LecturaEstados) -> bool:
    return any(c.concepto in {"ventas", "costo_ventas"} for c in lectura.cuentas)


def _problema(mensaje: str) -> Pregunta:
    return Pregunta(
        clave=None,
        pregunta=f"{mensaje} {_POR_CORREGIR}",
        para_que="No calculo hasta que esto quede bien.",
        bloquea=True,
    )


def _leer(conversacion: Conversacion, aplicadas: _Aplicadas, hoy: date) -> _Leido:
    balances: list[LecturaEstados] = []
    estados: list[LecturaEstados] = []
    problemas: list[Pregunta] = []
    unidad_dicha = aplicadas.entendidas.get("unidad")
    unidad: Unidad | None = None
    for archivo in conversacion.archivos:
        ruta = Path(archivo)
        try:
            lectura = leer_estados(ruta, hoy=hoy)
        except (OSError, ValueError) as error:
            problemas.append(_problema(f"No pude leer «{ruta.name}» ({error})."))
            continue
        preguntas = list(lectura.preguntas)
        if lectura.unidad is None and isinstance(unidad_dicha, str):
            lectura = lectura.model_copy(update={"unidad": unidad_dicha})
            preguntas = [p for p in preguntas if "en qué vienen las cifras" not in p]
        for suma in lectura.sumas_por_confirmar:
            if aplicadas.entendidas.get(_clave_de_suma(suma.concepto, suma.fecha)) is True:
                preguntas = [p for p in preguntas if p != suma.pregunta]
        lectura = lectura.model_copy(update={"preguntas": tuple(preguntas)})
        if lectura.fecha is None:
            problemas.append(_problema(f"«{ruta.name}» no dice de qué fecha son las cifras."))
        unidad = unidad or lectura.unidad
        (estados if _es_resultados(lectura) else balances).append(lectura)
    if not conversacion.archivos:
        problemas.append(_problema("Todavía no me mandas tus estados."))
    elif not balances:
        problemas.append(_problema("Me falta tu balance general."))
    if conversacion.archivos and not estados:
        problemas.append(_problema("Me falta tu estado de resultados."))
    if len(estados) > 1:
        nombres = " y ".join(f"«{e.archivo}»" for e in estados)
        problemas.append(_problema(f"Recibí {len(estados)} estados de resultados ({nombres}): uso uno."))
    return _Leido(balances, estados[0] if estados else None, problemas, unidad)


def _clave_de_suma(concepto: str, fecha: date | None) -> str:
    return f"suma:{concepto}:{fecha.isoformat() if fecha else 'sin-fecha'}"


# ---------------------------------------------------------------------------
# Pendientes, de la más importante a la menos importante
# ---------------------------------------------------------------------------


def _orden_de_problema(hallazgo: Hallazgo) -> int:
    return _PROBLEMAS.index(hallazgo.revision) if hallazgo.revision in _PROBLEMAS else len(_PROBLEMAS)


def _pendientes(
    leido: _Leido, revision: RevisionDeEstados | None, aplicadas: _Aplicadas
) -> list[Pregunta]:
    entendidas = aplicadas.entendidas
    problemas = list(leido.problemas)
    if revision is not None:
        problemas += [
            _problema(h.mensaje)
            for h in sorted(
                (h for h in revision.hallazgos if h.bloquea), key=_orden_de_problema
            )
        ]
    lecturas = [*leido.balances, *([leido.resultados] if leido.resultados else [])]
    for clave, valor in entendidas.items():
        if valor is False and _tipo(clave) == "suma":
            problemas.append(
                _problema("Me dijiste que no sume esas cuentas: no sé cuál usar.")
            )
        if valor is False and clave == "R8":
            problemas.append(_problema("Me dijiste que ese número no está bien."))

    preguntas: list[Pregunta] = []
    if revision is not None:
        for p in revision.preguntas:
            if p.codigo not in OPCIONES:
                continue  # «movida»: el dueño no mueve cuentas desde esta plática.
            clave = f"{p.codigo}:{p.cuenta}" if p.cuenta else p.codigo
            if clave in entendidas:
                continue
            preguntas.append(
                Pregunta(
                    clave=clave,
                    pregunta=p.pregunta,
                    para_que=p.para_que,
                    opciones=OPCIONES[p.codigo],
                    bloquea=p.bloquea,
                )
            )
    sin_unidad = [lectura.archivo or "tu archivo" for lectura in lecturas if lectura.unidad is None]
    if sin_unidad and "unidad" not in entendidas:
        nombres = " y ".join(f"«{nombre}»" for nombre in sin_unidad)
        preguntas.append(
            Pregunta(
                clave="unidad",
                pregunta=(
                    f"{nombres} no dicen en qué vienen las cifras: "
                    "¿pesos, miles de pesos o millones de pesos?"
                ),
                para_que="Para no confundir miles con pesos.",
                opciones=OPCIONES["unidad"],
                bloquea=True,
            )
        )
    if revision is not None and "R8" not in entendidas:
        dudosos = [h.mensaje for h in revision.hallazgos if h.revision == "R8"]
        if dudosos:
            preguntas.append(
                Pregunta(
                    clave="R8",
                    pregunta=f"Antes de calcular, revisa esto: {' '.join(dudosos)} ¿Está bien como viene?",
                    para_que="Para no calcular con un número mal escrito.",
                    opciones=OPCIONES["R8"],
                    bloquea=True,
                )
            )
    for lectura in lecturas:
        for suma in lectura.sumas_por_confirmar:
            clave = _clave_de_suma(suma.concepto, suma.fecha)
            if clave in entendidas:
                continue
            preguntas.append(
                Pregunta(
                    clave=clave,
                    pregunta=suma.pregunta,
                    para_que="Para usar el total correcto en el cálculo.",
                    opciones=OPCIONES["suma"],
                    bloquea=True,
                )
            )
    preguntas.sort(key=lambda p: _IMPORTANCIA.index(_tipo(p.clave or "")))
    return problemas + preguntas


# ---------------------------------------------------------------------------
# La lista ✔ / ? / ✘
# ---------------------------------------------------------------------------

_GRUPOS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("Bancos", ("bancos",), "No encontré bancos ni caja."),
    ("Clientes", ("clientes",), "No encontré clientes (cuentas por cobrar por ventas)."),
    ("Inventario", ("inventario",), "No encontré inventario. Si no vendes producto, no hace falta."),
    ("Proveedores", ("proveedores",), "No encontré proveedores."),
    ("Préstamos del banco", ("prestamos", "sobregiro"), ""),
    ("Capital", ("capital", "resultado_del_ejercicio"), "No encontré el capital."),
)
_NO_NEGATIVAS = frozenset({"clientes", "inventario", "proveedores"})
_DEL_ESTADO: tuple[tuple[str, str, bool], ...] = (
    ("ventas", "Ventas", True),
    ("costo_ventas", "Costo de ventas", True),
    ("gastos_operacion", "Gastos de operación", True),
    ("intereses", "Intereses (gastos financieros)", False),
    ("isr", "ISR", False),
    ("utilidad_neta", "Utilidad neta", True),
)
_PREGUNTAS_DE_LA_LISTA: tuple[tuple[str, str], ...] = (
    ("C1", "Qué parte de tus ventas es a crédito"),
    ("C2", "Si las ventas son todas o sólo lo facturado"),
    ("C3", "Cuánto sacaste tú del negocio"),
    ("C4", "Retiros de los socios o de capital"),
    ("C9", "Si clientes y proveedores incluyen IVA"),
)


def _montos(cuentas: list[CuentaEnCaja]) -> str:
    return "; ".join(f"«{c.nombre}» {formato_monto(c.monto)}" for c in cuentas)


def _dicho(valor: str) -> str:
    return f"me dijiste: {valor}."


def _lista(
    conversacion: Conversacion,
    leido: _Leido,
    revision: RevisionDeEstados | None,
    aplicadas: _Aplicadas,
) -> list[Renglon]:
    renglones: list[Renglon] = []

    def agrega(seccion: str, marca: Marca, nombre: str, detalle: str) -> None:
        renglones.append(Renglon(seccion=seccion, marca=marca, nombre=nombre, detalle=detalle))

    balance = "Balance general"
    fechas = revision.acomodo.fechas if revision is not None else ()
    cierre = (revision.balance_final if revision else None) or (fechas[-1] if fechas else None)
    if cierre is None:
        agrega(balance, "✘", "Balance al cierre", "Me falta tu balance general.")
    else:
        agrega(balance, "✔", "Balance al cierre", f"al {fecha_corta(cierre)}.")
    if revision is None or revision.periodo is None:
        otras = [f for f in fechas if f != cierre]
        detalle = (
            f"tengo uno al {fecha_corta(otras[0])}; " if otras else ""
        ) + "depende de si tu estado de resultados es del mes o del año."
        agrega(balance, "?", "Balance al inicio del periodo", detalle)
    elif revision.balance_inicial is not None:
        agrega(balance, "✔", "Balance al inicio del periodo", f"al {fecha_corta(revision.balance_inicial)}.")
    else:
        agrega(
            balance,
            "✘",
            "Balance al inicio del periodo",
            f"me falta el balance al {fecha_corta(revision.periodo.desde)}. Sin él no calculo "
            "el flujo neto, el flujo de operación ni los cambios del periodo; lo demás sí.",
        )

    if revision is not None and cierre is not None:
        al_cierre = [c for c in revision.acomodo.cuentas if c.fecha == cierre]
        for nombre, reglas, si_falta in _GRUPOS:
            cuentas = [c for c in al_cierre if c.regla in reglas]
            if not cuentas:
                agrega(balance, "✔" if not si_falta else "✘", nombre, si_falta or "No trae préstamos del banco.")
                continue
            negativa = any(c.regla in _NO_NEGATIVAS and c.monto < 0 for c in cuentas)
            agrega(balance, "✘" if negativa else "✔", nombre, _montos(cuentas))
        otras = [c for c in al_cierre if c.caja == "otras cuentas" and c.regla is not None]
        if otras:
            agrega(balance, "✔", "Otras cuentas", _montos(otras))
        sin_regla = {c.nombre: c for c in al_cierre if c.regla is None}
        for c in sin_regla.values():
            agrega(balance, "?", c.nombre, f"{formato_monto(c.monto)}: no sé en qué caja va.")
        for clave, valor in aplicadas.entendidas.items():
            if _tipo(clave) == "R7" and isinstance(valor, str):
                cuenta = clave.split(":", 1)[1]
                if any(c.nombre == cuenta for c in al_cierre):
                    dicho = next(o for o, regla in QUE_ES.items() if regla == valor)
                    agrega(balance, "✔", cuenta, _dicho(dicho))
        dudosas = {c.nombre for c in al_cierre if c.pregunta_interes}
        for nombre in sorted(dudosas):
            valor = aplicadas.entendidas.get(f"C11:{nombre}")
            if valor is None:
                agrega(balance, "?", f"{nombre}: ¿paga interés?", "Si paga interés, es deuda.")
            else:
                texto = "no sé" if isinstance(valor, _NoSe) else ("sí paga" if valor else "no paga")
                agrega(balance, "✔", f"{nombre}: ¿paga interés?", _dicho(texto))
        r1 = [h for h in revision.hallazgos if h.revision == "R1"]
        if r1 and all(h.resultado == "cuadra" for h in r1):
            agrega(balance, "✔", "Activo = pasivo + capital", "cuadra en cada fecha.")
        elif r1:
            agrega(balance, "✘", "Activo = pasivo + capital", "no cuadra (abajo te digo por cuánto).")

    estado = "Estado de resultados"
    resultados = leido.resultados
    if resultados is None:
        agrega(estado, "✘", "Estado de resultados", "Me falta tu estado de resultados.")
    else:
        agrega(estado, "✔", "Estado de resultados", f"«{resultados.archivo}».")
        if revision is not None and revision.periodo is not None:
            p = revision.periodo
            agrega(
                estado,
                "✔",
                "Periodo",
                f"{p.tipo}: del {fecha_corta(p.desde)} al {fecha_corta(p.hasta)} ({p.dias} días).",
            )
        else:
            agrega(estado, "?", "Periodo", "¿es sólo del mes o el acumulado del año?")
        hasta = resultados.fecha
        por_sumar = {
            s.concepto
            for s in resultados.sumas_por_confirmar
            if s.fecha == hasta and aplicadas.entendidas.get(_clave_de_suma(s.concepto, s.fecha)) is not True
        }
        for concepto, nombre, obligatorio in _DEL_ESTADO:
            del_concepto = [
                c for c in resultados.cuentas if c.concepto == concepto and c.fecha == hasta
            ]
            renglones_del = [c for c in del_concepto if not c.es_total] or del_concepto[:1]
            if not renglones_del:
                agrega(
                    estado,
                    "✘" if obligatorio else "?",
                    nombre,
                    "no viene en tu estado de resultados.",
                )
                continue
            detalle = "; ".join(f"«{c.nombre}» {formato_monto(c.monto)}" for c in renglones_del)
            negativa = concepto == "ventas" and any(c.monto < 0 for c in renglones_del)
            marca: Marca = "✘" if negativa else ("?" if concepto in por_sumar else "✔")
            agrega(estado, marca, nombre, detalle)

    preguntas = "Lo que te pregunto"
    sin_unidad = any(
        lectura.unidad is None
        for lectura in [*leido.balances, *([resultados] if resultados else [])]
    )
    if sin_unidad or "unidad" in aplicadas.entendidas:
        valor = aplicadas.entendidas.get("unidad")
        if isinstance(valor, str):
            agrega(preguntas, "✔", "En qué vienen las cifras", _dicho(valor))
        else:
            agrega(preguntas, "?", "En qué vienen las cifras", "tus archivos no lo dicen.")
    for codigo, nombre in _PREGUNTAS_DE_LA_LISTA:
        if codigo in aplicadas.entendidas:
            agrega(preguntas, "✔", nombre, _dicho(conversacion.respuestas[codigo]))
        else:
            agrega(preguntas, "?", nombre, "te lo pregunto.")

    if revision is not None:
        revisiones = "Revisiones"
        fallan = {h.revision for h in revision.hallazgos if h.resultado != "cuadra"}
        cuadran = sorted(
            {h.revision for h in revision.hallazgos if h.resultado == "cuadra"} - fallan,
            key=lambda r: int(r[1:]),
        )
        for h in revision.hallazgos:
            if h.resultado == "cuadra" or h.revision in {"R1"}:
                continue
            marca = "✘" if h.bloquea else "?"
            agrega(revisiones, marca, h.revision, h.mensaje)
        if cuadran:
            agrega(revisiones, "✔", "Revisiones que cuadran", ", ".join(cuadran) + ".")
    return renglones


# ---------------------------------------------------------------------------
# Anuncio y resumen
# ---------------------------------------------------------------------------


def _en_lista(nombres: list[str]) -> str:
    if len(nombres) <= 1:
        return "".join(nombres)
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


def _anuncio(calculo: ResultadoDelCurso, unidad: Unidad | None) -> str:
    final = calculo.balance_final
    del_cierre: list[Indicador] = [
        i for i in calculo.indicadores if i.fecha == final or i.fecha is None
    ]
    voy: list[str] = []
    no_puedo: dict[str, list[str]] = {}
    for indicador in del_cierre:
        if isinstance(indicador, Calculado):
            if indicador.nombre not in voy:
                voy.append(indicador.nombre)
        else:
            razon = (
                indicador.no_calculable
                if isinstance(indicador, NoCalculable)
                else f"no aplica: {indicador.no_aplica}"
            )
            nombres = no_puedo.setdefault(razon, [])
            if indicador.nombre not in nombres:
                nombres.append(indicador.nombre)
    if any(isinstance(p.flujo, Calculado) for p in calculo.poder_del_uno):
        voy.append("el poder del uno")
    partes = [f"Con esto voy a calcular: {_en_lista(voy)}."]
    for razon, nombres in no_puedo.items():
        partes.append(f"No puedo calcular {_en_lista(nombres)}, porque {razon}.")
    if unidad is not None and unidad != "pesos":
        partes.append(f"Tus cifras vienen en {unidad}: los montos de abajo están en {unidad}.")
    return " ".join(partes)


def _linea(indicador: Indicador) -> LineaDeResumen:
    base = {
        "clave": indicador.clave,
        "nombre": indicador.nombre,
        "fecha": indicador.fecha,
        "formula": indicador.formula,
        "lamina": indicador.lamina,
    }
    if isinstance(indicador, Calculado):
        return LineaDeResumen(
            valor=indicador.valor, unidad=indicador.unidad, origen=indicador.origen, **base
        )
    if isinstance(indicador, NoAplica):
        return LineaDeResumen(no_aplica=indicador.no_aplica, **base)
    return LineaDeResumen(no_calculable=indicador.no_calculable, **base)


def _resumen(calculo: ResultadoDelCurso) -> list[LineaDeResumen]:
    final = calculo.balance_final
    if final is None:
        return []
    lineas: list[LineaDeResumen] = []
    for clave in RESUMEN:
        try:
            lineas.append(_linea(calculo.indicador(clave, final)))
        except KeyError:
            continue
    return lineas


def _valor(linea: LineaDeResumen) -> str:
    assert linea.valor is not None
    if linea.unidad == "proporción":
        return str(linea.valor)
    texto = formato_monto(linea.valor)
    return f"{texto} días" if linea.unidad == "días" else texto


def _texto_de_linea(linea: LineaDeResumen) -> str:
    if linea.valor is not None:
        return (
            f"- {linea.nombre}: {_valor(linea)}\n"
            f"  {linea.formula}. {linea.origen} (lámina {linea.lamina})."
        )
    if linea.no_aplica is not None:
        return f"- {linea.nombre}: no aplica: {linea.no_aplica}"
    return f"- {linea.nombre}: no calculable: {linea.no_calculable}"


# ---------------------------------------------------------------------------
# Las travesuras (S86.25): opcional, sin juicio, después del resumen
# ---------------------------------------------------------------------------

PREGUNTA_TRAVESURAS = Pregunta(
    clave="C6",
    pregunta=(
        "Opcional, sin juicio: ¿la empresa pagó gastos personales tuyos o de tu familia, "
        "o hubo ventas que no quedaron en tus estados? Según el curso de cash que vimos, "
        f"pasa seguido; por ejemplo: {', '.join(EJEMPLOS_DE_TRAVESURAS)}. "
        "Si quieres verlos, dime cada uno con su monto en pesos. Si no hay, contesta «no»."
    ),
    para_que=(
        "Para ver tu utilidad como si esos gastos no estuvieran. "
        "Solo sumo los montos que tú me des; no estimo ninguno."
    ),
    opciones=OPCIONES["C6"],
)


@dataclass(frozen=True)
class _Travesuras:
    pregunta: Pregunta | None = None
    resultado: UtilidadAjustada | None = None
    sin_monto: tuple[str, ...] = ()


def _travesuras(estados: EstadosRevisados, entendidas: dict[str, Entendido]) -> _Travesuras:
    """Suma solo lo que dijo el dueño; sin respuesta, hace la pregunta opcional."""
    ajustes: list[AjusteDelDueno] = []
    sin_monto: list[str] = []
    for clave, valor in entendidas.items():
        if _tipo(clave) != "C6" or clave == "C6":
            continue
        concepto = clave.split(":", 1)[1].strip()
        if isinstance(valor, Decimal):
            ajustes.append(AjusteDelDueno(concepto=concepto, monto=valor))
        else:
            sin_monto.append(concepto)
    if not ajustes and not sin_monto and entendidas.get("C6") is not False:
        return _Travesuras(pregunta=PREGUNTA_TRAVESURAS)
    return _Travesuras(resultado=utilidad_ajustada(estados, ajustes), sin_monto=tuple(sin_monto))


def _parte_de_travesuras(parte: Calculado | NoCalculable) -> str:
    if isinstance(parte, NoCalculable):
        return f"- {parte.nombre}: no calculable: {parte.no_calculable}"
    return (
        f"- {parte.nombre}: {formato_monto(parte.valor)}\n"
        f"  {parte.formula}. {parte.origen} (lámina {parte.lamina})."
    )


def _texto_de_travesuras(resultado: UtilidadAjustada, sin_monto: tuple[str, ...]) -> str:
    lineas = ["Tu utilidad sin travesuras (gastos personales que pagó la empresa):"]
    lineas.append(_parte_de_travesuras(resultado.utilidad_contable))
    if resultado.ajustes:
        lineas.append("- Ajustes que me dijiste:")
        lineas += [f"  - {a.concepto}: {formato_monto(a.monto)}" for a in resultado.ajustes]
    else:
        lineas.append("- Ajustes que me dijiste: ninguno.")
    lineas += [f"  - «{concepto}»: sin monto no lo sumo." for concepto in sin_monto]
    lineas.append(_parte_de_travesuras(resultado.utilidad_ajustada))
    lineas.append(
        "Solo sumo los montos que tú me diste; no estimo ninguno. "
        f"No recalculo impuestos. {resultado.aviso}"
    )
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# El paso
# ---------------------------------------------------------------------------


def atender(
    conversacion: Conversacion, *, hoy: date, carpeta: Path = CARPETA
) -> Paso:
    """Un mensaje de ESCALA: lista, hasta 3 preguntas o el anuncio y el resumen."""

    aplicadas = _aplicar(conversacion)
    leido = _leer(conversacion, aplicadas, hoy)
    revision: RevisionDeEstados | None = None
    if leido.balances or leido.resultados is not None:
        revision = revisar_estados(
            leido.balances, leido.resultados, respuestas=aplicadas.respuestas, hoy=hoy
        )
    pendientes = _pendientes(leido, revision, aplicadas)
    lista = _lista(conversacion, leido, revision, aplicadas)
    destino = f"{carpeta.as_posix().rstrip('/')}/{carpeta_de(conversacion.empresa)}/"

    calculo: ResultadoDelCurso | None = None
    estados: EstadosRevisados | None = None
    anuncio: str | None = None
    resumen: list[LineaDeResumen] = []
    travesuras = _Travesuras()
    if not pendientes and revision is not None and leido.resultados is not None:
        estados = EstadosRevisados(
            revision=revision, resultados=leido.resultados, respuestas=aplicadas.respuestas
        )
        calculo = calcular_curso(estados)
        if calculo.no_calculable is None:
            anuncio = _anuncio(calculo, leido.unidad)
            resumen = _resumen(calculo)
            travesuras = _travesuras(estados, aplicadas.entendidas)
        else:
            estados = None

    paso = Paso(
        empresa=conversacion.empresa,
        carpeta=destino,
        lista=tuple(lista),
        preguntas=tuple(pendientes[:3]),
        pendientes=len(pendientes),
        errores=aplicadas.errores,
        anuncio=anuncio,
        calculo=calculo,
        resumen=tuple(resumen),
        pregunta_travesuras=travesuras.pregunta,
        travesuras=travesuras.resultado,
        sin_monto=travesuras.sin_monto,
        estados=estados,
    )
    return paso.model_copy(update={"mensaje": _mensaje(paso, hoy)})


def _mensaje(paso: Paso, hoy: date) -> str:
    partes = [f"Analizo los estados de {paso.empresa.rstrip('.')}."]
    partes.append("Esto es lo que necesito (✔ lo tengo · ? no me queda claro · ✘ me falta):")
    seccion = ""
    renglones: list[str] = []
    for renglon in paso.lista:
        if renglon.seccion != seccion:
            seccion = renglon.seccion
            renglones.append(f"\n{seccion}")
        renglones.append(f"{renglon.marca} {renglon.nombre}: {renglon.detalle}")
    partes.append("\n".join(renglones).strip("\n"))
    if paso.errores:
        partes.append("\n".join(paso.errores))
    if paso.preguntas:
        problemas = any(p.clave is None for p in paso.preguntas)
        encabezado = (
            "No calculo todavía: esto no cuadra o me falta."
            if problemas
            else "No calculo todavía. Antes necesito que me contestes esto."
        )
        partes.append(
            f"{encabezado} Van {len(paso.preguntas)} de {paso.pendientes} pendientes:"
        )
        numeradas: list[str] = []
        for numero, pregunta in enumerate(paso.preguntas, start=1):
            texto = f"{numero}. {pregunta.pregunta}\n   Para qué: {pregunta.para_que}"
            if pregunta.opciones:
                texto += f"\n   Puedes contestar: {' · '.join(pregunta.opciones)}."
            numeradas.append(texto)
        partes.append("\n".join(numeradas))
        return "\n\n".join(partes)
    if paso.calculo is not None and paso.calculo.no_calculable is not None:
        partes.append(f"No calculo: {paso.calculo.no_calculable}")
        return "\n\n".join(partes)
    if paso.anuncio is not None:
        partes.append(paso.anuncio)
    if paso.resumen and paso.calculo is not None and paso.calculo.balance_final is not None:
        cierre = fecha_corta(paso.calculo.balance_final)
        lineas = "\n".join(_texto_de_linea(linea) for linea in paso.resumen)
        partes.append(f"Resumen al {cierre} (lo calculó la calculadora de ESCALA):\n{lineas}")
        if paso.travesuras is not None:
            partes.append(_texto_de_travesuras(paso.travesuras, paso.sin_monto))
        elif paso.pregunta_travesuras is not None:
            pregunta = paso.pregunta_travesuras
            partes.append(
                f"{pregunta.pregunta}\n   Para qué: {pregunta.para_que}"
                f"\n   Puedes contestar: {' · '.join(pregunta.opciones)}."
            )
        partes.append(
            f"¿Guardo tus estados revisados en {paso.carpeta} con fecha {hoy.isoformat()}? "
            "Si quieres, responde «sí». Sin tu «sí» no guardo nada."
        )
    return "\n\n".join(partes)


# ---------------------------------------------------------------------------
# Entrada interna
# ---------------------------------------------------------------------------


def _imprime(texto: str) -> None:
    salida = sys.stdout
    reconfigurar = getattr(salida, "reconfigure", None)
    if callable(reconfigurar):
        reconfigurar(encoding="utf-8")
    salida.write(texto + "\n")


def _no(razon: str) -> int:
    _imprime(json.dumps({"no_calculable": razon}, ensure_ascii=False))
    return 2


def _argumentos() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="escala_server.cash.escenario",
        description="Analiza el balance general y el estado de resultados del dueño.",
        exit_on_error=False,
    )
    parser.add_argument("--empresa", required=True)
    parser.add_argument("--archivo", action="append", default=[])
    parser.add_argument("--quita-archivo", action="append", default=[])
    parser.add_argument("--responde", action="append", default=[])
    parser.add_argument("--guardar")
    parser.add_argument("--carpeta", default=str(CARPETA))
    parser.add_argument("--conversacion")
    parser.add_argument("--hoy")
    parser.add_argument("--formato", choices=("json", "texto"), default="json")
    return parser


def ruta_del_borrador(empresa: str) -> Path:
    """El borrador de la plática: privado del usuario, sobrevive un reinicio."""

    return Path.home() / ".escala" / "borradores" / f"{carpeta_de(empresa)}.json"


class EscrituraInsegura(Exception):
    """La ruta es un enlace simbólico: no se escribe ni se lee a través de él."""


def _sin_enlace(ruta: Path) -> None:
    if ruta.is_symlink() or ruta.parent.is_symlink():
        raise EscrituraInsegura(
            f"{ruta} es un enlace simbólico; no escribo ni leo a través de un enlace"
        )


def escribir_privado(ruta: Path, texto: str, *, carpeta_privada: bool = False) -> None:
    """Escribe de forma atómica (temporal en la misma carpeta + ``os.replace``).

    El archivo queda 0o600. Con ``carpeta_privada`` la carpeta queda 0o700.
    Nunca sigue un enlace simbólico: si ``ruta`` lo es, no escribe.
    """

    ruta.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _sin_enlace(ruta)
    if carpeta_privada:
        os.chmod(ruta.parent, 0o700)
    descriptor, temporal = tempfile.mkstemp(dir=ruta.parent, prefix=".", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
            archivo.write(texto)
        os.chmod(temporal, 0o600)
        os.replace(temporal, ruta)  # reemplaza la entrada; no sigue enlaces
    except BaseException:
        Path(temporal).unlink(missing_ok=True)
        raise


def _lee(ruta: Path) -> str:
    _sin_enlace(ruta)
    return ruta.read_text(encoding="utf-8")


def es_si(respuesta: str | None) -> bool:
    """Sólo «sí» (o «si») cuenta como permiso para guardar."""

    return respuesta is not None and _limpia(respuesta) == "si"


def _libre(carpeta: Path, nombre: str) -> Path:
    """Nunca sobrescribe: la segunda versión del día es ``-2``, luego ``-3``…"""

    ruta = carpeta / f"{nombre}.json"
    version = 2
    while ruta.exists() or ruta.is_symlink():
        ruta = carpeta / f"{nombre}-{version}.json"
        version += 1
    return ruta


def guardar(paso: Paso, conversacion: Conversacion, *, carpeta: Path, hoy: date) -> list[Path]:
    """Escribe en ``carpeta/<empresa>/``. Llamar sólo después de un «sí» del dueño."""

    destino = carpeta / carpeta_de(conversacion.empresa)
    destino.mkdir(parents=True, exist_ok=True)
    platica = destino / "conversacion.json"
    escribir_privado(platica, conversacion.model_dump_json(indent=2))
    guardados = [platica]
    if paso.estados is not None:
        revisados = _libre(destino, f"estados-revisados-{hoy.isoformat()}")
        escribir_privado(revisados, paso.estados.model_dump_json(indent=2))
        guardados.append(revisados)
    return guardados


def _mensaje_de_guardado(guardados: list[Path]) -> str:
    nombres = " y ".join(f"«{ruta.name}»" for ruta in guardados)
    carpeta = guardados[0].parent.as_posix()
    texto = f"Guardé {nombres} en {carpeta}/."
    if len(guardados) == 1:
        texto += " Todavía no hay cálculo: guardé la plática para seguir otro día."
    return texto


def main(argv: Sequence[str] | None = None) -> int:
    """``python -m escala_server.cash.escenario --empresa … --archivo …`` → JSON."""

    try:
        args = _argumentos().parse_args(list(sys.argv[1:] if argv is None else argv))
    except (argparse.ArgumentError, SystemExit):
        return _no(
            "uso: python -m escala_server.cash.escenario --empresa NOMBRE "
            "[--archivo RUTA ...] [--responde CLAVE=VALOR ...] [--guardar sí]"
        )
    try:
        hoy = date.fromisoformat(args.hoy) if args.hoy else date.today()
    except ValueError:
        return _no(f"la fecha «{args.hoy}» no es AAAA-MM-DD")
    empresa: str = args.empresa
    trabajo = Path(args.conversacion) if args.conversacion else ruta_del_borrador(empresa)
    carpeta = Path(args.carpeta)
    conversacion = Conversacion(empresa=empresa)
    # Entre mensajes: el archivo de trabajo. Otro día: lo que el dueño guardó con «sí».
    guardada = carpeta / carpeta_de(empresa) / "conversacion.json"
    anterior = (
        trabajo
        if trabajo.exists() or trabajo.is_symlink()
        else guardada
        if guardada.exists() or guardada.is_symlink()
        else None
    )
    if anterior is not None:
        try:
            conversacion = Conversacion.model_validate_json(_lee(anterior))
        except EscrituraInsegura as error:
            return _no(str(error))
        except (OSError, ValidationError):
            return _no(f"no pude leer la plática guardada en {anterior}")
    archivos = [a for a in conversacion.archivos if a not in args.quita_archivo]
    for archivo in args.archivo:
        ruta = str(Path(archivo).resolve())
        if ruta not in archivos:
            archivos.append(ruta)
    respuestas = dict(conversacion.respuestas)
    for respuesta in args.responde:
        clave, igual, valor = str(respuesta).partition("=")
        if not igual:
            return _no(f"la respuesta «{respuesta}» no trae CLAVE=VALOR")
        respuestas[clave.strip()] = valor.strip()
    conversacion = conversacion.model_copy(
        update={"empresa": empresa, "archivos": tuple(archivos), "respuestas": respuestas}
    )
    paso = atender(conversacion, hoy=hoy, carpeta=carpeta)
    guardados: list[Path] = []
    try:
        escribir_privado(
            trabajo,
            conversacion.model_dump_json(indent=2),
            carpeta_privada=args.conversacion is None,
        )
        if es_si(args.guardar):
            guardados = guardar(paso, conversacion, carpeta=carpeta, hoy=hoy)
    except EscrituraInsegura as error:
        return _no(str(error))
    if guardados:
        partes = [p for p in paso.mensaje.split("\n\n") if not p.startswith("¿Guardo ")]
        partes.append(_mensaje_de_guardado(guardados))
        paso = paso.model_copy(update={"mensaje": "\n\n".join(partes)})
    if args.formato == "texto":
        _imprime(paso.mensaje)
        return 0
    salida = json.loads(paso.model_dump_json())
    salida["guardado"] = [ruta.as_posix() for ruta in guardados]
    salida["conversacion"] = trabajo.as_posix()
    _imprime(json.dumps(salida, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
