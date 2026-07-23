from __future__ import annotations

import pytest
from pydantic import ValidationError
from pathlib import Path

from escala_server.executive import (
    build_cockpit,
    DiagnosticAnswer,
    EvidenceItem,
    ExecutiveDiagnostic,
    CoachingRequest,
    ExecutionState,
    ExecutionTask,
    Goal,
    GuidanceRequest,
    Priority,
    PersistenceError,
    SessionContinuity,
    StrategyAnswer,
    ProfileAnswer,
    build_company_profile,
    build_diagnostic,
    render_cockpit_html,
    build_strategy_plan,
    build_honest_guidance,
    load_execution_state,
    route_coaching,
    save_execution_state,
    write_cockpit,
)
from escala_server.executive.models import Decision
from escala_server.workspace.authority import WorkspaceAuthorityError, WorkspaceConfig


def test_profile_preserves_unknowns_and_material_questions() -> None:
    result = build_company_profile(
        (
            ProfileAnswer(key="company_name", value="Nopal Foods", status="fact"),
            ProfileAnswer(key="industry", value="alimentos", status="fact"),
            ProfileAnswer(key="employees", value=28, status="fact"),
            ProfileAnswer(key="critical_number", value=None, status="unknown"),
            ProfileAnswer(
                key="stage",
                value="regional",
                status="inference",
                question="¿Es regional?",
            ),
        )
    )

    assert result.status == "needs_clarification"
    assert result.profile.field("company_name").value == "Nopal Foods"
    assert result.profile.field("critical_number").status == "unknown"
    assert result.unresolved_fields == ("stage", "critical_number")
    assert result.questions[0].field == "stage"


def test_profile_is_ready_when_required_facts_are_supplied() -> None:
    result = build_company_profile(
        (
            ProfileAnswer(key="company_name", value="Nopal Foods", status="fact"),
            ProfileAnswer(key="industry", value="alimentos", status="fact"),
            ProfileAnswer(key="stage", value="regional", status="fact"),
            ProfileAnswer(key="employees", value=28, status="fact"),
            ProfileAnswer(key="critical_number", value="margen bruto", status="fact"),
        )
    )

    assert result.status == "ready"
    assert result.unresolved_fields == ()
    assert [field.key for field in result.profile.fields] == [
        "company_name",
        "industry",
        "stage",
        "employees",
        "critical_number",
    ]


def test_diagnostic_emits_four_evidence_backed_0_to_100_assessments() -> None:
    scores: tuple[tuple[Decision, int], ...] = (
        ("people", 64),
        ("strategy", 51),
        ("execution", 73),
        ("cash", 42),
    )
    answers = tuple(
        DiagnosticAnswer(
            decision=decision, score=score, source_ids=(f"src-{decision}",)
        )
        for decision, score in scores
    )

    diagnostic = build_diagnostic(answers)

    assert [item.decision for item in diagnostic.assessments] == [
        "people",
        "strategy",
        "execution",
        "cash",
    ]
    assert diagnostic.assessment_for("cash").score == 42
    assert diagnostic.assessment_for("cash").evidence_status == "supported"
    assert diagnostic.assessment_for("cash").evidence_count == 1
    assert diagnostic.overall_score == 58


def test_diagnostic_keeps_missing_decision_evidence_limited() -> None:
    diagnostic = build_diagnostic(
        (DiagnosticAnswer(decision="people", score=80, source_ids=("people-1",)),)
    )

    cash = diagnostic.assessment_for("cash")
    assert cash.score is None
    assert cash.evidence_status == "evidence_limited"
    assert cash.questions == (
        "Necesito evidencia o una respuesta del dueño para Cash.",
    )
    assert diagnostic.status == "evidence_limited"


def test_owner_input_is_an_explicit_supported_attribution() -> None:
    diagnostic = build_diagnostic(
        (DiagnosticAnswer(decision="strategy", score=67, attribution="owner_input"),)
    )

    assessment = diagnostic.assessment_for("strategy")
    assert assessment.evidence_status == "supported"
    assert assessment.attribution == ("owner_input",)


def test_invalid_score_and_path_bearing_evidence_fail_closed() -> None:
    with pytest.raises(ValidationError):
        DiagnosticAnswer(decision="cash", score=101, source_ids=("cash-1",))

    with pytest.raises(ValidationError):
        EvidenceItem(source_id="cash-1", locator="/Users/private/transcript.txt")


def test_closed_models_reject_arbitrary_fields() -> None:
    with pytest.raises(ValidationError):
        ProfileAnswer.model_validate(
            {"key": "industry", "value": "alimentos", "status": "fact", "leaked": "no"}
        )


def _supported_diagnostic() -> ExecutiveDiagnostic:
    return build_diagnostic(
        (
            DiagnosticAnswer(
                decision="people", score=64, source_ids=("people-source",)
            ),
            DiagnosticAnswer(
                decision="strategy", score=51, source_ids=("strategy-source",)
            ),
            DiagnosticAnswer(
                decision="execution", score=73, source_ids=("execution-source",)
            ),
            DiagnosticAnswer(
                decision="cash",
                score=42,
                source_ids=("cash-source",),
                freshness="stale",
                blocker="Cobranza atrasada",
            ),
        )
    )


def test_cockpit_selects_supported_pain_and_drills_to_evidence() -> None:
    cockpit = build_cockpit(_supported_diagnostic())

    assert cockpit.focus_decision == "cash"
    assert cockpit.drill_down.source_ids == ("cash-source",)
    assert cockpit.drill_down.freshness == "stale"
    assert cockpit.drill_down.blockers == ("Cobranza atrasada",)
    assert cockpit.drill_down.next_action
    assert len(cockpit.cards) == 4


def test_cockpit_does_not_turn_missing_evidence_into_pain() -> None:
    diagnostic = build_diagnostic(
        (
            DiagnosticAnswer(
                decision="people", score=70, source_ids=("people-source",)
            ),
            DiagnosticAnswer(decision="cash", score=55, source_ids=("cash-source",)),
        )
    )

    cockpit = build_cockpit(diagnostic)

    assert cockpit.focus_decision == "cash"
    assert cockpit.card_for("strategy").status == "evidence_limited"
    assert cockpit.card_for("strategy").score is None


def test_cockpit_html_is_escaped_and_deterministic() -> None:
    diagnostic = build_diagnostic(
        (
            DiagnosticAnswer(
                decision="cash",
                score=30,
                source_ids=("cash-source",),
                blocker="<script>alert('x')</script>",
            ),
        )
    )
    first = render_cockpit_html(build_cockpit(diagnostic))
    second = render_cockpit_html(build_cockpit(diagnostic))

    assert first == second
    assert "&lt;script&gt;" in first
    assert "<script>alert" not in first
    assert "https://" not in first


def test_write_cockpit_is_local_deterministic_and_does_not_touch_exchange(
    tmp_path: Path,
) -> None:
    root = tmp_path
    exchange = root / "exchange"
    exchange.mkdir()
    config = WorkspaceConfig(
        platform="macos",
        data_root=root / "data",
        database_path=root / "data" / "escala.sqlite",
        exchange_root=exchange,
    )
    cockpit = build_cockpit(_supported_diagnostic())

    first = write_cockpit(config, cockpit)
    first_html = (config.data_root / ".escala-executive" / "cockpit.html").read_text()
    second = write_cockpit(config, cockpit)
    second_html = (config.data_root / ".escala-executive" / "cockpit.html").read_text()

    assert first == second
    assert first_html == second_html
    assert first.html_path == ".escala-executive/cockpit.html"
    assert first.json_path == ".escala-executive/cockpit.json"
    assert list(exchange.iterdir()) == []


def test_write_cockpit_rejects_authoritative_database_inside_exchange(
    tmp_path: Path,
) -> None:
    root = tmp_path
    exchange = root / "exchange"
    exchange.mkdir()
    config = WorkspaceConfig(
        platform="macos",
        data_root=root / "data",
        database_path=exchange / "shared.sqlite",
        exchange_root=exchange,
    )

    with pytest.raises(WorkspaceAuthorityError):
        write_cockpit(config, build_cockpit(_supported_diagnostic()))


def test_strategy_plan_preserves_vision_and_unresolved_opsp_sections() -> None:
    plan = build_strategy_plan(
        (
            StrategyAnswer(
                key="purpose", value="hacer accesible la comida sana", status="fact"
            ),
            StrategyAnswer(key="bhag", value="100 tiendas en 10 años", status="fact"),
            StrategyAnswer(
                key="brand_promise", value="entrega en 30 minutos", status="fact"
            ),
        )
    )

    assert plan.status == "needs_clarification"
    assert plan.purpose == "hacer accesible la comida sana"
    assert plan.bhag == "100 tiendas en 10 años"
    assert "critical_number" in plan.unresolved
    assert any("critical_number" in question for question in plan.questions)


def test_complete_strategy_plan_is_ready_without_fabricating_values() -> None:
    keys = (
        "vision",
        "purpose",
        "bhag",
        "sandbox",
        "brand_promise",
        "profit_per_x",
        "annual_goal",
        "critical_number",
    )
    plan = build_strategy_plan(
        tuple(
            StrategyAnswer(key=key, value=f"owner-{key}", status="fact") for key in keys
        )
    )

    assert plan.status == "ready"
    assert plan.unresolved == ()
    assert plan.critical_number == "owner-critical_number"


def test_coaching_routes_explicit_cash_request_to_existing_skill() -> None:
    route = route_coaching(
        CoachingRequest(decision="cash", question="Quiero analizar mi caja."),
        _supported_diagnostic(),
    )

    assert route.skill == "/escala-cash"
    assert route.supported is True
    assert route.decision == "cash"
    assert "solicitud" in route.rationale.lower()


def test_coaching_default_route_uses_lowest_supported_decision() -> None:
    route = route_coaching(CoachingRequest(), _supported_diagnostic())

    assert route.decision == "cash"
    assert route.skill == "/escala-cash"
    assert route.supported is True


def test_coaching_does_not_claim_unsupported_people_analysis() -> None:
    diagnostic = build_diagnostic(
        (DiagnosticAnswer(decision="cash", score=55, source_ids=("cash-source",)),)
    )
    route = route_coaching(CoachingRequest(decision="people"), diagnostic)

    assert route.decision == "people"
    assert route.skill == "/escala-people"
    assert route.supported is False
    assert route.questions
    assert "evidencia" in route.questions[0].lower()


def test_execution_state_round_trips_goals_priorities_tasks_and_continuity(
    tmp_path: Path,
) -> None:
    exchange = tmp_path / "exchange"
    exchange.mkdir()
    config = WorkspaceConfig(
        platform="macos",
        data_root=tmp_path / "data",
        database_path=tmp_path / "data" / "escala.sqlite",
        exchange_root=exchange,
    )
    state = ExecutionState(
        goals=(
            Goal(
                id="g1",
                title="Cobrar cartera",
                owner="Ana",
                due_date="2026-08-01",
                progress=40,
            ),
        ),
        priorities=(
            Priority(
                id="p1",
                title="Reducir días de cobro",
                owner="Ana",
                due_date="2026-07-31",
                progress=25,
            ),
        ),
        tasks=(
            ExecutionTask(
                id="t1",
                title="Confirmar saldos",
                owner="Luis",
                due_date="2026-07-25",
                priority_id="p1",
                progress=10,
            ),
        ),
        continuity=SessionContinuity(
            session_id="session-1",
            next_prompt="Confirmar CCC",
            pending_questions=("cash_conversion_cycle",),
        ),
    )

    receipt = save_execution_state(config, state)
    loaded = load_execution_state(config)

    assert loaded == state
    assert receipt.path == ".escala-executive/execution.json"
    assert (config.data_root / ".escala-executive" / "execution.json").is_file()
    assert list(exchange.iterdir()) == []


def test_execution_state_rejects_database_inside_exchange(tmp_path: Path) -> None:
    exchange = tmp_path / "exchange"
    exchange.mkdir()
    config = WorkspaceConfig(
        platform="macos",
        data_root=tmp_path / "data",
        database_path=exchange / "shared.sqlite",
        exchange_root=exchange,
    )
    state = ExecutionState(continuity=SessionContinuity(session_id="session-1"))

    with pytest.raises(WorkspaceAuthorityError):
        save_execution_state(config, state)


def test_corrupt_execution_state_fails_without_empty_fallback(tmp_path: Path) -> None:
    exchange = tmp_path / "exchange"
    exchange.mkdir()
    config = WorkspaceConfig(
        platform="macos",
        data_root=tmp_path / "data",
        database_path=tmp_path / "data" / "escala.sqlite",
        exchange_root=exchange,
    )
    output_dir = config.data_root / ".escala-executive"
    output_dir.mkdir(parents=True)
    (output_dir / "execution.json").write_text("{not-json", encoding="utf-8")

    with pytest.raises(PersistenceError):
        load_execution_state(config)


def test_honest_guidance_separates_facts_inferences_and_unknowns() -> None:
    guidance = build_honest_guidance(
        GuidanceRequest(
            topic="cash",
            facts=("Ventas de junio: 1.2M",),
            inferences=("Cobranza podría ser el cuello de botella",),
            unknowns=("cash_conversion_cycle",),
            question="¿Cuál es nuestro CCC?",
        )
    )

    assert guidance.status == "evidence_limited"
    assert guidance.facts == ("Ventas de junio: 1.2M",)
    assert guidance.inferences == ("Cobranza podría ser el cuello de botella",)
    assert guidance.unknowns == ("cash_conversion_cycle",)
    assert guidance.questions == ("¿Cuál es nuestro CCC?",)
    assert "cash_conversion_cycle" in guidance.next_action


def test_honest_guidance_does_not_invent_when_question_is_unbounded() -> None:
    guidance = build_honest_guidance(GuidanceRequest(topic="strategy"))

    assert guidance.status == "evidence_limited"
    assert guidance.facts == ()
    assert guidance.inferences == ()
    assert guidance.unknowns == ("strategy",)
    assert guidance.questions
