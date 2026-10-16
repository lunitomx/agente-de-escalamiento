"""Panel «Tu perfil ideal» (S86.21).

Según el curso de cash que vimos (F3b.1 y la lámina de perfil ideal): el dueño
pone sus límites ideal / regular / malo para seis indicadores y ve un semáforo
con su meta y su distancia. Los límites son del dueño; el ejemplo del curso
(versión B) sólo se ofrece como ejemplo.

Python calcula y decide los colores (``perfil.atender``, con pruebas). Esta
página sólo pinta: cada número lleva su «sale de:» y no trae scripts que hagan
cuentas. Sin los seis límites no hay página: ESCALA pregunta primero.

Entrada::

    python -m escala_server.cash.panel_perfil --empresa NOMBRE --estados E.json
        [--responde CLAVE=VALOR ...] [--guardar sí] [--html salida.html]
        [--carpeta work/cash] [--conversacion RUTA] [--hoy AAAA-MM-DD]

Entre mensajes la plática vive en un borrador privado
(``~/.escala/borradores/<empresa>-perfil.json``). Los límites se guardan en
``work/cash/<empresa>/perfil-ideal.json`` sólo con ``--guardar sí``.
"""

from __future__ import annotations

import argparse
from datetime import date
import html
import json
from pathlib import Path
import sys
from typing import Sequence

from pydantic import ValidationError

from escala_server.cash.curso import BaseDeDias, EstadosRevisados
from escala_server.cash.escenario import (
    CARPETA,
    EscrituraInsegura,
    carpeta_de,
    escribir_privado,
)
from escala_server.cash.perfil import (
    DeUnPeso,
    PasoDelPerfil,
    PlaticaDelPerfil,
    Tarjeta,
    atender,
    es_si,
    guardar_perfil,
    leer_guardado,
    porcentajes_de_un_peso,
    valores_del_perfil,
)
from escala_server.financial.formatos import fecha_corta, formato_monto

USO = (
    "uso: python -m escala_server.cash.panel_perfil --empresa NOMBRE --estados E.json "
    "[--responde CLAVE=VALOR ...] [--guardar sí] [--html salida.html]"
)

_ESTILO = """
:root { --fondo:#f7f6f2; --tinta:#1f2328; --suave:#6b7075; --linea:#d9d6cc; --tarjeta:#ffffff;
  --verde:#1f7a4d; --amarillo:#a06a00; --rojo:#b3261e; --gris:#6b7075; --aviso:#8a5a00; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --fondo:#16181b;
  --tinta:#e8e6e1; --suave:#9aa0a6; --linea:#33373c; --tarjeta:#1f2226; --verde:#5cc28f;
  --amarillo:#f0b43c; --rojo:#ff8a80; --gris:#9aa0a6; --aviso:#f0b43c; } }
:root[data-theme="dark"] { --fondo:#16181b; --tinta:#e8e6e1; --suave:#9aa0a6; --linea:#33373c;
  --tarjeta:#1f2226; --verde:#5cc28f; --amarillo:#f0b43c; --rojo:#ff8a80; --gris:#9aa0a6; --aviso:#f0b43c; }
* { box-sizing:border-box; }
body { margin:0; background:var(--fondo); color:var(--tinta);
  font:16px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width:960px; margin:0 auto; padding:24px 16px 48px; }
h1 { font-size:1.6rem; margin:0 0 4px; } h2 { font-size:1.15rem; margin:28px 0 10px; }
.sub { color:var(--suave); margin:0 0 16px; }
.avisos { display:grid; gap:8px; margin-bottom:16px; }
.aviso { border-left:4px solid var(--aviso); background:var(--tarjeta); padding:10px 12px; border-radius:6px; }
.tarjetas { display:grid; grid-template-columns:repeat(auto-fit, minmax(270px, 1fr)); gap:12px; }
.tarjeta { background:var(--tarjeta); border:1px solid var(--linea); border-top:8px solid var(--gris);
  border-radius:12px; padding:14px; }
.tarjeta.verde { border-top-color:var(--verde); } .tarjeta.amarillo { border-top-color:var(--amarillo); }
.tarjeta.rojo { border-top-color:var(--rojo); }
.tarjeta h3 { font-size:1rem; margin:0 0 6px; }
.nivel { display:inline-block; font-size:.85rem; font-weight:650; margin-bottom:6px; }
.verde .nivel { color:var(--verde); } .amarillo .nivel { color:var(--amarillo); } .rojo .nivel { color:var(--rojo); }
.cifra { font-size:1.6rem; font-weight:650; font-variant-numeric:tabular-nums; }
.dato { margin-top:10px; font-size:.95rem; }
.razon, .porque, .limites { font-size:.85rem; color:var(--suave); margin-top:8px; }
.sale { font-size:.75rem; color:var(--suave); margin-top:2px; overflow-wrap:anywhere; }
table { width:100%; border-collapse:collapse; background:var(--tarjeta); border:1px solid var(--linea);
  border-radius:12px; overflow:hidden; }
td { padding:8px 12px; border-top:1px solid var(--linea); vertical-align:top; }
td.num { text-align:right; font-variant-numeric:tabular-nums; font-weight:600; white-space:nowrap; }
.nota { font-size:.85rem; color:var(--suave); margin-top:8px; }
.pie { margin-top:28px; font-size:.8rem; color:var(--suave); }
"""

_PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tu perfil ideal</title>
<style>{estilo}</style>
</head>
<body>
<main>
<h1>Tu perfil ideal</h1>
<p class="sub">Tu semáforo con tus límites. El color usa el valor sin redondear.</p>
{cuerpo}
<p class="pie">Según el curso de cash que vimos. ESCALA calcula cada número con tus estados
y los colores con tus límites; esta página sólo los muestra.</p>
</main>
<script id="datos-perfil" type="application/json">{datos}</script>
</body>
</html>
"""


def _e(texto: str) -> str:
    return html.escape(texto)


def _sale_de(origen: str) -> str:
    return origen if origen.startswith("sale de:") else f"sale de: {origen}"


def _con_unidad(tarjeta: Tarjeta, mostrado: str) -> str:
    return f"{mostrado}%" if tarjeta.unidad == "%" else f"{mostrado} días"


def _tarjeta(tarjeta: Tarjeta) -> str:
    color = tarjeta.color or "gris"
    titulo = f"<h3>{_e(tarjeta.nombre)}</h3>"
    meta = (
        f'<div class="dato">Tu ideal: {_e(_con_unidad(tarjeta, format(tarjeta.meta.normalize(), "f")))}</div>'
        f'<div class="sale">{_e(_sale_de(tarjeta.origen_meta))}</div>'
    )
    limites = f'<div class="limites">{_e(tarjeta.texto_limites)}</div>'
    if tarjeta.valor is None or tarjeta.color is None:
        razon = tarjeta.razon or "no calculable"
        cuerpo = (
            '<div class="nivel">sin color</div>'
            f'<div class="razon">No calculable: {_e(razon)}</div>{meta}{limites}'
        )
    else:
        valor = tarjeta.valor
        cuerpo = (
            f'<div class="nivel">{_e(tarjeta.color)} · {_e(tarjeta.nivel or "")}</div>'
            f'<div class="cifra">{_e(_con_unidad(tarjeta, formato_monto(valor.mostrado)))}</div>'
            f'<div class="sale">{_e(_sale_de(valor.origen))}</div>'
            f"{meta}"
            f'<div class="dato">{_e(tarjeta.texto_distancia)}</div>'
            f'<div class="sale">{_e(_sale_de(tarjeta.origen_distancia))}</div>'
            f"{limites}"
            f'<div class="porque">{_e(tarjeta.por_que or "")}</div>'
        )
    return f'<section class="tarjeta {color}" id="{tarjeta.clave}">{titulo}{cuerpo}</section>'


def _de_un_peso(peso: DeUnPeso | None) -> str:
    if peso is None:
        return ""
    titulo = "<h2>De cada peso que vendes</h2>"
    if peso.no_calculable is not None:
        return f'{titulo}<div class="aviso">No calculable: {_e(peso.no_calculable)}</div>'
    cuando = f'<p class="sub">Al {_e(fecha_corta(peso.fecha))}.</p>' if peso.fecha else ""
    filas = "".join(
        f"<tr><td>{_e(parte.nombre)}<div class=\"sale\">{_e(_sale_de(parte.origen))}</div></td>"
        f'<td class="num">{_e(formato_monto(parte.mostrado))}%</td></tr>'
        for parte in peso.partes
    )
    nota = f'<p class="nota">{_e(peso.nota_fiscal)}</p>' if peso.nota_fiscal else ""
    return f"{titulo}{cuando}<table>{filas}</table>{nota}"


def _avisos(paso: PasoDelPerfil) -> str:
    cajas = "".join(f'<div class="aviso">{_e(aviso)}</div>' for aviso in paso.avisos)
    return f'<div class="avisos">{cajas}</div>' if cajas else ""


def pagina(paso: PasoDelPerfil) -> str:
    """HTML de un archivo. Sin los seis límites no hay página: ESCALA pregunta primero."""
    if not paso.pintar or not paso.tarjetas:
        raise ValueError("faltan límites: ESCALA pregunta antes de pintar")
    tarjetas = "".join(_tarjeta(t) for t in paso.tarjetas)
    cuerpo = f'{_avisos(paso)}<div class="tarjetas">{tarjetas}</div>{_de_un_peso(paso.de_un_peso)}'
    datos = paso.model_dump_json().replace("</", "<\\/")
    return _PLANTILLA.format(estilo=_ESTILO, cuerpo=cuerpo, datos=datos)


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


def _argumentos() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="escala_server.cash.panel_perfil",
        description="Tu perfil ideal: tus límites y tu semáforo.",
        exit_on_error=False,
    )
    parser.add_argument("--empresa", required=True)
    parser.add_argument("--estados", required=True)
    parser.add_argument("--responde", action="append", default=[])
    parser.add_argument("--guardar")
    parser.add_argument("--html")
    parser.add_argument("--carpeta", default=str(CARPETA))
    parser.add_argument("--conversacion")
    parser.add_argument("--hoy")
    return parser


def ruta_del_borrador(empresa: str) -> Path:
    """La plática del perfil entre mensajes: privada del usuario."""
    return Path.home() / ".escala" / "borradores" / f"{carpeta_de(empresa)}-perfil.json"


def _lee_platica(ruta: Path, empresa: str) -> PlaticaDelPerfil | str:
    if ruta.is_symlink():
        return f"{ruta} es un enlace simbólico; no leo a través de un enlace"
    if not ruta.exists():
        return PlaticaDelPerfil(empresa=empresa)
    try:
        return PlaticaDelPerfil.model_validate_json(ruta.read_text(encoding="utf-8"))
    except (OSError, ValidationError):
        return f"no pude leer la plática del perfil en {ruta}"


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _argumentos().parse_args(list(sys.argv[1:] if argv is None else argv))
    except (argparse.ArgumentError, SystemExit):
        return _no(USO)
    try:
        hoy = date.fromisoformat(args.hoy) if args.hoy else date.today()
    except ValueError:
        return _no(f"la fecha «{args.hoy}» no es AAAA-MM-DD")
    empresa: str = args.empresa
    try:
        texto = Path(args.estados).read_text(encoding="utf-8")
    except OSError:
        return _no(f"no pude leer el archivo {args.estados}")
    try:
        estados = EstadosRevisados.model_validate_json(texto)
    except ValidationError:
        return _no(
            "el archivo no trae estados revisados por ESCALA "
            "(la revisión del balance y el estado de resultados)"
        )
    carpeta = Path(args.carpeta)
    guardado = leer_guardado(empresa, carpeta=carpeta)
    if isinstance(guardado, str):
        return _no(guardado)
    trabajo = Path(args.conversacion) if args.conversacion else ruta_del_borrador(empresa)
    platica = _lee_platica(trabajo, empresa)
    if isinstance(platica, str):
        return _no(platica)
    respuestas = dict(platica.respuestas)
    for respuesta in args.responde:
        clave, igual, valor = str(respuesta).partition("=")
        if not igual:
            return _no(f"la respuesta «{respuesta}» no trae CLAVE=VALOR")
        respuestas[clave.strip()] = valor.strip()
    platica = PlaticaDelPerfil(empresa=empresa, respuestas=respuestas)
    paso = atender(
        platica,
        valores_del_perfil(estados, BaseDeDias.de(estados.respuestas)),
        porcentajes_de_un_peso(estados),
        guardado=guardado,
    )
    ruta_guardada: Path | None = None
    try:
        escribir_privado(
            trabajo, platica.model_dump_json(indent=2), carpeta_privada=args.conversacion is None
        )
        if es_si(args.guardar):
            ruta_guardada = guardar_perfil(paso, empresa, carpeta=carpeta, hoy=hoy)
    except EscrituraInsegura as error:
        return _no(str(error))
    if ruta_guardada is not None:
        partes = [p for p in paso.mensaje.split("\n\n") if not _pide_guardar(p)]
        partes.append(
            f"Guardé tus límites en {ruta_guardada.as_posix()}. "
            "La próxima vez pinto con ellos sin volver a preguntar."
        )
        paso = paso.model_copy(update={"mensaje": "\n\n".join(partes), "pide_guardar": False})
    salida_html: str | None = None
    if args.html and paso.pintar:
        destino = Path(args.html)
        destino.write_text(pagina(paso), encoding="utf-8")
        salida_html = destino.as_posix()
    salida = json.loads(paso.model_dump_json())
    salida["guardado"] = ruta_guardada.as_posix() if ruta_guardada is not None else None
    salida["pagina"] = salida_html
    salida["conversacion"] = trabajo.as_posix()
    _imprime(json.dumps(salida, ensure_ascii=False, indent=2))
    return 0


def _pide_guardar(parrafo: str) -> bool:
    return parrafo.startswith(("¿Guardo ", "Si quieres guardar"))


if __name__ == "__main__":
    raise SystemExit(main())
