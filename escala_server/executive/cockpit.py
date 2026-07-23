"""Deterministic local executive cockpit projection and writer."""

from __future__ import annotations

import hashlib
import html
import json
import os
from pathlib import Path
import tempfile

from ..workspace.authority import (
    WorkspaceAuthorityError,
    WorkspaceConfig,
    validate_workspace,
)
from .models import (
    CockpitArtifact,
    CockpitCard,
    DECISIONS,
    ExecutiveCockpit,
    ExecutiveDiagnostic,
    PainDrillDown,
)


def build_cockpit(diagnostic: ExecutiveDiagnostic) -> ExecutiveCockpit:
    """Build four cards and select the lowest supported score as focus."""

    cards: list[CockpitCard] = []
    for assessment in diagnostic.assessments:
        action = (
            assessment.questions[0]
            if assessment.questions
            else f"Revisar {assessment.decision} con /escala-{assessment.decision}."
        )
        cards.append(
            CockpitCard(
                decision=assessment.decision,
                score=assessment.score,
                status=assessment.evidence_status,
                freshness=assessment.freshness,
                evidence_count=assessment.evidence_count,
                blockers=assessment.blockers,
                questions=assessment.questions,
                recommended_action=action,
            )
        )

    supported = [
        card for card in cards if card.score is not None and card.status == "supported"
    ]
    focus = min(
        supported,
        key=lambda card: (
            card.score if card.score is not None else 101,
            DECISIONS.index(card.decision),
        ),
        default=None,
    )
    if focus is None:
        drill_down = PainDrillDown(
            next_action="Responder las preguntas materiales antes de declarar un dolor de la empresa."
        )
        status = (
            "unresolved" if diagnostic.status == "unresolved" else "evidence_limited"
        )
    else:
        drill_down = PainDrillDown(
            decision=focus.decision,
            score=focus.score,
            source_ids=next(
                item.source_ids
                for item in diagnostic.assessments
                if item.decision == focus.decision
            ),
            freshness=focus.freshness,
            blockers=focus.blockers,
            questions=focus.questions,
            next_action=focus.recommended_action,
        )
        status = diagnostic.status
    return ExecutiveCockpit(
        cards=tuple(cards),
        focus_decision=focus.decision if focus else None,
        drill_down=drill_down,
        status=status,
    )


def render_cockpit_json(cockpit: ExecutiveCockpit) -> str:
    """Render stable JSON without timestamps or machine paths."""

    return json.dumps(
        cockpit.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def render_cockpit_html(cockpit: ExecutiveCockpit) -> str:
    """Render an escaped, self-contained HTML cockpit."""

    cards: list[str] = []
    for card in cockpit.cards:
        score = "No evaluado" if card.score is None else f"{card.score}/100"
        blockers = ", ".join(card.blockers) if card.blockers else "Ninguno reportado"
        questions = (
            " ".join(card.questions) if card.questions else "Sin preguntas pendientes."
        )
        cards.append(
            '<article class="decision-card" data-decision="'
            f'{html.escape(card.decision)}">'
            f"<h2>{html.escape(card.decision.title())}</h2>"
            f'<p class="score">{html.escape(score)}</p>'
            f"<p>Status: <strong>{html.escape(card.status)}</strong></p>"
            f"<p>Freshness: {html.escape(card.freshness)} · Evidence: {card.evidence_count}</p>"
            f"<p>Blockers: {html.escape(blockers)}</p>"
            f"<p>Questions: {html.escape(questions)}</p>"
            f"<p>Next: {html.escape(card.recommended_action)}</p>"
            "</article>"
        )
    focus = html.escape(cockpit.focus_decision or "Sin foco soportado")
    drill = cockpit.drill_down
    source_ids = (
        ", ".join(drill.source_ids) if drill.source_ids else "Ninguna fuente atribuida"
    )
    blockers = ", ".join(drill.blockers) if drill.blockers else "Ninguno reportado"
    questions = (
        " ".join(drill.questions) if drill.questions else "Sin preguntas pendientes."
    )
    return (
        "<!doctype html>\n"
        '<html lang="es"><head><meta charset="utf-8">'
        "<title>ESCALA Executive Cockpit</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem}"
        ".cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}"
        ".decision-card{border:1px solid #ccd4dd;border-radius:10px;padding:1rem}"
        ".score{font-size:2rem;font-weight:700;margin:.25rem 0}</style></head><body>"
        "<main><h1>ESCALA Executive Cockpit</h1>"
        f'<p data-status="{html.escape(cockpit.status)}">Estado: {html.escape(cockpit.status)}</p>'
        f'<section aria-labelledby="focus"><h2 id="focus">Foco recomendado: {focus}</h2>'
        f"<p>Fuentes: {html.escape(source_ids)}</p>"
        f"<p>Freshness: {html.escape(drill.freshness)} · Blockers: {html.escape(blockers)}</p>"
        f"<p>Questions: {html.escape(questions)}</p>"
        f"<p>Next: {html.escape(drill.next_action)}</p></section>"
        f'<section class="cards" aria-label="Four decisions">{"".join(cards)}</section>'
        "</main></body></html>\n"
    )


def write_cockpit(
    config: WorkspaceConfig, cockpit: ExecutiveCockpit
) -> CockpitArtifact:
    """Write the cockpit only under validated installer-local data root."""

    receipt = validate_workspace(config)
    if receipt.status != "pass":
        code = receipt.findings[0].code if receipt.findings else "workspace_invalid"
        raise WorkspaceAuthorityError(code)
    output_dir = (
        config.data_root.expanduser().resolve(strict=False) / ".escala-executive"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    html_bytes = render_cockpit_html(cockpit).encode("utf-8")
    json_bytes = (render_cockpit_json(cockpit) + "\n").encode("utf-8")
    _atomic_write(output_dir / "cockpit.html", html_bytes)
    _atomic_write(output_dir / "cockpit.json", json_bytes)
    return CockpitArtifact(
        html_path=".escala-executive/cockpit.html",
        json_path=".escala-executive/cockpit.json",
        content_sha256=hashlib.sha256(html_bytes + json_bytes).hexdigest(),
    )


def _atomic_write(path: Path, content: bytes) -> None:
    """Write bytes using a same-directory temporary file and replace."""

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
