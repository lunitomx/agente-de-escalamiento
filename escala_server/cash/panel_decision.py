"""Las páginas para decidir: precio contra volumen y margen antes de impuestos (S86.26).

Según el curso de cash que vimos. Los números salen de la calculadora
(``curso.precio_contra_volumen`` de S86.23 y ``BloqueDelMargen`` de S86.24);
la página sólo los pinta. Cada número lleva su fórmula y su «sale de:», y la
página no trae ningún script. Lo fiscal sólo se muestra.
"""

from __future__ import annotations

from decimal import Decimal
import html

from escala_server.cash.curso import (
    BloqueDelMargen,
    Calculado,
    CifraDePrecioVolumen,
    Indicador,
    NoAplica,
    NoCalculable,
    PrecioContraVolumen,
)
from escala_server.financial.formatos import fecha_corta, formato_monto

CIEN = Decimal("100")

_ESTILO = """
:root { --fondo:#f7f5f0; --tarjeta:#fff; --tinta:#1d1d1b; --suave:#5f5e5a; --linea:#d9d6cf;
  --bien:#1f7a4d; --mal:#b3261e; --barra:#2f5d8a; }
@media (prefers-color-scheme: dark) { :root { --fondo:#171716; --tarjeta:#23221f; --tinta:#f2f0ea;
  --suave:#b4b1a8; --linea:#3a3935; --bien:#5cc28e; --mal:#f2867c; --barra:#7fb0e0; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--fondo); color:var(--tinta);
  font:16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width:860px; margin:0 auto; padding:24px 16px 48px; }
h1 { font-size:1.6rem; margin:0 0 4px; } h2 { font-size:1.15rem; margin:28px 0 8px; }
.sub { color:var(--suave); margin:0 0 16px; }
.mensajes { background:var(--tarjeta); border:1px solid var(--linea); border-radius:12px; padding:12px 16px; }
.mensajes p { margin:6px 0; }
.cifras { display:grid; gap:10px; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); }
.cifra { background:var(--tarjeta); border:1px solid var(--linea); border-radius:12px; padding:12px 14px; }
.cifra b { display:block; font-size:1.3rem; font-variant-numeric:tabular-nums; }
.cifra .nombre { font-weight:600; }
.cifra .formula, .cifra .origen, .cifra .fuente { font-size:.85rem; color:var(--suave); margin:4px 0 0; }
.cifra.escala { border-color:var(--barra); }
.medidor { position:relative; height:28px; border-radius:14px; background:var(--linea); margin:12px 0 4px; }
.medidor .barra { position:absolute; left:0; top:0; bottom:0; border-radius:14px; background:var(--barra); }
.medidor .linea { position:absolute; top:-6px; bottom:-6px; width:3px; background:var(--tinta); }
.escala-medidor { display:flex; justify-content:space-between; font-size:.8rem; color:var(--suave); }
.arriba { color:var(--bien); font-weight:600; } .abajo { color:var(--mal); font-weight:600; }
.aviso { color:var(--suave); }
.pie { margin-top:28px; font-size:.8rem; color:var(--suave); }
"""

_PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title>
<style>{estilo}</style>
</head>
<body>
<main>
<h1>{titulo}</h1>
{cuerpo}
<p class="pie">Según el curso de cash que vimos. ESCALA calcula cada número con tus estados;
esta página sólo los muestra.</p>
</main>
</body>
</html>
"""


def _e(texto: str) -> str:
    return html.escape(texto, quote=True)


def _signo(valor: Decimal) -> str:
    texto = formato_monto(abs(valor))
    return f"−{texto}" if valor < 0 else texto


def _sale_de(origen: str) -> str:
    return origen if origen.startswith("sale de:") else f"sale de: {origen}"


def _con_unidad(valor: Decimal, unidad: str) -> str:
    if unidad == "%":
        return f"{_signo(valor)}%"
    if unidad == "veces":
        return f"{_signo(valor)} veces"
    return _signo(valor)


def _cifra_pv(cifra: CifraDePrecioVolumen | NoCalculable) -> str:
    if isinstance(cifra, NoCalculable):
        return (
            f'<div class="cifra"><span class="nombre">{_e(cifra.nombre)}</span>'
            f'<p class="aviso">No calculable: {_e(cifra.no_calculable)}</p></div>'
        )
    clase = "cifra escala" if cifra.fuente == "cálculo de ESCALA" else "cifra"
    return (
        f'<div class="{clase}"><span class="nombre">{_e(cifra.nombre)}</span>'
        f"<b>{_e(_con_unidad(cifra.valor, cifra.unidad))}</b>"
        f'<p class="formula">{_e(cifra.formula)}</p>'
        f'<p class="origen">{_e(_sale_de(cifra.origen))} (lámina {_e(cifra.lamina)})</p>'
        f'<p class="fuente">{_e("Está en el curso" if cifra.fuente == "curso" else "Cálculo de ESCALA")}</p>'
        "</div>"
    )


def pagina_precio_volumen(pv: PrecioContraVolumen) -> str:
    """Precio contra volumen y el costo de un descuento, en un archivo sin scripts."""
    titulo = "Precio contra volumen"
    if pv.no_calculable is not None:
        cuerpo = f'<p class="aviso">No calculable: {_e(pv.no_calculable)}</p>'
    else:
        mensajes = "".join(f"<p>{_e(m)}</p>" for m in pv.mensajes)
        cifras = "".join(_cifra_pv(c) for c in pv.cifras)
        cuerpo = (
            f'<p class="sub">Con {pv.descuento}% de descuento y {pv.volumen}% más de volumen, '
            "como en el ejemplo del curso. Los marcados como cálculo de ESCALA no están "
            "en el curso.</p>"
            f'<div class="mensajes">{mensajes}</div>'
            f'<h2>Los números</h2><div class="cifras">{cifras}</div>'
        )
    return _PLANTILLA.format(titulo=titulo, estilo=_ESTILO, cuerpo=cuerpo)


def _indicador(indicador: Indicador) -> str:
    if isinstance(indicador, NoCalculable):
        return (
            f'<div class="cifra"><span class="nombre">{_e(indicador.nombre)}</span>'
            f'<p class="aviso">No calculable: {_e(indicador.no_calculable)}</p>'
            f'<p class="formula">{_e(indicador.formula)}</p></div>'
        )
    if isinstance(indicador, NoAplica):
        return (
            f'<div class="cifra"><span class="nombre">{_e(indicador.nombre)}</span>'
            f'<p class="aviso">No aplica: {_e(indicador.no_aplica)}</p>'
            f'<p class="formula">{_e(indicador.formula)}</p></div>'
        )
    return (
        f'<div class="cifra"><span class="nombre">{_e(indicador.nombre)}</span>'
        f"<b>{_e(_con_unidad(indicador.valor, indicador.unidad))}</b>"
        f'<p class="formula">{_e(indicador.formula)}</p>'
        f'<p class="origen">{_e(_sale_de(indicador.origen))} (lámina {_e(indicador.lamina)})</p>'
        "</div>"
    )


def _porcentaje_de_la_barra(valor: Decimal, tope: Decimal) -> str:
    acotado = min(max(valor, Decimal("0")), tope)
    return f"{(acotado * CIEN / tope).quantize(Decimal('0.1'))}%"


def _medidor(margen: BloqueDelMargen) -> str:
    pretax = margen.pretax
    linea = margen.linea_de_referencia
    if not isinstance(pretax, Calculado):
        return ""
    tope = max(linea * 3, pretax.valor + 5)
    lado = (
        '<span class="arriba">llega a la línea de referencia</span>'
        if margen.por_encima_de_la_linea
        else '<span class="abajo">queda abajo de la línea de referencia</span>'
    )
    return (
        f'<div class="medidor" role="img" aria-label="Margen {formato_monto(pretax.valor)}% '
        f'contra la línea de referencia del {linea}%">'
        f'<div class="barra" style="width:{_porcentaje_de_la_barra(pretax.valor, tope)}"></div>'
        f'<div class="linea" style="left:{_porcentaje_de_la_barra(linea, tope)}"></div></div>'
        f'<div class="escala-medidor"><span>0%</span><span>línea de referencia: {linea}%</span></div>'
        f"<p>Tu margen antes de impuestos es {formato_monto(pretax.valor)}%: {lado} del {linea}%.</p>"
    )


def pagina_margen(margen: BloqueDelMargen) -> str:
    """Margen antes de impuestos con la línea del 10%, salario de mercado y devoluciones."""
    titulo = "Margen antes de impuestos"
    partes = [
        f'<p class="sub">Al {_e(fecha_corta(margen.fecha))}.</p>',
        _medidor(margen),
        '<div class="cifras">',
        _indicador(margen.pretax),
        _indicador(margen.sobre_utilidad_bruta),
        _indicador(margen.pretax_con_salario),
        _indicador(margen.utilidad_real),
        _indicador(margen.devoluciones),
        _indicador(margen.isr),
        "</div>",
        f'<p class="aviso">{_e(margen.nota_fiscal)}</p>',
    ]
    return _PLANTILLA.format(titulo=titulo, estilo=_ESTILO, cuerpo="".join(partes))
