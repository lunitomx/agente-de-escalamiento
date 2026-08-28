"""Diagnose module — structured assessment across 4 decisions."""

from .explainable import score_diagnostic
from .intake import build_diagnostic_intake
from .prefill import build_prefill, confirm_prefill
from .result import build_diagnostic_result
from .models import (
    DiagnosticResult,
    DecisionScore,
    DiagnosticEvidence,
    DiagnosticIntake,
    ExplainableDiagnosis,
    FunnelMetrics,
    PrefillResult,
    RouteAction,
)
from .narrative import (
    CompanyUnderstanding,
    FocusProposal,
    NarrativeAssessment,
    NarrativeFinding,
    assessment_to_artifact,
    build_narrative_assessment,
    render_narrative_assessment,
)

__all__ = [
    "DiagnosticEvidence",
    "DiagnosticIntake",
    "DiagnosticResult",
    "DecisionScore",
    "ExplainableDiagnosis",
    "FunnelMetrics",
    "PrefillResult",
    "RouteAction",
    "CompanyUnderstanding",
    "FocusProposal",
    "NarrativeAssessment",
    "NarrativeFinding",
    "assessment_to_artifact",
    "build_prefill",
    "build_diagnostic_intake",
    "build_diagnostic_result",
    "build_narrative_assessment",
    "confirm_prefill",
    "render_narrative_assessment",
    "score_diagnostic",
]

from pathlib import Path
from ..core import read_yaml, write_yaml


# 5 questions per decision, mapped to ontology concepts
DIAGNOSE_QUESTIONS = {
    "people": {
        "key": "people",
        "label": "People — Personas",
        "summary": "Right people doing the right things right.",
        "questions": [
            {
                "id": "people_q1",
                "text": "¿Podrías re-contratar con entusiasmo a todos en tu equipo de liderazgo?",
                "concept": "concept-right-people-right-seats",
            },
            {
                "id": "people_q2",
                "text": "¿Tus empleados pueden articular los core values de la empresa?",
                "concept": "concept-core-values",
            },
            {
                "id": "people_q3",
                "text": "¿Cada persona sabe exactamente qué se espera de ella y cómo se mide su éxito?",
                "concept": "tool-face",
            },
            {
                "id": "people_q4",
                "text": "¿Tu proceso de contratación predice consistentemente buenos resultados?",
                "concept": "tool-topgrading",
            },
            {
                "id": "people_q5",
                "text": "¿Tienes un plan de desarrollo para tu equipo de liderazgo?",
                "concept": "tool-five-manager-activities",
            },
        ],
    },
    "strategy": {
        "key": "strategy",
        "label": "Strategy — Estrategia",
        "summary": "Creating a differentiated strategy that drives sustainable revenue growth.",
        "questions": [
            {
                "id": "strategy_q1",
                "text": "¿Puedes articular tu estrategia en una sola página (OPSP)?",
                "concept": "tool-opsp",
            },
            {
                "id": "strategy_q2",
                "text": "¿Tu equipo puede explicar qué hace diferente a tu empresa en 30 segundos?",
                "concept": "tool-7-strata",
            },
            {
                "id": "strategy_q3",
                "text": "¿Tienes una Brand Promise medible que tus clientes valoran?",
                "concept": "concept-brand-promise",
            },
            {
                "id": "strategy_q4",
                "text": "¿Sabes cuál es tu Profit per X (el motor económico de tu negocio)?",
                "concept": "tool-profit-per-x",
            },
            {
                "id": "strategy_q5",
                "text": "¿Tienes un BHAG que inspira a todo el equipo?",
                "concept": "concept-bhag",
            },
        ],
    },
    "execution": {
        "key": "execution",
        "label": "Execution — Ejecución",
        "summary": "Discipline of execution through rhythms, priorities, and data.",
        "questions": [
            {
                "id": "execution_q1",
                "text": "¿Tu equipo tiene un daily huddle de 15 minutos o menos?",
                "concept": "tool-daily-huddle",
            },
            {
                "id": "execution_q2",
                "text": "¿Cada empleado tiene 1-2 KPIs que revisa diariamente?",
                "concept": "tool-scoreboard",
            },
            {
                "id": "execution_q3",
                "text": "¿Tienen prioridades trimestrales claras con un Critical Number?",
                "concept": "concept-critical-number",
            },
            {
                "id": "execution_q4",
                "text": "¿Cada compromiso tiene un Who-What-When asignado?",
                "concept": "concept-priorities-rocks",
            },
            {
                "id": "execution_q5",
                "text": "¿El feedback de clientes y empleados se recolecta y actúa sistemáticamente?",
                "concept": "tool-execution-habits",
            },
        ],
    },
    "cash": {
        "key": "cash",
        "label": "Cash — Efectivo",
        "summary": "Cash flow as the fuel for growth.",
        "questions": [
            {
                "id": "cash_q1",
                "text": "¿Sabes cuántos días tarda tu empresa en convertir una inversión en cash de vuelta (CCC)?",
                "concept": "concept-ccc",
            },
            {
                "id": "cash_q2",
                "text": "¿Conoces tu Cash Conversion Cycle completo (ventas → entrega → cobro)?",
                "concept": "tool-ccc-analysis",
            },
            {
                "id": "cash_q3",
                "text": "¿Has calculado el impacto de mejorar 1% el precio, volumen o costos (Power of One)?",
                "concept": "tool-power-of-one",
            },
            {
                "id": "cash_q4",
                "text": "¿Tu crecimiento se auto-financia o dependes de deuda/inversión externa?",
                "concept": "concept-working-capital",
            },
            {
                "id": "cash_q5",
                "text": "¿Conoces tu ingreso por empleado y cómo se compara con tu industria?",
                "concept": "metric-revenue-per-employee",
            },
        ],
    },
}


SCORE_LABELS = {
    1: "No iniciado — sin proceso formal",
    2: "Ad hoc — algo de conciencia, sin sistema",
    3: "Emergente — frameworks básicos en lugar",
    4: "Establecido — sistemático, medido",
    5: "Optimizado — ventaja competitiva",
}

PRIORITY_ORDER = ["people", "strategy", "execution", "cash"]

ROUTING_RULES = {
    "people": "/escala-people",
    "strategy": "/escala-strategy",
    "execution": "/escala-execution",
    "cash": "/escala-cash",
}


def calculate_score(answers: list[int]) -> int:
    """Average of answer scores, rounded to nearest integer."""
    if not answers:
        return 0
    return round(sum(answers) / len(answers))


def detect_priority(scores: dict[str, int]) -> str:
    """Detect highest-priority decision (lowest score, tiebroken by PRIORITY_ORDER)."""
    valid = {k: v for k, v in scores.items() if v and v > 0}
    if not valid:
        return "people"
    lowest_score = min(valid.values())
    candidates = [k for k in PRIORITY_ORDER if k in valid and valid[k] == lowest_score]
    return candidates[0]


def run(context: dict) -> dict:
    """
    Execute diagnosis assessment.

    Context keys:
        - answers: dict of {question_id: score (1-5)}
        - decisions: list of decisions to assess (default: all 4)
        - mode: 'full' | 'partial' (default: 'full')
        - base_path: str
        - existing_scores: dict (for partial re-diagnosis)

    Returns:
        dict with output, artifacts, errors
    """
    base = Path(context.get("base_path", "."))
    if context.get("action") == "narrative_assessment":
        return _run_narrative_assessment(context, base)

    profile_path = base / ".escala" / "agent" / "memory" / "company-profile.yaml"
    profile = read_yaml(profile_path)

    answers = context.get("answers", {})
    decisions = context.get("decisions", list(DIAGNOSE_QUESTIONS.keys()))
    mode = context.get("mode", "full")
    existing_scores = context.get("existing_scores", profile.get("scores", {}))

    errors = []

    # Validate answers
    if mode == "full":
        required_decisions = list(DIAGNOSE_QUESTIONS.keys())
    else:
        required_decisions = decisions

    for dec_key in required_decisions:
        if dec_key not in DIAGNOSE_QUESTIONS:
            errors.append(f"Unknown decision: {dec_key}")
            continue
        qs = DIAGNOSE_QUESTIONS[dec_key]["questions"]
        missing = [q["id"] for q in qs if answers.get(q["id"]) is None]
        invalid = [
            q["id"]
            for q in qs
            if answers.get(q["id"]) is not None
            and (
                not isinstance(answers[q["id"]], int)
                or answers[q["id"]] < 1
                or answers[q["id"]] > 5
            )
        ]

        if missing:
            errors.append(f"{dec_key}: missing answers for {missing}")
        if invalid:
            errors.append(f"{dec_key}: invalid scores (must be 1-5) for {invalid}")

    if errors:
        return {"output": "", "artifacts": {}, "errors": errors}

    # Calculate scores
    new_scores = dict(existing_scores)
    for dec_key in decisions:
        qs = DIAGNOSE_QUESTIONS[dec_key]["questions"]
        dec_answers = [answers[q["id"]] for q in qs if answers.get(q["id"]) is not None]
        if dec_answers:
            new_scores[dec_key] = calculate_score(dec_answers)

    # Detect priority
    priority = detect_priority(new_scores)

    # Build report
    report_lines = [
        "## Diagnóstico de las 4 Decisiones",
        "",
        "| Decisión | Score | Nivel |",
        "|----------|-------|-------|",
    ]

    for dec_key in PRIORITY_ORDER:
        score = new_scores.get(dec_key, 0)
        level = SCORE_LABELS.get(score, "No evaluado")
        marker = " ⬅ PRIORIDAD" if dec_key == priority else ""
        report_lines.append(
            f"| {DIAGNOSE_QUESTIONS[dec_key]['label']} | {score} | {level}{marker} |"
        )

    report_lines.extend(
        [
            "",
            f"### Prioridad recomendada: {DIAGNOSE_QUESTIONS[priority]['label']}",
            "",
            f"{DIAGNOSE_QUESTIONS[priority]['summary']}",
            "",
            f"Tu score más bajo está en **{DIAGNOSE_QUESTIONS[priority]['label']}**. "
            f"Te recomiendo empezar por ahí con `{ROUTING_RULES[priority]}`.",
            "",
            "### Próximos pasos sugeridos",
            "",
        ]
    )

    remaining = [(k, v) for k, v in new_scores.items() if k != priority and v and v > 0]
    remaining.sort(key=lambda x: x[1])
    for dec_key, score in remaining:
        report_lines.append(
            f"- `{ROUTING_RULES[dec_key]}` — {DIAGNOSE_QUESTIONS[dec_key]['label']} (score: {score})"
        )

    report_lines.append("")
    report_lines.append("> Para re-evaluar: `/escala-diagnose`")

    output = "\n".join(report_lines)

    # Save scores to profile
    if profile:
        profile["scores"] = new_scores
        profile["focus"] = profile.get("focus", {})
        profile["focus"]["current_decision"] = priority
        profile["focus"]["last_diagnosis"] = str(
            __import__("datetime").datetime.now().date()
        )
        write_yaml(profile_path, profile)

    return {
        "output": output,
        "artifacts": {
            "scores": new_scores,
            "priority": priority,
            "profile_path": str(profile_path),
        },
        "errors": [],
    }


def _run_narrative_assessment(context: dict, base: Path) -> dict:
    """Build a confirmable narrative assessment without a required score."""
    from pydantic import ValidationError

    from .intake import build_diagnostic_intake
    from .narrative import (
        assessment_to_artifact,
        build_narrative_assessment,
        render_narrative_assessment,
    )

    try:
        intake = build_diagnostic_intake(
            company=context.get("company"),
            evidence=context.get("evidence", ()),
            open_context=context.get("open_context"),
            owner_context=context.get("owner_context"),
        )
        assessment = build_narrative_assessment(
            intake,
            company_summary=context.get("company_summary", ""),
            company_understanding=context.get("company_understanding", {}),
            findings=context.get("findings", ()),
            proposed_focuses=context.get("proposed_focuses", ()),
            open_questions=context.get("open_questions", ()),
            confirmation_status=context.get("confirmation_status", "pending"),
        )
    except (TypeError, ValidationError, ValueError) as exc:
        return {
            "output": "",
            "artifacts": {},
            "errors": [f"contexto inválido: {exc}"],
        }

    wants_persistence = bool(context.get("persist_authorized", False))
    if wants_persistence and assessment.confirmation_status == "pending":
        return {
            "output": "",
            "artifacts": {},
            "errors": [
                "El assessment requiere confirmación o corrección antes de guardarse."
            ],
        }

    profile_path = base / ".escala" / "agent" / "memory" / "company-profile.yaml"
    persisted_path: str | None = None
    if wants_persistence:
        profile = dict(read_yaml(profile_path) or {})
        artifact = assessment_to_artifact(assessment)
        assessments = list(profile.get("narrative_assessments", []))
        assessments.append(artifact)
        profile["narrative_assessments"] = assessments
        profile["narrative_assessment"] = artifact
        write_yaml(profile_path, profile)
        persisted_path = str(profile_path)

    return {
        "output": render_narrative_assessment(assessment),
        "artifacts": {
            "action": "narrative_assessment",
            "assessment": assessment_to_artifact(assessment),
            "persisted_assessment_path": persisted_path,
        },
        "errors": [],
    }


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.diagnose``."""
    result = run({})
    if result.get("output"):
        print(result["output"])
    for error in result.get("errors", []):
        print(error)
