"""Pure guided onboarding validation for E40."""

from __future__ import annotations

from collections.abc import Iterable

from .models import (
    CompanyProfile,
    OnboardingQuestion,
    OnboardingResult,
    ProfileAnswer,
    ProfileField,
)


REQUIRED_PROFILE_FIELDS: tuple[str, ...] = (
    "company_name",
    "industry",
    "stage",
    "employees",
    "critical_number",
)


def build_company_profile(answers: Iterable[ProfileAnswer]) -> OnboardingResult:
    """Build a stable profile while retaining unanswered material fields."""

    answer_map: dict[str, ProfileAnswer] = {}
    for answer in answers:
        answer_map[answer.key] = answer

    fields: list[ProfileField] = []
    unresolved: list[str] = []
    questions: list[OnboardingQuestion] = []
    for key in REQUIRED_PROFILE_FIELDS:
        answer = answer_map.get(key)
        if answer is None:
            unresolved.append(key)
            questions.append(
                OnboardingQuestion(
                    field=key,
                    prompt=f"¿Cuál es el valor actual de {key.replace('_', ' ')}?",
                    reason="missing",
                )
            )
            fields.append(ProfileField(key=key, value=None, status="unknown"))
            continue
        fields.append(
            ProfileField(
                key=key,
                value=answer.value,
                status=answer.status,
                question=answer.question,
            )
        )
        if answer.status != "fact" or answer.value is None:
            unresolved.append(key)
            questions.append(
                OnboardingQuestion(
                    field=key,
                    prompt=answer.question
                    or f"¿Puedes confirmar {key.replace('_', ' ')}?",
                    reason="uncertain" if answer.status == "inference" else "missing",
                )
            )

    profile = CompanyProfile(fields=tuple(fields))
    return OnboardingResult(
        profile=profile,
        status="ready" if not unresolved else "needs_clarification",
        unresolved_fields=tuple(unresolved),
        questions=tuple(questions),
    )
