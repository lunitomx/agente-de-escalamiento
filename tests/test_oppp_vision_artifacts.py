"""Acceptance tests for S65.4 narrative OPPP and Vision artifacts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from validators.oppp_vision_artifacts import (
    ArtifactConfirmation,
    NarrativeAnswer,
    build_narrative_artifact,
    request_confirmed_persistence,
)


def _known(text: str, origin: str = "personal-statement") -> dict[str, str]:
    return {"status": "known", "text": text, "origin": origin}


def test_oppp_draft_preserves_detailed_personal_answers_and_visible_gaps() -> None:
    artifact = build_narrative_artifact(
        "procedure.build-leader-oppp",
        {
            "relationships": _known(
                "Reservaré una cena sin teléfono cada miércoles con mi pareja."
            ),
            "achievements": {"status": "unknown"},
            "rituals": _known(
                "Caminaré treinta minutos antes de abrir el correo cada mañana."
            ),
            "wealth": {"status": "unknown"},
        },
        commitments={
            "owner": _known("La líder revisará el plan cada viernes."),
            "kpi": {"status": "unknown"},
            "who_what_when": _known(
                "La líder agenda las cenas antes del primer lunes del mes."
            ),
            "review_cadence": _known("Revisión personal semanal los viernes."),
        },
    )

    assert artifact.context == "personal"
    assert artifact.persistence.mode == "proposed"
    assert artifact.fields["relationships"].text.startswith("Reservaré")
    assert {"achievements", "wealth", "kpi"}.issubset(artifact.open_questions)
    assert artifact.assumptions == []


def test_vision_keeps_company_local_fact_separate_from_model_hypothesis() -> None:
    artifact = build_narrative_artifact(
        "procedure.build-vision-summary",
        {
            "purpose": _known(
                "Ayudamos a clínicas a reducir esperas y errores de coordinación.",
                "company-local",
            ),
            "customer": _known(
                "Creemos que las clínicas regionales valorarán más trazabilidad.",
                "model-hypothesis",
            ),
            "differentiator": {"status": "unknown"},
            "future_direction": _known(
                "Buscamos una oferta repetible en tres ciudades durante dos años.",
                "company-local",
            ),
        },
        commitments={
            "owner": _known(
                "La dirección valida esta propuesta con el equipo.", "company-local"
            ),
            "kpi": {"status": "unknown"},
            "who_what_when": {"status": "unknown"},
            "review_cadence": _known(
                "El equipo revisa la visión cada trimestre.", "company-local"
            ),
        },
    )

    assert artifact.context == "company"
    assert artifact.fields["purpose"].origin == "company-local"
    assert artifact.fields["customer"].origin == "model-hypothesis"
    assert artifact.assumptions == ["customer"]
    assert {"differentiator", "kpi", "who_what_when"}.issubset(artifact.open_questions)


@pytest.mark.parametrize("value", ["1", "2", "3", "4", "5"])
def test_likert_number_cannot_replace_a_narrative_answer(value: str) -> None:
    with pytest.raises(
        ValidationError, match="narrative answer cannot be a Likert score"
    ):
        NarrativeAnswer.model_validate(
            {"status": "known", "text": value, "origin": "personal-statement"}
        )


def test_unknown_answer_cannot_hide_text_or_origin() -> None:
    with pytest.raises(
        ValidationError, match="unknown answer cannot carry text or origin"
    ):
        NarrativeAnswer.model_validate(
            {"status": "unknown", "text": "no debería estar", "origin": "company-local"}
        )


def test_personal_artifact_rejects_company_origin_and_missing_detail() -> None:
    with pytest.raises(
        ValueError, match="personal artifact accepts only personal statements"
    ):
        build_narrative_artifact(
            "procedure.build-leader-oppp",
            {
                "relationships": _known(
                    "Una respuesta detallada para relaciones.", "company-local"
                ),
                "achievements": {"status": "unknown"},
                "rituals": {"status": "unknown"},
                "wealth": {"status": "unknown"},
            },
            commitments={
                "owner": {"status": "unknown"},
                "kpi": {"status": "unknown"},
                "who_what_when": {"status": "unknown"},
                "review_cadence": {"status": "unknown"},
            },
        )


def test_confirmation_is_required_before_confirmed_persistence() -> None:
    artifact = build_narrative_artifact(
        "procedure.build-vision-summary",
        {
            "purpose": _known(
                "Ayudamos a dueños a tener operaciones más claras.", "company-local"
            ),
            "customer": {"status": "unknown"},
            "differentiator": {"status": "unknown"},
            "future_direction": {"status": "unknown"},
        },
        commitments={
            "owner": {"status": "unknown"},
            "kpi": {"status": "unknown"},
            "who_what_when": {"status": "unknown"},
            "review_cadence": {"status": "unknown"},
        },
    )

    with pytest.raises(ValueError, match="explicit human confirmation is required"):
        request_confirmed_persistence(artifact, None)

    request = request_confirmed_persistence(
        artifact,
        ArtifactConfirmation(
            confirmation_id="confirmation.vision.owner",
            consent_receipt="consent.local.vision",
            confirmed_by="person.company.owner",
        ),
    )
    assert request.mode == "confirmed"
    assert request.path == "state/company/strategy.yaml"
    assert request.writes_state is False
