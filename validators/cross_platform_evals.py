"""Semantic parity evaluation for the E68 Codex and Claude routing suite."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from validators.activation_evals import (
    ActivationObservation,
    ActivationSuite,
    evaluate_activation_suite,
)


@dataclass(frozen=True)
class CrossPlatformCaseResult:
    case_id: str
    codex_action: str
    claude_action: str
    codex_procedure_id: str | None
    claude_procedure_id: str | None
    equivalent: bool


@dataclass(frozen=True)
class CrossPlatformEvaluation:
    cases: tuple[CrossPlatformCaseResult, ...]
    codex_precision: float
    codex_recall: float
    claude_precision: float
    claude_recall: float
    semantic_differences: tuple[str, ...]


def evaluate_cross_platform(
    suite: ActivationSuite,
    codex_observations: Sequence[ActivationObservation],
    claude_observations: Sequence[ActivationObservation],
) -> CrossPlatformEvaluation:
    """Compare resolved procedures, so approved aliases remain equivalent."""

    codex = evaluate_activation_suite(suite, codex_observations)
    claude = evaluate_activation_suite(suite, claude_observations)
    codex_by_id = {result.case_id: result for result in codex.cases}
    claude_by_id = {result.case_id: result for result in claude.cases}
    cases: list[CrossPlatformCaseResult] = []
    differences: list[str] = []
    for case in suite.cases:
        codex_case = codex_by_id[case.case_id]
        claude_case = claude_by_id[case.case_id]
        equivalent = (
            codex_case.observed_action == claude_case.observed_action
            and codex_case.observed_procedure_id == claude_case.observed_procedure_id
        )
        if not equivalent:
            differences.append(case.case_id)
        cases.append(
            CrossPlatformCaseResult(
                case_id=case.case_id,
                codex_action=codex_case.observed_action,
                claude_action=claude_case.observed_action,
                codex_procedure_id=codex_case.observed_procedure_id,
                claude_procedure_id=claude_case.observed_procedure_id,
                equivalent=equivalent,
            )
        )
    return CrossPlatformEvaluation(
        cases=tuple(cases),
        codex_precision=codex.precision,
        codex_recall=codex.recall,
        claude_precision=claude.precision,
        claude_recall=claude.recall,
        semantic_differences=tuple(differences),
    )
