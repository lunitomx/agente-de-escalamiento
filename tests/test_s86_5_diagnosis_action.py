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


# --- T2: the sheet offer, once, and the hand-off to the tracker -------------

PAN_RICO_TAB = (
    "Participant Name\t\tRosa Demo\n"
    "Monthly Commitments\n"
    "\tFocus Area\tPriorities\tKPIs\tDue Dates\n"
    "\tCash\tPagar al proveedor de harina\t1 pago\t15/10/2026\n"
)


def _confirm_tab(base: Path) -> None:
    from coaching.tracker.flow import run as tracker_run

    result = tracker_run(
        {
            "action": "confirm",
            "base_path": str(base),
            "user_confirmed": True,
            "tab_name": "Rosa",
            "pasted_text": PAN_RICO_TAB,
        }
    )
    assert result.errors == []


def test_with_a_confirmed_tab_the_offer_is_one_short_question(tmp_path: Path) -> None:
    _confirm_tab(tmp_path)

    last = run(_context(tmp_path))["output"]

    assert last.endswith(messages.SHEET_OFFER)


def test_without_a_confirmed_tab_the_offer_appears_once(tmp_path: Path) -> None:
    first = run(_context(tmp_path))
    again = run(_context(tmp_path, sheet_offer_made=True))

    assert first["output"].endswith(messages.SHEET_OFFER_NO_TAB)
    assert first["output"].count("¿Lo anoto") == 1
    assert first["artifacts"]["sheet_offer"] is True
    # already offered (or the owner said "después"): never again
    assert "¿Lo anoto" not in again["output"]
    assert "después" not in again["output"]
    assert again["artifacts"]["sheet_offer"] is False
    # the closing still has the action, who and when
    assert "Esta semana:" in again["output"]
    assert "Responsable: tú." in again["output"]
    assert "Fecha: viernes 9 de octubre." in again["output"]


def test_tracker_request_is_a_commitment_row_for_the_month(tmp_path: Path) -> None:
    request = run(_context(tmp_path))["artifacts"]["tracker_request"]

    assert request == {
        "action": "propose",
        "base_path": str(tmp_path),
        "table": "commitments",
        "month": "2026-10",
        "plan": {
            "priorities": [
                {
                    "priority": (
                        "Llama a tus 3 clientes más grandes y pide pago a 30 días."
                    ),
                    "decision": "cash",
                    "due": DUE,
                }
            ]
        },
    }


def test_after_yes_the_tracker_proposes_the_commitment(tmp_path: Path) -> None:
    from coaching.tracker.flow import run as tracker_run

    _confirm_tab(tmp_path)
    request = dict(run(_context(tmp_path))["artifacts"]["tracker_request"])
    request["pasted_text"] = PAN_RICO_TAB  # the agent adds the tab it reads

    result = tracker_run(request)

    assert result.errors == []
    assert result.proposal is not None
    row = result.proposal.rows[0]
    assert row.priority.startswith("Llama a tus 3 clientes más grandes")
    assert row.due == DUE
    assert row.focus_area == "Cash"  # the label the sheet already uses
    assert DUE in result.paste_block
    assert "compromisos de octubre" in result.message


def test_another_responsible_goes_into_the_row(tmp_path: Path) -> None:
    result = run(
        _context(tmp_path, weekly_action=_action(responsible="Laura, tu encargada"))
    )

    priority = result["artifacts"]["tracker_request"]["plan"]["priorities"][0]
    assert priority["priority"].endswith("(responsable: Laura, tu encargada)")


def test_without_a_confirmed_tab_the_tracker_asks_for_it_first(tmp_path: Path) -> None:
    from coaching.tracker.flow import run as tracker_run

    request = run(_context(tmp_path))["artifacts"]["tracker_request"]

    result = tracker_run(request)

    assert result.errors == ["needs_confirmed_tab"]
