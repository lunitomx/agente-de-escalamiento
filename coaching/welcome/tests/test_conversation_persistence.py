"""Tests for conversational welcome state persistence."""

from __future__ import annotations

import datetime
from pathlib import Path

from coaching.core import read_yaml
from coaching.welcome.conversation import (
    MaturityProfile,
    WelcomeState,
    is_state_fresh,
    load_welcome_state,
    save_welcome_state,
)


def test_save_writes_state_when_authorized(tmp_path: Path) -> None:
    state = WelcomeState(phase="concern")
    path = save_welcome_state(tmp_path, state, authorized=True)

    assert path is not None
    assert path.exists()
    data = read_yaml(path)
    assert data["phase"] == "concern"
    assert data["schema_version"] == 1
    assert "authorized_at" in data
    assert "updated_at" in data


def test_save_returns_none_when_not_authorized(tmp_path: Path) -> None:
    state = WelcomeState(phase="concern")
    path = save_welcome_state(tmp_path, state, authorized=False)

    assert path is None
    assert not (_state_path(tmp_path)).exists()


def test_load_returns_saved_state(tmp_path: Path) -> None:
    state = WelcomeState(
        phase="source",
        profile=MaturityProfile.SPECIFIC,
        area="cash",
        next_action="evidence",
        concern="ventas bajaron",
    )
    save_welcome_state(tmp_path, state, authorized=True)

    loaded = load_welcome_state(tmp_path)
    assert loaded is not None
    assert loaded.phase == "source"
    assert loaded.area == "cash"
    assert loaded.concern == "ventas bajaron"


def test_load_returns_none_when_missing(tmp_path: Path) -> None:
    assert load_welcome_state(tmp_path) is None


def test_is_state_fresh_true_for_recent_state(tmp_path: Path) -> None:
    state = WelcomeState(phase="concern")
    save_welcome_state(tmp_path, state, authorized=True)

    assert is_state_fresh(tmp_path, max_age_days=7) is True


def test_is_state_fresh_false_for_old_state(tmp_path: Path) -> None:
    state = WelcomeState(phase="concern")
    save_welcome_state(tmp_path, state, authorized=True)

    path = _state_path(tmp_path)
    data = read_yaml(path)
    old = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=10)
    data["updated_at"] = old.isoformat()
    path.write_text(
        __import__("yaml").safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    assert is_state_fresh(tmp_path, max_age_days=7) is False


def _state_path(base_path: Path) -> Path:
    return base_path / ".escala" / "agent" / "memory" / "welcome-state.yaml"
