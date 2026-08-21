"""Acceptance tests for E52 conversational welcome persistence."""

from __future__ import annotations

from pathlib import Path

from coaching.welcome import (
    WelcomeState,
    begin_welcome,
    is_state_fresh,
    load_welcome_state,
    respond_to_welcome,
    save_welcome_state,
)


def test_saved_state_can_be_reloaded_for_continuity(tmp_path: Path) -> None:
    """A user authorizes persistence and a later session reloads the state."""
    base = tmp_path

    # First session: user describes a cash concern and authorizes save.
    first = begin_welcome()
    second = respond_to_welcome(
        first.state, "Mis ventas bajaron y no sé cuánto cash tengo."
    )
    assert second.state.area == "cash"

    saved_path = save_welcome_state(base, second.state, authorized=True)
    assert saved_path is not None
    assert saved_path.exists()

    # Later session: load and continue.
    loaded = load_welcome_state(base)
    assert loaded is not None
    assert loaded.area == "cash"
    assert is_state_fresh(base, max_age_days=7) is True

    # The agent can use the loaded area to route the conversation.
    continuation = respond_to_welcome(loaded, "sí, quiero revisar mi CCC")
    assert continuation.state.area == "cash"


def test_unauthorized_state_is_not_persisted(tmp_path: Path) -> None:
    state = WelcomeState(phase="concern")
    path = save_welcome_state(tmp_path, state, authorized=False)

    assert path is None
    assert load_welcome_state(tmp_path) is None
