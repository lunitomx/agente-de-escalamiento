"""``python -m coaching.journey``: check -> record -> interview (E84 S84.1).

Includes the privacy check: the synthetic company's markers in the owner's
words never reach ``asks.yaml`` nor the ``check`` answer, and the interview
writes nothing to disk.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

from coaching.journey import messages
from coaching.journey.asks import asks_path
from coaching.journey.flow import run

ROOT = Path(__file__).resolve().parents[3]
MARKERS = ["zorblax", "ximena", "vrkalova", "987654"]
OWNER_TEXT = (
    "En Panadería Zorblax, Ximena Vrkalova dice que vendimos $987,654 "
    "pero pocos compran por WhatsApp"
)


def _check(base: Path, **signals: object) -> dict[str, object]:
    return {
        "action": "check",
        "base_path": str(base),
        "today": "2026-09-30",
        "signals": {"owner_text": OWNER_TEXT, **signals},
    }


def _files(base: Path) -> list[Path]:
    return sorted(path for path in base.rglob("*") if path.is_file())


def test_check_asks_once_for_the_pan_rico_phrase(tmp_path: Path) -> None:
    result = run(_check(tmp_path))

    assert result.errors == []
    assert result.decision is not None
    assert (result.decision.ask, result.decision.reason) == (True, "T1")
    assert result.message == messages.ASK_NEW
    assert _files(tmp_path) == []  # checking never writes


def test_check_reads_the_last_decline_from_disk(tmp_path: Path) -> None:
    run(
        {
            "action": "record",
            "base_path": str(tmp_path),
            "today": "2026-09-20",
            "outcome": "despues",
            "reason": "T1",
        }
    )

    result = run(_check(tmp_path))

    assert result.decision is not None
    assert (result.decision.ask, result.decision.reason) == (False, "N2")
    assert result.message == ""


def test_check_after_the_silence_asks_again(tmp_path: Path) -> None:
    run(
        {
            "action": "record",
            "base_path": str(tmp_path),
            "today": "2026-08-01",
            "outcome": "no",
            "reason": "T1",
        }
    )

    result = run(_check(tmp_path))

    assert result.decision is not None
    assert result.decision.ask is True


def test_explicit_decline_in_signals_wins_over_disk(tmp_path: Path) -> None:
    result = run(_check(tmp_path, last_declined_on="2026-09-29"))

    assert result.decision is not None
    assert result.decision.reason == "N2"


def test_check_reads_review_by_of_a_saved_journey(tmp_path: Path) -> None:
    folder = tmp_path / ".escala/my-company/journey"
    folder.mkdir(parents=True)
    (folder / "journey.yaml").write_text("review_by: 2026-12-01\n", encoding="utf-8")

    result = run(_check(tmp_path))

    assert result.decision is not None
    assert result.decision.reason == "N1"


def test_check_fills_funnel_gaps_from_funnel_metrics(tmp_path: Path) -> None:
    context = _check(tmp_path, owner_text="")
    context["funnel"] = {"prospects": 120, "wins": 18}

    result = run(context)

    assert result.decision is not None
    assert (result.decision.ask, result.decision.reason) == (True, "T3")


def test_asked_this_conversation_blocks(tmp_path: Path) -> None:
    result = run(_check(tmp_path, asked_this_conversation=True))

    assert result.decision is not None
    assert result.decision.reason == "N3"


def test_record_yes_starts_the_interview(tmp_path: Path) -> None:
    result = run(
        {
            "action": "record",
            "base_path": str(tmp_path),
            "today": "2026-10-02",
            "outcome": "si",
            "reason": "T1",
        }
    )

    assert result.errors == []
    assert result.saved_to == ".escala/my-company/journey/asks.yaml"
    assert result.step is not None
    assert result.step.field == "necesidad"
    assert result.message == result.step.message


def test_record_later_says_it_will_not_insist(tmp_path: Path) -> None:
    result = run(
        {
            "action": "record",
            "base_path": str(tmp_path),
            "today": "2026-10-02",
            "outcome": "despues",
            "reason": "T2",
        }
    )

    assert result.message == messages.LATER
    assert result.step is None


def test_record_rejects_free_text_reasons(tmp_path: Path) -> None:
    result = run(
        {
            "action": "record",
            "base_path": str(tmp_path),
            "today": "2026-10-02",
            "outcome": "no",
            "reason": OWNER_TEXT,
        }
    )

    assert result.errors
    assert _files(tmp_path) == []


def test_interview_returns_next_question_and_writes_nothing(tmp_path: Path) -> None:
    result = run(
        {
            "action": "interview",
            "base_path": str(tmp_path),
            "today": "2026-10-02",
            "answers": [
                {"stage": "se_entera", "field": "necesidad", "answer": "Pan fresco"},
            ],
        }
    )

    assert result.errors == []
    assert result.step is not None
    assert result.step.field == "donde"
    assert result.message == result.step.message
    assert _files(tmp_path) == []


def test_unknown_action_and_invalid_input_are_reported() -> None:
    assert run({"action": "save"}).errors == ["unknown_action"]
    assert run({"action": "check", "signals": {"constraint_area": "ventas"}}).errors


def test_privacy_markers_never_reach_disk_or_check_output(tmp_path: Path) -> None:
    checked = run(_check(tmp_path)).model_dump_json().lower()
    run(
        {
            "action": "record",
            "base_path": str(tmp_path),
            "today": "2026-09-30",
            "outcome": "no",
            "reason": "T1",
            "owner_text": OWNER_TEXT,
        }
    )
    stored = asks_path(tmp_path).read_text(encoding="utf-8").lower()

    for marker in MARKERS:
        assert marker not in checked
        assert marker not in stored
    assert yaml.safe_load(asks_path(tmp_path).read_text(encoding="utf-8")) == {
        "asks": [{"asked_on": "2026-09-30", "outcome": "no", "reason": "T1"}]
    }


def test_module_runs_as_a_command(tmp_path: Path) -> None:
    payload = json.dumps(_check(tmp_path))
    result = subprocess.run(
        [sys.executable, "-m", "coaching.journey"],
        input=payload,
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["decision"]["reason"] == "T1"
