"""S86.10: the door asks for consent the same way on every platform (A4).

The old promise ("nunca envíes información fuera de la carpeta local") cannot
be kept on any hosted assistant: what the owner says is processed on the
assistant's servers (E85 spike §5c). The door now says what leaves and asks
for a separate "sí" before each step that sends or keeps something.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOOR = ROOT / "escala-skills" / "escala" / "SKILL.md"

PLATFORM_NAMES = ("claude", "codex", "chatgpt", "openai", "anthropic", "hermes")


def consent_section(door: str) -> str:
    """The door's "## Consentimiento" section, title removed, one-line spaces."""
    match = re.search(r"^## Consentimiento\n(.*?)(?=^## |\Z)", door, re.M | re.S)
    assert match, "the door has no '## Consentimiento' section"
    return re.sub(r"\s+", " ", match.group(1)).strip()


def test_old_local_only_promise_is_gone() -> None:
    door = DOOR.read_text(encoding="utf-8")

    assert "fuera de la carpeta local" not in door
    assert "nunca sale de tu computadora" not in door.lower()


def test_consent_section_is_platform_neutral_and_short() -> None:
    consent = consent_section(DOOR.read_text(encoding="utf-8"))

    assert not [name for name in PLATFORM_NAMES if name in consent.lower()]
    assert len(consent.split()) <= 260


def test_consent_tells_the_truth_about_transmission() -> None:
    consent = consent_section(DOOR.read_text(encoding="utf-8"))

    assert "servidores" in consent
    assert "No le prometas que nada sale de su computadora" in consent


def test_consent_asks_before_each_step_with_a_real_example() -> None:
    consent = consent_section(DOOR.read_text(encoding="utf-8"))

    for step in ("Buscar en internet", "Guardar", "Escribir en su hoja", "Leer un archivo"):
        assert step in consent, step
    assert (
        "Para buscar precios de tu competencia voy a mandar a internet sólo "
        "'panadería en Puebla', sin tus números. ¿Va?"
    ) in consent
    # A "no" ends it for the conversation.
    assert "no lo vuelvas a pedir" in consent


def test_private_figures_never_leave_even_with_a_yes() -> None:
    """E83: searches never carry the company's names, people or figures."""
    consent = consent_section(DOOR.read_text(encoding="utf-8"))

    assert "ni con su sí" in consent
    assert "cifras" in consent
