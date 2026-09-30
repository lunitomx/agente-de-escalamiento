# pyright: strict
"""Build, show and save a research report (E83 S83.1).

The report is written by this module, never by the private specialist, and
only after the owner chose an option. It lives in
``.escala/my-company/research/AAAA-MM-DD-<modo>.md`` (git-ignored) with one
line in ``index.yaml``. URLs stay inside the report; the index keeps only the
local reference, the decision and the review date.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import cast

import yaml
from pydantic import ValidationError

from coaching.research import messages
from coaching.research.engine import grade_claim, review_date
from coaching.research.models import (
    DecisionOption,
    IndexEntry,
    ResearchClaim,
    ResearchFrame,
    ResearchReport,
    SourceRecord,
)

RESEARCH_DIR = Path(".escala") / "my-company" / "research"
INDEX_NAME = "index.yaml"


def build_report(
    *,
    frame: ResearchFrame,
    researched_on: date,
    sources: list[SourceRecord],
    claims: list[ResearchClaim],
    options: list[DecisionOption],
    recommendation: str,
    recommendation_reason: str,
    not_found: list[str] | None = None,
    limits: list[str] | None = None,
    chosen: str | None = None,
) -> ResearchReport:
    """Grade every claim from its sources and assemble a validated report.

    Without web search the first limit always says so and how many of the
    owner's sources were used. ``chosen`` is the label of the owner's option.
    """
    by_id = {source.source_id: source for source in sources}
    graded = [grade_claim(claim, by_id, researched_on) for claim in claims]
    all_limits = list(limits or [])
    if frame.search_mode == "sin_busqueda":
        line = messages.no_search_limit(len(sources))
        all_limits = [line, *(item for item in all_limits if item != line)]
    picked = None
    if chosen is not None:
        picked = next((option for option in options if option.label == chosen), None)
        if picked is None:
            raise ValueError("chosen_not_an_option")
    return ResearchReport(
        frame=frame,
        researched_on=researched_on,
        sources=sources,
        claims=graded,
        not_found=list(not_found or []),
        limits=all_limits,
        options=options,
        recommendation=recommendation,
        recommendation_reason=recommendation_reason,
        chosen=picked,
        review_by=review_date(researched_on),
    )


def _cite(report: ResearchReport, ids: list[str]) -> str:
    by_id = {source.source_id: source for source in report.sources}
    parts: list[str] = []
    for source_id in ids:
        source = by_id[source_id]
        when = (
            messages.spanish_date(source.published_on)
            if source.published_on
            else "sin fecha"
        )
        parts.append(f"{source.publisher}, {when}")
    return "; ".join(parts)


_KIND_LABEL = {"dato": "", "supuesto": "Supuesto: ", "inferencia": "Deducción: "}
_STATUS_LABEL = {"confirmado": "**Confirmado**", "por_confirmar": "**Por confirmar**"}


def _finding(report: ResearchReport, claim: ResearchClaim) -> str:
    line = f"- {_STATUS_LABEL[claim.status]} — {_KIND_LABEL[claim.kind]}{claim.text}"
    if claim.supporting:
        line += f" (según {_cite(report, claim.supporting)})"
    if claim.status == "por_confirmar" and claim.next_source:
        line += f" Lo confirmaría: {claim.next_source}."
    return line


def _option(option: DecisionOption) -> str:
    text = f"{option.label}) {option.text}"
    if option.kind == "esperar" and option.missing_data and option.by_date:
        text += (
            f": antes consigo {option.missing_data} para el "
            f"{messages.spanish_date(option.by_date)}"
        )
    return text


def _contrary(report: ResearchReport) -> list[str]:
    return [
        f"- {claim.text} → lo contradice {_cite(report, claim.contrary)}"
        for claim in report.claims
        if claim.contrary
    ]


def report_message(report: ResearchReport) -> str:
    """The short result shown to the owner; it always ends asking the decision."""
    blocks: list[str] = []
    if report.limits:
        blocks.append("\n".join(report.limits))
    blocks.append(
        "Lo que encontré:\n"
        + "\n".join(_finding(report, claim) for claim in report.claims)
        if report.claims
        else "Lo que encontré: nada que pueda sostener con fuentes."
    )
    contrary = _contrary(report)
    blocks.append(
        "Lo que dice lo contrario:\n"
        + ("\n".join(contrary) if contrary else messages.NOTHING_CONTRARY)
    )
    blocks.append(
        "Lo que no encontré:\n"
        + (
            "\n".join(f"- {item}" for item in report.not_found)
            if report.not_found
            else messages.NOTHING_MISSING
        )
    )
    blocks.append(
        "Con esto tus opciones son:\n"
        + "\n".join(_option(option) for option in report.options)
    )
    blocks.append(
        f"Te recomiendo {report.recommendation} porque "
        f"{report.recommendation_reason}. ¿Cuál tomas?"
    )
    return "\n\n".join(blocks)


def render_markdown(report: ResearchReport) -> str:
    """The readable report saved in the company folder (URLs live only here)."""
    frame = report.frame
    lines = [
        f"# {frame.question}",
        "",
        f"- Fecha: {messages.spanish_date(report.researched_on)}",
        f"- Decisión que informa: {frame.decision_informed}",
        f"- Revisar antes del: {messages.spanish_date(report.review_by)}",
        "",
        report_message(report),
        "",
    ]
    if report.chosen is not None:
        lines += ["## Decisión tomada", "", _option(report.chosen), ""]
    lines += ["## Fuentes", ""]
    for source in report.sources:
        where = f" — {source.url}" if source.url else ""
        when = (
            messages.spanish_date(source.published_on)
            if source.published_on
            else "sin fecha"
        )
        lines.append(
            f"- [{source.source_id}] {source.title} ({source.publisher}, {when}){where}"
            f"\n  > {source.excerpt}"
        )
    if frame.queries:
        lines += ["", "## Búsquedas", ""]
        lines += [f"- {query}" for query in frame.queries]
    return "\n".join(lines) + "\n"


def _index_path(base: Path) -> Path:
    return base / RESEARCH_DIR / INDEX_NAME


def load_index(base: Path) -> list[IndexEntry]:
    """Saved research references, or an empty list if missing or unreadable."""
    try:
        raw: object = yaml.safe_load(_index_path(base).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return []
    if not isinstance(raw, dict):
        return []
    items = cast(dict[str, object], raw).get("entries")
    if not isinstance(items, list):
        return []
    try:
        return [IndexEntry.model_validate(item) for item in cast(list[object], items)]
    except ValidationError:
        return []


def _free_path(folder: Path, stem: str) -> Path:
    path = folder / f"{stem}.md"
    counter = 2
    while path.exists():
        path = folder / f"{stem}-{counter}.md"
        counter += 1
    return path


def save_report(report: ResearchReport, base: Path) -> Path:
    """Write the report and its index line; requires the owner's chosen option."""
    if report.chosen is None:
        raise ValueError("needs_chosen_option")
    folder = base / RESEARCH_DIR
    folder.mkdir(parents=True, exist_ok=True)
    path = _free_path(folder, f"{report.researched_on.isoformat()}-{report.frame.mode}")
    path.write_text(render_markdown(report), encoding="utf-8")
    entry = IndexEntry(
        reference=(RESEARCH_DIR / path.name).as_posix(),
        mode=report.frame.mode,
        question=report.frame.question,
        decision_area=report.frame.decision_area,
        decision=_option(report.chosen),
        researched_on=report.researched_on,
        review_by=report.review_by,
    )
    entries = [*load_index(base), entry]
    _index_path(base).write_text(
        yaml.safe_dump(
            {"entries": [item.model_dump(mode="json") for item in entries]},
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path
