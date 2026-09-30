"""Research report: short result, always ends in a decision, saved only with a yes.

Synthetic data only; files go to a pytest temporary folder.
"""

from __future__ import annotations

import shutil
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from coaching.research import messages
from coaching.research.models import (
    DecisionOption,
    ResearchClaim,
    ResearchFrame,
    ResearchReport,
    SourceRecord,
    without_urls,
)
from coaching.research.report import (
    build_report,
    load_index,
    load_saved_report,
    render_markdown,
    report_message,
    save_report,
)

ROOT = Path(__file__).resolve().parents[3]
TODAY = date(2026, 9, 30)
JARGON = (
    "triangul",
    "TAM",
    "módulo",
    "escala-strategy-research",
    "benchmark",
    "por_confirmar",
)


def _frame(search_mode: str = "web") -> ResearchFrame:
    return ResearchFrame.model_validate(
        {
            "concern": "Creo que cobro poco",
            "question": "¿Cobro menos que negocios parecidos en Puebla?",
            "decision_informed": "Subir o no el precio del kilo en enero",
            "mode": "benchmark",
            "decision_area": "cash",
            "offer_category": "tortillas de maíz",
            "geography": "Puebla",
            "queries": ["precios de tortillas de maíz en Puebla 2026"],
            "search_mode": search_mode,
            "confirmed": True,
        }
    )


def _source(source_id: str, publisher: str, origin: str = "web") -> SourceRecord:
    return SourceRecord.model_validate(
        {
            "source_id": source_id,
            "origin": origin,
            "title": f"Precios {source_id}",
            "publisher": publisher,
            "url": f"https://ejemplo-{source_id}.test/precios"
            if origin == "web"
            else None,
            "published_on": (TODAY - timedelta(days=20)).isoformat(),
            "consulted_on": TODAY.isoformat(),
            "excerpt": f"El kilo cuesta 24 pesos ({source_id})",
        }
    )


WEB = [
    _source("s1", "Diario Uno"),
    _source("s2", "Revista Dos"),
    _source("s3", "Cámara Tres"),
    _source("s4", "Blog Cuatro"),
]
OPTIONS = [
    DecisionOption(label="A", text="Subir 8% en enero"),
    DecisionOption(label="B", text="Mantener el precio y cambiar el paquete"),
    DecisionOption(
        label="C",
        text="Todavía no decidir",
        kind="esperar",
        missing_data="Tres cotizaciones de tortillerías de mi zona",
        by_date=date(2026, 10, 15),
    ),
]


def _claims() -> list[ResearchClaim]:
    return [
        ResearchClaim(
            text="El kilo de tortilla cuesta entre 22 y 26 pesos en Puebla.",
            kind="dato",
            supporting=["s1", "s2", "s3"],
            contrary=["s4"],
            status="por_confirmar",
        ),
        ResearchClaim(
            text="Los clientes aceptan subidas pequeñas si se avisan antes.",
            kind="supuesto",
            supporting=["s2"],
            next_source="Preguntar a cinco clientes frecuentes",
        ),
    ]


def _report(
    *,
    frame: ResearchFrame | None = None,
    sources: list[SourceRecord] | None = None,
    claims: list[ResearchClaim] | None = None,
    not_found: list[str] | None = None,
    options: list[DecisionOption] | None = None,
    recommendation: str = "A",
    chosen: str | None = None,
) -> ResearchReport:
    return build_report(
        frame=frame or _frame(),
        researched_on=TODAY,
        sources=WEB if sources is None else sources,
        claims=_claims() if claims is None else claims,
        not_found=(
            ["Precios publicados de tortillerías de la colonia"]
            if not_found is None
            else not_found
        ),
        options=OPTIONS if options is None else options,
        recommendation=recommendation,
        recommendation_reason="tu precio está abajo del rango y el costo del maíz subió",
        chosen=chosen,
    )


def test_build_report_regrades_claims_and_sets_the_review_date() -> None:
    report = _report()

    assert report.claims[0].status == "confirmado"
    assert report.claims[0].confidence == "media"  # contrary evidence
    assert report.claims[1].status == "por_confirmar"
    assert report.review_by == date(2026, 12, 29)


def test_report_needs_a_confirmed_frame() -> None:
    with pytest.raises(ValidationError, match="frame_not_confirmed"):
        _report(frame=_frame().model_copy(update={"confirmed": False}))


def test_report_holds_at_most_three_findings_and_two_or_three_options() -> None:
    claim = _claims()[1]
    with pytest.raises(ValidationError):
        _report(claims=[claim, claim, claim, claim])
    with pytest.raises(ValidationError):
        _report(options=OPTIONS[:1])


def test_recommendation_must_be_one_of_the_options() -> None:
    with pytest.raises(ValidationError, match="recommendation_not_an_option"):
        _report(recommendation="Z")


def test_claims_must_cite_known_sources() -> None:
    bad = ResearchClaim(
        text="Algo sin fuente conocida", kind="dato", supporting=["fantasma"]
    )
    with pytest.raises(ValidationError, match="unknown_source"):
        _report(claims=[bad])


def test_message_shows_certainty_contrary_not_found_and_ends_in_a_decision() -> None:
    text = report_message(_report())

    assert "**Confirmado**" in text
    assert "**Por confirmar**" in text
    assert "Supuesto" in text
    assert "Blog Cuatro" in text  # lo que dice lo contrario
    assert "Lo que dice lo contrario" in text
    assert "Lo que no encontré" in text
    assert "Precios publicados de tortillerías de la colonia" in text
    assert "A) Subir 8% en enero" in text
    assert "Tres cotizaciones de tortillerías de mi zona" in text
    assert "15 de octubre de 2026" in text
    assert "Te recomiendo A" in text
    assert text.rstrip().endswith("¿Cuál tomas?")
    for word in JARGON:
        assert word not in text


def test_message_says_so_when_nothing_contradicts_or_is_missing() -> None:
    claims = [c.model_copy(update={"contrary": []}) for c in _claims()]
    text = report_message(_report(claims=claims, not_found=[]))

    assert messages.NOTHING_CONTRARY in text
    assert messages.NOTHING_MISSING in text


def test_without_search_only_owner_sources_count_and_the_limit_opens_the_report() -> (
    None
):
    owner = [
        _source("d1", "Cotización de proveedor", origin="dueño"),
        _source("d2", "Lista de precios pegada", origin="archivo_empresa"),
    ]
    claims = [
        ResearchClaim(
            text="El kilo cuesta 24 pesos con mi proveedor.",
            kind="dato",
            supporting=["d1", "d2"],
            next_source="El link de precios de una tortillería de tu zona",
        )
    ]
    report = _report(frame=_frame("sin_busqueda"), sources=owner, claims=claims)

    assert report.limits[0] == messages.no_search_limit(2)
    text = report_message(report)
    assert text.startswith(messages.no_search_limit(2))
    assert "El link de precios de una tortillería de tu zona" in text


def test_without_search_a_web_source_is_refused() -> None:
    with pytest.raises(ValidationError, match="web_source_without_search"):
        _report(frame=_frame("sin_busqueda"), claims=[])


def test_without_search_every_open_finding_says_what_would_confirm_it() -> None:
    owner = [_source("d1", "Cotización", origin="dueño")]
    claims = [
        ResearchClaim(text="El kilo cuesta 24 pesos.", kind="dato", supporting=["d1"])
    ]
    with pytest.raises(ValidationError, match="por_confirmar_needs_next_source"):
        _report(frame=_frame("sin_busqueda"), sources=owner, claims=claims)


def test_markdown_keeps_sources_urls_excerpts_and_searches() -> None:
    report = _report(chosen="A")
    text = render_markdown(report)

    assert "https://ejemplo-s1.test/precios" in text
    assert "El kilo cuesta 24 pesos (s1)" in text
    assert "precios de tortillas de maíz en Puebla 2026" in text
    assert "Subir 8% en enero" in text
    assert "29 de diciembre de 2026" in text


def test_chosen_option_must_exist() -> None:
    with pytest.raises(ValueError, match="chosen_not_an_option"):
        _report(chosen="Z")


def test_save_requires_a_chosen_option(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="needs_chosen_option"):
        save_report(_report(), tmp_path)
    assert not (tmp_path / ".escala").exists()


def test_save_writes_report_and_index_entry_without_urls(tmp_path: Path) -> None:
    report = _report(chosen="C")

    path = save_report(report, tmp_path)
    again = save_report(report, tmp_path)

    assert path == tmp_path / ".escala/my-company/research/2026-09-30-benchmark.md"
    assert again.name == "2026-09-30-benchmark-2.md"
    assert "Todavía no decidir" in path.read_text(encoding="utf-8")
    entries = load_index(tmp_path)
    assert [entry.reference for entry in entries] == [
        ".escala/my-company/research/2026-09-30-benchmark.md",
        ".escala/my-company/research/2026-09-30-benchmark-2.md",
    ]
    assert entries[0].decision_area == "cash"
    assert entries[0].review_by == date(2026, 12, 29)
    assert "Tres cotizaciones" in entries[0].decision
    index_text = (tmp_path / ".escala/my-company/research/index.yaml").read_text(
        encoding="utf-8"
    )
    assert "http" not in index_text
    assert yaml.safe_load(index_text)["entries"]


def test_unreadable_index_is_treated_as_empty(tmp_path: Path) -> None:
    folder = tmp_path / ".escala/my-company/research"
    folder.mkdir(parents=True)
    (folder / "index.yaml").write_text("entries: [roto", encoding="utf-8")

    assert load_index(tmp_path) == []


def test_research_folder_is_ignored_by_git() -> None:
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")

    result = subprocess.run(
        ["git", "check-ignore", "-q", ".escala/my-company/research/index.yaml"],
        cwd=ROOT,
        check=False,
    )

    assert result.returncode == 0


def test_save_keeps_the_structured_report_next_to_the_markdown(
    tmp_path: Path,
) -> None:
    """E83 S83.5: the next diagnosis reads the report without parsing Markdown."""
    report = _report(chosen="A")

    path = save_report(report, tmp_path)

    structured = path.with_suffix(".json")
    assert structured.exists()
    assert load_saved_report(tmp_path, load_index(tmp_path)[0]) == report


def test_saved_report_that_is_missing_or_broken_reads_as_none(
    tmp_path: Path,
) -> None:
    save_report(_report(chosen="A"), tmp_path)
    entry = load_index(tmp_path)[0]
    structured = tmp_path / entry.reference.replace(".md", ".json")

    structured.write_text("{roto", encoding="utf-8")
    assert load_saved_report(tmp_path, entry) is None
    structured.unlink()
    assert load_saved_report(tmp_path, entry) is None


def test_index_never_keeps_a_url_even_inside_the_decision_text(
    tmp_path: Path,
) -> None:
    """E83 S83.5: URLs do not leave the report, whatever text they come in."""
    options = [
        DecisionOption(
            label="A", text="Copiar el paquete de https://competidor.test/paquetes"
        ),
        DecisionOption(label="B", text="Ver www.otro.test/precios y decidir"),
    ]

    save_report(_report(options=options, chosen="A"), tmp_path)
    save_report(_report(options=options, recommendation="B", chosen="B"), tmp_path)

    index_text = (tmp_path / ".escala/my-company/research/index.yaml").read_text(
        encoding="utf-8"
    )
    assert "http" not in index_text
    assert "www." not in index_text
    assert "competidor.test" not in index_text
    assert "(enlace en el reporte)" in index_text
    assert "Copiar el paquete de" in index_text


def test_without_urls_leaves_plain_text_and_publishers_alone() -> None:
    assert without_urls("Subir 8% en enero") == "Subir 8% en enero"
    assert without_urls("según INEGI y Diario Uno") == "según INEGI y Diario Uno"
    assert (
        without_urls("ver HTTPS://X.test/a?b=1, luego decidir")
        == "ver (enlace en el reporte), luego decidir"
    )
    assert without_urls("en ejemplo.test/precios hay más") == (
        "en (enlace en el reporte) hay más"
    )
