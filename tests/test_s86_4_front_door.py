"""S86.4: the front door reaches every procedure ESCALA keeps.

The door reads one list, ``escala-skills/catalog.yaml``. A procedure is reachable
from an owner phrase when ``route_request`` sends the phrase to it, or sends it
to an area entry (cash, people, strategy, execution) whose next-step table names
the procedure in a row that mentions what the owner said (``hint``). That is how
research and the customer journey already pass through Strategy (E83, E84).

Every phrase below is synthetic.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pytest

from escala_server.capabilities import load_capability_catalog, route_request

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "escala-skills"
CATALOG_PATH = SKILLS / "catalog.yaml"

# procedure -> (owner phrase, hint in the area-entry row; None = direct route)
PHRASES: dict[str, tuple[str, str | None]] = {
    "escala-board": ("Quiero que mi junta de consejo revise todo", None),
    "escala-bugreport": ("Quiero reportar un problema", None),
    "escala-cash": ("No me alcanza el dinero", None),
    "escala-cash-acceleration": (
        "Quiero que el dinero me llegue más rápido",
        "más rápido",
    ),
    "escala-cash-ccc": ("No me pagan a tiempo", "te paga"),
    "escala-cash-finanzas": ("Te paso mis estados financieros", "estados financieros"),
    "escala-cash-power1": ("¿Cuánto dinero libero si cobro antes?", "liberas"),
    "escala-close": ("Terminamos por hoy", None),
    "escala-dashboard": ("Tablero de mis ventas", None),
    "escala-diagnose": ("¿Cómo vamos?", None),
    "escala-discover": ("No sé dónde están mis datos", None),
    "escala-evidence": ("¿En qué te basas para decir eso?", None),
    "escala-execution": ("Sólo apagamos incendios en la operación", None),
    "escala-execution-habits": (
        "En mi operación las cosas no se cumplen",
        "se cumplen",
    ),
    "escala-execution-pizarron": ("Te mando la foto del pizarrón", "pizarrón"),
    "escala-execution-priorities": (
        "¿Cuál es la prioridad de este trimestre?",
        "trimestre",
    ),
    "escala-execution-rhythms": ("Mis reuniones no sirven", "juntas"),
    "escala-execution-tracker": (
        "Prepárame para mi junta del grupo",
        "junta del grupo",
    ),
    "escala-export": ("Quiero exportar mi plan", None),
    "escala-goal": ("Quiero fijar mi meta del año", None),
    "escala-health": ("Revisa la instalación de ESCALA", None),
    "escala-level": ("Ya conozco el método, ve más rápido", None),
    "escala-memory": ("¿Qué recuerdas de mi empresa?", None),
    "escala-people": ("Mi equipo no sabe quién decide", None),
    "escala-people-fac": (
        "En mi equipo nadie sabe quién es responsable de qué",
        "responsable",
    ),
    "escala-people-organigrama": ("Te paso mi organigrama", "organigrama"),
    "escala-people-topgrading": ("Necesito contratar a alguien", "contratar"),
    "escala-people-values": (
        "Mi equipo no tiene claro lo que no se negocia",
        "no se negocia",
    ),
    "escala-progress": ("¿Cuánto he avanzado?", None),
    "escala-pulse": ("Quiero tomar el pulso de mi empresa", None),
    "escala-rhythm-quarterly": ("Prepara mi junta trimestral", "trimestral"),
    "escala-rhythm-weekly": ("Prepara mi junta semanal", "semanal"),
    "escala-strategy": ("La competencia nos está ganando", None),
    "escala-strategy-7strata": (
        "¿Qué me hace distinto de mi competencia?",
        "distinto",
    ),
    "escala-strategy-journey": ("Bajaron mis ventas", "ventas"),
    "escala-strategy-opsp": ("Quiero mi estrategia en una página", "página"),
    "escala-strategy-research": ("¿Cuánto cobra mi competencia?", "competencia"),
    "escala-strategy-swt": ("¿Cuáles son mis fortalezas y debilidades?", "fortalezas"),
    "escala-update": ("Actualiza ESCALA", None),
    "escala-welcome": ("Quiero retomar lo que dejamos pendiente", None),
    "escala-worksheet": ("Quiero llenar una hoja de trabajo", None),
}

AREA_ENTRIES = {"escala-cash", "escala-people", "escala-strategy", "escala-execution"}


def _plain(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", ascii_text.lower())


def _handoff_rows(entry: str) -> list[str]:
    """Table rows of an area entry's SKILL.md (its next-step table)."""
    text = (SKILLS / entry / "SKILL.md").read_text(encoding="utf-8")
    return [line for line in text.splitlines() if line.startswith("|")]


def _reaches(phrase: str, procedure: str, hint: str | None) -> bool:
    target = route_request(phrase).capability_id
    if hint is None:
        return target == procedure
    if target not in AREA_ENTRIES:
        return False
    return any(
        f"`{procedure}`" in row and _plain(hint) in _plain(row)
        for row in _handoff_rows(target)
    )


def test_every_keep_procedure_has_an_owner_phrase() -> None:
    catalog = load_capability_catalog(CATALOG_PATH)
    keep = {c.id for c in catalog.capabilities if c.disposition == "keep"}

    assert set(PHRASES) == keep - {"escala"}


@pytest.mark.parametrize(("procedure", "case"), sorted(PHRASES.items()))
def test_keep_procedure_is_reachable_from_the_door(
    procedure: str, case: tuple[str, str | None]
) -> None:
    phrase, hint = case

    assert _reaches(phrase, procedure, hint), (
        f"{phrase!r} -> {route_request(phrase).capability_id}, not {procedure}"
    )


@pytest.mark.parametrize(
    ("phrase", "procedure", "hint"),
    [
        ("Bajaron mis ventas", "escala-strategy", None),
        ("Mis ventas bajaron este mes", "escala-strategy", None),
        ("benchmark de ventas", "escala-strategy", None),
        ("marketing para subir mis ventas", "escala-strategy", None),
        ("Prepárame para mi junta del grupo", "escala-execution-tracker", "junta del grupo"),
        ("Tablero de mis ventas", "escala-dashboard", None),
        ("¿Cuánto cobra mi competencia?", "escala-strategy-research", "competencia"),
        # Real money phrases stay in Cash even when they mention sales.
        ("No vendo y no me alcanza para pagar", "escala-cash", None),
        ("No me pagan mis ventas", "escala-cash", None),
    ],
)
def test_audit_phrases_land_where_the_owner_expects(
    phrase: str, procedure: str, hint: str | None
) -> None:
    assert _reaches(phrase, procedure, hint)


def test_sales_are_strategy_not_cash() -> None:
    """escala/SKILL.md: sólo es Cash si no le alcanza o no le pagan."""
    catalog = load_capability_catalog(CATALOG_PATH)
    routes = {route.id: route for route in catalog.routes}

    assert "ventas" not in routes["cash"].keywords
    assert "ventas" in routes["strategy"].keywords


def test_door_reads_the_single_list_and_says_where_procedures_live() -> None:
    door = (SKILLS / "escala" / "SKILL.md").read_text(encoding="utf-8")

    assert "`escala-skills/catalog.yaml`" in door
    assert "`routes`" in door
    assert "`keep`" in door
    # One line says where the internal procedures live.
    assert "`escala-skills/escala-*/SKILL.md`" in door
    # Only the catalog.json reference ("../../") is relative: the Agent Plugin
    # package rejects any other "../" in the door.
    assert door.count("../") == 2
    # catalog.json stays the adapters' lifecycle contract, referenced once
    # (the plugin and Codex builders rewrite exactly one reference).
    assert door.count("../../capabilities/mvp/catalog.json") == 1
    assert "seis capacidades MVP" in door


@pytest.mark.parametrize(
    "phrase",
    ["Quiero exportar a Estados Unidos", "¿Cómo empiezo a exportar mi producto?"],
)
def test_exporting_as_business_is_not_downloading_the_plan(phrase: str) -> None:
    assert route_request(phrase).capability_id != "escala-export"


@pytest.mark.parametrize(
    "phrase", ["Descargar mi plan", "Quiero exportar mi plan", "Bájame mi plan en PDF"]
)
def test_downloading_the_plan_still_reaches_export(phrase: str) -> None:
    assert route_request(phrase).capability_id == "escala-export"
