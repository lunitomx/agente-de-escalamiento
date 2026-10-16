"""S86.17 — «Analiza mi balance general y mi estado de resultados» usa la entrada.

La puerta, ``escala-cash`` y ``escala-cash-finanzas`` mandan esa frase al
escenario (``calcular.py escenario``). El modelo muestra el mensaje tal cual,
repite las preguntas como vienen, nunca escribe números y sólo guarda con «sí».
"""

from __future__ import annotations

from pathlib import Path

import pytest

from escala_server.capabilities import route_request

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "escala-skills"
PUERTA = SKILLS / "escala" / "SKILL.md"
CASH = SKILLS / "escala-cash" / "SKILL.md"
FINANZAS = SKILLS / "escala-cash-finanzas" / "SKILL.md"
ENTRADA = "escala_server/cash/calcular.py escenario"


def _texto(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "frase",
    [
        "analiza mi balance general y mi estado de resultados",
        "analiza mi balance general",
        "te paso mi balance general",
    ],
)
def test_la_frase_llega_a_cash(frase: str) -> None:
    assert route_request(frase).capability_id == "escala-cash"


@pytest.mark.parametrize(
    "ruta", [PUERTA, CASH, FINANZAS], ids=["puerta", "cash", "finanzas"]
)
def test_usan_la_entrada_del_escenario(ruta: Path) -> None:
    texto = _texto(ruta)
    assert ENTRADA in texto
    assert "analiza mi balance general y mi estado de resultados" in texto


@pytest.mark.parametrize("ruta", [PUERTA, FINANZAS], ids=["puerta", "finanzas"])
def test_el_modelo_no_escribe_numeros_y_repite_las_preguntas(ruta: Path) -> None:
    texto = _texto(ruta)
    assert "`mensaje` tal cual" in texto
    assert "Nunca escribas un número que no venga en `mensaje`" in texto
    assert "--guardar sí" in texto


def test_cash_manda_los_estados_a_finanzas() -> None:
    assert "balance general" in _texto(CASH).split("### Step 4")[0]


def test_finanzas_no_guarda_sin_si() -> None:
    texto = _texto(FINANZAS)
    assert "work/cash/power-of-one.md" not in texto
    assert "Sin su «sí» no guardes nada" in texto
    # El escenario lee, pregunta y revisa: el modelo ya no arma la lista a mano.
    assert "escala_server.financial.lector" not in texto
    assert "--responde" in texto
