"""Panel «Las tres medidas de tu flujo» y los 4 capítulos (S86.20).

Según el curso de cash que vimos (Parte III, L25 y L58–L64):

- **flujo neto** = −(deuda neta al final − deuda neta al inicio): la medida del
  director general;
- **flujo de operación** = utilidad de operación − cambio en capital de trabajo:
  el indicador del equipo;
- **flujo marginal** = utilidad bruta ÷ ventas − capital de trabajo ÷ ventas:
  qué pasa con el efectivo cuando creces.

Las tres salen de la calculadora (``curso.py``). Este módulo no las recalcula.

Los 4 capítulos (L59) cuentan la historia del flujo neto. La tabla de la lámina
no suma: le falta una 5ª fila, lo que salió del capital sin ser utilidad
(Δ capital − utilidad neta). Con ella:

    utilidad neta − Δ capital de trabajo − Δ otras cuentas + (Δ capital − utilidad neta) = flujo neto

Los capítulos se calculan **por renglones** del balance; el flujo neto, con los
totales de la calculadora. Si no igualan al centavo, la página lo avisa. Antes,
el panel de contabilidad (S86.18) revisa que cada caja cuadre por renglones; si
no cuadra, este panel tampoco sale y ESCALA pregunta.

La 5ª fila se compara con los retiros que dijo el dueño (C3 + C4), como la
revisión R9 de S86.15 y con la misma tolerancia.

Flujo neto ajustado (L70) = flujo neto + flujo de las 7 palancas del poder del uno.

Entrada: ``python -m escala_server.cash.flujo <estados-revisados.json> <salida.html>``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import html
import json
from pathlib import Path
import sys
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, ValidationError

from escala_server.cash import contabilidad
from escala_server.cash.contabilidad import PreguntaDelPanel
from escala_server.cash.curso import (
    Calculado,
    EstadosRevisados,
    Indicador,
    NoAplica,
    NoCalculable,
    ResultadoDelCurso,
    calcular_curso,
    utilidad_ajustada,
)
from escala_server.financial.cajas import Caja, CuentaEnCaja, con_signo
from escala_server.financial.formatos import fecha_corta, formato_monto
from escala_server.financial.revisiones import TOLERANCIA, Respuestas

CERO = Decimal("0")
LAMINA_CAPITULOS = "L59"
LAMINA_ENGANA = "L25"
LAMINA_AJUSTADO = "L70"

CLAVES_DE_MEDIDAS: tuple[tuple[str, str], ...] = (
    (
        "flujo_neto",
        "La medida del director general: cuánto efectivo dejó o pidió la empresa.",
    ),
    (
        "flujo_de_operacion",
        "El indicador del equipo: cuánto efectivo deja la operación.",
    ),
    (
        "marginal",
        "Qué pasa con tu efectivo cuando creces: de cada peso más de venta, cuánto queda.",
    ),
)


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Medida(_Modelo):
    indicador: Indicador
    para_quien: str


class CambioDeRenglon(_Modelo):
    """Un renglón del balance en dos fechas, con el signo que lleva en su caja.

    ``cambio`` = al final − al inicio; ``efecto`` = −cambio, lo que le hizo al efectivo.
    """

    nombre: str
    al_inicio: Decimal
    al_final: Decimal
    cambio: Decimal
    efecto: Decimal
    origen: str


class Capitulo(_Modelo):
    clave: Literal[
        "rentabilidad", "capital_de_trabajo", "otras_cuentas", "salidas_de_capital"
    ]
    nombre: str
    valor: Decimal
    formula: str
    origen: str
    lamina: str
    desglose: tuple[CambioDeRenglon, ...] = ()


class PreguntaDeRetiros(_Modelo):
    codigo: Literal["C3", "C4"]
    pregunta: str
    para_que: str


class ComparacionDeRetiros(_Modelo):
    """La 5ª fila contra lo que dijo el dueño (C3 + C4)."""

    quinta_fila: Decimal
    salio: Decimal
    dijo: Decimal | None
    sin_explicar: Decimal | None
    estado: Literal["cuadra", "sin explicar", "sin respuesta"]
    mensaje: str
    preguntas: tuple[PreguntaDeRetiros, ...] = ()


class PanelDelFlujo(_Modelo):
    no_calculable: str | None = None
    preguntas: tuple[PreguntaDelPanel, ...] = ()
    medidas: tuple[Medida, ...] = ()
    engana: Calculado | None = None
    flujo_neto: Calculado | None = None
    capitulos: tuple[Capitulo, ...] = ()
    capitulos_no_calculable: str | None = None
    suma_de_capitulos: Decimal | None = None
    cuadre: Literal["cuadra", "aviso"] | None = None
    aviso: str | None = None
    retiros: ComparacionDeRetiros | None = None
    flujo_ajustado: Indicador | None = None
    frase: str = ""

    def medida(self, clave: str) -> Indicador:
        for medida in self.medidas:
            if medida.indicador.clave == clave:
                return medida.indicador
        raise KeyError(clave)

    def capitulo(self, clave: str) -> Capitulo:
        for capitulo in self.capitulos:
            if capitulo.clave == clave:
                return capitulo
        raise KeyError(clave)


# ---------------------------------------------------------------------------
# Cambios por renglón
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Saldo:
    renglon: int | str
    lado: str
    monto: Decimal  # como viene en el balance
    con_signo: Decimal  # con el signo de su caja


def _saldos(cuentas: Sequence[CuentaEnCaja], caja: Caja) -> dict[str, _Saldo]:
    saldos: dict[str, _Saldo] = {}
    for c in cuentas:
        if c.caja != caja or c.lado is None:
            continue
        previo = saldos.get(c.nombre)
        signo = con_signo(c.lado, caja, c.monto)
        if previo is None:
            saldos[c.nombre] = _Saldo(c.renglon, c.lado, c.monto, signo)
        else:
            saldos[c.nombre] = _Saldo(
                previo.renglon,
                previo.lado,
                previo.monto + c.monto,
                previo.con_signo + signo,
            )
    return saldos


def _lectura(lado: str, cambio: Decimal) -> str:
    """Qué le pasó al efectivo, en palabras del dueño."""
    monto = formato_monto(abs(cambio))
    if cambio == 0:
        return "no cambió"
    if lado == "activo":
        if cambio > 0:
            return f"pusiste {monto} ahí (salió efectivo)"
        return f"liberaste {monto} (entró efectivo)"
    if cambio > 0:
        return f"pagaste {monto} (salió efectivo)"
    return f"te financiaron {monto} más (entró efectivo)"


def _cambios(
    inicial: Sequence[CuentaEnCaja],
    final: Sequence[CuentaEnCaja],
    caja: Caja,
    ini: date,
    fin: date,
) -> tuple[CambioDeRenglon, ...]:
    antes, despues = _saldos(inicial, caja), _saldos(final, caja)
    nombres = list(despues) + [n for n in antes if n not in despues]
    cambios: list[CambioDeRenglon] = []
    for nombre in nombres:
        a, d = antes.get(nombre), despues.get(nombre)
        al_inicio = a.con_signo if a else CERO
        al_final = d.con_signo if d else CERO
        cambio = al_final - al_inicio
        ref = d or a
        assert ref is not None
        crudo_ini = formato_monto(a.monto) if a else "no estaba (0.00)"
        crudo_fin = formato_monto(d.monto) if d else "ya no está (0.00)"
        cambios.append(
            CambioDeRenglon(
                nombre=nombre,
                al_inicio=al_inicio,
                al_final=al_final,
                cambio=cambio,
                efecto=-cambio,
                origen=(
                    f"sale de: tu balance, renglón {ref.renglon} ({ref.lado}): {nombre} "
                    f"{crudo_ini} al {fecha_corta(ini)} → {crudo_fin} al {fecha_corta(fin)}: "
                    f"{_lectura(ref.lado, cambio)}"
                ),
            )
        )
    return tuple(cambios)


def _texto_suma(partes: Sequence[tuple[str, Decimal]]) -> str:
    textos = [
        f"{'−' if monto < 0 else '+'} {nombre} {formato_monto(abs(monto))}"
        for nombre, monto in partes
    ]
    texto = " ".join(textos) or "no hay cuentas en esta caja (0.00)"
    return texto[2:] if texto.startswith("+ ") else texto


def _suma(cambios: Sequence[CambioDeRenglon]) -> Decimal:
    return sum((c.cambio for c in cambios), CERO)


# ---------------------------------------------------------------------------
# Piezas del panel
# ---------------------------------------------------------------------------


def _razon(indicador: Indicador) -> str:
    if isinstance(indicador, NoCalculable):
        return indicador.no_calculable
    if isinstance(indicador, NoAplica):
        return indicador.no_aplica
    return ""


def _medidas(resultado: ResultadoDelCurso, fin: date) -> tuple[Medida, ...]:
    return tuple(
        Medida(indicador=resultado.indicador(clave, fin), para_quien=para_quien)
        for clave, para_quien in CLAVES_DE_MEDIDAS
    )


def _engana(
    inicial: Sequence[CuentaEnCaja], final: Sequence[CuentaEnCaja], ini: date, fin: date
) -> Calculado | None:
    def bancos(cuentas: Sequence[CuentaEnCaja]) -> Decimal | None:
        de_bancos = [c.monto for c in cuentas if c.regla == "bancos"]
        return sum(de_bancos, CERO) if de_bancos else None

    b_ini, b_fin = bancos(inicial), bancos(final)
    if b_ini is None or b_fin is None:
        return None
    return Calculado(
        clave="cambio_en_bancos",
        nombre="Bancos al final − bancos al inicio",
        fecha=fin,
        valor=b_fin - b_ini,
        unidad="pesos",
        formula="caja y bancos al final − caja y bancos al inicio (no es el flujo: engaña)",
        origen=(
            f"sale de: caja y bancos al {fecha_corta(fin)} {formato_monto(b_fin)} − "
            f"caja y bancos al {fecha_corta(ini)} {formato_monto(b_ini)}"
        ),
        lamina=LAMINA_ENGANA,
    )


def _flujo_ajustado(flujo_neto: Calculado, resultado: ResultadoDelCurso) -> Indicador:
    nombre = "Flujo neto ajustado del poder del uno"
    formula = "flujo neto + flujo de las 7 palancas del poder del uno"
    palancas = resultado.poder_del_uno_flujo
    if not isinstance(palancas, Calculado):
        razon = (
            _razon(palancas)
            if palancas is not None
            else "no se calculó el poder del uno"
        )
        return NoCalculable(
            clave="flujo_neto_ajustado",
            nombre=nombre,
            fecha=flujo_neto.fecha,
            formula=formula,
            lamina=LAMINA_AJUSTADO,
            no_calculable=f"el flujo de las 7 palancas no se calcula: {razon}",
        )
    detalle = palancas.origen.removeprefix("sale de: ")
    return Calculado(
        clave="flujo_neto_ajustado",
        nombre=nombre,
        fecha=flujo_neto.fecha,
        valor=flujo_neto.valor + palancas.valor,
        unidad="pesos",
        formula=formula,
        origen=(
            f"sale de: flujo neto {formato_monto(flujo_neto.valor)} + flujo de las 7 palancas "
            f"{formato_monto(palancas.valor)} ({detalle})"
        ),
        lamina=LAMINA_AJUSTADO,
    )


def _preguntas_de_retiros(
    respuestas: Respuestas, salio: Decimal
) -> tuple[PreguntaDeRetiros, ...]:
    if salio >= 0:
        contexto = (
            f"Tu capital creció {formato_monto(salio)} menos que tu utilidad neta."
        )
    else:
        contexto = (
            f"Tu capital creció {formato_monto(abs(salio))} más que tu utilidad neta."
        )
    para_que = f"Para explicar la 5ª fila de los 4 capítulos. {contexto}"
    preguntas: list[PreguntaDeRetiros] = []
    if respuestas.retiros_del_dueno is None:
        preguntas.append(
            PreguntaDeRetiros(
                codigo="C3",
                pregunta=(
                    f"{contexto} ¿Cuánto sacaste tú del negocio en el periodo "
                    "(gastos personales, retiros)?"
                ),
                para_que=para_que,
            )
        )
    if respuestas.retiros_de_capital is None:
        preguntas.append(
            PreguntaDeRetiros(
                codigo="C4",
                pregunta=(
                    f"{contexto} ¿Hubo retiros de los socios, dividendos o retiros de capital "
                    "en el periodo? ¿Por cuánto?"
                ),
                para_que=para_que,
            )
        )
    return tuple(preguntas)


def _retiros(quinta: Decimal, respuestas: Respuestas | None) -> ComparacionDeRetiros:
    respuestas = respuestas or Respuestas()
    salio = -quinta
    preguntas = _preguntas_de_retiros(respuestas, salio)
    if respuestas.retiros_del_dueno is None and respuestas.retiros_de_capital is None:
        return ComparacionDeRetiros(
            quinta_fila=quinta,
            salio=salio,
            dijo=None,
            sin_explicar=None,
            estado="sin respuesta",
            mensaje=(
                f"Salieron del capital {formato_monto(salio)} sin ser utilidad. "
                "Todavía no me dices cuánto retiraste tú ni los socios."
            ),
            preguntas=preguntas,
        )
    # Una sola definición con R9 (S86.15): C3 + C4; lo que no contestó cuenta 0.
    dijo = (respuestas.retiros_del_dueno or CERO) + (
        respuestas.retiros_de_capital or CERO
    )
    sin_explicar = salio - dijo
    if abs(sin_explicar) <= TOLERANCIA:
        estado: Literal["cuadra", "sin explicar"] = "cuadra"
        mensaje = (
            f"Salieron del capital {formato_monto(salio)} y me dijiste "
            f"{formato_monto(dijo)} de retiros: cuadra."
        )
    else:
        estado = "sin explicar"
        mensaje = (
            f"Salieron del capital {formato_monto(salio)} y me dijiste "
            f"{formato_monto(dijo)} de retiros: sin explicar: {formato_monto(sin_explicar)}. "
            "¿Qué pasó con esa diferencia?"
        )
    return ComparacionDeRetiros(
        quinta_fila=quinta,
        salio=salio,
        dijo=dijo,
        sin_explicar=sin_explicar,
        estado=estado,
        mensaje=mensaje,
        preguntas=preguntas,
    )


def _frase(capitulos: Sequence[Capitulo], flujo_neto: Calculado) -> str:
    un, ct, otras, salidas = capitulos
    # (si salió efectivo, si entró)
    textos = {
        "capital_de_trabajo": (
            "se quedaron en clientes, inventario y proveedores",
            "te liberaron clientes, inventario y proveedores",
        ),
        "otras_cuentas": (
            "se fueron a otras cuentas (activo fijo, pagos a acreedores y documentos)",
            "entraron de otras cuentas (activo fijo, acreedores y documentos)",
        ),
        "salidas_de_capital": (
            "salieron del capital sin ser utilidad (retiros, dividendos u otros)",
            "entraron al capital sin ser utilidad (aportaciones de los socios u otros)",
        ),
    }
    partes: list[str] = []
    for capitulo in (ct, otras, salidas):
        sale, entra = textos[capitulo.clave]
        if capitulo.valor < 0:
            partes.append(f"{formato_monto(abs(capitulo.valor))} {sale}")
        elif capitulo.valor > 0:
            partes.append(f"{formato_monto(capitulo.valor)} {entra}")
    if un.valor >= 0:
        inicio = f"Ganaste {formato_monto(un.valor)} de utilidad neta"
    else:
        inicio = f"Perdiste {formato_monto(abs(un.valor))} de utilidad neta"
    movimiento = "; ".join(partes) if partes else "nada más se movió"
    if flujo_neto.valor < 0:
        cierre = (
            f"En total salió {formato_monto(abs(flujo_neto.valor))} más de lo que entró, "
            "y tu deuda neta creció en esa cantidad: ese dinero lo pusieron bancos o préstamos."
        )
    else:
        cierre = (
            f"En total te quedaron {formato_monto(flujo_neto.valor)}, "
            "y tu deuda neta bajó en esa cantidad."
        )
    return f"{inicio}. Pero {movimiento}. {cierre}"


# ---------------------------------------------------------------------------
# El panel
# ---------------------------------------------------------------------------


def panel_de(estados: EstadosRevisados) -> PanelDelFlujo:
    """Las tres medidas, los 4 capítulos con su 5ª fila y el flujo ajustado."""

    resultado = calcular_curso(estados)
    if resultado.no_calculable is not None:
        return PanelDelFlujo(no_calculable=resultado.no_calculable)
    fin, ini = resultado.balance_final, resultado.balance_inicial
    assert fin is not None
    medidas = _medidas(resultado, fin)
    flujo_neto = resultado.indicador("flujo_neto", fin)
    if not isinstance(flujo_neto, Calculado) or ini is None:
        return PanelDelFlujo(no_calculable=_razon(flujo_neto), medidas=medidas)

    revisado = contabilidad.panel_de(estados)
    if revisado.no_calculable is not None:
        return PanelDelFlujo(no_calculable=revisado.no_calculable, medidas=medidas)
    if revisado.preguntas:
        return PanelDelFlujo(preguntas=revisado.preguntas, medidas=medidas)

    cuentas = estados.revision.acomodo.cuentas
    inicial = [c for c in cuentas if c.fecha == ini]
    final = [c for c in cuentas if c.fecha == fin]
    base = {
        "medidas": medidas,
        "engana": _engana(inicial, final, ini, fin),
        "flujo_neto": flujo_neto,
        "flujo_ajustado": _flujo_ajustado(flujo_neto, resultado),
    }

    neta = utilidad_ajustada(estados, []).utilidad_contable
    if not isinstance(neta, Calculado):
        return PanelDelFlujo(capitulos_no_calculable=neta.no_calculable, **base)

    ct = _cambios(inicial, final, "capital de trabajo", ini, fin)
    otras = _cambios(inicial, final, "otras cuentas", ini, fin)
    capital = _cambios(inicial, final, "capital", ini, fin)
    d_ct, d_otras, d_capital = _suma(ct), _suma(otras), _suma(capital)
    quinta = d_capital - neta.valor
    capitulos = (
        Capitulo(
            clave="rentabilidad",
            nombre="I. Rentabilidad",
            valor=neta.valor,
            formula="utilidad neta del periodo",
            origen=neta.origen,
            lamina=LAMINA_CAPITULOS,
        ),
        Capitulo(
            clave="capital_de_trabajo",
            nombre="II. Capital de trabajo",
            valor=-d_ct,
            formula="−(capital de trabajo al final − capital de trabajo al inicio), por renglones",
            origen=f"sale de: −({_texto_suma([(c.nombre, c.cambio) for c in ct])})",
            lamina=LAMINA_CAPITULOS,
            desglose=ct,
        ),
        Capitulo(
            clave="otras_cuentas",
            nombre="III. Otras cuentas",
            valor=-d_otras,
            formula="−(otras cuentas al final − otras cuentas al inicio), por renglones",
            origen=f"sale de: −({_texto_suma([(c.nombre, c.cambio) for c in otras])})",
            lamina=LAMINA_CAPITULOS,
            desglose=otras,
        ),
        Capitulo(
            clave="salidas_de_capital",
            nombre="5ª fila. Salidas de capital"
            if quinta <= 0
            else "5ª fila. Entradas de capital",
            valor=quinta,
            formula="(capital al final − capital al inicio) − utilidad neta",
            origen=(
                f"sale de: (capital al {fecha_corta(fin)} {formato_monto(sum((c.al_final for c in capital), CERO))}"
                f" − capital al {fecha_corta(ini)} {formato_monto(sum((c.al_inicio for c in capital), CERO))})"
                f" − utilidad neta {formato_monto(neta.valor)}"
            ),
            lamina=f"{LAMINA_CAPITULOS} (la lámina no la trae: sin ella la tabla no suma)",
            desglose=capital,
        ),
    )
    suma = sum((c.valor for c in capitulos), CERO)
    diferencia = abs(suma - flujo_neto.valor)
    aviso = None
    if diferencia > 0:
        aviso = (
            f"Los capítulos suman {formato_monto(suma)} y el flujo neto es "
            f"{formato_monto(flujo_neto.valor)}: no igualan por {formato_monto(diferencia)}. "
            "¿Redondeo o falta una cuenta?"
        )
    return PanelDelFlujo(
        capitulos=capitulos,
        suma_de_capitulos=suma,
        cuadre="aviso" if aviso else "cuadra",
        aviso=aviso,
        retiros=_retiros(quinta, estados.respuestas),
        frase=_frase(capitulos, flujo_neto),
        **base,
    )


# ---------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------

_ESTILO = """
:root { --fondo:#f7f6f2; --tinta:#1f2328; --suave:#6b7075; --linea:#d9d6cc;
  --tarjeta:#ffffff; --aviso:#8a5a00; --mal:#b3261e; --bien:#1e7a46; --total:#2f5d9e; }
@media (prefers-color-scheme: dark) { :root { --fondo:#16181b; --tinta:#e8e6e1;
  --suave:#9aa0a6; --linea:#33373c; --tarjeta:#1f2226; --aviso:#f0b43c; --mal:#ff8a80;
  --bien:#6fd39a; --total:#8db4ff; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--fondo); color:var(--tinta);
  font:16px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width:960px; margin:0 auto; padding:24px 16px 48px; }
h1 { font-size:1.6rem; margin:0 0 4px; } .sub { color:var(--suave); margin:0 0 20px; }
h2 { font-size:1.15rem; margin:28px 0 10px; }
.tarjetas { display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:12px; }
.tarjeta { background:var(--tarjeta); border:1px solid var(--linea); border-radius:12px; padding:14px; }
.tarjeta h3 { margin:0 0 4px; font-size:1rem; }
.cifra { font-size:1.5rem; font-weight:650; font-variant-numeric:tabular-nums; }
.monto { font-variant-numeric:tabular-nums; white-space:nowrap; }
.origen { font-size:.78rem; color:var(--suave); margin:2px 0 0; overflow-wrap:anywhere; }
.frase { font-size:1.1rem; font-weight:600; margin:16px 0 8px; }
.cascada { background:var(--tarjeta); border:1px solid var(--linea); border-radius:12px; padding:14px; }
.fila { margin:10px 0; }
.fila .titulo { display:flex; justify-content:space-between; gap:8px; font-weight:600; }
.pista { position:relative; height:22px; background:transparent; border-bottom:1px dashed var(--linea); }
.barra { position:absolute; top:3px; height:16px; border-radius:3px; min-width:2px; }
.sube { background:var(--bien); } .baja { background:var(--mal); } .total { background:var(--total); }
details { margin-top:6px; } summary { cursor:pointer; font-size:.9rem; }
.renglon { display:flex; justify-content:space-between; gap:8px; font-size:.9rem; margin-top:4px; }
.aviso { border-left:4px solid var(--aviso); background:var(--tarjeta); padding:10px 12px; border-radius:6px; margin:10px 0; }
.pregunta { border-left:4px solid var(--mal); }
.cuadra { border-left:4px solid var(--bien); }
.pie { margin-top:24px; font-size:.8rem; color:var(--suave); }
"""

_PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Las tres medidas de tu flujo</title>
<style>{estilo}</style>
</head>
<body>
<main>
<h1>Las tres medidas de tu flujo</h1>
<p class="sub">Por qué ganaste dinero y aun así tienes menos efectivo.</p>
{cuerpo}
<p class="pie">Según el curso de cash que vimos: flujo neto = −(deuda neta al final − deuda neta al inicio);
flujo de operación = utilidad de operación − cambio en capital de trabajo; flujo marginal = utilidad bruta ÷ ventas
− capital de trabajo ÷ ventas. La tabla de los 4 capítulos del curso no suma: le falta la 5ª fila (lo que salió del
capital sin ser utilidad). La lámina 59 imprime −3,705,843 de financiamiento: es un error de captura; el número que sale
de los estados es el que ves aquí. ESCALA calcula cada cifra con tus estados; abajo de cada una dice de dónde sale.</p>
</main>
</body>
</html>
"""


def _e(texto: str) -> str:
    return html.escape(texto)


def _valor_de(indicador: Indicador) -> str:
    if isinstance(indicador, Calculado):
        if indicador.unidad == "proporción":
            return f"{indicador.valor:.4f}"
        return formato_monto(indicador.valor)
    return f"no calculable: {_razon(indicador)}"


def _indicador_html(indicador: Indicador, para_quien: str = "") -> str:
    origen = (
        f'<p class="origen">{_e(indicador.origen)} ({_e(indicador.formula)}; lámina {_e(indicador.lamina)})</p>'
        if isinstance(indicador, Calculado)
        else f'<p class="origen">{_e(indicador.formula)}; lámina {_e(indicador.lamina)}</p>'
    )
    quien = f"<p>{_e(para_quien)}</p>" if para_quien else ""
    return (
        f'<div class="tarjeta"><h3>{_e(indicador.nombre)}</h3>'
        f'<div class="cifra">{_e(_valor_de(indicador))}</div>{quien}{origen}</div>'
    )


def _desglose_html(capitulo: Capitulo) -> str:
    if not capitulo.desglose:
        return ""
    renglones = "".join(
        f'<div class="renglon"><span>{_e(r.nombre)}</span>'
        f'<span class="monto">{formato_monto(r.efecto)}</span></div>'
        f'<p class="origen">{_e(r.origen)}</p>'
        for r in capitulo.desglose
    )
    return f"<details><summary>Ver por renglón (efecto en tu efectivo)</summary>{renglones}</details>"


def _cascada_html(panel: PanelDelFlujo) -> str:
    assert panel.flujo_neto is not None
    puntos = [CERO]
    acumulado = CERO
    tramos: list[tuple[Decimal, Decimal]] = []
    for capitulo in panel.capitulos:
        tramos.append((acumulado, acumulado + capitulo.valor))
        acumulado += capitulo.valor
        puntos.append(acumulado)
    puntos.append(panel.flujo_neto.valor)
    bajo, alto = min(puntos), max(puntos)
    rango = (alto - bajo) or Decimal("1")

    def barra(desde: Decimal, hasta: Decimal, clase: str) -> str:
        izquierda = (min(desde, hasta) - bajo) / rango * 100
        ancho = abs(hasta - desde) / rango * 100
        return f'<div class="pista"><div class="barra {clase}" style="left:{izquierda:.2f}%;width:{ancho:.2f}%"></div></div>'

    filas: list[str] = []
    for capitulo, (desde, hasta) in zip(panel.capitulos, tramos, strict=True):
        clase = "sube" if capitulo.valor >= 0 else "baja"
        filas.append(
            f'<div class="fila"><div class="titulo"><span>{_e(capitulo.nombre)}</span>'
            f'<span class="monto">{formato_monto(capitulo.valor)}</span></div>'
            f"{barra(desde, hasta, clase)}"
            f'<p class="origen">{_e(capitulo.origen)} ({_e(capitulo.formula)}; lámina {_e(capitulo.lamina)})</p>'
            f"{_desglose_html(capitulo)}</div>"
        )
    flujo = panel.flujo_neto
    filas.append(
        f'<div class="fila"><div class="titulo"><span>= IV. Flujo neto</span>'
        f'<span class="monto">{formato_monto(flujo.valor)}</span></div>'
        f"{barra(CERO, flujo.valor, 'total')}"
        f'<p class="origen">{_e(flujo.origen)} ({_e(flujo.formula)}; lámina {_e(flujo.lamina)})</p></div>'
    )
    return f'<div class="cascada">{"".join(filas)}</div>'


def _retiros_html(retiros: ComparacionDeRetiros) -> str:
    clase = {"cuadra": "cuadra", "sin explicar": "pregunta", "sin respuesta": "aviso"}[
        retiros.estado
    ]
    preguntas = "".join(
        f'<p class="aviso pregunta"><b>{_e(p.codigo)}.</b> {_e(p.pregunta)}<br><small>{_e(p.para_que)}</small></p>'
        for p in retiros.preguntas
    )
    return f'<p class="aviso {clase}">{_e(retiros.mensaje)}</p>{preguntas}'


def _cuerpo(panel: PanelDelFlujo) -> str:
    if panel.no_calculable is not None:
        return f'<p class="aviso">No calculable: {_e(panel.no_calculable)}</p>'
    if panel.preguntas:
        return "".join(
            f'<p class="aviso pregunta"><b>El panel no sale.</b> {_e(p.pregunta)}<br>'
            f"<small>{_e(p.para_que)}</small></p>"
            for p in panel.preguntas
        )
    partes: list[str] = []
    if panel.frase:
        partes.append(f'<p class="frase">{_e(panel.frase)}</p>')
    partes.append("<h2>Las tres medidas</h2>")
    partes.append(
        '<div class="tarjetas">'
        + "".join(_indicador_html(m.indicador, m.para_quien) for m in panel.medidas)
        + "</div>"
    )
    if panel.engana is not None:
        partes.append(
            '<p class="aviso">Lo que engaña: tus bancos cambiaron '
            f"{formato_monto(panel.engana.valor)}, pero eso no es tu flujo. "
            f"<br><small>{_e(panel.engana.origen)} (lámina {_e(panel.engana.lamina)})</small></p>"
        )
    partes.append("<h2>Los 4 capítulos: a dónde se fue tu utilidad</h2>")
    if panel.capitulos:
        if panel.aviso:
            partes.append(f'<p class="aviso">{_e(panel.aviso)}</p>')
        partes.append(_cascada_html(panel))
        if panel.retiros is not None:
            partes.append("<h2>La 5ª fila contra lo que me dijiste</h2>")
            partes.append(_retiros_html(panel.retiros))
    else:
        partes.append(
            f'<p class="aviso">No calculable: {_e(panel.capitulos_no_calculable or "")}</p>'
        )
    if panel.flujo_ajustado is not None:
        partes.append("<h2>Con el poder del uno</h2>")
        partes.append(
            '<div class="tarjetas">'
            + _indicador_html(
                panel.flujo_ajustado,
                "Tu flujo neto si mueves las 7 palancas un punto cada una.",
            )
            + "</div>"
        )
    return "".join(partes)


def pagina(panel: PanelDelFlujo) -> str:
    """HTML de un archivo, sin scripts: no necesita servidor."""
    return _PLANTILLA.format(estilo=_ESTILO, cuerpo=_cuerpo(panel))


# ---------------------------------------------------------------------------
# Entrada
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


def main(argv: Sequence[str] | None = None) -> int:
    """``python -m escala_server.cash.flujo <estados-revisados.json> <salida.html>``."""
    argumentos = list(sys.argv[1:] if argv is None else argv)
    if len(argumentos) != 2:
        return _no(
            "uso: python -m escala_server.cash.flujo <estados-revisados.json> <salida.html>"
        )
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
    panel = panel_de(estados)
    if panel.no_calculable is not None:
        return _no(panel.no_calculable)
    if panel.preguntas:
        _imprime(panel.model_dump_json())
        return 2
    salida = Path(argumentos[1])
    salida.write_text(pagina(panel), encoding="utf-8")
    _imprime(json.dumps({"pagina": str(salida)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
