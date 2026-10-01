"""
Tests for welcome module.
"""

import sys
from pathlib import Path

import pytest


def test_welcome_creates_profile(tmp_path):
    """Run welcome module and verify profile is created."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from coaching.welcome import run

    context = {
        "company_name": "TestCorp",
        "industry": "Tech",
        "employees": 15,
        "entry_methodology": "lean-canvas",
        "base_path": str(tmp_path),
    }
    result = run(context)
    assert len(result["errors"]) == 0, f"Errors: {result['errors']}"
    assert "TestCorp" in result["output"]
    assert result["artifacts"]["profile"]["company"]["name"] == "TestCorp"
    assert result["artifacts"]["profile"]["company"]["growth_stage"] == "growth"


def test_welcome_rejects_missing_name(tmp_path):
    """Welcome should error on missing company_name."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from coaching.welcome import run

    result = run(
        {
            "company_name": "",
            "industry": "Tech",
            "employees": 5,
            "base_path": str(tmp_path),
        }
    )
    assert any("company_name" in e for e in result["errors"])


def test_welcome_preserves_existing_scores(tmp_path):
    """Second run must not overwrite previously stored scores or focus."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from coaching.welcome import run
    from coaching.core import read_yaml, write_yaml

    profile_path = tmp_path / ".escala" / "agent" / "memory" / "company-profile.yaml"
    existing_profile = {
        "company": {
            "name": "OldCorp",
            "industry": "Retail",
            "employees": 25,
            "growth_stage": "growth",
            "entry_methodology": "skip",
        },
        "scores": {
            "people": 4,
            "strategy": 3,
            "execution": 5,
            "cash": 2,
            "overall": 3.5,
        },
        "focus": {"current_decision": "cash", "last_session": "2026-08-01"},
        "coaching": {"level": "ha", "level_source": "diagnosis"},
        "diagnosis_history": [{"date": "2026-08-01", "overall": 3.5}],
        "created": "2026-08-01",
    }
    write_yaml(profile_path, existing_profile)

    result = run(
        {
            "company_name": "NewCorp",
            "industry": "Tech",
            "employees": 15,
            "entry_methodology": "lean-canvas",
            "base_path": str(tmp_path),
        }
    )

    assert len(result["errors"]) == 0, f"Errors: {result['errors']}"
    stored = read_yaml(profile_path)

    # Explicitly provided fields are updated.
    assert stored["company"]["name"] == "NewCorp"
    assert stored["company"]["industry"] == "Tech"
    assert stored["company"]["employees"] == 15

    # Previously stored fields are preserved.
    assert stored["scores"] == existing_profile["scores"]
    assert stored["focus"] == existing_profile["focus"]
    assert stored["coaching"] == existing_profile["coaching"]
    assert stored["diagnosis_history"] == existing_profile["diagnosis_history"]
    assert stored["created"] == existing_profile["created"]


def test_stage_detection():
    """Verify stage detection logic."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from coaching.core import detect_stage

    assert detect_stage(3) == "startup"
    assert detect_stage(10) == "startup"
    assert detect_stage(15) == "growth"
    assert detect_stage(50) == "growth"
    assert detect_stage(100) == "scaling"
    assert detect_stage(500) == "expansion"


def test_adaptive_welcome_uses_dashboard_and_one_question_per_decision(tmp_path):
    """The actual Welcome entry point routes all four decisions without scores."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from coaching.welcome import run

    cases = {
        "Mi equipo no tiene responsables claros.": "¿Quiénes son hoy",
        "No entiendo frente a qué competencia gano.": "¿Cuál es el cliente",
        "Mi operación no tiene ritmo ni prioridades.": "¿Cuál es la prioridad",
        "No sé cuánto cash tengo disponible.": "¿Cuál fue tu ingreso",
    }
    for message, expected_question in cases.items():
        result = run(
            {
                "action": "adaptive_conversation",
                "message": message,
                "base_path": str(tmp_path),
            }
        )

        assert result["errors"] == []
        assert result["output"].startswith(expected_question)
        assert result["output"].count("?") == 1
        assert result["artifacts"]["evidence_dashboard"]


def test_adaptive_welcome_persists_only_authorized_confirmed_facts(tmp_path):
    """Structured facts are local and require explicit persistence authorization."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from coaching.evidence.facts import load_facts
    from coaching.welcome import run

    fact = {
        "metric_definition": "Ingreso",
        "period": "2026-07",
        "source": "ERP local",
        "confidence": "high",
        "value": 100,
        "decision": "cash",
    }
    rejected = run(
        {
            "action": "adaptive_conversation",
            "message": "Necesito entender mi cash.",
            "confirmed_facts": [fact],
            "base_path": str(tmp_path),
        }
    )
    assert rejected["errors"]
    assert load_facts(tmp_path) == []

    accepted = run(
        {
            "action": "adaptive_conversation",
            "message": "Necesito entender mi cash.",
            "confirmed_facts": [fact],
            "persist_authorized": True,
            "base_path": str(tmp_path),
        }
    )
    assert accepted["errors"] == []
    assert accepted["output"].startswith("¿Cuánto cobraste")
    assert len(load_facts(tmp_path)) == 1


def test_adaptive_welcome_offers_continuity_from_fresh_authorized_state(tmp_path):
    """A later local Welcome entry point asks before it resumes saved context."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from coaching.welcome import WelcomeState, run, save_welcome_state

    save_welcome_state(
        tmp_path,
        WelcomeState(phase="source", area="cash", next_action="evidence"),
        authorized=True,
    )

    result = run({"action": "adaptive_conversation", "base_path": str(tmp_path)})

    assert result["errors"] == []
    assert "La última vez trabajamos en tu dinero" in result["output"]
    assert result["artifacts"]["resumed_from_local_state"] is True


@pytest.mark.parametrize(
    ("decision", "message"),
    [
        ("people", "Mi equipo no tiene responsables claros."),
        ("strategy", "No entiendo frente a qué competencia gano."),
        ("execution", "Mi operación no tiene ritmo ni prioridades."),
        ("cash", "No sé cuánto cash tengo disponible."),
    ],
)
def test_adaptive_welcome_handles_known_and_noncomparable_evidence(
    tmp_path, decision, message
):
    """Every decision skips known evidence and makes ambiguity visible."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from coaching.evidence.facts import Fact, save_fact
    from coaching.welcome import default_onboarding_requirements, run

    requirements = [
        requirement
        for requirement in default_onboarding_requirements()
        if requirement.decision == decision
    ]
    known_path = tmp_path / f"{decision}-known"
    for requirement in requirements:
        save_fact(
            known_path,
            Fact(
                metric_definition=requirement.metric_definition,
                period="2026-Q3",
                source="archivo local",
                confidence="high",
                value="confirmado",
                decision=decision,
            ),
        )
    known = run(
        {
            "action": "adaptive_conversation",
            "message": message,
            "base_path": str(known_path),
        }
    )
    assert known["errors"] == []
    assert "Ya tengo los datos comparables" in known["output"]

    blocked_path = tmp_path / f"{decision}-blocked"
    first = requirements[0]
    save_fact(
        blocked_path,
        Fact(
            metric_definition=first.metric_definition,
            period="2026-Q3",
            source="archivo local ambiguo",
            confidence="medium",
            comparable=False,
            value="pendiente de definición",
            decision=decision,
        ),
    )
    blocked = run(
        {
            "action": "adaptive_conversation",
            "message": message,
            "base_path": str(blocked_path),
        }
    )
    assert blocked["errors"] == []
    assert "no es comparable" in blocked["output"]
