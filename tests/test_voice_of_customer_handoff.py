from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / ".raise/evidence/voice-of-customer.md"
E34 = ROOT / "work/epics/e34-voice-of-customer-evidence-system"


def test_voice_of_customer_handoff_references_implemented_api() -> None:
    text = HANDOFF.read_text(encoding="utf-8")

    assert "CustomerEvidenceRecord" in text
    assert "normalize_raw_quotes" in text
    assert "map_evidence_to_strategy" in text
    assert "tests/fixtures/voice_of_customer/" in text
    assert "evidence ids" in text
    assert "gaps" in text


def test_handoff_is_canonical_not_old_draft_dependent() -> None:
    text = HANDOFF.read_text(encoding="utf-8")

    assert "Canonical Voice of Customer evidence contract" in text
    assert "Do not use old E19/E20 draft folders as the source of truth" in text


def test_e34_final_audit_distinguishes_fixtures_from_real_evidence() -> None:
    text = (E34 / "final-audit.md").read_text(encoding="utf-8")

    assert "Fixture data is not real customer evidence" in text
    assert "tests/fixtures/voice_of_customer/" in text
    assert "Real customer evidence supplied: none in this implementation" in text


def test_e34_retrospective_records_all_stories_complete() -> None:
    text = (E34 / "retrospective.md").read_text(encoding="utf-8")

    for story_id in ("S34.1", "S34.2", "S34.3", "S34.4", "S34.5"):
        assert f"{story_id} | Complete" in text
    assert "E35 remains separate" in text
