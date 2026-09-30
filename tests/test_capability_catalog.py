"""E56 contracts for one public orchestrator and a closed skill catalog."""

from __future__ import annotations

from pathlib import Path

import pytest

from escala_server.capabilities import (
    CatalogError,
    load_capability_catalog,
    load_legacy_aliases,
    public_install_skills,
    route_request,
    validate_catalog_sources,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "escala-skills" / "catalog.yaml"


def test_catalog_covers_every_canonical_skill_from_one_source() -> None:
    catalog = load_capability_catalog(CATALOG_PATH)

    assert validate_catalog_sources(catalog) == ()
    assert catalog.baseline == {"canonical_procedures": 65, "legacy_aliases": 39}
    assert len(catalog.capabilities) == 66  # 65 procedures plus public ESCALA.


def test_default_installation_exposes_only_the_public_front_door() -> None:
    catalog = load_capability_catalog(CATALOG_PATH)

    assert public_install_skills(catalog) == ("escala",)


def test_every_tracked_legacy_skill_has_one_explicit_alias() -> None:
    catalog = load_capability_catalog(CATALOG_PATH)
    legacy_sources = {
        path.parent.name
        for path in (ROOT / ".claude/legacy-skills").glob("scaleup-*/SKILL.md")
    }

    aliases = load_legacy_aliases(catalog)
    assert {alias.alias for alias in aliases} == legacy_sources
    assert len(aliases) == 39


@pytest.mark.parametrize(
    ("user_request", "capability"),
    [
        ("No tengo efectivo y me preocupa cobrar", "escala-cash"),
        ("Mi equipo no sabe quién decide", "escala-people"),
        ("La competencia nos está ganando", "escala-strategy"),
        ("¿Cómo está mi mercado?", "escala-strategy"),
        ("¿Cómo cobran mis competidores?", "escala-strategy"),
        ("¿Qué tendencias vienen para mi sector?", "escala-strategy"),
        ("¿Cuánto cobra mi competencia?", "escala-strategy"),
        ("Quiero un benchmark de mi oferta", "escala-strategy"),
        # Cash is evaluated first: "ventas" wins, and Cash can offer research.
        ("benchmark de ventas", "escala-cash"),
        ("Necesito ayuda con mi marketing", "escala-strategy"),
        ("No me llegan prospectos", "escala-strategy"),
        ("¿Cómo consigo más prospectos?", "escala-strategy"),
        # Cash is still evaluated first: sales words stay in Cash.
        ("marketing para subir mis ventas", "escala-cash"),
        # E84: sales-pain phrases reach Strategy, where the journey check runs.
        ("Mucha gente pregunta por WhatsApp pero pocos compran", "escala-strategy"),
        ("Me preguntan mucho pero no me compran", "escala-strategy"),
        ("Nadie me compra", "escala-strategy"),
        ("Compran una vez y no regresan", "escala-strategy"),
        ("No vuelven después de la primera compra", "escala-strategy"),
        ("Se me van los clientes", "escala-strategy"),
        ("No vendo nada este mes", "escala-strategy"),
        ("Vendo poco", "escala-strategy"),
        # ...and real cash phrases stay in Cash.
        ("No me pagan a tiempo", "escala-cash"),
        ("No me alcanza para la nómina", "escala-cash"),
        ("No me alcanza el dinero", "escala-cash"),
        ("No vendo y no me alcanza para pagar", "escala-cash"),
        ("Sólo apagamos incendios en la operación", "escala-execution"),
        ("¿Cómo vamos?", "escala-diagnose"),
        ("Quiero retomar lo que dejamos pendiente", "escala-welcome"),
        ("No sé por dónde empezar", "escala-welcome"),
    ],
)
def test_natural_requests_choose_an_explainable_first_capability(
    user_request: str, capability: str
) -> None:
    result = route_request(user_request)

    assert result.capability_id == capability
    assert result.reason.startswith("intent:")
    assert result.message


def test_legacy_rockefeller_alias_routes_to_the_canonical_execution_habits() -> None:
    result = route_request("/scaleup-execution-rockefeller")

    assert result.capability_id == "escala-execution-habits"
    assert result.reason == "legacy_alias"
    assert result.legacy_alias == "scaleup-execution-rockefeller"
    assert "consolidó" in result.message


def test_catalog_fails_closed_when_missing() -> None:
    with pytest.raises(CatalogError, match="catalog_unavailable"):
        load_capability_catalog(ROOT / "missing.yaml")


def test_public_skill_references_the_canonical_catalog_and_hides_commands() -> None:
    skill = (ROOT / "escala-skills/escala/SKILL.md").read_text(encoding="utf-8")

    assert "../../capabilities/mvp/catalog.json" in skill
    assert "No le pidas" in skill
    assert "slash-command" in skill
