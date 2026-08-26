"""E30 contract tests for longitudinal Accountability Groups."""

from __future__ import annotations

import sqlite3

from escala_server.accountability import AccountabilityStore

SYNTHETIC_WORKSHEET = """
Accountability Group Sharing Worksheet
UPDATE
Personal: Tuve una semana tranquila.
Business: Cerramos la primera prueba con tres clientes.
Accountability Group Sharing
1. Issue Statement
What is the situation you want to share with the group?
El lanzamiento se sigue moviendo porque el alcance no está claro.
2. What Scaling Up Pillar (People, Strategy, Execution or Cash) and/or tool does this issue relate to?
Have you tried to implement the tool? Yes or No?
Strategy; probamos el plan en una hoja.
3. Overview of Presentation
Background
Validamos demanda en entrevistas.
Current Situation
Tenemos dos alternativas de producto.
Future Options
Elegir una audiencia o probar dos mensajes.
4. Digging Deeper
Where do you feel most uncertain, confused or afraid?
No sé cuál evidencia es suficiente.
How might your own actions be contributing to the challenge you face?
He postergado fijar una fecha.
What would failing in this issue mean for you and those around you?
Perderíamos un trimestre.
What is your biggest personal challenge in facing this situation? What feelings do you have about the situation?
Quiero evitar el perfeccionismo.
What is the outcome you hope for? What is your level of confidence right now that you can achieve this outcome on a scale of 0-100 (0%: no hope; 100%: completely confident)?
Elegir una opción con evidencia. Tengo 90% de confianza.
Notes:
Probar el mensaje con cinco clientes.
"""


def _session(store: AccountabilityStore, *, held_on: str, tag: str = "foco") -> str:
    result = store.create_session(
        {
            "business_update": "Validamos una oferta con clientes reales",
            "issue_statement": "Necesitamos elegir un solo segmento",
            "pillar_and_tool": "Strategy y plan en una hoja",
            "desired_outcome": "Elegir el segmento y ejecutar una prueba",
            "confidence": 90,
        },
        held_on=held_on,
        tags=[tag],
        explicit_confirmation=True,
    )
    assert result.ready and result.data
    return result.data["id"]


def _commitment(store: AccountabilityStore, session_id: str, *, due_on: str) -> str:
    result = store.add_commitment(
        session_id,
        statement="Entrevistar cinco clientes del segmento elegido",
        owner="Eduardo",
        due_on=due_on,
        success_measure="Cinco entrevistas documentadas",
        explicit_confirmation=True,
    )
    assert result.ready and result.data
    return result.data["commitment_id"]


def test_import_is_preview_only_warns_and_requires_explicit_confirmation(tmp_path):
    store = AccountabilityStore(tmp_path)
    preview = store.preview_import(
        SYNTHETIC_WORKSHEET + " El presupuesto es USD 10,000.",
        title="Accountability sintético",
        held_on="2026-08-01",
        source_type="drive_connector",
    )

    assert preview.worksheet["decision_area"] == "strategy"
    assert preview.worksheet["confidence"] == 90
    assert "finanzas" in preview.warnings
    assert {"business_update", "issue_statement", "desired_outcome"} <= set(
        preview.recognized_fields
    )
    assert not store.runtime.db_path.exists()
    assert not store.confirm_import(preview, explicit_confirmation=False).ready
    assert not store.runtime.db_path.exists()

    saved = store.confirm_import(preview, explicit_confirmation=True)
    assert saved.ready and saved.data
    assert saved.data["source"]["type"] == "drive_connector"
    assert saved.data["source"]["consented_at"]
    assert saved.data["worksheet"]["personal_update"] == "Tuve una semana tranquila."


def test_commitment_requires_who_when_measure_and_review_evidence(tmp_path):
    store = AccountabilityStore(tmp_path)
    session_id = _session(store, held_on="2026-08-01")
    no = store.add_commitment(
        session_id,
        statement="Entrevistar clientes",
        owner="Eduardo",
        due_on="2026-08-15",
        success_measure="Cinco entrevistas",
        explicit_confirmation=False,
    )
    assert not no.ready
    commitment_id = _commitment(store, session_id, due_on="2026-08-15")

    invalid = store.review_commitment(
        commitment_id,
        status="done",
        result="Terminamos",
        evidence=None,
        blocker=None,
        learning=None,
        reviewed_on="2026-08-14",
        explicit_confirmation=True,
    )
    assert not invalid.ready and "evidence" in invalid.reason

    reviewed = store.review_commitment(
        commitment_id,
        status="done",
        result="Entrevistamos a los cinco clientes",
        evidence="Notas de cinco entrevistas",
        blocker=None,
        learning="El segmento valora rapidez",
        reviewed_on="2026-08-14",
        explicit_confirmation=True,
    )
    assert reviewed.ready and reviewed.data
    rubric = reviewed.data["rubric"]
    assert rubric["percent"] == 100
    assert rubric["derived"] is True
    assert rubric["criteria"]["result"] == {
        "points": 50,
        "max": 50,
        "reason": "done",
    }


def test_patterns_need_two_sessions_and_exclusion_is_reversible(tmp_path):
    store = AccountabilityStore(tmp_path)
    first = _session(store, held_on="2026-07-01", tag="perfeccionismo")
    first_commitment = _commitment(store, first, due_on="2026-07-15")
    assert store.review_commitment(
        first_commitment,
        status="not_done",
        result="No se completó",
        evidence=None,
        blocker="El alcance no estaba claro",
        learning="Definir alcance antes de comprometer fecha",
        reviewed_on="2026-07-16",
        explicit_confirmation=True,
    ).ready

    one = store.patterns()
    assert one.ready and one.data
    assert one.data["patterns"] == []
    assert any(item["kind"] == "decision_frequency" for item in one.data["observations"])

    second = _session(store, held_on="2026-08-01", tag="perfeccionismo")
    second_commitment = _commitment(store, second, due_on="2026-08-15")
    assert store.review_commitment(
        second_commitment,
        status="partial",
        result="Hicimos tres entrevistas",
        evidence="Tres notas de entrevista",
        blocker="El alcance no estaba claro",
        learning="Reservar tiempo en calendario",
        reviewed_on="2026-08-14",
        explicit_confirmation=True,
    ).ready

    two = store.patterns().data
    assert two
    kinds = {item["kind"] for item in two["patterns"]}
    assert {"decision_frequency", "confirmed_theme", "repeated_blocker", "confidence_gap"} <= kinds
    repeated = next(item for item in two["patterns"] if item["kind"] == "repeated_blocker")
    assert repeated["count"] == 2 and set(repeated["session_ids"]) == {first, second}

    excluded = store.set_included(
        second,
        included=False,
        reason="La sesión estaba duplicada",
        explicit_confirmation=True,
    )
    assert excluded.ready and excluded.data and excluded.data["included"] is False
    after = store.patterns().data
    assert after and after["session_count"] == 1 and after["patterns"] == []

    assert store.set_included(
        second,
        included=True,
        reason="Confirmé que era una sesión distinta",
        explicit_confirmation=True,
    ).ready
    assert store.patterns().data["session_count"] == 2
    with sqlite3.connect(store.runtime.db_path) as db:
        states = [row[0] for row in db.execute(
            "SELECT state FROM accountability_exclusions WHERE session_id=? ORDER BY changed_at, rowid",
            (second,),
        )]
    assert states == ["excluded", "included"]


def test_session_can_be_corrected_without_losing_source_or_consent(tmp_path):
    store = AccountabilityStore(tmp_path)
    session_id = _session(store, held_on="2026-08-01")
    before = store.get_session(session_id).data
    corrected = store.update_session(
        session_id,
        {"issue_statement": "Necesitamos elegir un segmento premium"},
        tags=["foco", "segmento"],
        explicit_confirmation=True,
    )
    assert corrected.ready and corrected.data and before
    assert corrected.data["worksheet"]["issue_statement"].endswith("premium")
    assert corrected.data["tags"] == ["foco", "segmento"]
    assert corrected.data["source"] == before["source"]


def test_public_summary_omits_personal_and_worksheet_narratives(tmp_path):
    store = AccountabilityStore(tmp_path)
    created = store.create_session(
        {
            "personal_update": "Una situación personal delicada",
            "business_update": "Creció la venta",
            "issue_statement": "No hay dueño de cobranza",
            "pillar_and_tool": "Cash",
            "desired_outcome": "Asignar responsable",
        },
        held_on="2026-08-26",
        explicit_confirmation=True,
    )
    assert created.ready

    summary = store.public_summary()

    assert summary.ready and summary.data
    encoded = str(summary.data)
    assert "situación personal delicada" not in encoded
    assert "No hay dueño de cobranza" not in encoded
    assert summary.data["sessions"][0]["decision_area"] == "cash"
