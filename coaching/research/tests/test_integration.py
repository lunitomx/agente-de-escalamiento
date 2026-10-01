"""Integration checkpoint (E83 S83.4): the three modes, with and without web
search, from the frame to the SWT and the next diagnosis.

Synthetic data only, on ``tmp_path``. What must hold end to end (owner
decisions 2026-09-30): no private data in a search, sources up to 90 days old,
findings fit whole or are refused, no URL leaves the reports, without search
one line on how to turn it on, and the diagnosis contract takes it as it is.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from coaching.diagnose.primary_constraint import (
    PrimaryConstraintRequest,
    diagnose_primary_constraint,
)
from coaching.research import messages
from coaching.research.flow import FlowResult, run
from coaching.research.models import PrivateTerms, normalize

TODAY = date(2026, 9, 30)
COMPANY = "Tortillas Zorblax"
PRIVATE = PrivateTerms(
    company_names=[COMPANY], people=["Ximena Vrkalova"], figures=["$987,654"]
)
SECRETS = ("zorblax", "vrkalova", "987,654", "987654")
OPTIONS = [
    {"label": "A", "text": "Seguir con el plan"},
    {
        "label": "B",
        "text": "Todavía no decidir",
        "kind": "esperar",
        "missing_data": "ventas de octubre",
        "by_date": "2026-10-31",
    },
]


def _source(source_id: str, publisher: str, search: str) -> dict[str, object]:
    web = search == "web"
    return {
        "source_id": source_id,
        "origin": "web" if web else "dueño",
        "title": f"Página {source_id}",
        "publisher": publisher,
        "url": f"https://ejemplo-{source_id}.test/p" if web else None,
        "published_on": (TODAY - timedelta(days=15)).isoformat(),
        "consulted_on": TODAY.isoformat(),
        "excerpt": f"Cita literal {source_id}",
    }


def _sources(search: str) -> list[dict[str, object]]:
    return [
        _source("s1", "Diario Uno", search),
        _source("s2", "Revista Dos", search),
        _source("s3", "Cámara Tres", search),
    ]


def _frame(mode: str, search: str, **fields: object) -> dict[str, object]:
    frame: dict[str, object] = {
        "concern": f"Quiero entender {mode} de {COMPANY}",
        "question": f"¿Qué dice el mercado ({mode})?",
        "decision_informed": "Qué hacer este trimestre",
        "mode": mode,
        "offer_category": "tortillas de maíz",
        "geography": "Puebla",
        "search_mode": search,
    }
    frame.update(fields)
    return frame


def _framed(base: Path, mode: str, search: str, **fields: object) -> FlowResult:
    result = run(
        {
            "action": "frame",
            "frame": _frame(mode, search, **fields),
            "private": PRIVATE.model_dump(),
            "base_path": str(base),
            "today": TODAY.isoformat(),
        }
    )
    assert result.errors == []
    assert result.frame is not None
    for query in result.frame.queries:
        assert not any(secret in normalize(query) for secret in SECRETS)
    if search == "sin_busqueda":
        assert result.message.startswith(messages.SEARCH_OFF)
        assert result.frame.queries == []
    else:
        assert result.frame.queries
    return result


def _pending(search: str) -> dict[str, object]:
    return {} if search == "web" else {"next_source": "la cámara del giro"}


def _save(base: Path, framed: FlowResult, search: str, **step: object) -> FlowResult:
    assert framed.frame is not None
    context: dict[str, object] = {
        "action": "save",
        "base_path": str(base),
        "today": TODAY.isoformat(),
        "frame": framed.frame.model_copy(update={"confirmed": True}).model_dump(
            mode="json"
        ),
        "private": PRIVATE.model_dump(),
        "sources": _sources(search),
        "options": OPTIONS,
        "recommendation": "A",
        "recommendation_reason": "es lo que dicen las fuentes",
        "user_confirmed": True,
        "chosen": "A",
    }
    context.update(step)
    return run(context)


def _benchmark(base: Path, search: str) -> None:
    framed = _framed(
        base,
        "benchmark",
        search,
        competitors=["Tortillería El Sol"],
        decision_area="cash",
    )
    comparables = [
        {
            "name": "Tortillería El Sol",
            "named_by_owner": True,
            "cells": {"precio": {"value": "24 pesos el kilo", "source_id": "s1"}},
        }
    ]
    saved = _save(
        base,
        framed,
        search,
        comparables=comparables,
        claims=[
            {
                "text": "El kilo cuesta entre 22 y 26 pesos",
                "kind": "dato",
                "supporting": ["s1", "s2", "s3"],
            }
        ],
    )
    assert saved.errors == []


def _market(base: Path, search: str) -> None:
    framed = _framed(base, "mercado", search, segment="fondas y restaurantes")
    assert framed.missing_question is None
    size: dict[str, object] = {
        "kind": "estimado",
        "low": 120000,
        "high": 180000,
        "unit": "kilos de tortilla al mes",
        "method": "fondas de la zona por kilos que compra cada una",
        "assumptions": ["cada fonda compra entre 40 y 60 kilos al mes"],
        "supporting": ["s1", "s2", "s3"],
        **_pending(search),
    }
    saved = _save(base, framed, search, market_size=size)
    assert saved.errors == []


def _strengths(base: Path, search: str) -> FlowResult:
    framed = _framed(base, "fortalezas-tendencias", search)
    assert framed.frame is not None
    assert framed.frame.competitors == ["Tortillería El Sol"]
    assert [item.name for item in framed.comparables] == ["Tortillería El Sol"]
    reused = [source.model_dump(mode="json") for source in framed.sources]
    claims: list[dict[str, object]] = [
        {
            "text": "El Sol no entrega a domicilio",
            "kind": "dato",
            "supporting": ["s1"],
            "side": "fortaleza",
            "against": ["Tortillería El Sol"],
            **_pending(search),
        },
        {
            "text": "Sube el precio del maíz",
            "kind": "dato",
            "supporting": ["s1", "s2", "s3"],
            "side": "tendencia",
        },
    ]
    common: dict[str, object] = {
        "sources": [*_sources(search), *reused],
        "comparables": [item.model_dump(mode="json") for item in framed.comparables],
    }
    too_long = _save(
        base,
        framed,
        search,
        claims=[
            {
                **claims[1],
                "text": "Sube el precio del maíz en todo el valle de Puebla por "
                "la sequía, el diésel y los nuevos permisos de molinos",
            }
        ],
        **common,
    )
    assert too_long.errors == ["finding_too_long"]
    saved = _save(base, framed, search, claims=claims, **common)
    assert saved.errors == []
    return saved


def _no_url(text: str) -> bool:
    return "://" not in text and "www." not in text.lower()


@pytest.mark.parametrize("search", ["web", "sin_busqueda"])
def test_three_modes_reach_the_swt_and_the_diagnosis(
    tmp_path: Path, search: str
) -> None:
    _benchmark(tmp_path, search)
    _market(tmp_path, search)
    strengths = _strengths(tmp_path, search)

    swt = run({"action": "swt", "base_path": str(tmp_path), "today": TODAY.isoformat()})
    assert swt.errors == []
    assert swt.saved_to == strengths.saved_to
    assert [item.side for item in swt.swt_evidence] == ["fortaleza", "tendencia"]
    assert all(
        item.label.startswith("Según fuentes externas") for item in swt.swt_evidence
    )
    assert all(_no_url(item.text) for item in swt.swt_evidence)
    assert _no_url(swt.message)
    assert not list(tmp_path.rglob("swt-*"))

    diagnosis = run(
        {"action": "diagnosis", "base_path": str(tmp_path), "today": TODAY.isoformat()}
    )
    assert diagnosis.errors == []
    inputs = diagnosis.diagnostic_inputs
    assert inputs is not None
    assert len(inputs.evidence) == 3
    lines = [
        *inputs.assumptions,
        *inputs.open_questions,
        *(fact.value for fact in inputs.evidence),
        *(fact.source_ref for fact in inputs.evidence),
    ]
    assert all(_no_url(line) for line in lines)
    assert not any(secret in normalize(line) for line in lines for secret in SECRETS)
    assert any(line.startswith("Mercado") for line in inputs.assumptions)

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
        for area in ("people", "execution")
    ]
    facts = [fact.model_dump(mode="json") for fact in inputs.evidence]
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
            "evidence": [*others, *facts],
            "decision_assessments": [
                {
                    "decision": area,
                    "status": "known" if area in ("cash", "strategy") else "hypothesis",
                    "rationale": "Señal descrita por la dirección o investigada.",
                    "evidence_ids": [
                        str(item["evidence_id"])
                        for item in [*others, *facts]
                        if item["decision"] == area
                    ],
                }
                for area in ("people", "strategy", "execution", "cash")
            ],
            "requested_primary_decision": "strategy",
            "assumptions": inputs.assumptions,
            "open_questions": inputs.open_questions,
        }
    )
    result = diagnose_primary_constraint(request)
    assert result.primary_constraint is not None
    assert result.output_contract.assumptions == inputs.assumptions
