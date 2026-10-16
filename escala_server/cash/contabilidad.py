"""Panel «Tu contabilidad real» (S86.18).

Según el curso de cash que vimos (F2.1, L16 y L18–L20), el balance se lee en dos
columnas que siempre igualan:

- **financiamiento** = deuda neta + capital: quién pone el dinero;
- **operación** = capital de trabajo + otras cuentas: en qué está.

Otras cuentas incluye el activo fijo (L56). El panel lo muestra aparte para que
el dueño lo vea, pero el total de otras cuentas es el del curso.

Otras cuentas se **suma por renglones** y se compara contra el residuo
(financiamiento − capital de trabajo). Si un renglón quedó en otra caja sin que
cambien los totales que revisó ESCALA, no igualan: el panel no sale y ESCALA
pregunta (adversarial A1). Las otras tres cajas también se suman por renglones
contra su total. La tolerancia es la de S86.15 (``revisiones.TOLERANCIA``).

Por cada 100 de ventas (F2.4, L54) sale de la calculadora del curso.

Entrada: ``python -m escala_server.cash.contabilidad <estados-revisados.json> <salida.html>``.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import html
import json
from pathlib import Path
import sys
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, ValidationError

from escala_server.cash.curso import (
    Calculado,
    EstadosRevisados,
    Indicador,
    NoCalculable,
    ResultadoDelCurso,
    calcular_curso,
)
from escala_server.financial.cajas import Caja, CuentaEnCaja, con_signo
from escala_server.financial.formatos import fecha_corta, formato_monto
from escala_server.financial.revisiones import TOLERANCIA

CERO = Decimal("0")
LAMINA_BALANCE = "L16 y L19"
LAMINA_OTRAS = "L56"
CLAVES_POR_CADA_100 = (
    "clientes_por_cada_100",
    "inventario_por_cada_100",
    "proveedores_por_cada_100",
    "capital_de_trabajo_por_cada_100",
)


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Renglon(_Modelo):
    """Una cuenta del balance dentro de su caja, con el signo que lleva en la caja."""

    nombre: str
    monto: Decimal
    origen: str


class Grupo(_Modelo):
    clave: str
    nombre: str
    total: Calculado
    renglones: tuple[Renglon, ...]


class BalanceSimplificado(_Modelo):
    fecha: date
    financiamiento: Calculado
    operacion: Calculado
    deuda_neta: Grupo
    capital: Grupo
    capital_de_trabajo: Grupo
    activo_fijo: Grupo
    resto_de_otras: Grupo
    otras_cuentas: Grupo
    residuo: Calculado
    cuadre: Literal["cuadra", "aviso"]
    aviso: str | None = None
    por_cada_100: tuple[Indicador, ...]
    frase: str

    @property
    def grupos(self) -> tuple[Grupo, ...]:
        return (
            self.deuda_neta,
            self.capital,
            self.capital_de_trabajo,
            self.activo_fijo,
            self.resto_de_otras,
            self.otras_cuentas,
        )


class PreguntaDelPanel(_Modelo):
    """Por qué el panel no sale, con las cifras, para preguntarle al dueño."""

    caja: Caja
    fecha: date
    por_renglones: Decimal
    contra: Decimal
    contra_que: str
    diferencia: Decimal
    pregunta: str
    para_que: str
    bloquea: bool = True


class PanelContabilidad(_Modelo):
    no_calculable: str | None = None
    preguntas: tuple[PreguntaDelPanel, ...] = ()
    balances: tuple[BalanceSimplificado, ...] = ()


# ---------------------------------------------------------------------------
# Renglones
# ---------------------------------------------------------------------------


def _con_signo(cuenta: CuentaEnCaja) -> Decimal:
    assert cuenta.lado is not None and cuenta.caja is not None
    return con_signo(cuenta.lado, cuenta.caja, cuenta.monto)


def _renglon(cuenta: CuentaEnCaja, fecha: date) -> Renglon:
    monto = _con_signo(cuenta)
    efecto = "suma" if monto >= 0 else "resta"
    return Renglon(
        nombre=cuenta.nombre,
        monto=monto,
        origen=(
            f"sale de: tu balance al {fecha_corta(fecha)}, renglón {cuenta.renglon}: "
            f"{cuenta.nombre} {formato_monto(cuenta.monto)} ({cuenta.lado}, {efecto} en {cuenta.caja})"
        ),
    )


def _de_la_caja(cuentas: Sequence[CuentaEnCaja], caja: Caja) -> list[CuentaEnCaja]:
    return [c for c in cuentas if c.caja == caja and c.lado is not None]


def _suma(cuentas: Sequence[CuentaEnCaja]) -> Decimal:
    return sum((_con_signo(c) for c in cuentas), CERO)


def _texto_suma(partes: Sequence[tuple[str, Decimal]]) -> str:
    """«a 1.00 + b 2.00 − c 3.00» con el signo de cada parte."""
    if not partes:
        return "no hay cuentas en esta caja (0.00)"
    textos: list[str] = []
    for nombre, monto in partes:
        signo = "−" if monto < 0 else "+"
        textos.append(f"{signo} {nombre} {formato_monto(abs(monto))}")
    texto = " ".join(textos)
    return texto[2:] if texto.startswith("+ ") else texto


def _numero(clave: str, nombre: str, fecha: date, valor: Decimal, formula: str, origen: str, lamina: str) -> Calculado:
    return Calculado(
        clave=clave,
        nombre=nombre,
        fecha=fecha,
        valor=valor,
        unidad="pesos",
        formula=formula,
        origen=f"sale de: {origen}",
        lamina=lamina,
    )


def _grupo_de_renglones(
    clave: str, nombre: str, formula: str, cuentas: Sequence[CuentaEnCaja], fecha: date
) -> Grupo:
    renglones = tuple(_renglon(c, fecha) for c in cuentas)
    total = sum((r.monto for r in renglones), CERO)
    origen = _texto_suma([(r.nombre, r.monto) for r in renglones])
    return Grupo(
        clave=clave,
        nombre=nombre,
        total=_numero(clave, nombre, fecha, total, formula, origen, LAMINA_OTRAS),
        renglones=renglones,
    )


# ---------------------------------------------------------------------------
# Revisión: renglones contra totales
# ---------------------------------------------------------------------------


def _pregunta(
    caja: Caja, fecha: date, por_renglones: Decimal, contra: Decimal, contra_que: str
) -> PreguntaDelPanel:
    diferencia = abs(por_renglones - contra)
    cuando = fecha_corta(fecha)
    return PreguntaDelPanel(
        caja=caja,
        fecha=fecha,
        por_renglones=por_renglones,
        contra=contra,
        contra_que=contra_que,
        diferencia=diferencia,
        pregunta=(
            f"Al {cuando}, {caja} suma {formato_monto(por_renglones)} por renglones, "
            f"pero {contra_que} da {formato_monto(contra)}: no igualan por "
            f"{formato_monto(diferencia)}. Puede que una cuenta haya cambiado de caja "
            "sin que ESCALA lo recalculara, o que falte una cuenta. "
            "¿Me mandas tus estados otra vez para revisarlos?"
        ),
        para_que=(
            "Si no igualan, una cuenta está en una caja que ESCALA no revisó "
            "y el panel diría algo que no es."
        ),
    )


def _revisa(
    fecha: date, cuentas: Sequence[CuentaEnCaja], resultado: ResultadoDelCurso
) -> tuple[PreguntaDelPanel | None, list[str]]:
    """Primero otras cuentas contra el residuo; luego cada caja contra su total."""

    def valor(clave: str) -> Decimal:
        indicador = resultado.indicador(clave, fecha)
        assert isinstance(indicador, Calculado), indicador
        return indicador.valor

    ct, dn, capital = valor("capital_de_trabajo"), valor("deuda_neta"), valor("capital")
    comparaciones: list[tuple[Caja, Decimal, Decimal, str]] = [
        (
            "otras cuentas",
            _suma(_de_la_caja(cuentas, "otras cuentas")),
            dn + capital - ct,
            "financiamiento menos capital de trabajo",
        ),
        ("capital de trabajo", _suma(_de_la_caja(cuentas, "capital de trabajo")), ct, "el total que revisó ESCALA"),
        ("deuda neta", _suma(_de_la_caja(cuentas, "deuda neta")), dn, "el total que revisó ESCALA"),
        ("capital", _suma(_de_la_caja(cuentas, "capital")), capital, "el total que revisó ESCALA"),
    ]
    avisos: list[str] = []
    for caja, por_renglones, contra, contra_que in comparaciones:
        diferencia = abs(por_renglones - contra)
        if diferencia > TOLERANCIA:
            return _pregunta(caja, fecha, por_renglones, contra, contra_que), []
        if diferencia > 0:
            avisos.append(f"{caja} no iguala por {formato_monto(diferencia)}")
    return None, avisos


# ---------------------------------------------------------------------------
# El balance simplificado
# ---------------------------------------------------------------------------


def _frase(ct_por_cada_100: Indicador) -> str:
    if isinstance(ct_por_cada_100, Calculado):
        valor = ct_por_cada_100.valor
        if valor >= 0:
            return (
                f"Por cada 100 pesos que vendes, {formato_monto(valor)} "
                "se quedan atrapados en capital de trabajo."
            )
        return (
            f"Por cada 100 pesos que vendes, tus proveedores te financian {formato_monto(abs(valor))} "
            "más de lo que tienes en clientes e inventario."
        )
    razon = ct_por_cada_100.no_calculable if isinstance(ct_por_cada_100, NoCalculable) else ct_por_cada_100.no_aplica
    return f"Por cada 100 de ventas: no calculable: {razon}"


def _balance(
    fecha: date, cuentas: Sequence[CuentaEnCaja], resultado: ResultadoDelCurso, avisos: list[str]
) -> BalanceSimplificado:
    def calculado(clave: str) -> Calculado:
        indicador = resultado.indicador(clave, fecha)
        assert isinstance(indicador, Calculado), indicador
        return indicador

    def grupo(clave: str, caja: Caja) -> Grupo:
        return Grupo(
            clave=clave,
            nombre=calculado(clave).nombre,
            total=calculado(clave),
            renglones=tuple(_renglon(c, fecha) for c in _de_la_caja(cuentas, caja)),
        )

    otras = _de_la_caja(cuentas, "otras cuentas")
    fijo = [c for c in otras if c.regla == "activo_fijo"]
    resto = [c for c in otras if c.regla != "activo_fijo"]
    otras_cuentas = _grupo_de_renglones(
        "otras_cuentas",
        "Otras cuentas",
        "suma de sus renglones: otros activos + activo fijo + diferidos − otras acreedoras − documentos",
        otras,
        fecha,
    )
    activo_fijo = _grupo_de_renglones("activo_fijo", "Activo fijo", "suma de sus renglones", fijo, fecha)
    resto_de_otras = _grupo_de_renglones(
        "resto_de_otras",
        "Resto de otras cuentas",
        "otras cuentas sin el activo fijo, suma de sus renglones",
        resto,
        fecha,
    )
    ct = grupo("capital_de_trabajo", "capital de trabajo")
    financiamiento = calculado("financiamiento")
    operacion_valor = ct.total.valor + otras_cuentas.total.valor
    operacion = _numero(
        "operacion",
        "Operación",
        fecha,
        operacion_valor,
        "capital de trabajo + activo fijo + resto de otras cuentas",
        _texto_suma(
            [
                ("capital de trabajo", ct.total.valor),
                ("activo fijo", activo_fijo.total.valor),
                ("resto de otras cuentas", resto_de_otras.total.valor),
            ]
        ),
        LAMINA_BALANCE,
    )
    dn, capital = calculado("deuda_neta"), calculado("capital")
    residuo = _numero(
        "otras_cuentas_por_diferencia",
        "Otras cuentas por diferencia",
        fecha,
        financiamiento.valor - ct.total.valor,
        "financiamiento − capital de trabajo",
        f"financiamiento {formato_monto(financiamiento.valor)} − capital de trabajo {formato_monto(ct.total.valor)}",
        LAMINA_OTRAS,
    )
    diferencia = abs(financiamiento.valor - operacion_valor)
    aviso = None
    if diferencia > 0 or avisos:
        aviso = (
            f"Al {fecha_corta(fecha)} financiamiento {formato_monto(financiamiento.valor)} y "
            f"operación {formato_monto(operacion_valor)} no igualan por {formato_monto(diferencia)}"
        )
        if avisos:
            aviso += " (" + "; ".join(avisos) + ")"
        aviso += ": ¿redondeo o falta una cuenta?"
    por_cada_100 = tuple(resultado.indicador(clave, fecha) for clave in CLAVES_POR_CADA_100)
    return BalanceSimplificado(
        fecha=fecha,
        financiamiento=financiamiento,
        operacion=operacion,
        deuda_neta=Grupo(
            clave="deuda_neta",
            nombre=dn.nombre,
            total=dn,
            renglones=tuple(_renglon(c, fecha) for c in _de_la_caja(cuentas, "deuda neta")),
        ),
        capital=Grupo(
            clave="capital",
            nombre=capital.nombre,
            total=capital,
            renglones=tuple(_renglon(c, fecha) for c in _de_la_caja(cuentas, "capital")),
        ),
        capital_de_trabajo=ct,
        activo_fijo=activo_fijo,
        resto_de_otras=resto_de_otras,
        otras_cuentas=otras_cuentas,
        residuo=residuo,
        cuadre="aviso" if aviso else "cuadra",
        aviso=aviso,
        por_cada_100=por_cada_100,
        frase=_frase(por_cada_100[-1]),
    )


def panel_de(estados: EstadosRevisados) -> PanelContabilidad:
    """El balance simplificado de cada fecha, o la pregunta de por qué no sale."""

    resultado = calcular_curso(estados)
    if resultado.no_calculable is not None:
        return PanelContabilidad(no_calculable=resultado.no_calculable)
    fechas = [f for f in (resultado.balance_final, resultado.balance_inicial) if f is not None]
    preguntas: list[PreguntaDelPanel] = []
    listos: list[tuple[date, list[CuentaEnCaja], list[str]]] = []
    for fecha in fechas:
        try:
            resultado.indicador("financiamiento", fecha)
        except KeyError:
            continue
        cuentas = [c for c in estados.revision.acomodo.cuentas if c.fecha == fecha]
        pregunta, avisos = _revisa(fecha, cuentas, resultado)
        if pregunta is not None:
            preguntas.append(pregunta)
        else:
            listos.append((fecha, cuentas, avisos))
    if preguntas:
        return PanelContabilidad(preguntas=tuple(preguntas))
    if not listos:
        return PanelContabilidad(no_calculable="falta el balance al final del periodo")
    return PanelContabilidad(
        balances=tuple(_balance(fecha, cuentas, resultado, avisos) for fecha, cuentas, avisos in listos)
    )


# ---------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------

_ESTILO = """
:root { --fondo:#f7f6f2; --tinta:#1f2328; --suave:#6b7075; --linea:#d9d6cc;
  --tarjeta:#ffffff; --aviso:#8a5a00; --mal:#b3261e; }
@media (prefers-color-scheme: dark) { :root { --fondo:#16181b; --tinta:#e8e6e1;
  --suave:#9aa0a6; --linea:#33373c; --tarjeta:#1f2226; --aviso:#f0b43c; --mal:#ff8a80; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--fondo); color:var(--tinta);
  font:16px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width:960px; margin:0 auto; padding:24px 16px 48px; }
h1 { font-size:1.6rem; margin:0 0 4px; } .sub { color:var(--suave); margin:0 0 20px; }
h2 { font-size:1.15rem; margin:28px 0 10px; }
.columnas { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.columna { background:var(--tarjeta); border:1px solid var(--linea); border-radius:12px; padding:14px; }
.columna h3 { margin:0 0 4px; font-size:1rem; }
.cifra { font-size:1.5rem; font-weight:650; font-variant-numeric:tabular-nums; }
.grupo { margin-top:12px; border-top:1px solid var(--linea); padding-top:8px; }
.grupo summary { cursor:pointer; display:flex; justify-content:space-between; gap:8px; font-weight:600; }
.monto { font-variant-numeric:tabular-nums; white-space:nowrap; }
.renglon { display:flex; justify-content:space-between; gap:8px; font-size:.9rem; margin-top:4px; }
.origen { font-size:.78rem; color:var(--suave); margin:2px 0 0; overflow-wrap:anywhere; }
.frase { font-size:1.15rem; font-weight:600; margin:16px 0 8px; }
.cien { display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:10px; }
.cien div { background:var(--tarjeta); border:1px solid var(--linea); border-radius:10px; padding:10px 12px; }
.aviso { border-left:4px solid var(--aviso); background:var(--tarjeta); padding:10px 12px; border-radius:6px; margin:10px 0; }
.pregunta { border-left:4px solid var(--mal); }
.pie { margin-top:24px; font-size:.8rem; color:var(--suave); }
@media (max-width:640px) { .columnas { grid-template-columns:1fr; } }
"""

_PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tu contabilidad real</title>
<style>{estilo}</style>
</head>
<body>
<main>
<h1>Tu contabilidad real</h1>
<p class="sub">Tu balance en dos columnas: quién pone el dinero (financiamiento)
y en qué está (operación). Las dos columnas siempre igualan.</p>
{cuerpo}
<p class="pie">Según el curso de cash que vimos: financiamiento = deuda neta + capital;
operación = capital de trabajo + otras cuentas (el activo fijo es parte de otras cuentas).
ESCALA calcula cada cifra con tus estados; abajo de cada una dice de dónde sale.</p>
</main>
</body>
</html>
"""


def _e(texto: str) -> str:
    return html.escape(texto)


def _cifra_de(numero: Calculado) -> str:
    return (
        f'<div class="cifra">{formato_monto(numero.valor)}</div>'
        f'<p class="origen">{_e(numero.origen)} ({_e(numero.formula)}; lámina {_e(numero.lamina)})</p>'
    )


def _grupo_html(grupo: Grupo) -> str:
    renglones = "".join(
        f'<div class="renglon"><span>{_e(r.nombre)}</span>'
        f'<span class="monto">{formato_monto(r.monto)}</span></div>'
        f'<p class="origen">{_e(r.origen)}</p>'
        for r in grupo.renglones
    )
    return (
        f'<details class="grupo"><summary><span>{_e(grupo.nombre)}</span>'
        f'<span class="monto">{formato_monto(grupo.total.valor)}</span></summary>'
        f'<p class="origen">{_e(grupo.total.origen)}</p>{renglones}</details>'
    )


def _indicador_html(indicador: Indicador) -> str:
    if isinstance(indicador, Calculado):
        return (
            f"<div><b>{_e(indicador.nombre)}</b>"
            f'<div class="cifra">{formato_monto(indicador.valor)}</div>'
            f'<p class="origen">{_e(indicador.origen)} (lámina {_e(indicador.lamina)})</p></div>'
        )
    razon = indicador.no_calculable if isinstance(indicador, NoCalculable) else indicador.no_aplica
    return f"<div><b>{_e(indicador.nombre)}</b><p>no calculable: {_e(razon)}</p></div>"


def _balance_html(balance: BalanceSimplificado) -> str:
    aviso = f'<p class="aviso">{_e(balance.aviso)}</p>' if balance.aviso else ""
    financiamiento = _grupo_html(balance.deuda_neta) + _grupo_html(balance.capital)
    operacion = (
        _grupo_html(balance.capital_de_trabajo)
        + _grupo_html(balance.activo_fijo)
        + _grupo_html(balance.resto_de_otras)
    )
    cien = "".join(_indicador_html(i) for i in balance.por_cada_100)
    return f"""<h2>Al {fecha_corta(balance.fecha)}</h2>
{aviso}<div class="columnas">
<section class="columna"><h3>Financiamiento</h3>{_cifra_de(balance.financiamiento)}{financiamiento}</section>
<section class="columna"><h3>Operación</h3>{_cifra_de(balance.operacion)}{operacion}
<p class="origen">Otras cuentas (activo fijo + resto): {formato_monto(balance.otras_cuentas.total.valor)}.
Por diferencia da {formato_monto(balance.residuo.valor)}; {_e(balance.residuo.origen)}.</p></section>
</div>
<p class="frase">{_e(balance.frase)}</p>
<div class="cien">{cien}</div>"""


def pagina(panel: PanelContabilidad) -> str:
    """HTML de un archivo, sin scripts: no necesita servidor."""
    if panel.no_calculable is not None:
        cuerpo = f'<p class="aviso">No calculable: {_e(panel.no_calculable)}</p>'
    elif panel.preguntas:
        cuerpo = "".join(
            f'<p class="aviso pregunta"><b>El panel no sale.</b> {_e(p.pregunta)}<br>'
            f"<small>{_e(p.para_que)}</small></p>"
            for p in panel.preguntas
        )
    else:
        cuerpo = "".join(_balance_html(b) for b in panel.balances)
    return _PLANTILLA.format(estilo=_ESTILO, cuerpo=cuerpo)


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
    """``python -m escala_server.cash.contabilidad <estados-revisados.json> <salida.html>``."""
    argumentos = list(sys.argv[1:] if argv is None else argv)
    if len(argumentos) != 2:
        return _no("uso: python -m escala_server.cash.contabilidad <estados-revisados.json> <salida.html>")
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
