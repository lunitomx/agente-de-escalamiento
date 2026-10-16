"""S86.34 — El simulador de las 7 palancas como artefacto en Claude.

La página que arma Python (S86.22) tiene que funcionar dentro de un artefacto:
todo en línea, sin red, sin diálogos ni descargas, tema claro y oscuro, legible
a 400 px. Los números siguen saliendo de la calculadora; la página sólo
multiplica.

Publicar es decisión del dueño: las instrucciones piden «sí» y avisan en una
oración que la página lleva sus números y que sólo él la ve hasta que la
comparta. Sin herramienta de artefactos (Codex u otro), se abre en el navegador
como hoy, y el escenario de Python no cambia.
"""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import re
from typing import Any

import pytest

from escala_server.cash import escenario
from escala_server.cash.curso import calcular_curso
from escala_server.cash.simulador import Simulador, pagina, simulador_de
from tests.test_s86_17_escenario_en_paquete import (
    ESTADOS,
    RESPUESTAS,
    _agent_plugin,
    _codex,
)
from tests.test_s86_22_simulador import (
    TODAS_EN_1,
    _d,
    _datos_de_la_pagina,
    _mi_empresa_estados,
    _simula,
)

ROOT = Path(__file__).resolve().parents[1]
PUERTA = ROOT / "escala-skills" / "escala" / "SKILL.md"
FINANZAS = ROOT / "escala-skills" / "escala-cash-finanzas" / "SKILL.md"
AVISO = (
    "Esta página lleva tus números y sólo tú la ves hasta que la compartas. "
    "¿La publico como artefacto?"
)
# Lo único que un artefacto deja cargar de fuera, siempre con versión exacta.
CDN_PERMITIDO = re.compile(
    r"^https://cdnjs\.cloudflare\.com/ajax/libs/[^/]+/\d+\.\d+\.\d+/"
)


@pytest.fixture(scope="module")
def simulador() -> Simulador:
    return simulador_de(calcular_curso(_mi_empresa_estados()))


@pytest.fixture(scope="module")
def html(simulador: Simulador) -> str:
    return pagina(simulador)


def _problemas(pagina_html: str) -> list[str]:
    """Lo que impide que la página funcione dentro de un artefacto."""
    problemas: list[str] = []
    for src in re.findall(
        r"<script\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)", pagina_html, re.I
    ):
        if not CDN_PERMITIDO.match(src):
            problemas.append(f"script de fuera: {src}")
    for link in re.findall(r"<link\b[^>]*>", pagina_html, re.I):
        if "stylesheet" in link.lower() or "preload" in link.lower():
            problemas.append(f"estilo de fuera: {link}")
    if re.search(r"@import|url\(\s*[\"']?https?:", pagina_html, re.I):
        problemas.append("CSS que carga algo de fuera")
    for red in (
        r"\bfetch\s*\(",
        r"XMLHttpRequest",
        r"WebSocket",
        r"EventSource",
        r"sendBeacon",
        r"localhost",
        r"127\.0\.0\.1",
    ):
        if re.search(red, pagina_html):
            problemas.append(f"red: {red}")
    for dialogo in (
        r"\balert\s*\(",
        r"\bconfirm\s*\(",
        r"\bprompt\s*\(",
        r"window\.open",
    ):
        if re.search(dialogo, pagina_html):
            problemas.append(f"diálogo: {dialogo}")
    for descarga in (r"\bdownload\b", r"createObjectURL"):
        if re.search(descarga, pagina_html):
            problemas.append(f"descarga: {descarga}")
    return problemas


# ---------------------------------------------------------------------------
# La página que arma Python
# ---------------------------------------------------------------------------


def test_la_pagina_del_simulador_funciona_en_un_artefacto(html: str) -> None:
    assert _problemas(html) == []
    # Todo en línea: los datos, el estilo y el script.
    assert '<script id="datos-simulador" type="application/json">' in html
    assert "<style>" in html and "SimuladorEscala" in html


@pytest.mark.parametrize(
    ("inyectado", "problema"),
    [
        ('<script src="https://example.com/lib.js"></script>', "script de fuera"),
        (
            '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/latest/d3.js"></script>',
            "script de fuera",
        ),
        ('<link rel="stylesheet" href="https://example.com/a.css">', "estilo de fuera"),
        ("<script>fetch('http://localhost:8000/api')</script>", "red"),
        ("<script>new XMLHttpRequest()</script>", "red"),
        ("<script>alert('hola')</script>", "diálogo"),
        ("<script>confirm('¿seguro?')</script>", "diálogo"),
        ("<script>prompt('precio')</script>", "diálogo"),
        ('<a href="x.csv" download>bajar</a>', "descarga"),
    ],
)
def test_la_revision_atrapa_lo_que_no_funciona(
    html: str, inyectado: str, problema: str
) -> None:
    malo = html.replace("</body>", inyectado + "</body>")
    assert any(p.startswith(problema) for p in _problemas(malo))


def test_cdnjs_con_version_exacta_si_se_permite(html: str) -> None:
    bueno = html.replace(
        "</body>",
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script></body>',
    )
    assert _problemas(bueno) == []


def test_tema_claro_y_oscuro(html: str) -> None:
    assert "color-scheme: light dark" in html
    # El sistema del dueño, salvo que el artefacto fuerce el tema claro.
    oscuro_del_sistema = re.search(
        r"@media \(prefers-color-scheme: dark\) \{\s*:root:not\(\[data-theme=\"light\"\]\) \{([^}]*)\}",
        html,
    )
    forzado = re.search(r":root\[data-theme=\"dark\"\] \{([^}]*)\}", html)
    assert oscuro_del_sistema and forzado
    assert oscuro_del_sistema.group(1) == forzado.group(1)
    assert "--fondo:#16181b" in forzado.group(1)
    # El fondo es explícito: no depende del blanco del navegador.
    assert re.search(r"body \{[^}]*background:var\(--fondo\)", html)


def test_se_lee_a_400_px(html: str) -> None:
    assert (
        '<meta name="viewport" content="width=device-width, initial-scale=1">' in html
    )
    # En pantallas angostas cada palanca va en una columna.
    angosta = re.search(
        r"@media \(max-width:(\d+)px\) \{ \.palanca \{ grid-template-columns:1fr; \}",
        html,
    )
    assert angosta and int(angosta.group(1)) >= 400
    # Nada con ancho fijo mayor a 400 px (sin contar los máximos).
    fijos = [int(n) for n in re.findall(r"(?<![-\w])(?:min-)?width:\s*(\d+)px", html)]
    assert all(n <= 400 for n in fijos), fijos
    for minimo in re.findall(r"minmax\((\d+)px", html):
        assert int(minimo) <= 368, minimo  # 400 menos 16 px de cada lado


def test_los_numeros_de_mi_empresa_siguen_saliendo_de_python(html: str) -> None:
    [anual] = _simula(
        _datos_de_la_pagina(html), [{"movimientos": TODAS_EN_1, "vista": "anual"}]
    )
    assert _d(anual["efectivo_total"]) == Decimal("1143864.91")
    assert _d(anual["utilidad"]) == Decimal("1010740.66")


# ---------------------------------------------------------------------------
# Las instrucciones que viajan al dueño
# ---------------------------------------------------------------------------


def _plano(texto: str) -> str:
    return re.sub(r"\s+", " ", texto)


def test_finanzas_ofrece_el_artefacto_solo_con_si() -> None:
    texto = _plano(FINANZAS.read_text(encoding="utf-8"))
    assert AVISO in texto
    assert "herramienta para publicar artefactos" in texto
    assert "Sin su «sí» no la publiques" in texto
    assert "panel-simulador-<fecha>.html" in texto
    # Sin la herramienta (Codex u otro asistente), como hoy: el navegador.
    assert "Si no tienes esa herramienta" in texto
    assert "ábrela en su navegador como hoy" in texto


def test_la_puerta_pide_si_antes_de_publicar() -> None:
    texto = _plano(PUERTA.read_text(encoding="utf-8"))
    assert "Publicar una página como artefacto" in texto
    assert AVISO in texto
    assert "sólo si puedes publicar artefactos" in texto


@pytest.mark.parametrize(
    "construir", [_agent_plugin, _codex], ids=["agent-plugin", "codex"]
)
def test_las_instrucciones_viajan_en_los_paquetes(
    tmp_path: Path, construir: Any
) -> None:
    puerta: Path = construir(tmp_path)
    procedimiento = puerta / "references" / "procedures" / "escala-cash-finanzas.md"
    assert AVISO in _plano(procedimiento.read_text(encoding="utf-8"))
    assert AVISO in _plano((puerta / "SKILL.md").read_text(encoding="utf-8"))


def test_el_escenario_no_ofrece_artefactos(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """La oferta vive en las instrucciones: Codex ve la misma salida que antes."""
    argumentos = [
        "--empresa",
        "Mi Empresa",
        "--archivo",
        str(ESTADOS / "aspel_balance.txt"),
        "--archivo",
        str(ESTADOS / "aspel_resultados.txt"),
        "--carpeta",
        str(tmp_path / "cash"),
        "--conversacion",
        str(tmp_path / "borrador.json"),
        "--hoy",
        "2026-01-31",
    ]
    for respuesta in (*RESPUESTAS, "C6=no"):
        argumentos += ["--responde", respuesta]
    assert escenario.main([*argumentos, "--guardar", "sí"]) == 0
    datos: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert any(
        r.endswith(".html") and "panel-simulador-" in r for r in datos["guardado"]
    )
    assert "artefacto" not in datos["mensaje"].lower()
