"""Panel «Días y ciclo del dinero» (S86.19).

Según el curso de cash que vimos (F2.2 y F2.3): cuántos días tardas en cobrar,
cuántos días tienes el inventario y cuántos días te dan tus proveedores; el
ciclo es lo que financias tú. La línea de tiempo va compra → pago → venta → cobro.

Python calcula todo (``curso.dias_del_dinero``, con pruebas). Esta página sólo
pinta: cada número lleva su «sale de:» y no trae ningún script que haga cuentas.

Entrada::

    python -m escala_server.cash.panel_dias <estados-revisados.json> <salida.html>
        [--iva sí|no|no sé] [--tasa-iva N] [--credito N]

Sin banderas usa lo que el dueño contestó en la revisión (C1 y C9). La tasa de
IVA es dato del dueño: sin ``--tasa-iva`` no se quita el IVA.
"""

from __future__ import annotations

import html
import json
from decimal import Decimal
from pathlib import Path
import sys
from typing import Sequence

from pydantic import ValidationError

from escala_server.cash.curso import (
    BaseDeDias,
    Calculado,
    Cambio,
    Cronograma,
    DiasDelAnio,
    DiasDelDinero,
    EstadosRevisados,
    Indicador,
    NoAplica,
    NoCalculable,
    dias_del_dinero,
)
from escala_server.financial.formatos import fecha_corta, formato_monto

USO = (
    "uso: python -m escala_server.cash.panel_dias <estados-revisados.json> <salida.html> "
    "[--iva sí|no|no sé] [--tasa-iva N] [--credito N]"
)

_CUENTAS: tuple[tuple[str, str, str], ...] = (
    ("clientes", "Días de clientes", "Cuánto tardas en cobrar. Menos es mejor."),
    ("inventario", "Días de inventario", "Cuánto tiempo guardas la mercancía. Menos es mejor."),
    ("proveedores", "Días de proveedores", "Cuánto tardas en pagar. Más es mejor para tu efectivo."),
    ("ciclo", "Ciclo del efectivo", "Clientes + inventario − proveedores: los días que financias tú."),
)

_ESTILO = """
:root { --fondo:#f7f6f2; --tinta:#1f2328; --suave:#6b7075; --linea:#d9d6cc;
  --tarjeta:#ffffff; --bien:#1f7a4d; --mal:#b3261e; --aviso:#8a5a00; --tramo:#e9c46a; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --fondo:#16181b;
  --tinta:#e8e6e1; --suave:#9aa0a6; --linea:#33373c; --tarjeta:#1f2226; --bien:#5cc28f;
  --mal:#ff8a80; --aviso:#f0b43c; --tramo:#8a6d1f; } }
:root[data-theme="dark"] { --fondo:#16181b; --tinta:#e8e6e1; --suave:#9aa0a6; --linea:#33373c;
  --tarjeta:#1f2226; --bien:#5cc28f; --mal:#ff8a80; --aviso:#f0b43c; --tramo:#8a6d1f; }
* { box-sizing:border-box; }
body { margin:0; background:var(--fondo); color:var(--tinta);
  font:16px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width:960px; margin:0 auto; padding:24px 16px 48px; }
h1 { font-size:1.6rem; margin:0 0 4px; } h2 { font-size:1.15rem; margin:28px 0 10px; }
.sub { color:var(--suave); margin:0 0 6px; } .rotulo { font-weight:600; margin:0 0 16px; }
.avisos { display:grid; gap:8px; margin-bottom:16px; }
.aviso { border-left:4px solid var(--aviso); background:var(--tarjeta); padding:10px 12px; border-radius:6px; }
.aviso b { color:var(--aviso); }
.tarjetas { display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:12px; }
.tarjeta { background:var(--tarjeta); border:1px solid var(--linea); border-radius:12px; padding:14px; }
.tarjeta h3 { font-size:1rem; margin:0 0 2px; } .tarjeta .que { font-size:.85rem; color:var(--suave); margin:0 0 10px; }
.anios { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.anio .fecha { font-size:.8rem; color:var(--suave); }
.anio .cifra { font-size:1.5rem; font-weight:650; font-variant-numeric:tabular-nums; }
.anio .razon { font-size:.9rem; color:var(--suave); }
.sale { font-size:.75rem; color:var(--suave); margin-top:4px; overflow-wrap:anywhere; }
.cambio { margin-top:10px; font-size:.9rem; font-weight:600; }
.mejoro { color:var(--bien); } .empeoro { color:var(--mal); } .otro { color:var(--suave); }
.linea { background:var(--tarjeta); border:1px solid var(--linea); border-radius:12px; padding:14px; margin-bottom:12px; }
.linea h3 { font-size:1rem; margin:0 0 12px; }
.eje { position:relative; height:44px; margin:0 8px 8px; }
.eje .base { position:absolute; left:0; right:0; top:20px; height:4px; background:var(--linea); border-radius:2px; }
.eje .tramo { position:absolute; top:16px; height:12px; background:var(--tramo); border-radius:6px; }
.eje .punto { position:absolute; top:12px; width:20px; height:20px; margin-left:-10px; border-radius:50%;
  background:var(--tinta); border:3px solid var(--tarjeta); }
.pasos { list-style:none; padding:0; margin:0; display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:8px; }
.pasos li { font-size:.9rem; } .pasos b { display:block; }
.financia { margin-top:10px; font-weight:600; }
.nota { font-size:.85rem; color:var(--suave); margin-top:8px; }
.pie { margin-top:28px; font-size:.8rem; color:var(--suave); }
@media (max-width:560px) { .anios { grid-template-columns:1fr; } }
"""

_PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Días y ciclo del dinero</title>
<style>{estilo}</style>
</head>
<body>
<main>
<h1>Días y ciclo del dinero</h1>
{cuerpo}
<p class="pie">Según el curso de cash que vimos. ESCALA calcula cada número con tus estados;
esta página sólo los muestra.</p>
</main>
<script id="datos-dias" type="application/json">{datos}</script>
</body>
</html>
"""


def _e(texto: str) -> str:
    return html.escape(texto)


def _dias(valor: Decimal) -> str:
    return formato_monto(valor)


def _sale_de(origen: str) -> str:
    return origen if origen.startswith("sale de:") else f"sale de: {origen}"


def _celda(fecha_texto: str, indicador: Indicador) -> str:
    if isinstance(indicador, Calculado):
        valor = f'<div class="cifra">{_dias(indicador.valor)} días</div>'
        detalle = f'<div class="sale">{_e(_sale_de(indicador.origen))}</div>'
    elif isinstance(indicador, NoCalculable):
        valor = f'<div class="razon">No calculable: {_e(indicador.no_calculable)}</div>'
        detalle = ""
    else:
        assert isinstance(indicador, NoAplica)
        valor = f'<div class="razon">No aplica: {_e(indicador.no_aplica)}</div>'
        detalle = ""
    return (
        f'<div class="anio"><div class="fecha">{_e(fecha_texto)}</div>{valor}{detalle}</div>'
    )


def _clase(cambio: Cambio) -> str:
    return {"mejoró": "mejoro", "empeoró": "empeoro"}.get(cambio.veredicto, "otro")


def _tarjeta(dias: DiasDelDinero, clave: str, nombre: str, que: str) -> str:
    celdas = "".join(
        _celda(f"Al {fecha_corta(anio.fecha)}", getattr(anio, clave)) for anio in dias.anios
    )
    try:
        cambio = dias.cambio(clave)
        renglon = f'<div class="cambio {_clase(cambio)}">{_e(cambio.texto)}</div>'
    except KeyError:
        renglon = ""
    return (
        f'<section class="tarjeta" id="{clave}"><h3>{_e(nombre)}</h3>'
        f'<p class="que">{_e(que)}</p><div class="anios">{celdas}</div>{renglon}</section>'
    )


def _posicion(dia: Decimal, escala: Decimal) -> str:
    if escala <= 0:
        return "0"
    return format(min(max(dia / escala * 100, Decimal(0)), Decimal(100)).quantize(Decimal("0.1")), "f")


def _financia(cronograma: Cronograma) -> str:
    financiados = cronograma.financiados
    if financiados > 0:
        return f"{_dias(financiados)} días que financias tú (del pago al proveedor al cobro)."
    if financiados < 0:
        return (
            f"{_dias(-financiados)} días que te financian tus proveedores "
            "(cobras antes de pagarles)."
        )
    return "Cobras el mismo día que pagas: no financias días."


def _linea(anio: DiasDelAnio) -> str:
    titulo = f"<h3>Al {_e(fecha_corta(anio.fecha))}</h3>"
    cronograma = anio.cronograma
    if cronograma is None:
        razon = anio.sin_cronograma or "no calculable"
        return f'<section class="linea">{titulo}<p class="razon">Sin línea de tiempo: {_e(razon)}</p></section>'
    escala = max(cronograma.cobro, cronograma.pago, cronograma.venta, Decimal(1))
    desde, hasta = sorted((cronograma.pago, cronograma.cobro))
    izquierda = _posicion(desde, escala)
    ancho = format(
        (Decimal(_posicion(hasta, escala)) - Decimal(izquierda)).quantize(Decimal("0.1")), "f"
    )
    puntos = "".join(
        f'<span class="punto" style="left:{_posicion(dia, escala)}%" title="{_e(nombre)}"></span>'
        for nombre, dia in (
            ("Compra", Decimal(0)),
            ("Pago", cronograma.pago),
            ("Venta", cronograma.venta),
            ("Cobro", cronograma.cobro),
        )
    )
    pasos = (
        "<li><b>Compra</b>día 0</li>"
        f"<li><b>Pagas al proveedor</b>día {_dias(cronograma.pago)}</li>"
        f"<li><b>Vendes</b>día {_dias(cronograma.venta)}</li>"
        f"<li><b>Cobras</b>día {_dias(cronograma.cobro)}</li>"
    )
    nota = f'<p class="nota">{_e(anio.nota)}</p>' if anio.nota else ""
    return (
        f'<section class="linea">{titulo}'
        f'<div class="eje" aria-hidden="true"><span class="base"></span>'
        f'<span class="tramo" style="left:{izquierda}%;width:{ancho}%"></span>{puntos}</div>'
        f'<ol class="pasos">{pasos}</ol>'
        f'<p class="financia">{_e(_financia(cronograma))}</p>'
        f'<div class="sale">{_e(_sale_de(cronograma.origen))}</div>{nota}</section>'
    )


def _avisos(dias: DiasDelDinero) -> str:
    cajas = [f'<div class="aviso"><b>Aviso.</b> {_e(a)}</div>' for a in dias.avisos]
    cajas += [f'<div class="aviso"><b>Pregunta.</b> {_e(p)}</div>' for p in dias.preguntas]
    return f'<div class="avisos">{"".join(cajas)}</div>' if cajas else ""


def _cuerpo(dias: DiasDelDinero) -> str:
    if dias.no_calculable is not None:
        return f'<div class="aviso"><b>No calculable:</b> {_e(dias.no_calculable)}</div>'
    sub = ""
    if dias.periodo is not None:
        sub = (
            f'<p class="sub">Tus estados del {_e(fecha_corta(dias.periodo.desde))} al '
            f"{_e(fecha_corta(dias.periodo.hasta))}: {dias.periodo.dias} días. "
            f"Días de cobro sobre {_e(dias.base_de_ventas)}.</p>"
        )
    tarjetas = "".join(_tarjeta(dias, clave, nombre, que) for clave, nombre, que in _CUENTAS)
    lineas = "".join(_linea(anio) for anio in dias.anios)
    return (
        f'{sub}<p class="rotulo">{_e(dias.rotulo)}</p>{_avisos(dias)}'
        f'<div class="tarjetas">{tarjetas}</div>'
        f"<h2>Línea de tiempo: compra → pago → venta → cobro</h2>{lineas}"
    )


def pagina(dias: DiasDelDinero) -> str:
    """HTML de un archivo: no necesita servidor ni nada de fuera."""
    datos = dias.model_dump_json().replace("</", "<\\/")
    return _PLANTILLA.format(estilo=_ESTILO, cuerpo=_cuerpo(dias), datos=datos)


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------

_IVA: dict[str, bool | None] = {"sí": True, "si": True, "no": False, "no sé": None, "no se": None}


def _imprime(texto: str) -> None:
    salida = sys.stdout
    reconfigurar = getattr(salida, "reconfigure", None)
    if callable(reconfigurar):
        reconfigurar(encoding="utf-8")
    salida.write(texto + "\n")


def _no(razon: str) -> int:
    _imprime(json.dumps({"no_calculable": razon}, ensure_ascii=False))
    return 2


def _banderas(resto: list[str]) -> dict[str, str] | str:
    """Las banderas como texto; si algo no se entiende, la razón."""
    leidas: dict[str, str] = {}
    i = 0
    while i < len(resto):
        bandera = resto[i]
        if bandera not in ("--iva", "--tasa-iva", "--credito") or i + 1 >= len(resto):
            return USO
        leidas[bandera] = resto[i + 1].strip().lower() if bandera == "--iva" else resto[i + 1]
        i += 2
    return leidas


def _base(estados: EstadosRevisados, banderas: dict[str, str]) -> BaseDeDias | str:
    guardada = BaseDeDias.de(estados.respuestas)
    campos: dict[str, object] = guardada.model_dump()
    if "--iva" in banderas:
        if banderas["--iva"] not in _IVA:
            return "--iva sólo acepta sí, no o no sé"
        campos["iva_incluido"] = _IVA[banderas["--iva"]]
    if "--tasa-iva" in banderas:
        campos["tasa_iva"] = banderas["--tasa-iva"]
    if "--credito" in banderas:
        campos["ventas_a_credito"] = banderas["--credito"]
    try:
        return BaseDeDias.model_validate(campos)
    except ValidationError:
        return (
            "no entendí la tasa de IVA o el porcentaje a crédito: "
            "escribe un número de 0 a 100, por ejemplo 16 o 60"
        )


def main(argv: Sequence[str] | None = None) -> int:
    argumentos = list(sys.argv[1:] if argv is None else argv)
    if len(argumentos) < 2:
        return _no(USO)
    banderas = _banderas(argumentos[2:])
    if isinstance(banderas, str):
        return _no(banderas)
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
    base = _base(estados, banderas)
    if isinstance(base, str):
        return _no(base)
    dias = dias_del_dinero(estados, base)
    if dias.no_calculable is not None:
        return _no(dias.no_calculable)
    salida = Path(argumentos[1])
    salida.write_text(pagina(dias), encoding="utf-8")
    _imprime(json.dumps({"pagina": str(salida)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
