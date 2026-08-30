from __future__ import annotations

import pytest

from validators.form_layout_review import (
    FormLayoutReviewReceipt,
    validate_form_layout_review,
)


def _receipt() -> FormLayoutReviewReceipt:
    return FormLayoutReviewReceipt.model_validate(
        {
            "schema_version": 1,
            "domain": "people",
            "status": "pass",
            "reviewer_ref": "reviewer-001",
            "reviewed_on": "2026-08-27",
            "source_url": "https://example.com/private-form.pdf",
            "source_edition": "Private form edition",
            "rights_state": "private-validation-only",
            "asset_persisted": False,
            "method": "manual-visual-inspection",
            "forms": [
                {
                    "tool_ref": "tool-one",
                    "page": 2,
                    "topology_status": "matched",
                    "checked_axes": 2,
                    "checked_fields": 4,
                    "mismatch_count": 0,
                }
            ],
        }
    )


def test_visual_layout_receipt_requires_private_manual_pass_evidence() -> None:
    receipt = _receipt()
    validate_form_layout_review(receipt)


def test_visual_layout_receipt_rejects_persisted_asset_or_named_reviewer() -> None:
    payload = _receipt().model_dump(mode="json")
    payload["asset_persisted"] = True
    with pytest.raises(ValueError):
        FormLayoutReviewReceipt.model_validate(payload)

    payload = _receipt().model_dump(mode="json")
    payload["reviewer_ref"] = "Ana García"
    with pytest.raises(ValueError, match="opaque"):
        FormLayoutReviewReceipt.model_validate(payload)


def test_visual_layout_receipt_rejects_repeated_form_or_unresolved_mismatch() -> None:
    payload = _receipt().model_dump(mode="json")
    payload["forms"].append(payload["forms"][0].copy())
    with pytest.raises(ValueError, match="repeats"):
        FormLayoutReviewReceipt.model_validate(payload)

    payload = _receipt().model_dump(mode="json")
    payload["forms"][0]["mismatch_count"] = 1
    with pytest.raises(ValueError):
        FormLayoutReviewReceipt.model_validate(payload)


def test_visual_layout_receipt_allows_distinct_front_and_back_parts() -> None:
    payload = _receipt().model_dump(mode="json")
    payload["forms"] = [
        payload["forms"][0] | {"tool_ref": "tool-opsp", "form_part": "front"},
        payload["forms"][0] | {"tool_ref": "tool-opsp", "form_part": "back", "page": 3},
    ]
    validate_form_layout_review(FormLayoutReviewReceipt.model_validate(payload))


def test_visual_layout_receipt_rejects_repeated_tool_without_parts() -> None:
    payload = _receipt().model_dump(mode="json")
    payload["forms"].append(payload["forms"][0] | {"page": 3})
    with pytest.raises(ValueError, match="requires an explicit part"):
        FormLayoutReviewReceipt.model_validate(payload)
