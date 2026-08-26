"""Natural-language acceptance coverage for Accountability Groups."""

from __future__ import annotations

import sqlite3
from datetime import date

from coaching.router.conversation import run


def _complete_preparation(root) -> None:
    assert "estructura real de eo" in run(
        "quiero preparar mi accountability", base_path=root
    ).lower()
    assert "de qué fecha" in run("sí", base_path=root).lower()
    answers = (
        "hoy",
        "Estoy aprendiendo a delegar mejor",
        "Crecieron las ventas pero se atrasó la cobranza",
        "No tenemos un dueño claro para cobrar",
        "Cash, usamos el cash conversion cycle",
        "El contador prepara el reporte y ventas promete fechas",
        "Hay veinte facturas vencidas y nadie da seguimiento diario",
        "Asignar un dueño, automatizar recordatorios o cambiar condiciones",
        "No sé si ventas debe conservar la relación con el cliente",
        "He permitido excepciones sin fecha",
        "Podríamos quedarnos sin efectivo para nómina",
        "Sostener conversaciones incómodas con clientes",
        "Salir con un responsable y un proceso semanal",
        "70",
        "Revisar los cinco saldos más grandes",
        "cobranza, delegación",
    )
    for answer in answers:
        response = run(answer, base_path=root)
    assert "confirmas guardarla" in response.lower()
    assert "compromiso verificable" in run("sí", base_path=root).lower()
    assert "qué acción" in run("sí", base_path=root).lower()
    commitment = (
        "Llamar a los cinco clientes con mayor saldo",
        "Gerardo",
        "2099-09-15",
        "Cinco acuerdos de pago registrados",
    )
    for answer in commitment:
        response = run(answer, base_path=root)
    assert "¿lo confirmas?" in response.lower()
    assert "guardé el compromiso" in run("sí", base_path=root).lower()


def test_generic_accountability_request_explains_three_capabilities(tmp_path):
    response = run("¿Qué puedes hacer con mis accountability?", base_path=tmp_path)

    assert "preparar" in response.lower()
    assert "evidencia" in response.lower()
    assert "patrones" in response.lower()
    assert "cómo se llama" not in response.lower()


def test_guided_preparation_and_explainable_review(tmp_path):
    _complete_preparation(tmp_path)

    response = run("quiero calificar mi accountability", base_path=tmp_path)
    assert "¿quedó hecho" in response.lower()
    assert "resultado observable" in run("hecho", base_path=tmp_path).lower()
    assert "evidencia" in run(
        "Los cinco clientes aceptaron una fecha de pago", base_path=tmp_path
    ).lower()
    assert "evidencia concreta" in run("sin evidencia", base_path=tmp_path).lower()
    assert "bloqueo" in run(
        "CRM con los cinco acuerdos y sus fechas", base_path=tmp_path
    ).lower()
    assert "aprendizaje" in run("ninguno", base_path=tmp_path).lower()
    assert "confirmas guardar" in run(
        "Separar promesa comercial de condición de crédito", base_path=tmp_path
    ).lower()
    result = run("sí", base_path=tmp_path)

    assert "seguimiento derivado" in result.lower()
    assert "no es una opinión 1–5" in result.lower()
    database = tmp_path / ".scaleup" / "memory" / "escala.db"
    with sqlite3.connect(database) as db:
        session = db.execute(
            "SELECT held_on, source_type, status FROM accountability_sessions"
        ).fetchone()
        commitment = db.execute(
            "SELECT owner, status, follow_through_percent FROM accountability_commitments"
        ).fetchone()
    assert session == (date.today().isoformat(), "manual", "reviewed")
    assert commitment == ("Gerardo", "done", 100)


def test_import_preview_never_persists_without_confirmation(tmp_path):
    document = """Accountability Group Sharing Worksheet
Business: Ventas crecieron
What is the situation you want to share with the group? Cobranza con 2 MDP vencidos
2. What Scaling Up Pillar Cash
Have you tried to implement the tool? Yes or No? Sí
3. Overview of Presentation
Background El contador prepara reportes
Current Situation No hay dueño
Future Options Asignar uno
4. Digging Deeper
Where do you feel most uncertain, confused or afraid? En el flujo
How might your own actions be contributing to the challenge you face? Permití excepciones
What would failing in this issue mean for you and those around you? Menos caja
What is your biggest personal challenge in facing this situation? Conversar
What is the outcome you hope for? Un dueño
Notes: Revisar semanalmente
"""

    response = run(document, base_path=tmp_path)

    assert "no guardé ni indexé" in response.lower()
    assert "finanzas" in response.lower()
    database = tmp_path / ".scaleup" / "memory" / "escala.db"
    assert not database.exists()


def test_patterns_are_requested_without_starting_onboarding(tmp_path):
    response = run("lee patrones de mis accountability", base_path=tmp_path)

    assert "todavía no hay sesiones" in response.lower()
    assert "cómo se llama" not in response.lower()
