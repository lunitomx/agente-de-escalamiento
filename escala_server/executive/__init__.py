"""Local executive cockpit and coaching contracts for E40."""

from .cockpit import (
    build_cockpit,
    render_cockpit_html,
    render_cockpit_json,
    write_cockpit,
)
from .coaching import build_strategy_plan, route_coaching
from .diagnostic import build_diagnostic
from .models import (
    CockpitArtifact,
    CockpitCard,
    CoachingRequest,
    CoachingRoute,
    DECISIONS,
    CompanyProfile,
    DiagnosticAnswer,
    DecisionAssessment,
    EvidenceItem,
    ExecutiveDiagnostic,
    ExecutiveCockpit,
    OnboardingQuestion,
    OnboardingResult,
    ProfileAnswer,
    ProfileField,
    PainDrillDown,
    StrategyAnswer,
    StrategyPlan,
)
from .onboarding import build_company_profile

__all__ = [
    "DECISIONS",
    "CockpitArtifact",
    "CockpitCard",
    "CoachingRequest",
    "CoachingRoute",
    "CompanyProfile",
    "DiagnosticAnswer",
    "DecisionAssessment",
    "EvidenceItem",
    "ExecutiveDiagnostic",
    "ExecutiveCockpit",
    "OnboardingQuestion",
    "OnboardingResult",
    "ProfileAnswer",
    "ProfileField",
    "PainDrillDown",
    "StrategyAnswer",
    "StrategyPlan",
    "build_cockpit",
    "build_company_profile",
    "build_diagnostic",
    "build_strategy_plan",
    "render_cockpit_html",
    "render_cockpit_json",
    "write_cockpit",
    "route_coaching",
]
