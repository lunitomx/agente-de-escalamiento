"""A saved research feeds the next diagnosis (E83 S83.5).

Only the owner's confirmed decision becomes a fact, pointing to the local
report; outside findings enter as assumptions, gaps as open questions; no URL
leaves the report. The diagnosis contract (``coaching/diagnose``) is used as
is. Synthetic data only; files go to a pytest temporary folder.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from coaching.diagnose import run as run_diagnose
from coaching.diagnose.primary_constraint import (
    PrimaryConstraintRequest,
    diagnose_primary_constraint,
)
from coaching.research import messages
from coaching.research.diagnosis import (
    MAX_ASSUMPTIONS,
    MAX_OPEN_QUESTIONS,
    load_diagnostic_inputs,
    to_diagnostic_inputs,
)
from coaching.research.models import (
    BenchmarkCell,
    Comparable,
    DecisionOption,
    ResearchClaim,
    ResearchFrame,
    ResearchReport,
    SourceRecord,
)
from coaching.research.flow import run
from coaching.research.report import build_report, load_index, save_report

TODAY = date(2026, 9, 30)
REFERENCE = ".escala/my-company/research/2026-09-30-benchmark.md"


def _frame(**fields: object) -> ResearchFrame:
    payload: dict[str, object] = {
        "concern": "Creo que cobro poco",
        "question": "¿Cobro menos que negocios parecidos en Puebla?",
        "decision_informed": "Subir o no el precio del kilo en enero",
        "mode": "benchmark",
        "decision_area": "cash",
        "offer_category": "tortillas de maíz",
        "geography": "Puebla",
        "competitors": ["Tortillería El Sol"],
        "queries": ["precios de tortillas de maíz en Puebla 2026"],
        "confirmed": True,
    }
    payload.update(fields)
    return ResearchFrame.model_validate(payload)


def _source(source_id: str, publisher: str, *, dated: bool = True) -> SourceRecord:
    return SourceRecord(
        source_id=source_id,
        origin="web",
        title=f"Precios {source_id}",
        publisher=publisher,
        url=f"https://ejemplo-{source_id}.test/precios",
        published_on=TODAY - timedelta(days=20) if dated else None,
        consulted_on=TODAY,
        excerpt=f"El kilo cuesta 24 pesos ({source_id})",
    )


SOURCES = [
    _source("s1", "Diario Uno"),
    _source("s2", "Revista Dos"),
    _source("s3", "Cámara Tres"),
    _source("s4", "Blog Cuatro", dated=False),
]
OPTIONS = [
    DecisionOption(label="A", text="Subir 8% el kilo en enero"),
    DecisionOption(label="B", text="Mantener el precio y cambiar el paquete"),
    DecisionOption(
        label="C",
        text="Todavía no decidir",
        kind="esperar",
        missing_data="tres cotizaciones de tortillerías de mi zona",
        by_date=date(2026, 10, 15),
    ),
]


def _report(
    *,
    chosen: str = "A",
    frame: ResearchFrame | None = None,
    claims: list[ResearchClaim] | None = None,
    not_found: list[str] | None = None,
    options: list[DecisionOption] | None = None,
    comparables: list[Comparable] | None = None,
    researched_on: date = TODAY,
) -> ResearchReport:
    return build_report(
        frame=frame or _frame(),
        researched_on=researched_on,
        sources=SOURCES,
        claims=(
            [
                ResearchClaim(
                    text="El kilo cuesta entre 22 y 26 pesos en Puebla.",
                    kind="dato",
                    supporting=["s1", "s2", "s3"],
                    contrary=["s4"],
                ),
                ResearchClaim(
                    text="Los clientes aceptan subidas pequeñas si se avisan.",
                    kind="supuesto",
                    supporting=["s2"],
                ),
            ]
            if claims is None
            else claims
        ),
        not_found=(
            ["Precios publicados de tortillerías de la colonia"]
            if not_found is None
            else not_found
        ),
        options=options or OPTIONS,
        recommendation="A",
        recommendation_reason="tu precio está abajo del rango y el maíz subió",
        chosen=chosen,
        comparables=comparables,
    )


# --- the decision is the only fact -------------------------------------------


def test_the_confirmed_decision_is_one_local_fact_pointing_to_the_report() -> None:
    inputs = to_diagnostic_inputs(_report(), REFERENCE, TODAY)

    assert len(inputs.evidence) == 1
    fact = inputs.evidence[0]
    assert fact.source_kind == "conversation"
    assert fact.answer_status == "fact"
    assert fact.source_ref == REFERENCE
    assert fact.decision == "cash"  # the frame's decision area
    assert fact.freshness == "current"
    assert fact.captured_at == TODAY
    assert fact.evidence_id == "research.2026-09-30-benchmark"
    assert isinstance(fact.value, str)
    assert "Subir 8% el kilo en enero" in fact.value
    assert "¿Cobro menos que negocios parecidos en Puebla?" in fact.value
    assert "A)" not in fact.value  # never the option's letter (design U3)
    assert "maíz subió" in fact.value  # its reason, when it was the recommended one


def test_a_decision_other_than_the_recommendation_does_not_borrow_its_reason() -> None:
    fact = to_diagnostic_inputs(_report(chosen="B"), REFERENCE, TODAY).evidence[0]

    assert isinstance(fact.value, str)
    assert "Mantener el precio y cambiar el paquete" in fact.value
    assert "maíz subió" not in fact.value


def test_waiting_is_a_decision_and_its_missing_data_is_an_open_question() -> None:
    inputs = to_diagnostic_inputs(_report(chosen="C"), REFERENCE, TODAY)

    value = inputs.evidence[0].value
    assert isinstance(value, str)
    assert "Todavía no decidir" in value
    assert any(
        "tres cotizaciones de tortillerías de mi zona" in item
        and item.startswith("Pendiente al 15 oct 2026:")
        for item in inputs.open_questions
    )


def test_the_decision_fact_is_accepted_by_the_diagnosis_as_it_is() -> None:
    """The contract does not change: the fact passes the primary-constraint gate."""
    inputs = to_diagnostic_inputs(_report(), REFERENCE, TODAY)
    fact = inputs.evidence[0]
    others = [
        {
            "evidence_id": f"conversation.{area}.1",
            "question_id": f"{area}-detail",
            "decision": area,
            "value": "La dirección lo describió con detalle y con un ejemplo reciente.",
            "source_kind": "conversation",
            "source_ref": "conversation:welcome",
            "rationale": "Respuesta detallada de la dirección.",
        }
        for area in ("people", "strategy", "execution")
    ]
    request = PrimaryConstraintRequest.model_validate(
        {
            "company_summary": "Tortillería sintética que vende por kilo en Puebla.",
            "company_understanding": {
                "industry": "Alimentos",
                "offering": "Tortillas de maíz",
                "target_customer": "Familias y fondas",
                "business_model": "Venta de mostrador",
                "primary_challenge": "Margen",
                "unknown_fields": [],
            },
            "evidence": [*others, fact.model_dump(mode="json")],
            "decision_assessments": [
                *(
                    {
                        "decision": area,
                        "status": "hypothesis",
                        "rationale": "Señal descrita por la dirección.",
                        "evidence_ids": [f"conversation.{area}.1"],
                    }
                    for area in ("people", "strategy", "execution")
                ),
                {
                    "decision": "cash",
                    "status": "known",
                    "rationale": "El dueño ya decidió su precio tras investigar.",
                    "evidence_ids": [fact.evidence_id],
                },
            ],
            "requested_primary_decision": "cash",
            "assumptions": inputs.assumptions,
            "open_questions": inputs.open_questions,
        }
    )

    diagnosis = diagnose_primary_constraint(request)

    assert diagnosis.primary_constraint is not None
    assert diagnosis.primary_constraint.evidence_ids == [fact.evidence_id]
    assert diagnosis.output_contract.assumptions == inputs.assumptions


def test_the_narrative_diagnosis_takes_the_fact_and_the_open_questions() -> None:
    inputs = to_diagnostic_inputs(_report(), REFERENCE, TODAY)
    fact = inputs.evidence[0]

    result = run_diagnose(
        {
            "action": "narrative_assessment",
            "company_summary": "Tortillería sintética que vende por kilo en Puebla.",
            "company_understanding": {"unknown_fields": list(_COMPANY_FIELDS)},
            "evidence": [fact.model_dump(mode="json")],
            "findings": [
                {
                    "decision": "cash",
                    "statement": "El dueño ya decidió su precio tras investigar",
                    "evidence_ids": [fact.evidence_id],
                    "implication": "El diagnóstico parte de esa decisión.",
                }
            ],
            "open_questions": inputs.open_questions,
        }
    )

    assert result["errors"] == []


_COMPANY_FIELDS = (
    "industry",
    "offering",
    "target_customer",
    "business_model",
    "primary_challenge",
)


# --- outside findings are assumptions, gaps are questions --------------------


def test_every_finding_is_an_assumption_with_status_and_date() -> None:
    inputs = to_diagnostic_inputs(_report(), REFERENCE, TODAY)

    confirmed, supposed = inputs.assumptions[:2]
    # 10-word finding: the month goes, the finding stays whole
    assert confirmed == "Ext. conf.: El kilo cuesta entre 22 y 26 pesos en Puebla."
    assert (
        supposed
        == "Sup. pend. sep26: Los clientes aceptan subidas pequeñas si se avisan."
    )
    assert "Los clientes aceptan subidas pequeñas" in supposed
    assert any(  # a finding some source contradicts is also a doubt
        item == "En duda: El kilo cuesta entre 22 y 26 pesos en Puebla."
        for item in inputs.open_questions
    )
    assert all(item.value != "El kilo" for item in inputs.evidence)
    assert len(inputs.evidence) == 1


LONG_WITH_FIGURE = (
    "Según datos del SNIIM, en Puebla el kilo de tortilla ronda los 17 pesos "
    "en septiembre"
)


def _fits(line: str) -> bool:
    return (
        line == line.strip()
        and len(line) <= 96
        and len(line.split()) <= 12
        and "/" not in line
        and "\\" not in line
        and "://" not in line
    )


def test_a_finding_keeps_its_figure_by_shortening_the_prefix_not_the_text() -> None:
    claim = ResearchClaim(
        text="En Puebla el kilo de tortilla ronda 17 pesos.", kind="dato"
    )

    inputs = to_diagnostic_inputs(_report(claims=[claim]), REFERENCE, TODAY)

    assert inputs.assumptions[0] == (
        "Ext. pend. sep26: En Puebla el kilo de tortilla ronda 17 pesos."
    )
    stale = to_diagnostic_inputs(
        _report(claims=[claim]), REFERENCE, TODAY + timedelta(days=91)
    )
    assert stale.assumptions[0].startswith(messages.STALE_MARK)
    assert stale.assumptions[0].endswith("ronda 17 pesos.")


def test_a_saved_finding_too_long_to_fit_is_never_cut() -> None:
    """A report saved before the rule: the line is left out, never mutilated."""
    report = _report(
        claims=[ResearchClaim(text=LONG_WITH_FIGURE, kind="dato", supporting=["s1"])],
        not_found=[LONG_WITH_FIGURE],
        chosen="C",
    )

    inputs = to_diagnostic_inputs(report, REFERENCE, TODAY + timedelta(days=91))

    lines = [*inputs.assumptions, *inputs.open_questions]
    assert all(_fits(line) for line in lines)
    assert not any(line.endswith("…") for line in lines)
    assert not any("ronda" in line and "17 pesos" not in line for line in lines)
    assert inputs.assumptions == []
    assert any("sólo en el reporte" in line for line in inputs.open_questions)


def _grade(claims: list[ResearchClaim]) -> dict[str, object]:
    return {
        "action": "grade",
        "today": TODAY.isoformat(),
        "sources": [item.model_dump(mode="json") for item in SOURCES],
        "claims": [item.model_dump(mode="json") for item in claims],
    }


def test_grade_rejects_a_finding_that_does_not_fit_and_asks_to_keep_the_figure() -> (
    None
):
    long = ResearchClaim(text=LONG_WITH_FIGURE, kind="dato", supporting=["s1"])
    slashed = ResearchClaim(text="El kilo cuesta 22/26 pesos.", kind="dato")

    for claim in (long, slashed):
        result = run(_grade([claim]))

        assert result.errors == ["finding_too_long"]
        assert claim.text in result.message
        assert "cifra" in result.message
        assert result.claims == []


def test_save_rejects_what_does_not_fit_and_writes_nothing(tmp_path: Path) -> None:
    report = _report()
    context: dict[str, object] = {
        "action": "save",
        "base_path": str(tmp_path),
        "user_confirmed": True,
        "chosen": "A",
        "today": TODAY.isoformat(),
        "frame": report.frame.model_dump(mode="json"),
        "sources": [item.model_dump(mode="json") for item in SOURCES],
        "claims": [{"text": LONG_WITH_FIGURE, "kind": "dato", "supporting": ["s1"]}],
        "options": [item.model_dump(mode="json") for item in OPTIONS],
        "recommendation": "A",
        "recommendation_reason": "tu precio está abajo del rango",
        "not_found": [],
    }

    long_finding = run(context)
    long_gap = run(
        {
            **context,
            "claims": [{"text": "El kilo cuesta 24 pesos.", "kind": "dato"}],
            "not_found": [LONG_WITH_FIGURE + " y en las colonias del sur"],
        }
    )
    long_cell = run(
        {
            **context,
            "claims": [],
            "comparables": [
                {
                    "name": "Tortillería El Sol",
                    "named_by_owner": True,
                    "cells": {
                        "precio": {
                            "value": "24 pesos el kilo de lunes a viernes y 26 "
                            "pesos el fin de semana",
                            "source_id": "s1",
                        }
                    },
                }
            ],
        }
    )

    assert long_finding.errors == ["finding_too_long"]
    assert long_gap.errors == ["finding_too_long"]
    assert long_cell.errors == ["finding_too_long"]
    assert not (tmp_path / ".escala").exists()


def test_counted_comparables_are_assumptions_and_candidates_are_not() -> None:
    comparables = [
        Comparable(
            name="Tortillería El Sol",
            named_by_owner=True,
            cells={"precio": BenchmarkCell(value="24 pesos el kilo", source_id="s1")},
        ),
        Comparable(
            name="Molino La Luna",
            found_in="s2",
            why="vende lo mismo en su zona",
            cells={"precio": BenchmarkCell(value="23 pesos", source_id="s2")},
        ),
    ]

    inputs = to_diagnostic_inputs(_report(comparables=comparables), REFERENCE, TODAY)

    lines = [item for item in inputs.assumptions if "Tortillería El Sol" in item]
    assert len(lines) == 1
    assert "precio: 24 pesos el kilo" in lines[0]
    assert lines[0].startswith("Comp.")
    assert "Tortillería El Sol" in lines[0]
    assert _fits(lines[0])
    assert not any("Molino La Luna" in item for item in inputs.assumptions)
    assert any("no encontrado" in item for item in inputs.open_questions)


def test_what_was_not_found_becomes_an_open_question() -> None:
    inputs = to_diagnostic_inputs(_report(), REFERENCE, TODAY)

    assert any(
        "Precios publicados de tortillerías de la colonia" in item
        for item in inputs.open_questions
    )


def test_no_url_leaves_the_report_even_when_the_agent_wrote_one_in_a_text() -> None:
    report = _report(
        claims=[
            ResearchClaim(
                text="Ver https://ejemplo-s1.test/precios: el kilo sube.",
                kind="dato",
                supporting=["s1"],
            )
        ],
        not_found=["El menú de www.competidor.test/menu"],
        options=[
            DecisionOption(label="A", text="Copiar ejemplo.test/paquetes en enero"),
            DecisionOption(label="B", text="Mantener el precio y cambiar el paquete"),
        ],
    )

    dumped = to_diagnostic_inputs(report, REFERENCE, TODAY).model_dump_json()

    assert "http" not in dumped
    assert "www." not in dumped
    assert ".test/" not in dumped
    assert messages.LINK_IN_REPORT in dumped


def test_lines_are_distinct_and_bounded_for_the_diagnosis_contract() -> None:
    claim = ResearchClaim(text="El kilo sube en enero.", kind="dato", supporting=["s1"])
    inputs = to_diagnostic_inputs(
        _report(claims=[claim, claim], not_found=["Lo mismo", "Lo mismo"]),
        REFERENCE,
        TODAY,
    )

    assert len(inputs.assumptions) == len(set(inputs.assumptions)) == 1
    assert len(inputs.open_questions) == len(set(inputs.open_questions))


# --- stale reports -----------------------------------------------------------


def test_a_report_past_its_review_date_enters_stale_with_an_offer_to_refresh() -> None:
    later = TODAY + timedelta(days=91)

    inputs = to_diagnostic_inputs(_report(), REFERENCE, later)

    assert inputs.evidence[0].freshness == "stale"
    assert inputs.evidence[0].confidence == "low"
    assert len(inputs.refresh_offers) == 1
    assert "¿Cobro menos que negocios parecidos en Puebla?" in inputs.refresh_offers[0]
    assert "29 de diciembre de 2026" in inputs.refresh_offers[0]
    assert all(item.startswith(messages.STALE_MARK) for item in inputs.assumptions)


def test_on_its_review_date_a_report_is_still_current() -> None:
    inputs = to_diagnostic_inputs(_report(), REFERENCE, TODAY + timedelta(days=90))

    assert inputs.evidence[0].freshness == "current"
    assert inputs.evidence[0].confidence == "high"
    assert inputs.refresh_offers == []


# --- reading the saved reports -----------------------------------------------


def test_nothing_saved_means_no_inputs(tmp_path: Path) -> None:
    inputs = load_diagnostic_inputs(tmp_path, TODAY)

    assert inputs.evidence == []
    assert inputs.assumptions == []
    assert inputs.open_questions == []


def test_saved_reports_feed_the_diagnosis_latest_per_topic(tmp_path: Path) -> None:
    save_report(_report(chosen="B", researched_on=TODAY - timedelta(days=10)), tmp_path)
    save_report(_report(chosen="A"), tmp_path)
    save_report(
        _report(
            frame=_frame(
                mode="mercado",
                decision_area="strategy",
                competitors=[],
                question="¿Crece la demanda de tortillas en Puebla?",
            ),
            chosen="B",
        ),
        tmp_path,
    )

    inputs = load_diagnostic_inputs(tmp_path, TODAY)

    references = [item.source_ref for item in inputs.evidence]
    assert references == [
        ".escala/my-company/research/2026-09-30-mercado.md",
        ".escala/my-company/research/2026-09-30-benchmark.md",
    ]  # newest first; the older benchmark decision was replaced by the newer one
    assert [item.decision for item in inputs.evidence] == ["strategy", "cash"]
    assert len(inputs.assumptions) <= MAX_ASSUMPTIONS
    assert len(inputs.open_questions) <= MAX_OPEN_QUESTIONS


def test_without_the_structured_report_the_decision_still_comes_from_the_index(
    tmp_path: Path,
) -> None:
    path = save_report(_report(chosen="A"), tmp_path)
    path.with_suffix(".json").write_text("{roto", encoding="utf-8")

    inputs = load_diagnostic_inputs(tmp_path, TODAY)

    assert len(inputs.evidence) == 1
    value = inputs.evidence[0].value
    assert isinstance(value, str)
    assert "Subir 8% el kilo en enero" in value
    assert "A)" not in value
    assert inputs.evidence[0].source_ref == load_index(tmp_path)[0].reference
    assert inputs.assumptions == []
    assert any(messages.DETAIL_UNREADABLE in item for item in inputs.open_questions)


def test_bounds_hold_across_many_saved_reports(tmp_path: Path) -> None:
    for mode, area in (
        ("benchmark", "cash"),
        ("benchmark", "strategy"),
        ("mercado", "strategy"),
        ("mercado", "cash"),
    ):
        claims = [
            ResearchClaim(text=f"{mode} {area} hallazgo {n}.", kind="dato")
            for n in range(3)
        ]
        save_report(
            _report(
                frame=_frame(mode=mode, decision_area=area),
                claims=claims,
                not_found=[f"{mode} {area} falta {n}" for n in range(3)],
                comparables=None,
            ),
            tmp_path,
        )

    inputs = load_diagnostic_inputs(tmp_path, TODAY)

    assert len(inputs.evidence) == 4
    assert len(inputs.assumptions) == MAX_ASSUMPTIONS
    assert len(inputs.open_questions) == MAX_OPEN_QUESTIONS


# --- the flow ----------------------------------------------------------------


def test_flow_diagnosis_action_hands_back_the_inputs_and_the_offer(
    tmp_path: Path,
) -> None:
    save_report(_report(chosen="A"), tmp_path)

    result = run(
        {"action": "diagnosis", "base_path": str(tmp_path), "today": "2027-01-15"}
    )

    assert result.errors == []
    assert result.diagnostic_inputs is not None
    assert result.diagnostic_inputs.evidence[0].freshness == "stale"
    assert result.message == result.diagnostic_inputs.refresh_offers[0]


def test_saved_message_says_the_next_diagnosis_starts_from_the_decision() -> None:
    assert "parto de esta decisión" in messages.saved_message(date(2026, 12, 29))
