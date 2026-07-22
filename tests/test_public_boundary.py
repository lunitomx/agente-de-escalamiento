from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import pytest
from pydantic import ValidationError
import yaml

from validators.public_boundary import (
    BoundaryFindingCode,
    BoundaryLocatorKind,
    BoundarySurface,
    PublicBoundaryFinding,
    PublicPathDisposition,
    classify_public_path,
    group_boundary_findings,
    load_exposure_baseline_link,
    load_public_boundary_policy,
    public_boundary_policy_hash,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "governance/public-boundary.yaml"
BASELINE_PATH = (
    ROOT
    / "work/epics/e36-product-truth-ip-governance/stories"
    / "s36.2-evidence/baseline.json"
)
BASELINE_SHA256 = "3ae688c34b8cb13dcf96bd72198aeee6e4eace0a432b413cc654d1c279943dce"


def _write_policy(tmp_path: Path, data: dict[str, Any]) -> Path:
    path = tmp_path / "public-boundary.yaml"
    path.write_text(
        yaml.safe_dump(data, allow_unicode=False, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _policy_data() -> dict[str, Any]:
    data = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _finding(
    *,
    rule_id: str = "public.source_identity",
    code: BoundaryFindingCode = BoundaryFindingCode.PROHIBITED_TEXT,
    surface: BoundarySurface = BoundarySurface.PRIVATE_HEAD,
    locator: str = "README.md",
) -> PublicBoundaryFinding:
    return PublicBoundaryFinding(
        rule_id=rule_id,
        code=code,
        surface=surface,
        locator_kind=BoundaryLocatorKind.RELATIVE_PATH,
        locator=locator,
    )


def test_canonical_policy_loads_strictly_and_hashes_stably() -> None:
    first = load_public_boundary_policy(POLICY_PATH)
    second = load_public_boundary_policy(POLICY_PATH)

    assert first.schema_version == 1
    assert first.default_disposition is PublicPathDisposition.NOT_ELIGIBLE
    assert first.precedence == [
        PublicPathDisposition.DENIED,
        PublicPathDisposition.CANDIDATE_PUBLIC,
    ]
    assert {rule.deny_class.value for rule in first.path_rules if rule.deny_class} == {
        "raw",
        "derived",
        "private",
        "internal",
    }
    assert first.forbidden_yaml_root_keys == ["source"]
    assert public_boundary_policy_hash(first) == public_boundary_policy_hash(second)
    assert len(public_boundary_policy_hash(first)) == 64


@pytest.mark.parametrize(
    "mutator",
    [
        lambda data: data.update({"unknown_root": True}),
        lambda data: data.update({"default_disposition": "denied"}),
        lambda data: data.update({"precedence": ["candidate_public", "denied"]}),
        lambda data: data["path_rules"][0].update({"unknown": True}),
        lambda data: data["path_rules"][0].update({"disposition": "unknown"}),
        lambda data: data["path_rules"][0].update({"globs": ["../**"]}),
        lambda data: data["path_rules"][0].update({"globs": ["**"]}),
        lambda data: data["path_rules"][1].update({"id": data["path_rules"][0]["id"]}),
        lambda data: data["path_rules"][0].update({"deny_class": "internal"}),
    ],
)
def test_policy_rejects_unknown_incomplete_or_unsafe_contracts(
    tmp_path: Path,
    mutator: Callable[[dict[str, Any]], None],
) -> None:
    data = _policy_data()
    mutator(data)

    with pytest.raises(ValidationError):
        load_public_boundary_policy(_write_policy(tmp_path, data))


@pytest.mark.parametrize(
    ("rule_index", "rule"),
    [
        (
            3,
            {
                "id": "deny.internal_nested",
                "disposition": "denied",
                "deny_class": "internal",
                "globs": ["work/private/**"],
            },
        ),
        (
            -1,
            {
                "id": "canary.coaching_nested",
                "disposition": "candidate_public",
                "deny_class": None,
                "globs": ["coaching/private/**"],
            },
        ),
    ],
)
def test_policy_rejects_ambiguous_same_disposition_overlaps(
    tmp_path: Path,
    rule_index: int,
    rule: dict[str, Any],
) -> None:
    data = _policy_data()
    rules = data["path_rules"]
    assert isinstance(rules, list)
    if rule_index == -1:
        rules.append(rule)
    else:
        rules.insert(rule_index + 1, rule)

    with pytest.raises(ValidationError):
        load_public_boundary_policy(_write_policy(tmp_path, data))


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("README.md", PublicPathDisposition.CANDIDATE_PUBLIC),
        ("coaching/strategy/session.py", PublicPathDisposition.CANDIDATE_PUBLIC),
        (
            "escala_server/data/book-knowledge.json",
            PublicPathDisposition.DENIED,
        ),
        ("work/private/evidence.md", PublicPathDisposition.DENIED),
        ("new/unclassified.txt", PublicPathDisposition.NOT_ELIGIBLE),
    ],
)
def test_path_classification_is_deny_first_and_closed_by_default(
    path: str,
    expected: PublicPathDisposition,
) -> None:
    policy = load_public_boundary_policy(POLICY_PATH)

    assert classify_public_path(policy, path) is expected


@pytest.mark.parametrize(
    "path",
    ["/private/file.txt", "../private.txt", "safe/../private.txt", "safe\\file.txt"],
)
def test_path_classification_rejects_unsafe_locators(path: str) -> None:
    policy = load_public_boundary_policy(POLICY_PATH)

    with pytest.raises(ValueError):
        classify_public_path(policy, path)


def test_generic_validator_does_not_hard_code_prohibited_terms() -> None:
    policy = load_public_boundary_policy(POLICY_PATH)
    validator_source = (ROOT / "validators/public_boundary.py").read_text(
        encoding="utf-8"
    )

    assert all(
        term.casefold() not in validator_source.casefold()
        for rule in policy.vocabulary_rules
        for term in rule.terms
    )


def test_finding_is_frozen_safe_and_rejects_sensitive_extra_fields() -> None:
    finding = _finding()
    assert finding.model_dump(mode="json") == {
        "rule_id": "public.source_identity",
        "code": "prohibited_text",
        "surface": "private_head",
        "locator_kind": "relative_path",
        "locator": "README.md",
    }

    payload = finding.model_dump(mode="json")
    payload["matched_value"] = "sentinel-secret-value"
    with pytest.raises(ValidationError):
        PublicBoundaryFinding.model_validate(payload)
    with pytest.raises(ValidationError):
        PublicBoundaryFinding.model_validate(
            {**finding.model_dump(mode="json"), "locator": "/private/root"}
        )
    with pytest.raises(ValidationError):
        PublicBoundaryFinding.model_validate(
            {**finding.model_dump(mode="json"), "rule_id": "https://private.invalid"}
        )

    with pytest.raises(ValidationError):
        finding.locator = "changed.md"  # type: ignore[misc]


def test_findings_group_deterministically_without_values() -> None:
    findings = [
        _finding(locator="README.md"),
        _finding(locator="coaching/a.md"),
        _finding(
            rule_id="public.provenance",
            code=BoundaryFindingCode.PROHIBITED_YAML_KEY,
            surface=BoundarySurface.PRIVATE_WORKTREE,
            locator="conocimiento/a.yaml",
        ),
    ]

    groups = group_boundary_findings(reversed(findings))

    assert [group.model_dump(mode="json") for group in groups] == [
        {
            "rule_id": "public.provenance",
            "code": "prohibited_yaml_key",
            "surface": "private_worktree",
            "count": 1,
        },
        {
            "rule_id": "public.source_identity",
            "code": "prohibited_text",
            "surface": "private_head",
            "count": 2,
        },
    ]


def test_canonical_s36_2_baseline_link_is_exact_and_typed() -> None:
    assert hashlib.sha256(BASELINE_PATH.read_bytes()).hexdigest() == BASELINE_SHA256
    policy = load_public_boundary_policy(POLICY_PATH)

    link = load_exposure_baseline_link(ROOT, policy)

    assert link.baseline_sha256 == BASELINE_SHA256
    assert link.scan_status == "complete"
    assert link.policy_sha256 == (
        "7eec173c0b2a132b15a3a1dfda8cfdeeac36e27621a1bf5a70a0fe37b61c7b0c"
    )
    assert link.verifier_source_commit == "e863f781600a99c476e0f1182ddcc8552983b7e3"
    assert link.raw_surface_states.model_dump(mode="json") == {
        "worktree": "absent",
        "git_head": "present",
        "git_history": "historical",
    }


def test_baseline_link_rejects_hash_or_surface_drift(tmp_path: Path) -> None:
    baseline_locator = Path("baseline.json")
    (tmp_path / baseline_locator).write_bytes(BASELINE_PATH.read_bytes())
    data = _policy_data()
    baseline = data["baseline"]
    assert isinstance(baseline, dict)
    baseline["locator"] = baseline_locator.as_posix()
    baseline["sha256"] = "0" * 64
    policy = load_public_boundary_policy(_write_policy(tmp_path, data))

    with pytest.raises(ValueError):
        load_exposure_baseline_link(tmp_path, policy)

    drifted_receipt = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    for finding in drifted_receipt["findings"]:
        if (
            finding["rule_id"] == "reference.raw_asset"
            and finding["surface"] == "git_head"
        ):
            finding["presence"] = "absent"
    drifted_bytes = (json.dumps(drifted_receipt, sort_keys=True) + "\n").encode()
    (tmp_path / baseline_locator).write_bytes(drifted_bytes)
    baseline["sha256"] = hashlib.sha256(drifted_bytes).hexdigest()
    policy = load_public_boundary_policy(_write_policy(tmp_path, data))

    with pytest.raises(ValueError):
        load_exposure_baseline_link(tmp_path, policy)
