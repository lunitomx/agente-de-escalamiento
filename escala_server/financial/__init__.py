"""Local financial intelligence contracts for E38.

The package intentionally stops at a profiled, explainable boundary. It reads
documents from the E37 exchange seam and never writes to the source workbook or
to a synchronized database.
"""

from .profiling import (
    FinancialWorkbookProfile,
    MappingAnswer,
    MappingCandidate,
    MappingQuestion,
    profile_financial_workbook,
    render_profile_receipt_json,
    render_profile_receipt_markdown,
    resolve_mapping_answers,
)

__all__ = [
    "FinancialWorkbookProfile",
    "MappingAnswer",
    "MappingCandidate",
    "MappingQuestion",
    "profile_financial_workbook",
    "render_profile_receipt_json",
    "render_profile_receipt_markdown",
    "resolve_mapping_answers",
]
