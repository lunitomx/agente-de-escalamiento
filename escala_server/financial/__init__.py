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
from .statements import (
    FinancialFigure,
    FinancialStatements,
    Provenance,
    StatementView,
    reconstruct_statements,
)
from .cash_decision import (
    CashAssumptions,
    CashDecision,
    CashImpact,
    CashScenarioRequest,
    CashScenarioResult,
    ValidatedCashInputs,
    build_cash_decision,
    render_cash_decision_receipt_json,
    render_cash_decision_receipt_markdown,
)
from .report import (
    CashReportArtifact,
    render_cash_report_receipt_json,
    render_cash_report_receipt_markdown,
    write_cash_report,
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
    "FinancialFigure",
    "FinancialStatements",
    "Provenance",
    "StatementView",
    "reconstruct_statements",
    "CashAssumptions",
    "CashDecision",
    "CashImpact",
    "CashScenarioRequest",
    "CashScenarioResult",
    "ValidatedCashInputs",
    "build_cash_decision",
    "render_cash_decision_receipt_json",
    "render_cash_decision_receipt_markdown",
    "CashReportArtifact",
    "render_cash_report_receipt_json",
    "render_cash_report_receipt_markdown",
    "write_cash_report",
]
