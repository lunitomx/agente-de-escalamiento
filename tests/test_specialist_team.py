from __future__ import annotations

import pytest

from escala_server.handlers import SpecialistTeamHandler
from escala_server.specialist_team import (
    SPECIALIST_CONTRACTS,
    TeamReviewError,
    choose_team,
    minimum_context,
    review,
)


def test_four_private_contracts_define_triggers_non_triggers_and_limits() -> None:
    assert set(SPECIALIST_CONTRACTS) == {"cash", "execution", "people", "strategy"}
    for contract in SPECIALIST_CONTRACTS.values():
        assert contract.trigger and contract.non_trigger and contract.minimum_context
        assert contract.permissions and contract.output and contract.limits


def test_simple_case_uses_one_specialist_without_team_theater() -> None:
    route = choose_team({"areas": ["cash"]})
    assert route["mode"] == "single_specialist"
    assert route["roles"] == ("cash-analyst",)


def test_transversal_case_routes_minimal_specialists_critic_and_verifier() -> None:
    route = choose_team({"areas": ["cash", "execution"], "material_risk": True})
    assert route["mode"] == "team"
    assert route["roles"] == (
        "cash-analyst",
        "execution-operator",
        "independent-critic",
        "evidence-verifier",
    )


def test_context_is_minimal_per_specialist() -> None:
    request = {
        "areas": ["cash", "strategy"],
        "evidence": [
            {
                "areas": ["cash"],
                "source_id": "cash-1",
                "period": "2026-Q2",
                "unit": "MXN",
            },
            {"areas": ["strategy"], "source_id": "market-1"},
            {"areas": ["people"], "source_id": "private-1"},
        ],
    }
    assert len(minimum_context(request, "cash")) == 1
    assert len(minimum_context(request, "strategy")) == 1


def test_verifier_blocks_cash_number_without_period_and_unit() -> None:
    result = review(
        {
            "areas": ["cash", "execution"],
            "evidence": [
                {"areas": ["cash"], "source_id": "cash-1"},
                {"areas": ["execution"], "source_id": "ops-1"},
            ],
            "claims": [],
        }
    )
    assert result["verification"]["blocked"] is True
    assert "periodo o unidad" in result["synthesis"]["risk"]


def test_disagreement_never_becomes_a_majority_decision() -> None:
    result = review(
        {
            "areas": ["cash", "strategy"],
            "evidence": [
                {
                    "areas": ["cash"],
                    "source_id": "cash-1",
                    "period": "2026-Q2",
                    "unit": "MXN",
                },
                {"areas": ["strategy"], "source_id": "market-1"},
            ],
            "claims": [
                {"topic": "precio", "position": "reducir"},
                {"topic": "precio", "position": "mantener"},
            ],
        }
    )
    assert len(result["disagreements"]) == 1
    assert "dato verificable" in result["synthesis"]["next_question"]
    assert "mayoría" in result["synthesis"]["risk"]


def test_unknown_area_or_invalid_claim_fails_closed() -> None:
    with pytest.raises(TeamReviewError, match="unknown"):
        choose_team({"areas": ["research"]})
    with pytest.raises(TeamReviewError, match="topic"):
        review({"areas": ["cash"], "evidence": [], "claims": [{}]})


def test_local_api_handler_returns_one_executive_synthesis() -> None:
    result = SpecialistTeamHandler().review(
        {
            "areas": ["cash", "execution"],
            "evidence": [
                {
                    "areas": ["cash"],
                    "source_id": "cash-1",
                    "period": "2026-Q2",
                    "unit": "MXN",
                },
                {"areas": ["execution"], "source_id": "ops-1"},
            ],
            "claims": [],
        }
    )
    assert result["status"] == "ok"
    assert "synthesis" in result["data"]
    assert "agents" not in result["data"]["synthesis"]["decision_suggested"].lower()


def test_review_enforces_limits_and_reports_them_to_the_owner() -> None:
    result = review(
        {
            "areas": ["cash"],
            "rounds_used": 1,
            "time_limit_ms": 1_000,
            "evidence": [
                {
                    "areas": ["cash"],
                    "source_id": "cash-1",
                    "period": "2026-Q2",
                    "unit": "MXN",
                    "sensitivity": "financial",
                }
            ],
            "claims": [],
        }
    )
    assert result["coordination_limits"]["rounds_allowed"] == 1
    assert result["coordination_limits"]["rounds_used"] == 1
    assert result["coordination_limits"]["elapsed_ms"] <= 1_000
    assert (
        result["coordination_limits"]["privacy_boundary"]
        == "tagged-minimum-context-only"
    )

    with pytest.raises(TeamReviewError, match="one clarification"):
        review({"areas": ["cash"], "rounds_used": 2, "evidence": [], "claims": []})


def test_personal_or_financial_evidence_fails_closed_outside_its_boundary() -> None:
    with pytest.raises(TeamReviewError, match="People consent"):
        review(
            {
                "areas": ["people"],
                "evidence": [
                    {
                        "areas": ["people"],
                        "source_id": "people-1",
                        "sensitivity": "personal",
                    }
                ],
                "claims": [],
            }
        )
    with pytest.raises(TeamReviewError, match="within Cash"):
        review(
            {
                "areas": ["cash", "strategy"],
                "evidence": [
                    {
                        "areas": ["cash", "strategy"],
                        "source_id": "financial-1",
                        "period": "2026-Q2",
                        "unit": "MXN",
                        "sensitivity": "financial",
                    }
                ],
                "claims": [],
            }
        )


def test_synthesis_keeps_the_full_executive_contract_without_inventing_owner() -> None:
    result = review(
        {
            "areas": ["cash", "execution"],
            "evidence": [
                {
                    "areas": ["cash"],
                    "source_id": "cash-1",
                    "period": "2026-Q2",
                    "unit": "MXN",
                },
                {"areas": ["execution"], "source_id": "ops-1"},
            ],
            "claims": [],
        }
    )
    synthesis = result["synthesis"]
    assert synthesis["status"] == "ready"
    assert synthesis["primary_constraint"] is None
    assert synthesis["evidence_ids"] == ("cash-1", "ops-1")
    assert synthesis["assumptions"] == ()
    assert synthesis["owner_suggestion"] is None
    assert synthesis["review_cadence"] is None
