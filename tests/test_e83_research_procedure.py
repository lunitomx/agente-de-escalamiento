"""E83 S83.1: research is an internal strategy procedure reached only via ESCALA."""

from __future__ import annotations

import json
from pathlib import Path

from coaching.research.messages import SEARCH_OFF, SWT_ASK
from escala_server.capabilities import load_capability_catalog, public_install_skills
from escala_server.specialist_team import SPECIALIST_CONTRACTS

ROOT = Path(__file__).resolve().parents[1]
PROCEDURE = ROOT / "escala-skills" / "escala-strategy-research" / "SKILL.md"


def _procedure() -> str:
    return PROCEDURE.read_text(encoding="utf-8")


def test_research_is_an_internal_strategy_procedure() -> None:
    catalog = load_capability_catalog(ROOT / "escala-skills" / "catalog.yaml")

    capability = catalog.capability("escala-strategy-research")
    assert capability.visibility == "internal"
    assert capability.owner == "strategy"
    assert "escala-strategy-research" not in public_install_skills(catalog)


def test_procedure_declares_its_name_and_drives_the_flow_module() -> None:
    text = _procedure()

    assert text.startswith("---\n")
    assert "name: escala-strategy-research" in text
    assert "python3 -m coaching.research" in text
    for action in ("frame", "grade", "report", "save"):
        assert f'"action": "{action}"' in text


def test_procedure_carries_the_search_rules_and_the_search_off_line() -> None:
    text = _procedure()

    assert SEARCH_OFF in text
    assert "no el nombre de la plataforma" in text
    assert "abriste la página" in text
    assert "cita literal" in text
    assert "Lo que recuerdas no es fuente" in text
    assert "user_confirmed" in text
    assert "¿Qué decisión quieres tomar con esto?" in text
    assert "ChatGPT" in text  # only to say it is not promised (E85)


def test_strategy_specialist_offers_research_from_its_next_step_table() -> None:
    text = (ROOT / "escala-skills" / "escala-strategy" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "escala-strategy-research" in text


def test_strategy_trigger_is_unchanged() -> None:
    trigger = SPECIALIST_CONTRACTS["strategy"].trigger
    contract = json.loads(
        (ROOT / "adapters/specialists/contract.json").read_text(encoding="utf-8")
    )
    strategy = next(
        s for s in contract["specialists"] if s["decision_area"] == "strategy"
    )

    assert strategy["trigger"] == trigger
    assert "research" not in trigger.lower()


def test_mvp_capability_catalog_is_unchanged_by_research() -> None:
    catalog = (ROOT / "capabilities/mvp/catalog.json").read_text(encoding="utf-8")

    assert "research" not in catalog


def test_procedure_drives_the_comparables_step_of_the_benchmark() -> None:
    """E83 S83.2: comparables confirmed by the owner, one source per cell."""
    text = _procedure()

    assert '"action": "comparables"' in text
    assert '"competitors"' in text
    assert '"named_by_owner"' in text
    assert '"owner_confirmed"' in text
    assert "hasta que diga que sí" in text
    assert "nunca un estimado" in text
    assert "no encontrado" in text
    assert "Máximo cinco negocios" in text
    assert "tipo de negocio" in text  # offer_category carries e.g. "tortillería"
    for dimension in ("precio", "paquetes", "canales", "metricas"):
        assert f'"{dimension}"' in text


DIAGNOSE = ROOT / "escala-skills" / "escala-diagnose" / "SKILL.md"


def test_diagnose_reads_saved_research_through_the_existing_fields() -> None:
    """E83 S83.5: a saved decision enters the next diagnosis as a local fact."""
    text = DIAGNOSE.read_text(encoding="utf-8")

    assert '"action": "diagnosis"' in text
    assert "python3 -m coaching.research" in text
    assert "diagnostic_inputs" in text
    assert "refresh_offers" in text
    for field in ("evidence", "assumptions", "open_questions"):
        assert f"`{field}`" in text
    assert "nunca como hecho" in text  # outside findings stay assumptions


def test_diagnose_offers_research_as_a_text_next_step_without_a_handoff() -> None:
    text = DIAGNOSE.read_text(encoding="utf-8")

    assert "Strategy" in text and "precio o margen" in text
    assert "S75.3" in text  # route choice not built: no simulated hand-off
    assert "escala-strategy-research" not in text  # never named to the owner


def test_research_procedure_says_the_diagnosis_starts_from_the_decision() -> None:
    text = _procedure()

    assert "parto de esta decisión" in text or "siguiente diagnóstico" in text
    assert '"action": "check_sources"' in text
    assert '"pages"' in text
    assert "sin_revisar" in text  # a page not opened is never "verified"
    assert "Claude Desktop tampoco está verificado" in text


def test_codex_search_off_line_is_concrete_only_where_verified() -> None:
    """S83.5 matrix: codex-cli 0.157.1 defaults to cached search (no live page)."""
    text = _procedure()

    assert "codex --search" in text
    assert 'web_search = "live"' in text
    assert "cached" in text


def test_procedure_asks_for_short_findings_that_keep_their_figure() -> None:
    """S83.5: a finding reaches the diagnosis whole or is rejected, never cut."""
    text = _procedure()

    assert "10 palabras o menos, con su cifra" in text
    assert "finding_too_long" in text
    assert "El kilo de tortilla en Puebla cuesta 17 pesos" in text  # good
    assert "ronda los 17 pesos en septiembre" in text  # bad: too long


def test_procedure_drives_the_market_mode() -> None:
    """E83 S83.3: size as a range with method, or not estimable yet."""
    text = _procedure()

    assert "### Paso 3c: Tamaño del mercado" in text
    assert '"market_size"' in text
    for field in ('"low"', '"high"', '"unit"', '"method"', '"assumptions"'):
        assert field in text
    assert '"kind": "no_estimable"' in text and '"missing_data"' in text
    assert '"figures"' in text and "nunca las promedies" in text
    assert "missing_question" in text
    # Where a size comes from (owner decision 2026-09-30): INEGI is not first.
    for where in ("cámaras", "asociaciones", "prensa", "reportes de industria"):
        assert where in text
    assert "INEGI no es la fuente principal" in text
    assert "por confirmar" in text and "tres fuentes" in text
    assert "entrar o crecer" in text  # the decision it ends in


def test_procedure_says_a_type_of_business_is_never_private() -> None:
    text = _procedure()

    assert "tipo de negocio" in text
    assert "nunca cuenta como dato de su empresa" in text
    assert "sólo pasa si esa palabra está en lo que vende" not in text  # pre-S83.3


SWT = ROOT / "escala-skills" / "escala-strategy-swt" / "SKILL.md"


def test_procedure_drives_the_strengths_and_trends_mode() -> None:
    """E83 S83.4: sides against confirmed comparables, dated trends."""
    text = _procedure()

    assert "### Paso 3d: Fortalezas, debilidades y tendencias" in text
    assert '"side"' in text and '"against"' in text
    for side in ('"fortaleza"', '"debilidad"', '"tendencia"'):
        assert side in text
    assert '"base_path"' in text  # frame reuses the current benchmark
    assert "siguen siendo candidatos" in text
    assert "90 días" in text
    assert "escala-strategy-swt" in text and "no escribas otro SWT" in text


def test_swt_brings_outside_evidence_into_the_same_file() -> None:
    """E83 S83.4, D9: one SWT; outside evidence marked, graded, separate."""
    text = SWT.read_text(encoding="utf-8")

    assert SWT_ASK in text
    assert '"action": "swt"' in text
    assert "Según fuentes externas" in text
    assert "Evidencia externa" in text
    assert "por confirmar" in text
    assert text.count("work/strategy/swt-{año}-Q{trimestre}.md") == 1
    assert "no escribas otro SWT" in text
    assert "sin URLs" in text
    assert text.index("Evidencia externa") < text.index("### Step 5: Guardar")
