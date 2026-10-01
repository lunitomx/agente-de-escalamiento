"""S86.5: the diagnosis ends with ONE action for this week.

The last message carries the main constraint in one sentence, one action for
this week, who does it, the date in plain Spanish and the offer to note it as a
commitment in the owner's group sheet. Honesty: every number in the action
comes from the evidence it cites; without data the action is "gather X".

Fixtures are synthetic: "Pan Rico", the demo bakery already used by E84.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from coaching.diagnose import messages, run

TODAY = "2026-10-05"  # lunes
DUE = "2026-10-09"  # viernes

CASH_EVIDENCE = (
    "Les vendo pan a 3 cafeterías grandes y me pagan a 60 días; "
    "una me pagó a 30 días cuando se lo pedí."
)

WEEKLY_ACTION: dict[str, object] = {
    "decision": "cash",
    "constraint": "Tu freno principal es que cobras a 60 días.",
    "action": "llama a tus 3 clientes más grandes y pide pago a 30 días.",
    "responsible": "tú",
    "due": DUE,
    "evidence_ids": ["panrico.cash.1"],
}


def _context(base: Path, **overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "action": "narrative_assessment",
        "base_path": str(base),
        "today": TODAY,
        "company": {"name": "Pan Rico"},
        "company_summary": "Pan Rico hornea pan y lo vende a cafeterías de la zona.",
        "company_understanding": {
            "industry": "Panadería",
            "offering": "Pan dulce y de caja",
            "target_customer": "Cafeterías de la zona",
            "business_model": "Venta a crédito a negocios",
            "primary_challenge": "No le alcanza el dinero a fin de mes",
            "unknown_fields": [],
        },
        "evidence": [
            {
                "evidence_id": "panrico.cash.1",
                "question_id": "cash-open-1",
                "decision": "cash",
                "value": CASH_EVIDENCE,
                "source_kind": "conversation",
                "source_ref": "conversation:diagnose",
                "rationale": "Lo contó la dueña con detalle.",
            }
        ],
        "findings": [
            {
                "decision": "cash",
                "statement": "Cobrar a 60 días deja la caja corta a fin de mes",
                "evidence_ids": ["panrico.cash.1"],
                "status": "observed",
                "implication": "Acortar el cobro libera dinero sin vender más.",
            }
        ],
        "proposed_focuses": [
            {
                "decision": "cash",
                "rationale": "Es lo que más le aprieta hoy.",
                "evidence_ids": ["panrico.cash.1"],
            }
        ],
        "confirmation_status": "confirmed",
        "weekly_action": dict(WEEKLY_ACTION),
    }
    context.update(overrides)
    return context


def _action(**overrides: object) -> dict[str, object]:
    action = dict(WEEKLY_ACTION)
    action.update(overrides)
    return action


# --- T1: the last message ---------------------------------------------------


def test_owner_date_is_plain_spanish() -> None:
    assert messages.owner_date(date(2026, 10, 9)) == "viernes 9 de octubre"
    assert messages.owner_date(date(2026, 10, 5)) == "lunes 5 de octubre"


def test_last_message_has_constraint_action_owner_date_and_sheet_offer(
    tmp_path: Path,
) -> None:
    result = run(_context(tmp_path))

    assert result["errors"] == []
    last = result["output"]
    assert last.startswith("Tu freno principal es que cobras a 60 días.")
    assert "Esta semana: llama a tus 3 clientes más grandes" in last
    assert "Responsable: tú." in last
    assert "Fecha: viernes 9 de octubre." in last
    assert "¿Lo anoto como compromiso en tu hoja" in last
    # the date stays ISO in the data
    action = result["artifacts"]["weekly_action"]
    assert action["due"] == DUE
    assert result["artifacts"]["closing_message"] == last


def test_closing_is_one_action_not_another_session(tmp_path: Path) -> None:
    last = run(_context(tmp_path))["output"]

    assert "profundizar" not in last
    assert "revisión a fondo" not in last
    assert last.count("Esta semana:") == 1


def test_another_responsible_is_named(tmp_path: Path) -> None:
    result = run(
        _context(tmp_path, weekly_action=_action(responsible="Laura, tu encargada"))
    )

    assert "Responsable: Laura, tu encargada." in result["output"]


def test_action_needs_the_reading_confirmed_first(tmp_path: Path) -> None:
    result = run(_context(tmp_path, confirmation_status="pending"))

    assert result["output"] == ""
    assert result["errors"]


def test_number_not_in_the_evidence_is_rejected(tmp_path: Path) -> None:
    invented = _action(action="llama a tus 5 clientes y pide pago a 15 días.")

    result = run(_context(tmp_path, weekly_action=invented))

    assert result["output"] == ""
    assert any("número" in error for error in result["errors"])


def test_without_data_the_action_is_to_gather_it(tmp_path: Path) -> None:
    gather = _action(
        constraint="Tu freno principal parece ser que cobras tarde.",
        action="junta cuánto te debe cada cafetería y desde cuándo.",
    )

    result = run(_context(tmp_path, weekly_action=gather))

    assert result["errors"] == []
    assert "Esta semana: junta cuánto te debe cada cafetería" in result["output"]


def test_constraint_is_one_sentence(tmp_path: Path) -> None:
    two = _action(constraint="Cobras a 60 días. Y además vendes poco.")

    assert run(_context(tmp_path, weekly_action=two))["errors"]


def test_date_must_fall_this_week(tmp_path: Path) -> None:
    late = run(_context(tmp_path, weekly_action=_action(due="2026-10-30")))
    past = run(_context(tmp_path, weekly_action=_action(due="2026-10-01")))

    assert late["errors"] and past["errors"]


def test_action_area_needs_a_finding(tmp_path: Path) -> None:
    other_area = _action(decision="people")

    assert run(_context(tmp_path, weekly_action=other_area))["errors"]


def test_without_weekly_action_the_old_closing_stays(tmp_path: Path) -> None:
    context = _context(tmp_path, confirmation_status="pending")
    del context["weekly_action"]

    result = run(context)

    assert result["errors"] == []
    assert "¿Lo ves igual" in result["output"]


@pytest.mark.parametrize("bad", ["", "9 de octubre", "2026-13-01"])
def test_due_must_be_an_iso_date(tmp_path: Path, bad: str) -> None:
    assert run(_context(tmp_path, weekly_action=_action(due=bad)))["errors"]
