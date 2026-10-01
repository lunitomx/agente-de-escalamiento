"""``python -m coaching.journey``: check -> record -> interview (E84 S84.1).

Includes the privacy check: the synthetic company's markers in the owner's
words never reach ``asks.yaml`` nor the ``check`` answer, and the interview
writes nothing to disk.
"""

from __future__ import annotations

import json
import subprocess
from datetime import date
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
    assert (result.step.stage, result.step.field) == ("se_entera", "paso")
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
                {
                    "stage": "se_entera",
                    "field": "paso",
                    "answer": "Por Instagram, unos 40",
                },
            ],
        }
    )

    assert result.errors == []
    assert result.step is not None
    assert (result.step.stage, result.step.field) == ("pregunta", "paso")
    assert result.message == result.step.message
    assert _files(tmp_path) == []


def test_unknown_action_and_invalid_input_are_reported() -> None:
    assert run({"action": "publish"}).errors == ["unknown_action"]
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


def test_explicit_null_never_masks_what_disk_remembers(tmp_path: Path) -> None:
    run(
        {
            "action": "record",
            "base_path": str(tmp_path),
            "today": "2026-09-20",
            "outcome": "no",
            "reason": "T1",
        }
    )
    folder = tmp_path / ".escala/my-company/journey"
    (folder / "journey.yaml").write_text("review_by: 2026-12-01\n", encoding="utf-8")

    declined = run(_check(tmp_path, last_declined_on=None))
    older = run(_check(tmp_path, last_declined_on="2026-01-01"))
    (folder / "asks.yaml").write_text("asks: []\n", encoding="utf-8")
    current = run(_check(tmp_path, journey_review_by=None))

    assert declined.decision is not None and declined.decision.reason == "N2"
    assert older.decision is not None and older.decision.reason == "N2"
    assert current.decision is not None and current.decision.reason == "N1"


def _corrupt_asks(base: Path) -> Path:
    path = asks_path(base)
    path.parent.mkdir(parents=True)
    path.write_text("asks: [roto", encoding="utf-8")
    return path


def test_a_corrupt_memory_never_turns_into_asking_again(tmp_path: Path) -> None:
    _corrupt_asks(tmp_path)

    result = run({**_check(tmp_path), "today": date.today().isoformat()})

    assert result.decision is not None
    assert (result.decision.ask, result.decision.reason) == (False, "N2")
    assert asks_path(tmp_path).read_text(encoding="utf-8") == "asks: [roto"


def test_recording_over_a_corrupt_memory_keeps_a_backup_and_says_so(
    tmp_path: Path,
) -> None:
    _corrupt_asks(tmp_path)

    result = run(
        {
            "action": "record",
            "base_path": str(tmp_path),
            "today": "2026-10-02",
            "outcome": "no",
            "reason": "T1",
        }
    )

    assert result.errors == []
    assert result.notes == [
        "asks_corrupt_backed_up:.escala/my-company/journey/asks.yaml.bak"
    ]
    backup = asks_path(tmp_path).with_name("asks.yaml.bak")
    assert backup.read_text(encoding="utf-8") == "asks: [roto"


def test_build_and_save_reject_unknown_stages_and_remote_sources(
    tmp_path: Path,
) -> None:
    base = {"base_path": str(tmp_path), "today": "2026-10-01"}
    bad_stage = run({**base, "action": "build", "counts": {"vende": {}}})
    assert bad_stage.errors
    remote = run(
        {
            **base,
            "action": "build",
            "counts": {
                "compra": {
                    "value": 1,
                    "period": "2026-09",
                    "source": "https://crm.example",
                    "origin": "dato_con_periodo",
                }
            },
        }
    )
    assert remote.errors
    unknown_choice = run({**base, "action": "save", "chosen": "Z"})
    assert unknown_choice.errors == ["chosen_must_be_an_option"]
    assert _files(tmp_path) == []


def test_customers_said_in_build_drops_the_not_asked_warning(tmp_path: Path) -> None:
    result = run(
        {
            "base_path": str(tmp_path),
            "today": "2026-10-01",
            "action": "build",
            "answers": [
                {"stage": "compra", "field": "paso", "answer": "por WhatsApp, 18"},
                {"stage": "compra", "field": "friccion", "answer": "tardo"},
            ],
            "evidence": [
                {
                    "stage": "compra",
                    "origin": "clientes_dijeron",
                    "text": "tardas en contestar",
                    "asked_on": "2026-09-20",
                    "asked_count": 4,
                }
            ],
        }
    )
    assert result.errors == []
    assert "no se lo hemos preguntado" not in result.message
    assert "Se lo preguntaste a 4 clientes" in result.message
