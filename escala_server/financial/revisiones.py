"""ESCALA revisa que tus estados cuadren antes de calcular (S86.15).

Toma lo que leyó el lector (S86.14), acomoda el balance en sus 4 cajas
(``cajas.py``), empareja los balances con el periodo del estado de resultados
y corre las revisiones R1–R11 del curso de cash que vimos. Devuelve hallazgos
y preguntas como datos. Si algo bloquea, ESCALA no calcula y dice por qué,
con el número.

Aquí no hay indicadores (S86.16) ni conversación (S86.17). Tampoco se
multiplica nunca un periodo: se entregan los días que cubre el estado.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .cajas import Acomodo, Caja, CuentaEnCaja, TotalesPorCaja, acomodar
from .formatos import fecha_corta, formato_monto, palabras
from .lector import DIAS_PARA_AVISAR, CuentaLeida, LecturaEstados

# Datos de ESCALA (configurables), no del curso:
# - tolerancia de R1/R2/R3: el curso dice 1 peso.
# - umbral de tasa anormal: 25% anual. Sólo sirve para formular la pregunta C11.
TOLERANCIA = Decimal("1")
UMBRAL_TASA = Decimal("0.25")
_DIAS_DE_UN_ANIO = range(360, 367)
_CERO = Decimal("0")
_CIEN = Decimal("100")

Periodo = Literal["mes", "acumulado del año"]
Resultado = Literal["cuadra", "aviso", "no cuadra", "no revisable"]
Revision = Literal["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11"]


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Respuestas(_Modelo):
    """Lo que el dueño ya contestó. ``None`` = todavía no contesta."""

    periodo: Periodo | None = None  # C10
    ventas_a_credito: Decimal | None = Field(default=None, ge=0, le=100)  # C1, en %
    ventas_completas: Literal["todas", "solo lo facturado"] | None = None  # C2
    retiros_del_dueno: Decimal | None = None  # C3
    retiros_de_capital: Decimal | None = None  # C4
    iva_incluido: bool | None = None  # C9
    pagan_interes: dict[str, bool] = Field(default_factory=dict[str, bool])  # C11
    movimientos: dict[str, Caja] = Field(default_factory=dict[str, Caja])


class PeriodoDelEstado(_Modelo):
    tipo: Periodo
    desde: date  # cierre anterior: el balance inicial va a esta fecha
    hasta: date
    dias: int


class Hallazgo(_Modelo):
    revision: Revision
    resultado: Resultado
    mensaje: str
    bloquea: bool = False
    fecha: date | None = None
    diferencia: Decimal | None = None


class PreguntaPendiente(_Modelo):
    codigo: str  # C1–C11, R7 o «movida»
    pregunta: str
    para_que: str
    bloquea: bool = False
    cuenta: str | None = None


class RevisionDeEstados(_Modelo):
    acomodo: Acomodo
    periodo: PeriodoDelEstado | None
    balance_inicial: date | None
    balance_final: date | None
    hallazgos: tuple[Hallazgo, ...]
    preguntas: tuple[PreguntaPendiente, ...]
    # intereses ÷ promedio de la deuda bancaria × 100; sólo con un estado de 12 meses.
    tasa_deuda_bancaria: Decimal | None = None
    # Igual, sumando los pasivos que no sabemos si pagan interés (C11).
    tasa_con_documentos: Decimal | None = None

    @property
    def puede_calcular(self) -> bool:
        return not any(h.bloquea for h in self.hallazgos) and not any(
            p.bloquea for p in self.preguntas
        )


# ---------------------------------------------------------------------------
# Periodo
# ---------------------------------------------------------------------------


def _fin_del_mes_anterior(fecha: date) -> date:
    return fecha.replace(day=1) - timedelta(days=1)


def _periodo(tipo: Periodo, hasta: date) -> PeriodoDelEstado:
    if tipo == "acumulado del año":
        desde = date(hasta.year - 1, 12, 31)
    else:
        desde = _fin_del_mes_anterior(hasta)
    return PeriodoDelEstado(tipo=tipo, desde=desde, hasta=hasta, dias=(hasta - desde).days)


def _fecha_del_estado(resultados: LecturaEstados | None) -> date | None:
    if resultados is None:
        return None
    fechas = [c.fecha for c in resultados.cuentas if c.fecha is not None]
    return max(fechas) if fechas else resultados.fecha


def _del_estado(
    resultados: LecturaEstados | None, concepto: str, fecha: date | None
) -> Decimal | None:
    if resultados is None or fecha is None:
        return None
    for cuenta in resultados.cuentas:
        if cuenta.concepto == concepto and not cuenta.es_total and cuenta.fecha == fecha:
            return cuenta.monto
    return None


# ---------------------------------------------------------------------------
# Revisiones
# ---------------------------------------------------------------------------


def _compara(
    diferencia: Decimal, tolerancia: Decimal
) -> Literal["cuadra", "aviso", "no cuadra"]:
    if diferencia == 0:
        return "cuadra"
    return "aviso" if diferencia <= tolerancia else "no cuadra"


def _r1(totales: TotalesPorCaja, tolerancia: Decimal) -> Hallazgo:
    fuentes = totales.pasivo + totales.capital_contable
    diferencia = abs(totales.activo - fuentes)
    resultado = _compara(diferencia, tolerancia)
    cuando = fecha_corta(totales.fecha)
    activo, otro_lado = formato_monto(totales.activo), formato_monto(fuentes)
    if resultado == "cuadra":
        mensaje = (
            f"Tu balance cuadra al {cuando}: el activo suma {activo} "
            f"y el pasivo más el capital suman {otro_lado}."
        )
    elif resultado == "aviso":
        mensaje = (
            f"Al {cuando} tu activo suma {activo} y el pasivo más el capital suman "
            f"{otro_lado}: no cuadra por {formato_monto(diferencia)}: "
            "¿redondeo o falta una cuenta?"
        )
    else:
        mensaje = (
            f"Al {cuando} tu activo suma {activo} y el pasivo más el capital suman "
            f"{otro_lado}: no cuadra por {formato_monto(diferencia)}. "
            "No calculo nada hasta que cuadre: ¿falta una cuenta o hay una cifra mal escrita?"
        )
    return Hallazgo(
        revision="R1",
        resultado=resultado,
        mensaje=mensaje,
        bloquea=resultado == "no cuadra",
        fecha=totales.fecha,
        diferencia=diferencia,
    )


def _r10(totales: TotalesPorCaja, tolerancia: Decimal) -> Hallazgo:
    por_diferencia = totales.deuda_neta + totales.capital - totales.capital_de_trabajo
    diferencia = abs(totales.otras_cuentas - por_diferencia)
    resultado = _compara(diferencia, tolerancia)
    mensaje = (
        f"Al {fecha_corta(totales.fecha)} otras cuentas suman "
        f"{formato_monto(totales.otras_cuentas)} por renglones y "
        f"{formato_monto(por_diferencia)} por diferencia "
        "(deuda neta + capital − capital de trabajo)."
    )
    if resultado != "cuadra":
        mensaje += " Si no coinciden, hay una cuenta en la caja equivocada o el balance no cuadra."
    # R1 ya bloquea si el balance no cuadra; R10 sólo lo dice en cajas.
    return Hallazgo(
        revision="R10",
        resultado=resultado,
        mensaje=mensaje,
        fecha=totales.fecha,
        diferencia=diferencia,
    )


def _que_suma(total: CuentaLeida) -> Literal["activo", "pasivo", "capital", "pasivo y capital"] | None:
    resto = palabras(total.nombre)[1:]
    if resto == ("activo",):
        return "activo"
    if resto == ("pasivo",):
        return "pasivo"
    if resto in {("capital",), ("capital", "contable")}:
        return "capital"
    if resto in {
        ("pasivo", "y", "capital"),
        ("pasivo", "capital"),
        ("pasivo", "y", "capital", "contable"),
        ("pasivo", "mas", "capital"),
    }:
        return "pasivo y capital"
    return None


def _r3(acomodo: Acomodo, tolerancia: Decimal) -> list[Hallazgo]:
    hallazgos: list[Hallazgo] = []
    for total in acomodo.totales_del_documento:
        que = _que_suma(total)
        totales = acomodo.en(total.fecha) if total.fecha is not None else None
        if que is None or totales is None:
            continue
        suma = {
            "activo": totales.activo,
            "pasivo": totales.pasivo,
            "capital": totales.capital_contable,
            "pasivo y capital": totales.pasivo + totales.capital_contable,
        }[que]
        diferencia = abs(total.monto - suma)
        resultado = _compara(diferencia, tolerancia)
        mensaje = (
            f"«{total.nombre}» al {fecha_corta(totales.fecha)} dice "
            f"{formato_monto(total.monto)} y sus cuentas suman {formato_monto(suma)}"
        )
        mensaje += "." if resultado == "cuadra" else f": diferencia de {formato_monto(diferencia)}."
        hallazgos.append(
            Hallazgo(
                revision="R3",
                resultado=resultado,
                mensaje=mensaje,
                bloquea=resultado == "no cuadra",
                fecha=totales.fecha,
                diferencia=diferencia,
            )
        )
    return hallazgos


def _r2(
    acomodo: Acomodo,
    fecha: date | None,
    utilidad: Decimal | None,
    tolerancia: Decimal,
) -> Hallazgo:
    del_balance = next(
        (
            c
            for c in acomodo.cuentas
            if c.regla == "resultado_del_ejercicio" and c.fecha == fecha
        ),
        None,
    )
    if del_balance is None or utilidad is None or fecha is None:
        return Hallazgo(
            revision="R2",
            resultado="no revisable",
            mensaje=(
                "Tu balance no separa la utilidad del ejercicio: no puedo compararla "
                "con la utilidad neta del estado de resultados."
            ),
            fecha=fecha,
        )
    diferencia = abs(utilidad - del_balance.monto)
    resultado = _compara(diferencia, tolerancia)
    mensaje = (
        f"Tu estado de resultados da {formato_monto(utilidad)} de utilidad neta y el "
        f"balance dice {formato_monto(del_balance.monto)} en «{del_balance.nombre}»"
    )
    mensaje += "." if resultado == "cuadra" else f": diferencia de {formato_monto(diferencia)}. ¿Cuál es la buena?"
    # Avisa, no bloquea: el contador pudo traspasar parte de la utilidad.
    return Hallazgo(
        revision="R2",
        resultado=resultado,
        mensaje=mensaje,
        fecha=fecha,
        diferencia=diferencia,
    )


def _r4(
    periodo: PeriodoDelEstado | None,
    fechas: tuple[date, ...],
    inicial: date | None,
    final: date | None,
) -> list[Hallazgo]:
    if periodo is None:
        return []  # C10 bloquea y pregunta.
    hasta, desde = fecha_corta(periodo.hasta), fecha_corta(periodo.desde)
    if final is None:
        tengo = ", ".join(fecha_corta(f) for f in fechas) or "ninguna fecha"
        return [
            Hallazgo(
                revision="R4",
                resultado="no cuadra",
                bloquea=True,
                fecha=periodo.hasta,
                mensaje=(
                    f"Tu estado de resultados llega al {hasta}, pero tus balances son "
                    f"al {tengo}. Necesito el balance al {hasta}."
                ),
            )
        ]
    if inicial is None:
        return [
            Hallazgo(
                revision="R4",
                resultado="aviso",
                fecha=periodo.desde,
                mensaje=(
                    f"Tu estado cubre del {desde} al {hasta} ({periodo.dias} días), pero no "
                    f"tengo el balance al {desde}. Sin él no puedo medir cambios del periodo; "
                    "lo demás sí."
                ),
            )
        ]
    return [
        Hallazgo(
            revision="R4",
            resultado="cuadra",
            fecha=periodo.hasta,
            mensaje=(
                f"El balance al {desde} y el del {hasta} abren y cierran tu estado "
                f"de resultados ({periodo.dias} días)."
            ),
        )
    ]


def _r5(balances: list[LecturaEstados], resultados: LecturaEstados | None) -> Hallazgo:
    # El curso pide una sola moneda. El lector no distingue monedas: aquí se
    # revisa que todo venga en la misma unidad (pesos, miles o millones).
    lecturas = [*balances, *([resultados] if resultados is not None else [])]
    unidades = {lectura.unidad for lectura in lecturas if lectura.unidad is not None}
    if len(unidades) > 1:
        detalle = "; ".join(
            f"{'el balance' if lectura in balances else 'el estado de resultados'} en {lectura.unidad}"
            for lectura in lecturas
            if lectura.unidad is not None
        )
        return Hallazgo(
            revision="R5",
            resultado="no cuadra",
            bloquea=True,
            mensaje=(
                f"Tus archivos vienen en unidades distintas ({detalle}). "
                "No mezclo unidades: ¿me confirmas en qué viene cada uno?"
            ),
        )
    if not unidades:
        return Hallazgo(
            revision="R5",
            resultado="no revisable",
            mensaje="Tus archivos no dicen en qué vienen las cifras.",
        )
    return Hallazgo(
        revision="R5",
        resultado="cuadra",
        mensaje=f"Todo viene en {next(iter(unidades))}.",
    )


_NO_NEGATIVAS = {"clientes": "Clientes", "inventario": "Inventario", "proveedores": "Proveedores"}


def _r6(acomodo: Acomodo, resultados: LecturaEstados | None) -> list[Hallazgo]:
    negativas: list[tuple[str, Decimal, date | None]] = [
        (c.nombre, c.monto, c.fecha)
        for c in acomodo.cuentas
        if c.regla in _NO_NEGATIVAS and c.monto < 0
    ]
    if resultados is not None:
        negativas += [
            (c.nombre, c.monto, c.fecha)
            for c in resultados.cuentas
            if c.concepto == "ventas" and not c.es_total and c.monto < 0
        ]
    if not negativas:
        return [
            Hallazgo(
                revision="R6",
                resultado="cuadra",
                mensaje="Clientes, inventario, proveedores y ventas vienen en positivo.",
            )
        ]
    return [
        Hallazgo(
            revision="R6",
            resultado="no cuadra",
            bloquea=True,
            fecha=fecha,
            mensaje=(
                f"«{nombre}»"
                + (f" al {fecha_corta(fecha)}" if fecha is not None else "")
                + f" viene en {formato_monto(monto)}. Clientes, inventario, proveedores y "
                "ventas no son negativos: ¿es un saldo a favor, o tu sistema pone esa "
                "cuenta en negativo?"
            ),
        )
        for nombre, monto, fecha in negativas
    ]


def _r8(lecturas: list[LecturaEstados]) -> list[Hallazgo]:
    return [
        Hallazgo(revision="R8", resultado="aviso", mensaje=aviso.mensaje)
        for lectura in lecturas
        for aviso in lectura.avisos
        if aviso.codigo == "posible_digito_invertido"
    ]


def _r9(
    cambio_menos_utilidad: Decimal | None, respuestas: Respuestas, tolerancia: Decimal
) -> list[Hallazgo]:
    if cambio_menos_utilidad is None:
        return []
    if respuestas.retiros_de_capital is None and respuestas.retiros_del_dueno is None:
        return []  # C3/C4 todavía no se contestan; la pregunta C4 lleva el número.
    salio = -cambio_menos_utilidad
    dijo = (respuestas.retiros_de_capital or _CERO) + (respuestas.retiros_del_dueno or _CERO)
    diferencia = abs(salio - dijo)
    if diferencia <= tolerancia:
        return [
            Hallazgo(
                revision="R9",
                resultado="cuadra",
                diferencia=diferencia,
                mensaje=(
                    f"Tu capital cambió {formato_monto(salio)} menos de lo que explica la "
                    f"utilidad, y me dijiste {formato_monto(dijo)} de retiros: cuadra."
                ),
            )
        ]
    return [
        Hallazgo(
            revision="R9",
            resultado="aviso",
            diferencia=diferencia,
            mensaje=(
                f"Tu capital bajó {formato_monto(salio)} más de lo que explica la utilidad "
                f"(Δ capital − utilidad = {formato_monto(cambio_menos_utilidad)}). "
                f"Me dijiste {formato_monto(dijo)} de retiros. ¿Qué pasó con la diferencia "
                f"de {formato_monto(diferencia)}?"
            ),
        )
    ]


def _r11(final: date | None, hoy: date) -> list[Hallazgo]:
    if final is None:
        return []
    dias = (hoy - final).days
    if dias > DIAS_PARA_AVISAR:
        return [
            Hallazgo(
                revision="R11",
                resultado="aviso",
                fecha=final,
                mensaje=(
                    f"Tu balance más reciente es al {fecha_corta(final)}: tiene {dias} días. "
                    "Puedo trabajar con él, pero puede no reflejar cómo estás hoy. "
                    "¿Tienes uno más reciente?"
                ),
            )
        ]
    return [
        Hallazgo(
            revision="R11",
            resultado="cuadra",
            fecha=final,
            mensaje=f"Tu balance es reciente: tiene {dias} días.",
        )
    ]


# ---------------------------------------------------------------------------
# Tasa y preguntas
# ---------------------------------------------------------------------------


def _deuda_del_banco(cuentas: tuple[CuentaEnCaja, ...], fecha: date) -> Decimal:
    return sum(
        (
            c.monto
            for c in cuentas
            if c.fecha == fecha and c.caja == "deuda neta" and c.lado == "pasivo"
        ),
        _CERO,
    )


def _sin_contestar_interes(acomodo: Acomodo, respuestas: Respuestas) -> list[CuentaEnCaja]:
    return [
        c
        for c in acomodo.cuentas
        if c.pregunta_interes
        and not c.movida
        and c.caja == "otras cuentas"
        and c.nombre not in respuestas.pagan_interes
    ]


def _promedio(valores: list[Decimal]) -> Decimal | None:
    return sum(valores, _CERO) / len(valores) if valores else None


def _tasas(
    acomodo: Acomodo,
    respuestas: Respuestas,
    periodo: PeriodoDelEstado | None,
    fechas: list[date],
    intereses: Decimal | None,
) -> tuple[Decimal | None, Decimal | None]:
    if periodo is None or periodo.dias not in _DIAS_DE_UN_ANIO or intereses is None or not fechas:
        return None, None
    banco = _promedio([_deuda_del_banco(acomodo.cuentas, f) for f in fechas])
    tasa = intereses / banco * _CIEN if banco else None
    dudosas = _sin_contestar_interes(acomodo, respuestas)
    if not dudosas:
        return tasa, None
    con_documentos = _promedio(
        [
            _deuda_del_banco(acomodo.cuentas, f)
            + sum((c.monto for c in dudosas if c.fecha == f), _CERO)
            for f in fechas
        ]
    )
    return tasa, (intereses / con_documentos * _CIEN if con_documentos else None)


def _pct(valor: Decimal) -> str:
    return f"{valor:.2f}%"


def _preguntas(
    acomodo: Acomodo,
    sin_mover: Acomodo,
    respuestas: Respuestas,
    hasta: date | None,
    fecha_final: date | None,
    cambio_menos_utilidad: Decimal | None,
    tasas: tuple[Decimal | None, Decimal | None],
    umbral_tasa: Decimal,
) -> list[PreguntaPendiente]:
    preguntas: list[PreguntaPendiente] = []
    if respuestas.periodo is None:
        llega = f" llega al {fecha_corta(hasta)}" if hasta is not None else ""
        preguntas.append(
            PreguntaPendiente(
                codigo="C10",
                pregunta=(
                    f"Tu estado de resultados{llega}. ¿Es sólo del mes o es el acumulado "
                    "del año (desde enero)?"
                ),
                para_que="Para saber cuántos días cubre. Un acumulado nunca se multiplica.",
                bloquea=True,
            )
        )
    sin_caja: dict[str, CuentaEnCaja] = {}
    for cuenta in acomodo.cuentas:
        if cuenta.caja is None:
            sin_caja.setdefault(cuenta.nombre, cuenta)
    for cuenta in sin_caja.values():
        preguntas.append(
            PreguntaPendiente(
                codigo="R7",
                cuenta=cuenta.nombre,
                bloquea=True,
                pregunta=(
                    f"No sé en qué caja va «{cuenta.nombre}» ({formato_monto(cuenta.monto)}). "
                    "¿Es de la operación (clientes, inventario, proveedores), un préstamo que "
                    "paga interés, capital de los socios, u otra cuenta?"
                ),
                para_que="Sin caja no puedo cuadrar las cajas ni calcular.",
            )
        )
    if respuestas.ventas_a_credito is None:
        preguntas.append(
            PreguntaPendiente(
                codigo="C1",
                pregunta="¿Qué parte de tus ventas es a crédito (en porcentaje)?",
                para_que="Para calcular en cuántos días te pagan de verdad tus clientes.",
            )
        )
    if respuestas.ventas_completas is None:
        preguntas.append(
            PreguntaPendiente(
                codigo="C2",
                pregunta="¿Las ventas del estado son todas tus ventas o sólo lo facturado?",
                para_que="Para saber si el estado muestra tu negocio completo.",
            )
        )
    if respuestas.retiros_del_dueno is None:
        preguntas.append(
            PreguntaPendiente(
                codigo="C3",
                pregunta=(
                    "¿Cuánto sacaste tú del negocio en el periodo (sueldo, gastos "
                    "personales, retiros)?"
                ),
                para_que="Para ver cuánto te deja el negocio a ti.",
            )
        )
    if respuestas.retiros_de_capital is None:
        detalle = ""
        if cambio_menos_utilidad is not None and cambio_menos_utilidad < 0:
            detalle = (
                f" Tu capital creció {formato_monto(abs(cambio_menos_utilidad))} menos que "
                "la utilidad."
            )
        preguntas.append(
            PreguntaPendiente(
                codigo="C4",
                pregunta=f"¿Hubo retiros de los socios o de capital en el periodo?{detalle}",
                para_que="Para explicar el cambio del capital (quinto renglón de los 4 capítulos).",
            )
        )
    if respuestas.iva_incluido is None:
        preguntas.append(
            PreguntaPendiente(
                codigo="C9",
                pregunta="¿Tus saldos de clientes y proveedores incluyen IVA?",
                para_que="Para comparar clientes y proveedores con ventas y compras en la misma base.",
            )
        )
    tasa, tasa_con = tasas
    dudosas: dict[str, CuentaEnCaja] = {}
    for cuenta in _sin_contestar_interes(acomodo, respuestas):
        dudosas.setdefault(cuenta.nombre, cuenta)
    for cuenta in dudosas.values():
        pregunta = f"¿«{cuenta.nombre}» paga interés?"
        if tasa is not None and tasa > umbral_tasa * _CIEN:
            pregunta = (
                f"Con tu deuda del banco, los intereses dan una tasa de {_pct(tasa)} al año."
            )
            if tasa_con is not None:
                pregunta += f" Si sumo «{cuenta.nombre}», la tasa queda en {_pct(tasa_con)}."
            pregunta += f" ¿«{cuenta.nombre}» paga interés?"
        preguntas.append(
            PreguntaPendiente(
                codigo="C11",
                cuenta=cuenta.nombre,
                pregunta=pregunta,
                para_que="Si paga interés es deuda: pasa a deuda neta.",
            )
        )
    movidas: dict[str, CuentaEnCaja] = {}
    for cuenta in acomodo.cuentas:
        if cuenta.movida:
            movidas.setdefault(cuenta.nombre, cuenta)
    for cuenta in movidas.values():
        assert cuenta.caja is not None and cuenta.caja_por_regla is not None
        cuando = fecha_final or (acomodo.fechas[-1] if acomodo.fechas else None)
        antes = sin_mover.en(cuando) if cuando is not None else None
        despues = acomodo.en(cuando) if cuando is not None else None
        cambio = ""
        if cuando is not None and antes is not None and despues is not None:
            cambio = (
                f" Al {fecha_corta(cuando)}, {cuenta.caja} pasa de "
                f"{formato_monto(antes.de(cuenta.caja))} a {formato_monto(despues.de(cuenta.caja))}"
                f" y {cuenta.caja_por_regla} de {formato_monto(antes.de(cuenta.caja_por_regla))}"
                f" a {formato_monto(despues.de(cuenta.caja_por_regla))}."
            )
        preguntas.append(
            PreguntaPendiente(
                codigo="movida",
                cuenta=cuenta.nombre,
                pregunta=(
                    f"Moviste «{cuenta.nombre}» de {cuenta.caja_por_regla} a {cuenta.caja}."
                    f"{cambio} ¿Lo confirmas?"
                ),
                para_que="Mover una cuenta de caja cambia los resultados.",
            )
        )
    # Primero las que bloquean; el orden entre ellas se respeta.
    return sorted(preguntas, key=lambda p: not p.bloquea)


def revisar_estados(
    balances: list[LecturaEstados] | tuple[LecturaEstados, ...],
    resultados: LecturaEstados | None,
    *,
    respuestas: Respuestas | None = None,
    hoy: date,
    tolerancia: Decimal = TOLERANCIA,
    umbral_tasa: Decimal = UMBRAL_TASA,
) -> RevisionDeEstados:
    """Acomoda, empareja y revisa. No calcula indicadores ni multiplica periodos."""

    respuestas = respuestas or Respuestas()
    balances = list(balances)
    cuentas = [cuenta for lectura in balances for cuenta in lectura.cuentas]
    acomodo = acomodar(
        cuentas, movimientos=respuestas.movimientos, con_interes=respuestas.pagan_interes
    )
    sin_mover = acomodar(cuentas, con_interes=respuestas.pagan_interes)
    fechas = acomodo.fechas

    hasta = _fecha_del_estado(resultados)
    periodo = _periodo(respuestas.periodo, hasta) if respuestas.periodo and hasta else None
    if periodo is not None:
        final = periodo.hasta if periodo.hasta in fechas else None
        inicial = periodo.desde if periodo.desde in fechas else None
    else:
        final = fechas[-1] if fechas else None
        inicial = None

    utilidad = _del_estado(resultados, "utilidad_neta", hasta)
    intereses = _del_estado(resultados, "intereses", hasta)
    cambio_menos_utilidad: Decimal | None = None
    inicio, fin = (acomodo.en(inicial) if inicial else None), (acomodo.en(final) if final else None)
    if inicio is not None and fin is not None and utilidad is not None:
        cambio_menos_utilidad = fin.capital - inicio.capital - utilidad

    hallazgos: list[Hallazgo] = []
    for totales in acomodo.totales:
        hallazgos.append(_r1(totales, tolerancia))
    hallazgos.append(_r2(acomodo, final if final else hasta, utilidad, tolerancia))
    hallazgos += _r3(acomodo, tolerancia)
    hallazgos += _r4(periodo, fechas, inicial, final)
    hallazgos.append(_r5(balances, resultados))
    hallazgos += _r6(acomodo, resultados)
    hallazgos += _r8([*balances, *([resultados] if resultados is not None else [])])
    hallazgos += _r9(cambio_menos_utilidad, respuestas, tolerancia)
    for totales in acomodo.totales:
        hallazgos.append(_r10(totales, tolerancia))
    hallazgos += _r11(final if final else (fechas[-1] if fechas else None), hoy)

    tasas = _tasas(
        acomodo,
        respuestas,
        periodo,
        [f for f in (inicial, final) if f is not None],
        intereses,
    )
    preguntas = _preguntas(
        acomodo,
        sin_mover,
        respuestas,
        hasta,
        final,
        cambio_menos_utilidad,
        tasas,
        umbral_tasa,
    )
    return RevisionDeEstados(
        acomodo=acomodo,
        periodo=periodo,
        balance_inicial=inicial,
        balance_final=final,
        hallazgos=tuple(hallazgos),
        preguntas=tuple(preguntas),
        tasa_deuda_bancaria=tasas[0],
        tasa_con_documentos=tasas[1],
    )


# ---------------------------------------------------------------------------
# «Así acomodé tus cuentas»
# ---------------------------------------------------------------------------


def _celda(texto: str) -> str:
    return texto.replace("|", "/")


def render_asi_acomode(revision: RevisionDeEstados) -> str:
    acomodo = revision.acomodo
    lineas = [
        "Así acomodé tus cuentas",
        "",
        "| Cuenta | Monto | Fecha | Caja | Por qué |",
        "|---|---|---|---|---|",
    ]
    for cuenta in acomodo.cuentas:
        lineas.append(
            f"| {_celda(cuenta.nombre)} | {formato_monto(cuenta.monto)} | "
            f"{fecha_corta(cuenta.fecha) if cuenta.fecha else 'sin fecha'} | "
            f"{cuenta.caja or 'sin caja'} | {_celda(cuenta.porque)} |"
        )
    if acomodo.totales:
        lineas += [
            "",
            "Las 4 cajas (uso: activo suma y pasivo resta; fuente: pasivo y capital suman, activo resta)",
            "",
            "| Caja | " + " | ".join(fecha_corta(t.fecha) for t in acomodo.totales) + " |",
            "|---|" + "---|" * len(acomodo.totales),
        ]
        filas: list[tuple[str, Caja]] = [
            ("Capital de trabajo", "capital de trabajo"),
            ("Deuda neta", "deuda neta"),
            ("Otras cuentas", "otras cuentas"),
            ("Capital", "capital"),
        ]
        for etiqueta, caja in filas:
            lineas.append(
                f"| {etiqueta} | "
                + " | ".join(formato_monto(t.de(caja)) for t in acomodo.totales)
                + " |"
            )
    if revision.periodo is not None:
        p = revision.periodo
        lineas += [
            "",
            f"Periodo del estado: {p.tipo}, del {fecha_corta(p.desde)} al "
            f"{fecha_corta(p.hasta)} ({p.dias} días).",
        ]
    lineas += ["", "Revisiones", ""]
    for hallazgo in revision.hallazgos:
        if hallazgo.revision == "R1" or hallazgo.resultado != "cuadra":
            lineas.append(f"- {hallazgo.revision}: {hallazgo.mensaje}")
    if not revision.puede_calcular:
        lineas += ["", "No calculo nada todavía: primero hay que resolver lo que bloquea."]
    if revision.preguntas:
        lineas += ["", "Preguntas", ""]
        lineas += [
            f"- {p.codigo}{' (bloquea)' if p.bloquea else ''}: {p.pregunta}"
            for p in revision.preguntas
        ]
    return "\n".join(lineas) + "\n"
