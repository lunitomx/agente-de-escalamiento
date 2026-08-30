from __future__ import annotations

import json
from pathlib import Path

from validators.ontology_v2 import load_review_queue


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "scaling-up-llamaparse-2014"


def _units(candidate) -> set[str]:
    return {
        unit
        for evidence in candidate.proposed_node.evidence
        for unit in evidence.unit_ids
    }


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_e61_seven_strata_fidelity_links_sections_relations_and_visual_receipt() -> (
    None
):
    evidence = ROOT / "work/epics/e61-strategy-corpus-fidelity/evidence"
    queue = load_review_queue(evidence / "s61.2-strategy-review-queue.json")
    candidates = {item.candidate_id: item for item in queue.candidates}
    decisions = {item.candidate_id: item for item in queue.decisions}
    expected_sections = {f"{SOURCE}.u{number:04d}" for number in range(166, 174)}

    assert (
        _units(candidates["candidate.strategy.framework.seven-strata"])
        == expected_sections
    )
    assert expected_sections <= _units(
        candidates["candidate.strategy.tool.seven-strata"]
    )
    assert {decision.outcome.value for decision in decisions.values()} == {
        "approve-candidate"
    }
    assert f"{SOURCE}.u0174" in _units(
        candidates["candidate.strategy.tool.seven-strata"]
    )
    assert {f"{SOURCE}.u0175", f"{SOURCE}.u0176"}.isdisjoint(
        _units(candidates["candidate.strategy.tool.seven-strata"])
    )

    relations = _load_json(evidence / "s61.3-strategy-relations-review-queue.json")
    expected_by_suffix = {
        "mindshare": {f"{SOURCE}.u0166"},
        "sandbox-brand-promises": {f"{SOURCE}.u0167"},
        "brand-promise-guarantee": {f"{SOURCE}.u0168"},
        "one-phrase-strategy": {f"{SOURCE}.u0169"},
        "differentiating-activities": {f"{SOURCE}.u0170"},
        "x-factor": {f"{SOURCE}.u0171"},
        "profit-per-x-bhag": {f"{SOURCE}.u0172", f"{SOURCE}.u0173"},
    }
    for relation in relations["relations"]:
        suffix = relation["relation_id"].split(".")[-1]
        actual = {unit for entry in relation["evidence"] for unit in entry["unit_ids"]}
        assert actual == expected_by_suffix[suffix]

    visual = _load_json(evidence / "s61.4-visual-layout-review-2026-08-30.json")
    assert "tool.strategy-seven-strata" in {
        form["tool_ref"] for form in visual["forms"]
    }
    opsp_parts = {
        form["form_part"] for form in visual["forms"] if form["tool_ref"] == "tool.opsp"
    }
    assert opsp_parts == {"front", "back"}
    semantic = _load_json(evidence / "s61.6-official-form-semantic-receipt.json")
    assert semantic["superseded_by"] == "s61.4-visual-layout-review-2026-08-30.json"


def test_e62_execution_review_keeps_repairs_source_bounded_and_visual_receipt_linked() -> (
    None
):
    evidence = ROOT / "work/epics/e62-execution-corpus-fidelity/evidence"
    queue = load_review_queue(evidence / "s62.2-execution-review-queue.json")
    candidates = {item.candidate_id: item for item in queue.candidates}
    decisions = {item.candidate_id: item for item in queue.decisions}

    assert (
        "opportunity"
        not in candidates[
            "candidate.execution.tool.critical-number"
        ].working_text.lower()
    )
    assert (
        "memorable"
        not in candidates[
            "candidate.execution.routine.quarterly-theme"
        ].working_text.lower()
    )
    assert _units(candidates["candidate.execution.routine.daily-huddle"]) == {
        f"{SOURCE}.u0256",
        f"{SOURCE}.u0257",
    }
    assert _units(candidates["candidate.execution.routine.weekly-meeting"]) == {
        f"{SOURCE}.u0258",
        f"{SOURCE}.u0259",
    }
    assert {decision.reviewer_id for decision in decisions.values()} == {
        "e62-independent-fidelity-reviewer"
    }
    assert all(
        decision.reviewer_id != candidate.extractor_id
        for candidate in candidates.values()
        for decision in [decisions[candidate.candidate_id]]
    )

    rhythm = _load_json(evidence / "s62.3-rhythm-receipt-draft.json")
    assert rhythm["status"] == "approved-source-bounded"
    assert rhythm["reviewer_id"] == "e62-independent-fidelity-reviewer"
    assert all(
        item["duration_status"]
        == "source-bounded and independently reviewed; no canonical promotion"
        for item in rhythm["routines"]
    )
    semantic = _load_json(evidence / "s62.7-official-form-semantic-receipt.json")
    assert semantic["superseded_by"] == "s62.3-visual-layout-review-2026-08-30.json"
