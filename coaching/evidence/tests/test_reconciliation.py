from coaching.evidence import run
from coaching.evidence.reconciliation import (
    FinancialMeasurement,
    reconcile_financial_measurements,
)


def _measurement(**overrides):
    data = {
        "measurement_id": "source-a",
        "kind": "collection",
        "value": 100.0,
        "currency": "MXN",
        "period": "2026-07",
        "basis_date": "2026-07-31",
        "source": "erp-julio.csv",
    }
    data.update(overrides)
    return FinancialMeasurement(**data)


def test_same_nature_and_basis_is_reconciled_but_different_natures_are_blocked():
    result = reconcile_financial_measurements(
        [
            _measurement(),
            _measurement(measurement_id="source-b", source="banco-julio.csv"),
            _measurement(
                measurement_id="source-c", kind="settlement", source="pasarela.csv"
            ),
        ]
    )
    assert result.status == "ready"
    assert any(finding.kind == "agreement" for finding in result.findings)
    assert any(finding.kind == "incompatible" for finding in result.findings)


def test_mismatched_basis_or_conflict_requires_clarification_without_ratio():
    result = reconcile_financial_measurements(
        [
            _measurement(),
            _measurement(
                measurement_id="source-b", period="2026-06", source="erp-junio.csv"
            ),
        ]
    )
    assert result.status == "needs_clarification"
    assert result.findings[0].kind == "not_comparable"
    assert result.questions


def test_run_exposes_structured_result_and_no_implicit_comparison():
    result = run(
        {
            "action": "cash_reconciliation",
            "measurements": [
                _measurement().model_dump(),
                _measurement(
                    measurement_id="source-b", kind="purchase", source="compras.csv"
                ).model_dump(),
            ],
        }
    )
    assert result["errors"] == []
    findings = result["artifacts"]["reconciliation"]["findings"]
    assert findings[0]["kind"] == "incompatible"
