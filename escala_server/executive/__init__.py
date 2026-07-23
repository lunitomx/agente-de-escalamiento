"""Local executive cockpit and coaching contracts for E40."""

from .cockpit import (
    build_cockpit,
    render_cockpit_html,
    render_cockpit_json,
    write_cockpit,
)
from .diagnostic import build_diagnostic
from .models import (
    CockpitArtifact,
    CockpitCard,
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
)
from .onboarding import build_company_profile

__all__ = [
    "DECISIONS",
    "CockpitArtifact",
    "CockpitCard",
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
    "build_cockpit",
    "build_company_profile",
    "build_diagnostic",
    "render_cockpit_html",
    "render_cockpit_json",
    "write_cockpit",
]
