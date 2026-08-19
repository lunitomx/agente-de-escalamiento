"""Tests for local prefill and explicit confirmation."""

from __future__ import annotations

from coaching.diagnose.prefill import build_prefill, confirm_prefill


def test_current_profile_prefill_is_inference_with_provenance() -> None:
    result = build_prefill(
        {"company": {"name": "Demo", "industry": "Servicios"}, "updated": "2026-08-19"},
        today="2026-08-19",
    )

    name = next(item for item in result.evidence if item.evidence_id == "company.name")
    assert name.answer_status == "inference"
    assert name.source_kind == "profile"
    assert name.source_ref == "profile:company.name"
    assert name.freshness == "current"
    assert "company.name" in result.confirmation_ids


def test_stale_profile_is_visible_as_question() -> None:
    result = build_prefill(
        {"company": {"employees": 6}, "updated": "2025-01-01"},
        today="2026-08-19",
        freshness_days=90,
    )

    employees = next(
        item for item in result.evidence if item.evidence_id == "company.employees"
    )
    assert employees.freshness == "stale"
    assert any("employees" in question for question in result.questions)


def test_missing_capture_date_is_unknown_and_needs_confirmation() -> None:
    result = build_prefill({"company": {"industry": "Servicios"}}, today="2026-08-19")

    industry = next(
        item for item in result.evidence if item.evidence_id == "company.industry"
    )
    assert industry.freshness == "unknown"
    assert industry.confidence == "low"


def test_confirm_prefill_returns_new_facts_without_mutating_input() -> None:
    before = build_prefill(
        {"company": {"name": "Demo"}, "updated": "2026-08-19"},
        today="2026-08-19",
    )
    after = confirm_prefill(before, {"company.name"})

    assert before.evidence[0].answer_status == "inference"
    assert after.evidence[0].answer_status == "fact"
    assert after.evidence[0].freshness == "current"
    assert after.confirmation_ids == []
