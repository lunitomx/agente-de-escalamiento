"""Sampling a saved report's sources: the quote must be on the page (S83.5)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from coaching.research.flow import run
from coaching.research.models import (
    DecisionOption,
    ResearchClaim,
    ResearchFrame,
    ResearchReport,
    SourceRecord,
)
from coaching.research.report import build_report, load_index, save_report
from coaching.research.sampling import (
    check_sources,
    excerpt_in_page,
    pick_sources,
)

TODAY = date(2026, 9, 30)


def _source(source_id: str, *, origin: str = "web") -> SourceRecord:
    return SourceRecord.model_validate(
        {
            "source_id": source_id,
            "origin": origin,
            "title": f"Precios {source_id}",
            "publisher": f"Medio {source_id}",
            "url": f"https://ejemplo-{source_id}.test/precios"
            if origin == "web"
            else None,
            "published_on": "2026-09-10",
            "consulted_on": TODAY.isoformat(),
            "excerpt": f"El kilo de tortilla cuesta 24 pesos en Puebla ({source_id})",
        }
    )


def _report(sources: list[SourceRecord]) -> ResearchReport:
    frame = ResearchFrame.model_validate(
        {
            "concern": "Creo que cobro poco",
            "question": "¿Cobro menos que negocios parecidos en Puebla?",
            "decision_informed": "Subir o no el precio del kilo en enero",
            "mode": "benchmark",
            "decision_area": "cash",
            "offer_category": "tortillas de maíz",
            "geography": "Puebla",
            "queries": ["precios de tortillas de maíz en Puebla 2026"],
            "confirmed": True,
        }
    )
    return build_report(
        frame=frame,
        researched_on=TODAY,
        sources=sources,
        claims=[
            ResearchClaim(
                text="El kilo cuesta 24 pesos.",
                kind="dato",
                supporting=[item.source_id for item in sources],
            )
        ],
        not_found=[],
        options=[
            DecisionOption(label="A", text="Subir 8% el kilo en enero"),
            DecisionOption(label="B", text="Mantener el precio"),
        ],
        recommendation="A",
        recommendation_reason="tu precio está abajo del rango",
        chosen="A",
    )


def test_the_excerpt_is_found_in_the_page_text_whatever_the_markup() -> None:
    page = (
        "<html><head><style>p{}</style><script>var x='nada';</script></head>"
        "<body><p>Hoy <b>el  kilo de tortilla</b>\n cuesta 24&nbsp;pesos "
        "en PUEBLA (s1).</p></body></html>"
    )

    assert excerpt_in_page("El kilo de tortilla cuesta 24 pesos en Puebla (s1)", page)
    assert excerpt_in_page("el kilo de tortilla cuesta 24 pesos en puebla", page)


def test_accents_and_quotes_do_not_hide_the_excerpt() -> None:
    page = "<p>La demanda crecio en la region, dijo «la camara».</p>"

    assert excerpt_in_page('La demanda creció en la región, dijo "la cámara"', page)


def test_an_excerpt_cut_with_an_ellipsis_needs_every_piece() -> None:
    page = "<p>El kilo cuesta 24 pesos. Más abajo: en Puebla subió el maíz.</p>"

    assert excerpt_in_page("El kilo cuesta 24 pesos … en Puebla subió el maíz", page)
    assert not excerpt_in_page("El kilo cuesta 24 pesos … en Tlaxcala", page)


def test_a_different_text_or_an_empty_page_is_not_a_match() -> None:
    assert not excerpt_in_page(
        "El kilo cuesta 30 pesos", "<p>El kilo cuesta 24 pesos</p>"
    )
    assert not excerpt_in_page("El kilo cuesta 24 pesos", "")
    assert not excerpt_in_page(
        "El kilo cuesta 24 pesos", "<script>El kilo cuesta 24 pesos</script>"
    )


def test_only_web_sources_are_sampled_up_to_the_limit_in_report_order() -> None:
    sources = [
        _source("s1"),
        _source("d1", origin="dueño"),
        _source("s2"),
        _source("s3"),
        _source("s4"),
    ]

    picked = pick_sources(_report(sources), limit=3)

    assert [item.source_id for item in picked] == ["s1", "s2", "s3"]


def test_each_sampled_source_says_appears_does_not_appear_or_not_checked() -> None:
    report = _report([_source("s1"), _source("s2"), _source("s3")])
    pages = {
        "s1": "<p>El kilo de tortilla cuesta 24 pesos en Puebla (s1)</p>",
        "s2": "<p>Página sin la cita</p>",
    }

    checks = check_sources(report, pages)

    assert [(item.source_id, item.result) for item in checks] == [
        ("s1", "aparece"),
        ("s2", "no_aparece"),
        ("s3", "sin_revisar"),
    ]
    assert checks[0].url == "https://ejemplo-s1.test/precios"
    assert checks[0].publisher == "Medio s1"


def test_flow_check_sources_reads_the_saved_report_by_its_reference(
    tmp_path: Path,
) -> None:
    save_report(_report([_source("s1"), _source("s2")]), tmp_path)
    reference = load_index(tmp_path)[0].reference

    first = run(
        {"action": "check_sources", "base_path": str(tmp_path), "reference": reference}
    )
    second = run(
        {
            "action": "check_sources",
            "base_path": str(tmp_path),
            "reference": reference,
            "pages": {
                "s1": "El kilo de tortilla cuesta 24 pesos en Puebla (s1)",
                "s2": "otra cosa",
            },
        }
    )

    assert first.errors == []
    assert [item.result for item in first.source_checks] == ["sin_revisar"] * 2
    assert "ábrelas" in first.message or "Abre" in first.message
    assert second.errors == []
    assert [item.result for item in second.source_checks] == ["aparece", "no_aparece"]
    assert "1 con la cita" in second.message
    assert "1 sin ella" in second.message


def test_flow_check_sources_refuses_an_unknown_or_unreadable_report(
    tmp_path: Path,
) -> None:
    path = save_report(_report([_source("s1")]), tmp_path)
    reference = load_index(tmp_path)[0].reference

    unknown = run(
        {
            "action": "check_sources",
            "base_path": str(tmp_path),
            "reference": ".escala/my-company/research/otro.md",
        }
    )
    path.with_suffix(".json").write_text("{roto", encoding="utf-8")
    unreadable = run(
        {"action": "check_sources", "base_path": str(tmp_path), "reference": reference}
    )

    assert unknown.errors == ["unknown_report"]
    assert unreadable.errors == ["detail_unreadable"]
