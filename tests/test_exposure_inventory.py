from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from validators.exposure_inventory import (
    ExposureClassification,
    ExposureDisposition,
    ExposureFinding,
    ExposureSeverity,
    ExposureSurface,
    LocatorKind,
    build_risk_summary,
    exposure_policy_hash,
    load_exposure_policy,
    ordered_findings,
)


VALID_POLICY = """\
schema_version: 1
bounded_surfaces:
  - worktree
  - git_head
  - git_history
  - local_git_config
  - distribution_candidate
  - public_candidate
max_text_bytes: 1048576
distribution:
  default_eligibility: not_eligible
  generated_staging: not_built
rules:
  - id: reference.raw_asset
    surfaces: [worktree, git_head, git_history, public_candidate]
    classification: raw_reference
    severity: critical
    locator_kind: relative_path
    disposition: remove_in_s36_3
    matchers:
      path_globs: ["*.pdf"]
      content_terms: []
      secret_shapes: []
  - id: secret.assignment
    surfaces: [worktree, git_head, public_candidate]
    classification: secret_candidate
    severity: high
    locator_kind: sha256
    disposition: review_security
    matchers:
      path_globs: []
      content_terms: []
      secret_shapes: [assignment]
  - id: config.authenticated_remote
    surfaces: [local_git_config]
    classification: credential_risk
    severity: critical
    locator_kind: remote_name
    disposition: review_security
    matchers:
      path_globs: []
      content_terms: []
      secret_shapes: [authenticated_url]
"""


def _write_policy(tmp_path: Path, content: str = VALID_POLICY) -> Path:
    path = tmp_path / "exposure-policy.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def _finding(
    *,
    rule_id: str = "reference.raw_asset",
    surface: ExposureSurface = ExposureSurface.GIT_HEAD,
    classification: ExposureClassification = ExposureClassification.RAW_REFERENCE,
    severity: ExposureSeverity = ExposureSeverity.CRITICAL,
    locator_kind: LocatorKind = LocatorKind.RELATIVE_PATH,
    locator: str = "reference-asset.pdf",
    disposition: ExposureDisposition = ExposureDisposition.REMOVE_IN_S36_3,
) -> ExposureFinding:
    return ExposureFinding(
        rule_id=rule_id,
        surface=surface,
        classification=classification,
        severity=severity,
        locator_kind=locator_kind,
        locator=locator,
        disposition=disposition,
    )


def test_policy_loads_strict_contract_and_has_stable_hash(tmp_path: Path) -> None:
    first = load_exposure_policy(_write_policy(tmp_path))
    second = load_exposure_policy(_write_policy(tmp_path))

    assert first.schema_version == 1
    assert first.bounded_surfaces == list(ExposureSurface)
    assert first.max_text_bytes == 1_048_576
    assert first.distribution.default_eligibility == "not_eligible"
    assert first.distribution.generated_staging == "not_built"
    assert [rule.id for rule in first.rules] == [
        "config.authenticated_remote",
        "reference.raw_asset",
        "secret.assignment",
    ]
    assert exposure_policy_hash(first) == exposure_policy_hash(second)
    assert len(exposure_policy_hash(first)) == 64


@pytest.mark.parametrize(
    "content",
    [
        VALID_POLICY + "unknown_root: true\n",
        VALID_POLICY.replace("max_text_bytes: 1048576", "max_text_bytes: 0"),
        VALID_POLICY.replace("  - public_candidate\n", ""),
        VALID_POLICY.replace("classification: raw_reference", "classification: x"),
        VALID_POLICY.replace('path_globs: ["*.pdf"]', 'path_globs: ["../*.pdf"]'),
        VALID_POLICY.replace(
            "  - id: secret.assignment",
            "  - id: reference.raw_asset",
        ),
        VALID_POLICY.replace("secret_shapes: [assignment]", "secret_shapes: [unknown]"),
    ],
)
def test_policy_rejects_unknown_incomplete_or_unsafe_contracts(
    tmp_path: Path,
    content: str,
) -> None:
    with pytest.raises(ValidationError):
        load_exposure_policy(_write_policy(tmp_path, content))


@pytest.mark.parametrize(
    ("locator_kind", "locator"),
    [
        (LocatorKind.RELATIVE_PATH, "/absolute/private.txt"),
        (LocatorKind.RELATIVE_PATH, "../private.txt"),
        (LocatorKind.RELATIVE_PATH, "safe/../private.txt"),
        (LocatorKind.RELATIVE_PATH, "safe\\private.txt"),
        (LocatorKind.SHA256, "not-a-sha"),
        (LocatorKind.REMOTE_NAME, "unsafe remote"),
    ],
)
def test_finding_rejects_unsafe_locators(
    locator_kind: LocatorKind,
    locator: str,
) -> None:
    with pytest.raises(ValidationError):
        _finding(locator_kind=locator_kind, locator=locator)


def test_finding_rejects_sensitive_or_unknown_serialized_fields() -> None:
    payload = _finding().model_dump(mode="json")
    payload["raw_value"] = "must-never-be-a-model-field"

    with pytest.raises(ValidationError):
        ExposureFinding.model_validate(payload)


@pytest.mark.parametrize(
    "finding",
    [
        {
            "rule_id": "secret.assignment",
            "surface": "git_head",
            "classification": "secret_candidate",
            "severity": "high",
            "locator_kind": "relative_path",
            "locator": "config.txt",
            "disposition": "review_security",
        },
        {
            "rule_id": "config.authenticated_remote",
            "surface": "local_git_config",
            "classification": "credential_risk",
            "severity": "critical",
            "locator_kind": "sha256",
            "locator": "a" * 64,
            "disposition": "review_security",
        },
        {
            "rule_id": "reference.raw_asset",
            "surface": "git_head",
            "classification": "raw_reference",
            "severity": "critical",
            "locator_kind": "relative_path",
            "locator": "reference.pdf",
            "disposition": "review_security",
        },
    ],
)
def test_finding_rejects_incoherent_classification_boundary(
    finding: dict[str, str],
) -> None:
    with pytest.raises(ValidationError):
        ExposureFinding.model_validate(finding)


def test_findings_are_ordered_deterministically() -> None:
    lower = _finding(
        rule_id="public.methodology",
        surface=ExposureSurface.WORKTREE,
        classification=ExposureClassification.PUBLIC_VOCABULARY,
        severity=ExposureSeverity.HIGH,
        locator="README.md",
        disposition=ExposureDisposition.REVIEW_IN_S36_3,
    )
    higher = _finding(locator="reference-asset.pdf")

    assert ordered_findings([higher, lower]) == [lower, higher]
    assert ordered_findings([lower, higher]) == [lower, higher]


def test_risk_summary_is_complete_and_deterministic() -> None:
    findings = [
        _finding(),
        _finding(
            rule_id="public.methodology",
            classification=ExposureClassification.PUBLIC_VOCABULARY,
            severity=ExposureSeverity.HIGH,
            locator="README.md",
            disposition=ExposureDisposition.REVIEW_IN_S36_3,
        ),
        _finding(
            rule_id="internal.work",
            classification=ExposureClassification.INTERNAL_PATH,
            severity=ExposureSeverity.MEDIUM,
            locator="work/private.md",
            disposition=ExposureDisposition.BLOCK_IN_S36_5,
        ),
    ]

    summary = build_risk_summary(findings)

    assert summary.model_dump(mode="json") == {
        "critical": 1,
        "high": 1,
        "medium": 1,
        "low": 0,
        "info": 0,
    }
