"""S86.16 — Ningún procedimiento de cash le pide al modelo que calcule.

Recorre los procedimientos de cash (``escala-skills/escala-cash*``), el agente
``escala-agent/skills/escala-cash`` y su conocimiento. Falla si alguno pide
calcular con las capacidades del modelo, trae límites inventados (CCC > 90,
DSO > 60, margen < 30 %) o rangos por industria. Los que hablan de números
deben mandar a la calculadora y decir qué pasa si falta Python.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from escala_server.cash import PowerOfOneEngine

ROOT = Path(__file__).resolve().parents[1]

PROCEDIMIENTOS = sorted((ROOT / "escala-skills").glob("escala-cash*/SKILL.md"))
AGENTE = sorted((ROOT / "escala-agent" / "skills" / "escala-cash").rglob("*.md"))
CONOCIMIENTO = sorted((ROOT / ".escala" / "knowledge" / "cash").glob("*.md")) + [
    ROOT / ".escala" / "agent" / "sub-agents" / "cash.md"
]
TODOS = PROCEDIMIENTOS + AGENTE + CONOCIMIENTO

# Los que muestran números al dueño: deben mandar a la calculadora.
CON_NUMEROS = [
    ROOT / "escala-skills" / nombre / "SKILL.md"
    for nombre in (
        "escala-cash",
        "escala-cash-ccc",
        "escala-cash-finanzas",
        "escala-cash-power1",
    )
] + [ROOT / "escala-agent" / "skills" / "escala-cash" / "SKILL.md"]

PROHIBIDO: dict[str, str] = {
    "calcular con el modelo": (
        r"capacidades nativas|con (tus|sus) (propias )?capacidades|"
        r"calcula(s|r)? con (tus|sus) propias|eres el motor|"
        r"calcula(s|r)? usando las f[oó]rmulas|aplica las f[oó]rmulas|"
        r"usas tu propia inteligencia"
    ),
    "límite inventado de días": r"\b(ccc|dso|dio|dpo|ciclo)\s*[<>]\s*-?\d|[<>]\s*\d+\s*d(í|i)as|\|\s*[<>]\s*\d+\s*d\b",
    "límite inventado de margen": r"margen[^\n]*[<>]\s*\d+\s*%",
    "rangos por industria": r"(benchmarks?|rangos?) por industria|\|\s*industria\s*\||^##+\s*benchmarks",
    "anualizar ×12": r"multiplica por 12|×\s*12\b",
}


def problemas(texto: str) -> list[str]:
    encontrados: list[str] = []
    for nombre, patron in PROHIBIDO.items():
        for coincidencia in re.finditer(
            patron, texto, flags=re.IGNORECASE | re.MULTILINE
        ):
            encontrados.append(f"{nombre}: «{coincidencia.group(0)}»")
    return encontrados


def test_hay_procedimientos_que_revisar() -> None:
    assert len(PROCEDIMIENTOS) >= 5
    assert AGENTE
    assert len(CONOCIMIENTO) >= 20


@pytest.mark.parametrize(
    "ejemplo",
    [
        "Usa las capacidades nativas de Claude Code para hacer cálculos.",
        "- Si CCC > 90 días: ALERTA",
        "- Si DSO > 60 días: ALERTA",
        "- Si Margen Bruto < 30%: ALERTA",
        "| > 60d | Peligro |",
        "## Benchmarks por Industria",
        "| Industria | Margen | CCC |",
        "**Tú (el LLM) eres el motor.**",
        "Si te dio datos mensuales, multiplica por 12.",
    ],
)
def test_el_revisor_atrapa_lo_prohibido(ejemplo: str) -> None:
    assert problemas(ejemplo)


@pytest.mark.parametrize("ruta", TODOS, ids=lambda ruta: str(ruta.relative_to(ROOT)))
def test_ningun_procedimiento_calcula_con_el_modelo(ruta: Path) -> None:
    assert problemas(ruta.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(
    "ruta", CON_NUMEROS, ids=lambda ruta: str(ruta.relative_to(ROOT))
)
def test_los_numeros_salen_de_la_calculadora(ruta: Path) -> None:
    texto = ruta.read_text(encoding="utf-8")
    assert "escala_server/cash/calcular.py" in texto
    assert "No voy a hacer las cuentas de memoria." in texto


def test_la_puerta_manda_a_la_calculadora() -> None:
    puerta = (ROOT / "escala-skills" / "escala" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "references/calculadora/escala_server/cash/calcular.py" in puerta
    assert "No voy a hacer las cuentas de memoria." in puerta


def test_el_motor_no_trae_rangos_por_industria() -> None:
    assert not hasattr(PowerOfOneEngine, "benchmark_by_industry")
