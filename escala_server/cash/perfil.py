"""Tu perfil ideal, con tus límites (S86.21).

Según el curso de cash que vimos:

- **F3b.1 (L33)** de cada peso que vendes, cuánto es costo, utilidad bruta,
  gastos de operación y utilidad de operación (y los renglones de abajo).
- **Perfiles (L33, L44, L48, L71)**: un semáforo verde / amarillo / rojo para
  seis indicadores. El curso trae dos versiones y dice que sus límites son de
  ejemplo («60 días, aquí inventado»). Cada dueño fija los suyos.

Reglas de esta página:

- Sin límites del dueño no hay semáforo: ESCALA pregunta antes de pintar.
- Cada límite dice si incluye el borde («más de 50» no; «50 o más» sí).
- El color se decide con el valor sin redondear. Ejemplo: proveedores 19.587…
  días con rojo «menos de 20» es rojo, aunque redondeado a 20 se vería amarillo.
- La versión B del curso se ofrece como ejemplo. Sus gastos se contradicen
  (óptimo menos de 33, regular de 30 a 33): se le muestra al dueño y él decide.
"""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from escala_server.cash.curso import (
    AVISO_FISCAL,
    BaseDeDias,
    Calculado,
    EstadosRevisados,
    NoAplica,
    NoCalculable,
    dias_del_dinero,
)
from escala_server.cash.archivos import carpeta_de, escribir_privado
from escala_server.financial.formatos import fecha_corta, formato_monto
from escala_server.financial.lector import LecturaEstados

CENTAVO = Decimal("0.01")
CIEN = Decimal("100")
CERO = Decimal("0")

Clave = Literal[
    "utilidad_bruta",
    "gastos",
    "utilidad_de_operacion",
    "dias_clientes",
    "dias_inventario",
    "dias_proveedores",
]
Unidad = Literal["%", "días"]
Color = Literal["verde", "amarillo", "rojo"]
Nivel = Literal["óptimo", "regular", "malo"]

INDICADORES: tuple[Clave, ...] = (
    "utilidad_bruta",
    "gastos",
    "utilidad_de_operacion",
    "dias_clientes",
    "dias_inventario",
    "dias_proveedores",
)

# clave → (nombre, unidad, ¿más es mejor?, lámina)
DEFINICIONES: dict[Clave, tuple[str, Unidad, bool, str]] = {
    "utilidad_bruta": ("% de utilidad bruta", "%", True, "L33 y L71"),
    "gastos": ("% de gastos de operación", "%", False, "L33 y L71"),
    "utilidad_de_operacion": ("% de utilidad de operación", "%", True, "L33 y L71"),
    "dias_clientes": ("Días de clientes", "días", False, "L48 y L71"),
    "dias_inventario": ("Días de inventario", "días", False, "L48 y L71"),
    "dias_proveedores": ("Días de proveedores", "días", True, "L48 y L71"),
}

NIVELES: dict[Color, Nivel] = {"verde": "óptimo", "amarillo": "regular", "rojo": "malo"}


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _dos(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def _numero(valor: Decimal) -> str:
    """50 → «50»; 47.5 → «47.5» (sin notación científica)."""
    texto = format(valor.normalize(), "f")
    return texto


# ---------------------------------------------------------------------------
# F3b.1 — de cada peso que vendes
# ---------------------------------------------------------------------------


class ParteDeUnPeso(_Modelo):
    clave: str
    nombre: str
    valor: Decimal  # % sin redondear
    mostrado: Decimal  # 2 decimales
    formula: str
    origen: str
    lamina: str = "L33"


class DeUnPeso(_Modelo):
    no_calculable: str | None = None
    fecha: date | None = None
    partes: tuple[ParteDeUnPeso, ...] = ()
    nota_fiscal: str | None = None


def _renglon(resultados: LecturaEstados, concepto: str, fecha: date) -> Decimal | None:
    """Como la calculadora: los renglones del concepto; si sólo hay total, el total."""
    del_concepto = [
        c for c in resultados.cuentas if c.concepto == concepto and c.fecha == fecha
    ]
    renglones = [c for c in del_concepto if not c.es_total] or del_concepto[:1]
    if not renglones:
        return None
    return sum((c.monto for c in renglones), CERO)


def _dinero(valor: Decimal) -> str:
    return formato_monto(_dos(valor))


def _parte(
    clave: str, nombre: str, monto: Decimal, texto: str, ventas: Decimal
) -> ParteDeUnPeso:
    valor = monto / ventas * CIEN
    return ParteDeUnPeso(
        clave=clave,
        nombre=nombre,
        valor=valor,
        mostrado=_dos(valor),
        formula=f"{nombre.lower()} ÷ ventas × 100",
        origen=f"sale de: {texto} ÷ ventas {_dinero(ventas)} × 100",
    )


def porcentajes_de_un_peso(estados: EstadosRevisados) -> DeUnPeso:
    """F3b.1: cada renglón del estado de resultados como % de las ventas del año actual."""
    revision = estados.revision
    fecha = revision.balance_final
    if not revision.puede_calcular or fecha is None:
        return DeUnPeso(no_calculable="faltan los estados revisados del año actual")
    resultados = estados.resultados
    ventas = _renglon(resultados, "ventas", fecha)
    if ventas is None:
        return DeUnPeso(
            no_calculable=f"falta el renglón de ventas del estado de resultados al {fecha_corta(fecha)}",
            fecha=fecha,
        )
    if ventas <= 0:
        return DeUnPeso(
            no_calculable=f"las ventas al {fecha_corta(fecha)} son 0 o menos: no se puede dividir entre ellas",
            fecha=fecha,
        )
    costo = _renglon(resultados, "costo_ventas", fecha) or CERO
    gastos = _renglon(resultados, "gastos_operacion", fecha) or CERO
    ub = ventas - costo
    uo = ub - gastos
    partes = [
        _parte(
            "costo",
            "Costo de ventas",
            costo,
            f"costo de ventas {_dinero(costo)}",
            ventas,
        ),
        _parte(
            "utilidad_bruta",
            "Utilidad bruta",
            ub,
            f"utilidad bruta {_dinero(ub)} (ventas {_dinero(ventas)} − costo de ventas {_dinero(costo)})",
            ventas,
        ),
        _parte(
            "gastos",
            "Gastos de operación",
            gastos,
            f"gastos de operación {_dinero(gastos)}",
            ventas,
        ),
        _parte(
            "utilidad_de_operacion",
            "Utilidad de operación",
            uo,
            f"utilidad de operación {_dinero(uo)} (utilidad bruta {_dinero(ub)} − gastos {_dinero(gastos)})",
            ventas,
        ),
    ]
    abajo = (
        ("intereses", "gastos_financieros", "Gastos financieros"),
        (
            "utilidad_antes_impuestos",
            "utilidad_antes_impuestos",
            "Utilidad antes de impuestos",
        ),
        ("isr", "isr", "ISR"),
        ("utilidad_neta", "utilidad_neta", "Utilidad neta"),
    )
    hay_isr = False
    for concepto, clave, nombre in abajo:
        monto = _renglon(resultados, concepto, fecha)
        if monto is None:
            continue  # sólo lo que trae tu estado; no se inventa un renglón
        hay_isr = hay_isr or concepto == "isr"
        texto = f"{nombre if nombre == 'ISR' else nombre.lower()} {_dinero(monto)}"
        partes.append(_parte(clave, nombre, monto, texto, ventas))
    return DeUnPeso(
        fecha=fecha,
        partes=tuple(partes),
        nota_fiscal=AVISO_FISCAL if hay_isr else None,
    )


# ---------------------------------------------------------------------------
# Los seis valores del perfil
# ---------------------------------------------------------------------------


class ValorDelPerfil(_Modelo):
    clave: Clave
    nombre: str
    unidad: Unidad
    fecha: date
    valor: Decimal  # sin redondear: decide el color
    mostrado: Decimal  # 2 decimales: lo que se lee
    origen: str
    lamina: str


class SinValor(_Modelo):
    clave: Clave
    nombre: str
    unidad: Unidad
    razon: str


ValorOSin = ValorDelPerfil | SinValor


def valores_del_perfil(
    estados: EstadosRevisados, base: BaseDeDias
) -> tuple[ValorOSin, ...]:
    """Los seis indicadores del año actual, sin redondear y con su «sale de:»."""
    peso = porcentajes_de_un_peso(estados)
    por_clave: dict[Clave, ValorOSin] = {}
    porcentajes: tuple[Clave, ...] = (
        "utilidad_bruta",
        "gastos",
        "utilidad_de_operacion",
    )
    for clave in porcentajes:
        nombre, unidad, _, lamina = DEFINICIONES[clave]
        parte = next((p for p in peso.partes if p.clave == clave), None)
        if parte is None or peso.fecha is None:
            por_clave[clave] = SinValor(
                clave=clave,
                nombre=nombre,
                unidad=unidad,
                razon=f"no calculable: {peso.no_calculable}",
            )
            continue
        por_clave[clave] = ValorDelPerfil(
            clave=clave,
            nombre=nombre,
            unidad=unidad,
            fecha=peso.fecha,
            valor=parte.valor,
            mostrado=parte.mostrado,
            origen=parte.origen,
            lamina=lamina,
        )
    dias = dias_del_dinero(estados, base)
    final = estados.revision.balance_final
    anio = None
    if dias.no_calculable is None and final is not None:
        anio = next((a for a in dias.anios if a.fecha == final), None)
    de_dias: tuple[tuple[Clave, str], ...] = (
        ("dias_clientes", "clientes"),
        ("dias_inventario", "inventario"),
        ("dias_proveedores", "proveedores"),
    )
    for clave, cuenta in de_dias:
        nombre, unidad, _, lamina = DEFINICIONES[clave]
        if anio is None:
            razon = dias.no_calculable or "falta el balance al final del periodo"
            por_clave[clave] = SinValor(
                clave=clave,
                nombre=nombre,
                unidad=unidad,
                razon=f"no calculable: {razon}",
            )
            continue
        indicador = getattr(anio, cuenta)
        crudo = anio.sin_redondear.get(cuenta)
        if isinstance(indicador, Calculado) and crudo is not None:
            origen = indicador.origen
            if dias.iva != "como vienen" or dias.base_de_ventas != "ventas totales":
                origen = f"{origen} ({dias.rotulo})"
            por_clave[clave] = ValorDelPerfil(
                clave=clave,
                nombre=nombre,
                unidad=unidad,
                fecha=anio.fecha,
                valor=crudo,
                mostrado=indicador.valor,
                origen=origen,
                lamina=lamina,
            )
        elif isinstance(indicador, NoCalculable):
            por_clave[clave] = SinValor(
                clave=clave,
                nombre=nombre,
                unidad=unidad,
                razon=f"no calculable: {indicador.no_calculable}",
            )
        else:
            assert isinstance(indicador, NoAplica | Calculado)
            razon = (
                indicador.no_aplica if isinstance(indicador, NoAplica) else "sin valor"
            )
            por_clave[clave] = SinValor(
                clave=clave, nombre=nombre, unidad=unidad, razon=f"no aplica: {razon}"
            )
    return tuple(por_clave[clave] for clave in INDICADORES)


# ---------------------------------------------------------------------------
# Límites, borde y color
# ---------------------------------------------------------------------------


class Borde(_Modelo):
    valor: Decimal
    incluye: bool  # True: el valor exacto del borde ya es de ese color


class Limites(_Modelo):
    """Los límites de un indicador. Entre el borde verde y el rojo es amarillo."""

    ideal: Decimal
    verde: Borde
    rojo: Borde
    fuente: Literal["tuyo", "ejemplo del curso (versión B)"] = "tuyo"


def _mas_es_mejor(clave: Clave) -> bool:
    return DEFINICIONES[clave][2]


def _es_verde(clave: Clave, valor: Decimal, borde: Borde) -> bool:
    if valor == borde.valor:
        return borde.incluye
    return valor > borde.valor if _mas_es_mejor(clave) else valor < borde.valor


def _es_rojo(clave: Clave, valor: Decimal, borde: Borde) -> bool:
    if valor == borde.valor:
        return borde.incluye
    return valor < borde.valor if _mas_es_mejor(clave) else valor > borde.valor


def color(clave: Clave, valor: Decimal, limites: Limites) -> Color:
    """El color de un valor. Pásale el valor sin redondear."""
    if _es_verde(clave, valor, limites.verde):
        return "verde"
    if _es_rojo(clave, valor, limites.rojo):
        return "rojo"
    return "amarillo"


def _con_unidad(clave: Clave, valor: Decimal) -> str:
    unidad = DEFINICIONES[clave][1]
    return f"{_numero(valor)}%" if unidad == "%" else f"{_numero(valor)} días"


def _texto_borde(clave: Clave, borde: Borde, de_verde: bool) -> str:
    arriba = _mas_es_mejor(clave) == de_verde
    numero = _con_unidad(clave, borde.valor)
    if borde.incluye:
        return f"{numero} o {'más' if arriba else 'menos'}"
    return f"{'más' if arriba else 'menos'} de {numero}"


def texto_de_limites(clave: Clave, limites: Limites) -> str:
    verde = _texto_borde(clave, limites.verde, True)
    rojo = _texto_borde(clave, limites.rojo, False)
    bajo, alto = sorted((limites.verde.valor, limites.rojo.valor))
    if bajo == alto:
        amarillo = f"exactamente {_con_unidad(clave, bajo)}"
    else:
        amarillo = f"de {_con_unidad(clave, bajo)} a {_con_unidad(clave, alto)}"
    return f"verde: {verde} · amarillo: {amarillo} · rojo: {rojo}"


def revisar_limites(clave: Clave, limites: Limites) -> str | None:
    """La razón si los límites no sirven (un valor sería verde y rojo a la vez)."""
    verde, rojo = limites.verde, limites.rojo
    mas = _mas_es_mejor(clave)
    pisan = (rojo.valor > verde.valor) if mas else (rojo.valor < verde.valor)
    if verde.valor == rojo.valor and verde.incluye and rojo.incluye:
        ejemplo = verde.valor
        pisan = True
    else:
        ejemplo = (verde.valor + rojo.valor) / 2
    if not pisan:
        return None
    nombre = DEFINICIONES[clave][0]
    return (
        f"tus límites de {nombre.lower()} se pisan: {texto_de_limites(clave, limites)}. "
        f"Un {_con_unidad(clave, ejemplo)} sería verde y rojo a la vez. ¿Cuál es el que vale?"
    )


# Según el curso de cash que vimos, versión B «Calidad del flujo» (L71). Ejemplo, no regla.
# Regular «47–50» incluye los dos bordes: verde «más de 50», rojo «menos de 47».
def _b(ideal: int, verde: int, rojo: int) -> Limites:
    return Limites(
        ideal=Decimal(ideal),
        verde=Borde(valor=Decimal(verde), incluye=False),
        rojo=Borde(valor=Decimal(rojo), incluye=False),
        fuente="ejemplo del curso (versión B)",
    )


VERSION_B: dict[Clave, Limites | None] = {
    "utilidad_bruta": _b(50, 50, 47),
    # Gastos se contradice en la lámina: lo resuelve el dueño (CONTRADICCION_GASTOS_B).
    "gastos": None,
    "utilidad_de_operacion": _b(20, 20, 18),
    "dias_clientes": _b(40, 40, 45),
    "dias_inventario": _b(30, 30, 35),
    "dias_proveedores": _b(25, 25, 20),
}

CONTRADICCION_GASTOS_B = (
    "En el ejemplo del curso los gastos de operación se contradicen: dice ideal 33%, "
    "óptimo menos de 33% y regular de 30% a 33% (y malo más de 30%, que el curso corrige "
    "a más de 33%). Un 31% sería óptimo y regular a la vez. No lo decido yo: dime tus límites."
)


# ---------------------------------------------------------------------------
# Lo que contesta el dueño: «ideal 50, verde más de 50, rojo menos de 47»
# ---------------------------------------------------------------------------

_NUM = r"(-?\d+(?:\.\d+)?)\s*(?:%|d[ií]as)?"
_OPERADORES: tuple[tuple[str, bool, bool], ...] = (
    # (expresión, ¿hacia arriba?, ¿incluye el borde?)
    (r"(?:>=|≥)\s*" + _NUM, True, True),
    (r"(?:<=|≤)\s*" + _NUM, False, True),
    (r">\s*" + _NUM, True, False),
    (r"<\s*" + _NUM, False, False),
    (r"m[aá]s\s+de\s+" + _NUM, True, False),
    (r"menos\s+de\s+" + _NUM, False, False),
    (_NUM + r"\s+o\s+m[aá]s", True, True),
    (_NUM + r"\s+o\s+menos", False, True),
)
EJEMPLO_DE_RESPUESTA = "ideal 50, verde más de 50, rojo menos de 47"


def _borde(texto: str) -> tuple[Decimal, bool, bool] | None:
    for patron, arriba, incluye in _OPERADORES:
        hallado = re.match(r"\s*" + patron, texto)
        if hallado:
            return Decimal(hallado.group(1)), arriba, incluye
    return None


def entender_limites(clave: Clave, texto: str) -> Limites | str:
    """Los límites que dijo el dueño, o la razón por la que no se entienden."""
    nombre = DEFINICIONES[clave][0].lower()
    limpio = texto.strip().lower()
    ideal = re.search(r"ideal\s*:?\s*" + _NUM, limpio)
    if ideal is None:
        return f"falta tu ideal de {nombre}. Ejemplo de respuesta: «{EJEMPLO_DE_RESPUESTA}»"
    bordes: dict[str, tuple[Decimal, bool, bool]] = {}
    for color_ in ("verde", "rojo"):
        hallado = re.search(
            color_ + r"\s*:?\s*(.*?)(?=(?:[,;]\s*)?(?:verde|rojo|ideal)\b|$)", limpio
        )
        leido = _borde(hallado.group(1)) if hallado else None
        if leido is None:
            return (
                f"no entendí desde dónde es {color_} tu {nombre}. "
                f"Ejemplo de respuesta: «{EJEMPLO_DE_RESPUESTA}»"
            )
        bordes[color_] = leido
    mas = _mas_es_mejor(clave)
    if bordes["verde"][1] != mas or bordes["rojo"][1] == mas:
        sentido = "más es mejor" if mas else "menos es mejor"
        verde = "«más de»" if mas else "«menos de»"
        rojo = "«menos de»" if mas else "«más de»"
        return f"en {nombre}, {sentido}: el verde va con {verde} y el rojo con {rojo}. ¿Me lo dices otra vez?"
    return Limites(
        ideal=Decimal(ideal.group(1)),
        verde=Borde(valor=bordes["verde"][0], incluye=bordes["verde"][2]),
        rojo=Borde(valor=bordes["rojo"][0], incluye=bordes["rojo"][2]),
    )


# ---------------------------------------------------------------------------
# El semáforo de una tarjeta
# ---------------------------------------------------------------------------


class Tarjeta(_Modelo):
    clave: Clave
    nombre: str
    unidad: Unidad
    valor: ValorDelPerfil | None = None
    razon: str | None = None
    limites: Limites
    texto_limites: str
    color: Color | None = None
    nivel: Nivel | None = None
    por_que: str | None = None
    meta: Decimal
    origen_meta: str
    distancia: Decimal | None = None
    texto_distancia: str = ""
    origen_distancia: str = ""


def _sin_redondear(valor: Decimal) -> str:
    return format(
        valor.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP).normalize(), "f"
    )


def semaforo(valor: ValorOSin, limites: Limites) -> Tarjeta:
    clave = valor.clave
    nombre, unidad, mas, _ = DEFINICIONES[clave]
    origen_meta = (
        "sale de: tu límite"
        if limites.fuente == "tuyo"
        else "sale de: el ejemplo del curso (versión B) que tomaste"
    )
    base = Tarjeta(
        clave=clave,
        nombre=nombre,
        unidad=unidad,
        limites=limites,
        texto_limites=texto_de_limites(clave, limites),
        meta=limites.ideal,
        origen_meta=f"{origen_meta}: ideal {_con_unidad(clave, limites.ideal)}",
    )
    if isinstance(valor, SinValor):
        return base.model_copy(update={"razon": valor.razon})
    pinta = color(clave, valor.valor, limites)
    diferencia = valor.valor - limites.ideal
    distancia = _dos(diferencia)
    medida = "puntos" if unidad == "%" else "días"
    if distancia == 0:
        texto = f"Estás en tu ideal de {_con_unidad(clave, limites.ideal)}."
    else:
        lado = "arriba" if distancia > 0 else "debajo"
        bien = (distancia > 0) == mas
        cuanto = f"{formato_monto(abs(distancia))} {medida}"
        texto = (
            f"{cuanto} {lado} de tu ideal de {_con_unidad(clave, limites.ideal)}. "
            + ("Mejor que tu ideal." if bien else f"Te falta mejorar {cuanto}.")
        )
    return base.model_copy(
        update={
            "valor": valor,
            "color": pinta,
            "nivel": NIVELES[pinta],
            "por_que": (
                f"{pinta} con el valor sin redondear ({_sin_redondear(valor.valor)}): "
                f"{texto_de_limites(clave, limites)}"
            ),
            "distancia": distancia,
            "texto_distancia": texto,
            "origen_distancia": (
                f"sale de: tu valor {formato_monto(valor.mostrado)} − ideal {_numero(limites.ideal)}"
            ),
        }
    )


# ---------------------------------------------------------------------------
# La plática: ESCALA pregunta antes de pintar; guarda sólo con «sí»
# ---------------------------------------------------------------------------

MAXIMO_DE_PREGUNTAS = 3
ARCHIVO = "perfil-ideal.json"

# Lo que puede contestar el dueño: clave corta o completa → indicador.
ALIAS: dict[str, Clave] = {
    "ub": "utilidad_bruta",
    "utilidad_bruta": "utilidad_bruta",
    "gastos": "gastos",
    "uo": "utilidad_de_operacion",
    "utilidad_de_operacion": "utilidad_de_operacion",
    "clientes": "dias_clientes",
    "dias_clientes": "dias_clientes",
    "inventario": "dias_inventario",
    "dias_inventario": "dias_inventario",
    "proveedores": "dias_proveedores",
    "dias_proveedores": "dias_proveedores",
}


class PlaticaDelPerfil(_Modelo):
    """Lo que el dueño ha contestado. Nunca cifras calculadas."""

    empresa: str
    respuestas: dict[str, str] = Field(default_factory=dict)


class PerfilGuardado(_Modelo):
    empresa: str
    guardado: date
    limites: dict[Clave, Limites]


class PreguntaDelPerfil(_Modelo):
    clave: str
    pregunta: str


class PasoDelPerfil(_Modelo):
    mensaje: str
    preguntas: tuple[PreguntaDelPerfil, ...] = ()
    limites: dict[Clave, Limites] = Field(default_factory=dict)
    tarjetas: tuple[Tarjeta, ...] = ()  # vacío: no se pinta
    de_un_peso: DeUnPeso | None = None
    pintar: bool = False
    pide_guardar: bool = False
    avisos: tuple[str, ...] = ()


def es_si(respuesta: str | None) -> bool:
    return respuesta is not None and respuesta.strip().lower() in ("sí", "si")


def _ejemplo(clave: Clave) -> str:
    limites = VERSION_B[clave]
    if limites is None:
        return CONTRADICCION_GASTOS_B
    return (
        f"Según el curso de cash que vimos, un ejemplo es: ideal {_con_unidad(clave, limites.ideal)}; "
        f"{texto_de_limites(clave, limites)}."
    )


def _pregunta_de(clave: Clave, error: str | None, con_curso: bool) -> PreguntaDelPerfil:
    nombre = DEFINICIONES[clave][0]
    sentido = "más es mejor" if _mas_es_mejor(clave) else "menos es mejor"
    del_curso = VERSION_B[clave]
    borde = _numero(del_curso.verde.valor) if del_curso is not None else "30"
    partes: list[str] = []
    if error is not None:
        partes.append(
            error[0].upper() + error[1:] + ("" if error.endswith((".", "?")) else ".")
        )
    partes.append(
        f"{nombre} ({sentido}): ¿cuál es tu ideal, desde dónde es verde y desde dónde es rojo? "
        f"Dime si el borde cuenta: «más de {borde}» no incluye el {borde}; «{borde} o más» sí."
    )
    if clave == "gastos" and con_curso:
        partes.append(CONTRADICCION_GASTOS_B)
    elif error is None:
        partes.append(_ejemplo(clave))
    return PreguntaDelPerfil(clave=clave, pregunta=" ".join(partes))


def _pregunta_del_curso() -> PreguntaDelPerfil:
    renglones = "".join(
        f"\n   - {DEFINICIONES[clave][0]}: {_ejemplo(clave).split(', un ejemplo es: ')[-1].rstrip('.')}"
        for clave in INDICADORES
        if VERSION_B[clave] is not None
    )
    return PreguntaDelPerfil(
        clave="curso",
        pregunta=(
            f"Según el curso de cash que vimos, un ejemplo es (versión B):{renglones}\n"
            "Son límites de ejemplo: el curso mismo dice que cada empresa pone los suyos. "
            "¿Los tomo como punto de partida y luego cambias los que quieras? (sí / no). "
            "Los gastos de ese ejemplo se contradicen; te los pregunto aparte."
        ),
    )


def _linea_de_tarjeta(tarjeta: Tarjeta) -> str:
    if tarjeta.valor is None or tarjeta.color is None:
        return f"- {tarjeta.nombre}: sin color, {tarjeta.razon}."
    valor = tarjeta.valor
    unidad = "%" if valor.unidad == "%" else " días"
    return (
        f"- {tarjeta.nombre}: {formato_monto(valor.mostrado)}{unidad} → {tarjeta.color} "
        f"({tarjeta.nivel}). {tarjeta.texto_distancia}"
    )


def atender(
    platica: PlaticaDelPerfil,
    valores: tuple[ValorOSin, ...],
    de_un_peso: DeUnPeso | None,
    *,
    guardado: PerfilGuardado | None,
) -> PasoDelPerfil:
    """Arma los límites (guardados < ejemplo del curso < lo que contestó el dueño) y decide.

    Si falta un solo límite, pregunta (máximo 3) y no pinta.
    """
    limites: dict[Clave, Limites] = (
        dict(guardado.limites) if guardado is not None else {}
    )
    respuestas = platica.respuestas
    con_curso = es_si(respuestas.get("curso"))
    if con_curso:
        for clave in INDICADORES:
            del_curso = VERSION_B[clave]
            if del_curso is not None:
                limites[clave] = del_curso
    errores: dict[Clave, str] = {}
    avisos: list[str] = []
    for llave, texto in respuestas.items():
        if llave == "curso":
            continue
        clave = ALIAS.get(llave.strip().lower())
        if clave is None:
            avisos.append(f"No conozco el indicador «{llave}»; no lo usé.")
            continue
        entendido = entender_limites(clave, texto)
        razon = (
            entendido
            if isinstance(entendido, str)
            else revisar_limites(clave, entendido)
        )
        if razon is not None:
            errores[clave] = razon
            limites.pop(clave, None)
        else:
            assert isinstance(entendido, Limites)
            limites[clave] = entendido
    ordenados: dict[Clave, Limites] = {
        c: limites[c] for c in INDICADORES if c in limites
    }
    faltan: list[Clave] = [c for c in INDICADORES if c not in ordenados]
    if faltan:
        preguntas: list[PreguntaDelPerfil] = []
        if guardado is None and "curso" not in respuestas and not ordenados:
            preguntas.append(_pregunta_del_curso())
        # Primero lo que el dueño contestó y no se entendió.
        faltan.sort(key=lambda clave: clave not in errores)
        for clave in faltan:
            preguntas.append(_pregunta_de(clave, errores.get(clave), con_curso))
        preguntas = preguntas[:MAXIMO_DE_PREGUNTAS]
        mensaje = [
            "Antes de pintar tu semáforo necesito tus límites: tu ideal, desde dónde es verde "
            "y desde dónde es rojo. No pinto colores con límites que no son tuyos.",
            f"Me {'falta' if len(faltan) == 1 else 'faltan'} {len(faltan)} de {len(INDICADORES)}.",
        ]
        if con_curso:
            mensaje.append(
                "Tomé el ejemplo del curso para "
                + ", ".join(DEFINICIONES[c][0].lower() for c in ordenados)
                + "."
            )
        mensaje += [f"{i}. {p.pregunta}" for i, p in enumerate(preguntas, start=1)]
        mensaje += avisos
        if ordenados:
            mensaje.append(
                "Si quieres guardar lo que llevamos, responde «sí». Sin tu «sí» no guardo nada."
            )
        return PasoDelPerfil(
            mensaje="\n\n".join(mensaje),
            preguntas=tuple(preguntas),
            limites=ordenados,
            de_un_peso=de_un_peso,
            pide_guardar=bool(ordenados),
            avisos=tuple(avisos),
        )
    tarjetas = tuple(semaforo(valor, ordenados[valor.clave]) for valor in valores)
    pide_guardar = guardado is None or guardado.limites != ordenados
    mensaje = ["Tu semáforo, con tus límites (el color usa el valor sin redondear):"]
    mensaje += [_linea_de_tarjeta(t) for t in tarjetas]
    mensaje += avisos
    if pide_guardar:
        mensaje.append(
            "¿Guardo estos límites para la próxima vez? Si quieres, responde «sí». "
            "Sin tu «sí» no guardo nada."
        )
    return PasoDelPerfil(
        mensaje="\n\n".join(mensaje),
        limites=ordenados,
        tarjetas=tarjetas,
        de_un_peso=de_un_peso,
        pintar=True,
        pide_guardar=pide_guardar,
        avisos=tuple(avisos),
    )


def ruta_del_perfil(empresa: str, *, carpeta: Path) -> Path:
    return carpeta / carpeta_de(empresa) / ARCHIVO


def leer_guardado(empresa: str, *, carpeta: Path) -> PerfilGuardado | str | None:
    """El perfil que el dueño guardó con «sí»; la razón si no se puede leer; None si no hay."""
    ruta = ruta_del_perfil(empresa, carpeta=carpeta)
    if ruta.is_symlink():
        return f"{ruta} es un enlace simbólico; no leo a través de un enlace"
    if not ruta.exists():
        return None
    try:
        return PerfilGuardado.model_validate_json(ruta.read_text(encoding="utf-8"))
    except (OSError, ValidationError):
        return f"no pude leer tus límites guardados en {ruta}"


def guardar_perfil(
    paso: PasoDelPerfil, empresa: str, *, carpeta: Path, hoy: date
) -> Path | None:
    """Escribe ``carpeta/<empresa>/perfil-ideal.json``. Llamar sólo después de un «sí».

    Sin límites no escribe nada. Guardar otra vez reemplaza el perfil: es la
    decisión vigente del dueño, dicha con «sí».
    """
    if not paso.limites:
        return None
    ruta = ruta_del_perfil(empresa, carpeta=carpeta)
    perfil = PerfilGuardado(empresa=empresa, guardado=hoy, limites=paso.limites)
    escribir_privado(ruta, perfil.model_dump_json(indent=2))
    return ruta
