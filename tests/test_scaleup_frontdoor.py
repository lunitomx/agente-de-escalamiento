"""Deterministic public front-door routing tests."""
from __future__ import annotations

from coaching.router import detect_public_intent, run


def test_natural_intents_route_without_exposing_commands(tmp_path):
    profile = {"company": {"name": "Acme"}}
    assert detect_public_intent("Quiero organizar mi empresa", profile) == "diagnosis"
    assert detect_public_intent("No sé por dónde empezar", profile) == "diagnosis"
    assert detect_public_intent("Quiero hacer mi plan en una hoja", profile) == "opsp"
    assert detect_public_intent("¿Cómo vamos con las tareas?", profile) == "progress"

    result = run({"action": "frontdoor", "message": "Quiero hacer mi plan en una hoja", "base_path": tmp_path})
    assert result["errors"] == []
    assert result["artifacts"]["intent"] == "opsp"
    assert result["artifacts"]["requires_command"] is False
    assert "/scaleup-" not in result["output"]


def test_unclear_first_request_recovers_to_onboarding(tmp_path):
    result = run({"action": "frontdoor", "message": "hola", "base_path": tmp_path})
    assert result["artifacts"]["intent"] == "onboarding"
    assert "¿Cómo se llama" in result["output"]
