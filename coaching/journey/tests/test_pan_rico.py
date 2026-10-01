"""Milestone M1 demo (E84): a synthetic conversation with "Pan Rico".

Pan Rico is a synthetic bakery that takes orders by WhatsApp. The test drives
``python -m coaching.journey`` the way the procedure does: one question, the
interview, the journey with its gaps and the loss, one decision, the save, and
the decision entering the next diagnosis as local evidence.
"""

from __future__ import annotations

from pathlib import Path

from coaching.journey import messages
from coaching.journey.flow import run

OWNER = "Mucha gente pregunta por WhatsApp pero pocos compran."
ANSWERS = [
    {
        "stage": "se_entera",
        "field": "paso",
        "answer": "por Facebook y de boca en boca, no sé cuántos",
    },
    {"stage": "pregunta", "field": "paso", "answer": "por WhatsApp, 120"},
    {"stage": "compra", "field": "paso", "answer": "apartan y pagan al recoger, 18"},
    {"stage": "recibe", "field": "paso", "answer": "pasan a la tienda, 18"},
    {"stage": "regresa", "field": "paso", "answer": "no sé"},
    {"stage": "compra", "field": "friccion", "answer": "tardo en contestar"},
]
# The agent knows the sources from the conversation; never from a URL.
COUNTS = {
    "pregunta": {
        "value": 120,
        "period": "2026-09",
        "source": "tu WhatsApp Business",
        "origin": "dato_con_periodo",
    },
    "compra": {
        "value": 18,
        "period": "2026-09",
        "source": "tu cuaderno",
        "origin": "dato_con_periodo",
    },
}


def _call(base: Path, **context: object) -> dict[str, object]:
    result = run({"base_path": str(base), "today": "2026-10-01", **context})
    assert result.errors == [], result.errors
    return result.model_dump(mode="json")


def test_pan_rico_conversation_end_to_end(tmp_path: Path) -> None:
    check = _call(tmp_path, action="check", signals={"owner_text": OWNER})
    assert check["message"] == messages.ASK_NEW  # one question, T1

    _call(tmp_path, action="record", outcome="si", reason="T1")
    step = _call(tmp_path, action="interview", answers=ANSWERS)
    assert step["step"]["done"] is True  # type: ignore[index]

    journey = {
        "answers": ANSWERS,
        "counts": COUNTS,
        "experiment": "responder en menos de 1 hora",
    }
    built = _call(tmp_path, action="build", **journey)
    text = str(built["message"])
    assert "Te pregunta: 120 en septiembre de 2026 (tu WhatsApp Business)." in text
    assert "Te compra: 18 en septiembre de 2026 (tu cuaderno)." in text
    assert "Regresa a comprar: falta cuántos en septiembre de 2026." in text
    assert "no se lo hemos preguntado a clientes" in text
    assert (
        "entre «Te pregunta» y «Te compra»: de 120 a 18 en septiembre de 2026" in text
    )
    assert "A) Durante 14 días en «Te compra»: responder en menos de 1 hora" in text
    assert "15 de octubre de 2026" in text and "Te recomiendo la A" in text
    assert not (tmp_path / ".escala/my-company/journey/journey.yaml").exists()

    refused = run(
        {"base_path": str(tmp_path), "today": "2026-10-01", "action": "save", **journey}
    )
    assert refused.errors == ["needs_chosen_option"]

    saved = _call(tmp_path, action="save", chosen="A", **journey)
    assert saved["saved_to"] == ".escala/my-company/journey/2026-10-01-journey.md"
    assert "sólo en tu computadora" in str(saved["message"])

    diagnosis = _call(tmp_path, action="diagnosis")
    inputs = diagnosis["diagnostic_inputs"]
    [fact] = inputs["evidence"]  # type: ignore[index]
    assert fact["source_kind"] == "conversation" and fact["answer_status"] == "fact"
    assert fact["source_ref"] == ".escala/my-company/journey/2026-10-01-journey.md"
    assert "Falta: cuántos en Regresa a comprar" in inputs["open_questions"]  # type: ignore[index]

    again = _call(tmp_path, action="check", signals={"owner_text": OWNER})
    assert again["decision"]["ask"] is False  # type: ignore[index]
    assert again["decision"]["reason"] == "N1"  # type: ignore[index]

    written = sorted(
        p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()
    )
    assert all(path.startswith(".escala/my-company/journey/") for path in written)
