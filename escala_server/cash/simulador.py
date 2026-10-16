"""Simulador de las 7 palancas (S86.22).

Según el curso de cash que vimos (F4.1), mover una palanca tiene dos lados:

- **cada periodo**: más venta, menos costo o gasto. Es utilidad y se repite.
- **una sola vez**: lo que se queda (o se libera) en clientes, inventario o
  proveedores. Es balance y pasa una vez.

Python da los dos coeficientes por punto (la calculadora del curso, que usa el
motor de S86.13) y arma una página de un solo archivo. La página sólo multiplica
movimiento × coeficiente; en la vista mensual reparte sólo el lado de cada
periodo. El de una sola vez va aparte: nunca se reparte ni se repite.

Entrada: ``python -m escala_server.cash.simulador <estados-revisados.json> <salida.html>``.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
import sys
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, ValidationError

from escala_server.cash.curso import (
    Calculado,
    EstadosRevisados,
    NoCalculable,
    PalancaDelSimulador,
    ResultadoDelCurso,
    calcular_curso,
)
from escala_server.financial.formatos import fecha_corta, formato_monto

JS = Path(__file__).with_name("simulador.js")
ROTULO = "antes de ISR"
LAMINA_PRECIO = "L38"
LAMINA_VOLUMEN = "L54"


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Vista(_Modelo):
    """Cómo se ve el resultado. ``meses`` es entre cuánto se reparte el lado de cada periodo."""

    clave: Literal["anual", "mensual", "acumulado"]
    nombre: str
    meses: int


class Advertencia(_Modelo):
    palanca: str
    texto: str
    origen: str
    lamina: str


class Simulador(_Modelo):
    no_calculable: str | None = None
    periodo: str = ""
    rotulo: Literal["antes de ISR"] = ROTULO
    vistas: tuple[Vista, ...] = ()
    sin_vista: tuple[str, ...] = ()
    palancas: tuple[PalancaDelSimulador, ...] = ()
    advertencias: tuple[Advertencia, ...] = ()
    rango_pct: int = 10
    rango_dias: int = 30


def _vistas(meses: int) -> tuple[tuple[Vista, ...], tuple[str, ...]]:
    mensual = Vista(clave="mensual", nombre="Cada mes", meses=meses)
    if meses == 12:
        return (Vista(clave="anual", nombre="El año", meses=1), mensual), ()
    suponer = (
        f"tus estados cubren {meses} {'mes' if meses == 1 else 'meses'}: "
        "llevarlo a 12 meses sería suponer, por eso no hay vista anual"
    )
    if meses == 1:
        return (mensual,), (suponer,)
    return (Vista(clave="acumulado", nombre=f"Los {meses} meses", meses=1), mensual), (
        suponer,
    )


def _advertencias(resultado: ResultadoDelCurso) -> tuple[Advertencia, ...]:
    precio = Advertencia(
        palanca="precio",
        texto=(
            "Según el curso de cash que vimos: al subir el precio, alguno quedó fuera "
            "del mercado. Revisa que tu precio siga dentro de lo que paga tu mercado."
        ),
        origen="sale de: el curso de cash, palanca del precio",
        lamina=LAMINA_PRECIO,
    )
    ct = None
    if resultado.balance_final is not None:
        try:
            ct = resultado.indicador(
                "capital_de_trabajo_por_cada_100", resultado.balance_final
            )
        except KeyError:
            ct = None
    if isinstance(ct, Calculado):
        texto = (
            "Según el curso de cash que vimos: crecer pide "
            f"{formato_monto(ct.valor)} por cada 100 de ventas en capital de trabajo. "
            "Ese efectivo sale antes de que llegue la utilidad."
        )
        origen = ct.origen
    else:
        razon = "falta el capital de trabajo por cada 100 de ventas"
        if isinstance(ct, NoCalculable):
            razon = ct.no_calculable
        texto = (
            "Según el curso de cash que vimos: crecer pide capital de trabajo por cada "
            f"100 de ventas; no calculable: {razon}."
        )
        origen = f"no calculable: {razon}"
    volumen = Advertencia(
        palanca="volumen", texto=texto, origen=origen, lamina=LAMINA_VOLUMEN
    )
    return precio, volumen


def simulador_de(resultado: ResultadoDelCurso) -> Simulador:
    """Arma los datos de la página desde el resultado de la calculadora del curso."""
    razon = resultado.no_calculable
    if razon is None and isinstance(resultado.poder_del_uno_flujo, NoCalculable):
        razon = resultado.poder_del_uno_flujo.no_calculable
    if razon is None and (not resultado.simulador or resultado.periodo is None):
        razon = "falta confirmar qué periodo cubren tus estados"
    if razon is not None or resultado.periodo is None:
        return Simulador(no_calculable=razon)
    periodo = resultado.periodo
    meses = (
        (periodo.hasta.year - periodo.desde.year) * 12
        + periodo.hasta.month
        - periodo.desde.month
    )
    if meses < 1:
        return Simulador(no_calculable="tus estados cubren menos de un mes")
    vistas, sin_vista = _vistas(meses)
    return Simulador(
        periodo=f"del {fecha_corta(periodo.desde)} al {fecha_corta(periodo.hasta)}",
        vistas=vistas,
        sin_vista=sin_vista,
        palancas=resultado.simulador,
        advertencias=_advertencias(resultado),
    )


# ---------------------------------------------------------------------------
# La página: un archivo, datos embebidos + simulador.js
# ---------------------------------------------------------------------------

_ESTILO = """
:root { --fondo:#f7f6f2; --tinta:#1f2328; --suave:#6b7075; --linea:#d9d6cc;
  --tarjeta:#ffffff; --bien:#1f7a4d; --mal:#b3261e; --aviso:#8a5a00; --gris:#a3a3a3; }
@media (prefers-color-scheme: dark) { :root { --fondo:#16181b; --tinta:#e8e6e1;
  --suave:#9aa0a6; --linea:#33373c; --tarjeta:#1f2226; --bien:#5cc28f; --mal:#ff8a80;
  --aviso:#f0b43c; --gris:#5f6368; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--fondo); color:var(--tinta);
  font:16px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width:960px; margin:0 auto; padding:24px 16px 48px; }
h1 { font-size:1.6rem; margin:0 0 4px; } .sub { color:var(--suave); margin:0 0 20px; }
.vistas { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; }
.vistas button { border:1px solid var(--linea); background:var(--tarjeta); color:var(--tinta);
  padding:6px 14px; border-radius:999px; cursor:pointer; font:inherit; }
.vistas button[aria-pressed="true"] { background:var(--tinta); color:var(--fondo); }
.tarjetas { display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px; }
.tarjeta { background:var(--tarjeta); border:1px solid var(--linea); border-radius:12px; padding:14px; }
.tarjeta h2 { font-size:.85rem; font-weight:600; color:var(--suave); margin:0 0 6px; }
.tarjeta .cifra { font-size:1.5rem; font-variant-numeric:tabular-nums; font-weight:650; }
.tarjeta .nota { font-size:.8rem; color:var(--suave); margin-top:4px; }
.pos { color:var(--bien); } .neg { color:var(--mal); }
.palancas { margin-top:20px; display:grid; gap:10px; }
.palanca { background:var(--tarjeta); border:1px solid var(--linea); border-radius:12px; padding:12px 14px;
  display:grid; grid-template-columns:minmax(140px, 1fr) minmax(160px, 2fr) auto; gap:8px 14px; align-items:center; }
.palanca .nombre { font-weight:600; } .palanca .mejora, .palanca .razon { font-size:.85rem; color:var(--suave); }
.palanca input[type=range] { width:100%; }
.palanca .mov { font-variant-numeric:tabular-nums; min-width:5.5em; text-align:right; }
.palanca .lados { grid-column:1 / -1; font-size:.85rem; color:var(--suave); font-variant-numeric:tabular-nums; }
.palanca.gris { opacity:.6; } .palanca.gris .nombre { color:var(--gris); }
.avisos { margin-top:16px; display:grid; gap:8px; }
.aviso { border-left:4px solid var(--aviso); background:var(--tarjeta); padding:10px 12px; border-radius:6px; }
.aviso b { color:var(--aviso); }
.pie { margin-top:24px; font-size:.8rem; color:var(--suave); }
@media (max-width:560px) { .palanca { grid-template-columns:1fr; } .palanca .mov { text-align:left; } }
"""

_PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Simulador de palancas</title>
<style>{estilo}</style>
</head>
<body>
<main>
<h1>Simulador de las 7 palancas</h1>
<p class="sub">Tus estados {periodo}. Todas las cifras son {rotulo}.</p>
{cuerpo}
</main>
<script id="datos-simulador" type="application/json">{datos}</script>
<script>
{js}
</script>
</body>
</html>
"""

_CUERPO = """<div class="vistas" id="vistas" role="group" aria-label="Vista"></div>
<div class="tarjetas">
  <div class="tarjeta"><h2>Utilidad <span data-vista-nombre></span> ({rotulo})</h2>
    <div class="cifra" id="utilidad">0.00</div>
    <div class="nota">Más venta, menos costo o gasto. Se repite cada periodo.</div></div>
  <div class="tarjeta"><h2>Efectivo <span data-vista-nombre></span> por la mejora ({rotulo})</h2>
    <div class="cifra" id="efectivo-cada-periodo">0.00</div>
    <div class="nota">Lo mismo que la utilidad: entra cada periodo.</div></div>
  <div class="tarjeta"><h2>Una sola vez en clientes, inventario y proveedores ({rotulo})</h2>
    <div class="cifra" id="una-vez">0.00</div>
    <div class="nota">Pasa una vez. No se reparte entre los meses ni se repite.</div></div>
  <div class="tarjeta"><h2>Efectivo total del periodo ({rotulo})</h2>
    <div class="cifra" id="efectivo-total">0.00</div>
    <div class="nota" id="nota-total">Cada periodo + una sola vez.</div></div>
</div>
<div class="avisos" id="avisos"></div>
<div class="palancas" id="palancas"></div>
<p class="pie">Según el curso de cash que vimos. ESCALA calcula los coeficientes con tus estados;
esta página sólo multiplica tu movimiento por ellos. {sin_vista}</p>"""


def pagina(sim: Simulador) -> str:
    """HTML de un archivo: no necesita servidor."""
    datos = sim.model_dump_json().replace("</", "<\\/")
    if sim.no_calculable is not None:
        cuerpo = f'<p class="aviso">No calculable: {html.escape(sim.no_calculable)}</p>'
    else:
        cuerpo = _CUERPO.format(
            rotulo=ROTULO, sin_vista=html.escape(" ".join(sim.sin_vista))
        )
    return _PLANTILLA.format(
        estilo=_ESTILO,
        periodo=html.escape(sim.periodo),
        rotulo=ROTULO,
        cuerpo=cuerpo,
        datos=datos,
        js=JS.read_text(encoding="utf-8"),
    )


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
    """``python -m escala_server.cash.simulador <estados-revisados.json> <salida.html>``."""
    argumentos = list(sys.argv[1:] if argv is None else argv)
    if len(argumentos) != 2:
        return _no(
            "uso: python -m escala_server.cash.simulador <estados-revisados.json> <salida.html>"
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
    sim = simulador_de(calcular_curso(estados))
    if sim.no_calculable is not None:
        return _no(sim.no_calculable)
    salida = Path(argumentos[1])
    salida.write_text(pagina(sim), encoding="utf-8")
    _imprime(json.dumps({"pagina": str(salida)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
