"""Páginas que el programa local ya no sirve, con un aviso en vez de un 404 mudo.

S86.33: el tablero viejo del poder del uno sumaba flujo + utilidad por palanca.
El poder del uno vive ahora en el simulador del recorrido de cash.
"""

from __future__ import annotations

_AVISO_PODER_DEL_UNO = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>El poder del uno se mudó | ESCALA</title>
<style>
body { font-family: system-ui, sans-serif; max-width: 40rem; margin: 3rem auto;
       padding: 0 1rem; line-height: 1.5; color: #1e293b; }
code { background: #f1f5f9; padding: 0 .25rem; border-radius: .25rem; }
</style>
</head>
<body>
<h1>El poder del uno ahora vive en el recorrido de cash</h1>
<p>Este tablero ya no existe. Sumaba de más: juntaba efectivo y utilidad en
cada palanca.</p>
<p>Ahora lo ves en el simulador del recorrido de cash. Ahí mueves cada palanca
con los números de tus estados, ya revisados.</p>
<p>Para pedirlo:</p>
<ol>
<li>En Claude, escribe <code>/escala-cash</code> o dile «quiero ver el poder del uno».</li>
<li>ESCALA lee tus estados, te pregunta lo que falte y calcula.</li>
<li>Al final te ofrece guardar el simulador. Con tu «sí» queda en la carpeta
de cash de tu empresa como <code>panel-simulador</code> con la fecha de hoy.</li>
</ol>
<p><a href="/">Volver al panel de control</a></p>
</body>
</html>
"""

PAGINAS_RETIRADAS: dict[str, str] = {
    "/dashboards/cash/power-of-one.html": _AVISO_PODER_DEL_UNO,
}


def pagina_retirada(ruta: str) -> str | None:
    """El aviso de una página que ya no existe, o ``None`` si la ruta no es una de ellas."""

    return PAGINAS_RETIRADAS.get(ruta)
