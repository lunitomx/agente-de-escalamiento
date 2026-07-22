"""Strict, source-neutral contracts for a local public-content boundary."""

from __future__ import annotations

from collections import Counter
from enum import Enum
import fnmatch
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.exposure_inventory import (
    ExposureInventoryReceipt,
    ExposurePresence,
    ExposureSurface,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


_RULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SAFE_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PublicPathDisposition(str, Enum):
    CANDIDATE_PUBLIC = "candidate_public"
    DENIED = "denied"
    NOT_ELIGIBLE = "not_eligible"


class DenyClass(str, Enum):
    RAW = "raw"
    DERIVED = "derived"
    PRIVATE = "private"
    INTERNAL = "internal"


class VocabularyTarget(str, Enum):
    PATH = "path"
    TEXT = "text"


class BoundaryFindingCode(str, Enum):
    PROHIBITED_PATH = "prohibited_path"
    PROHIBITED_TEXT = "prohibited_text"
    PROHIBITED_YAML_KEY = "prohibited_yaml_key"
    RAW_ASSET_TRACKED = "raw_asset_tracked"
    UNSAFE_OR_UNREADABLE = "unsafe_or_unreadable"
    BASELINE_MISMATCH = "baseline_mismatch"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"


class BoundarySurface(str, Enum):
    PRIVATE_WORKTREE = "private_worktree"
    PRIVATE_HEAD = "private_head"
    PRIVATE_HISTORY = "private_history"
    PUBLIC_CANDIDATE_HEAD = "public_candidate_head"


class BoundaryLocatorKind(str, Enum):
    RELATIVE_PATH = "relative_path"


class BaselineScanStatus(str, Enum):
    COMPLETE = "complete"


class BaselinePresence(str, Enum):
    ABSENT = "absent"
    PRESENT = "present"
    HISTORICAL = "historical"


class PublicPathRule(_StrictModel):
    id: str = Field(min_length=3, max_length=128)
    disposition: PublicPathDisposition
    deny_class: DenyClass | None
    globs: list[str] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_rule_id(value)

    @field_validator("globs")
    @classmethod
    def validate_globs(cls, values: list[str]) -> list[str]:
        validated = [_validate_safe_glob(value) for value in values]
        _reject_duplicates(validated, "path globs")
        return sorted(validated)

    @model_validator(mode="after")
    def validate_disposition(self) -> PublicPathRule:
        if self.disposition is PublicPathDisposition.NOT_ELIGIBLE:
            raise ValueError("not_eligible is reserved for the policy default")
        if self.disposition is PublicPathDisposition.DENIED:
            if self.deny_class is None:
                raise ValueError("denied rules require a deny class")
        elif self.deny_class is not None:
            raise ValueError("candidate-public rules cannot declare a deny class")
        return self


class VocabularyRule(_StrictModel):
    id: str = Field(min_length=3, max_length=128)
    targets: list[VocabularyTarget] = Field(min_length=1)
    terms: list[str] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_rule_id(value)

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, values: list[VocabularyTarget]) -> list[VocabularyTarget]:
        _reject_duplicates(values, "vocabulary targets")
        order = {target: index for index, target in enumerate(VocabularyTarget)}
        return sorted(values, key=order.__getitem__)

    @field_validator("terms")
    @classmethod
    def validate_terms(cls, values: list[str]) -> list[str]:
        validated = [_validate_safe_term(value) for value in values]
        folded = [value.casefold() for value in validated]
        _reject_duplicates(folded, "case-insensitive vocabulary terms")
        return sorted(validated, key=str.casefold)


class RawSurfaceStates(_StrictModel):
    worktree: Literal[BaselinePresence.ABSENT]
    git_head: Literal[BaselinePresence.PRESENT]
    git_history: Literal[BaselinePresence.HISTORICAL]


class ExposureBaselineContract(_StrictModel):
    locator: str = Field(min_length=1, max_length=1024)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scan_status: Literal[BaselineScanStatus.COMPLETE]
    policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    verifier_source_commit: str = Field(pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
    raw_rule_id: str = Field(min_length=3, max_length=128)
    raw_surface_states: RawSurfaceStates

    @field_validator("locator")
    @classmethod
    def validate_locator(cls, value: str) -> str:
        return _validate_relative_path(value)

    @field_validator("raw_rule_id")
    @classmethod
    def validate_raw_rule_id(cls, value: str) -> str:
        return _validate_rule_id(value)


class PublicBoundaryPolicy(_StrictModel):
    schema_version: Literal[1]
    max_text_bytes: int = Field(ge=1, le=104_857_600)
    default_disposition: Literal[PublicPathDisposition.NOT_ELIGIBLE]
    precedence: list[PublicPathDisposition]
    baseline: ExposureBaselineContract
    path_rules: list[PublicPathRule] = Field(min_length=5)
    vocabulary_rules: list[VocabularyRule] = Field(min_length=1)
    forbidden_yaml_root_keys: list[str] = Field(min_length=1)

    @field_validator("precedence")
    @classmethod
    def validate_precedence(
        cls,
        values: list[PublicPathDisposition],
    ) -> list[PublicPathDisposition]:
        expected = [
            PublicPathDisposition.DENIED,
            PublicPathDisposition.CANDIDATE_PUBLIC,
        ]
        if values != expected:
            raise ValueError("precedence must be deny-first and complete")
        return values

    @field_validator("path_rules")
    @classmethod
    def validate_path_rules(cls, values: list[PublicPathRule]) -> list[PublicPathRule]:
        _reject_duplicates([rule.id for rule in values], "path rule IDs")
        return sorted(values, key=lambda rule: rule.id)

    @field_validator("vocabulary_rules")
    @classmethod
    def validate_vocabulary_rules(
        cls,
        values: list[VocabularyRule],
    ) -> list[VocabularyRule]:
        _reject_duplicates([rule.id for rule in values], "vocabulary rule IDs")
        return sorted(values, key=lambda rule: rule.id)

    @field_validator("forbidden_yaml_root_keys")
    @classmethod
    def validate_forbidden_yaml_root_keys(cls, values: list[str]) -> list[str]:
        if any(_SAFE_KEY_PATTERN.fullmatch(value) is None for value in values):
            raise ValueError("unsafe YAML root key")
        _reject_duplicates(values, "YAML root keys")
        return sorted(values)

    @model_validator(mode="after")
    def validate_boundary(self) -> PublicBoundaryPolicy:
        required_denies = set(DenyClass)
        actual_denies = {
            rule.deny_class for rule in self.path_rules if rule.deny_class is not None
        }
        if actual_denies != required_denies:
            raise ValueError("raw, derived, private, and internal denies are required")
        if not any(
            rule.disposition is PublicPathDisposition.CANDIDATE_PUBLIC
            for rule in self.path_rules
        ):
            raise ValueError("at least one candidate-public rule is required")
        all_ids = [rule.id for rule in self.path_rules] + [
            rule.id for rule in self.vocabulary_rules
        ]
        _reject_duplicates(all_ids, "policy rule IDs")
        _reject_same_disposition_overlaps(self.path_rules)
        return self


class PublicBoundaryFinding(_StrictModel):
    rule_id: str = Field(min_length=3, max_length=128)
    code: BoundaryFindingCode
    surface: BoundarySurface
    locator_kind: Literal[BoundaryLocatorKind.RELATIVE_PATH]
    locator: str = Field(min_length=1, max_length=1024)

    @field_validator("rule_id")
    @classmethod
    def validate_rule_id(cls, value: str) -> str:
        return _validate_rule_id(value)

    @field_validator("locator")
    @classmethod
    def validate_locator(cls, value: str) -> str:
        return _validate_relative_path(value)


class BoundaryFindingGroup(_StrictModel):
    rule_id: str = Field(min_length=3, max_length=128)
    code: BoundaryFindingCode
    surface: BoundarySurface
    count: int = Field(ge=1)

    @field_validator("rule_id")
    @classmethod
    def validate_rule_id(cls, value: str) -> str:
        return _validate_rule_id(value)


class ExposureBaselineLink(_StrictModel):
    baseline_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scan_status: Literal[BaselineScanStatus.COMPLETE]
    policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    verifier_source_commit: str = Field(pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
    raw_surface_states: RawSurfaceStates


PublicPathRule.model_rebuild()
VocabularyRule.model_rebuild()
ExposureBaselineContract.model_rebuild()
PublicBoundaryPolicy.model_rebuild()
PublicBoundaryFinding.model_rebuild()
BoundaryFindingGroup.model_rebuild()
ExposureBaselineLink.model_rebuild()


def load_public_boundary_policy(policy_path: Path) -> PublicBoundaryPolicy:
    """Load and strictly validate a local public-boundary policy."""
    data: Any = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    return PublicBoundaryPolicy.model_validate(data)


def public_boundary_policy_hash(policy: PublicBoundaryPolicy) -> str:
    """Return a stable SHA-256 for normalized policy semantics."""
    payload = json.dumps(
        policy.model_dump(mode="json"),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def classify_public_path(
    policy: PublicBoundaryPolicy,
    relative_path: str,
) -> PublicPathDisposition:
    """Classify a safe relative path with explicit deny precedence."""
    safe_path = _validate_relative_path(relative_path)
    matching = [
        rule
        for rule in policy.path_rules
        if any(fnmatch.fnmatchcase(safe_path, pattern) for pattern in rule.globs)
    ]
    for disposition in policy.precedence:
        if any(rule.disposition is disposition for rule in matching):
            return disposition
    return PublicPathDisposition.NOT_ELIGIBLE


def group_boundary_findings(
    findings: Iterable[PublicBoundaryFinding],
) -> list[BoundaryFindingGroup]:
    """Group findings without carrying locators or matched values."""
    counts = Counter(
        (finding.rule_id, finding.code, finding.surface) for finding in findings
    )
    return [
        BoundaryFindingGroup(
            rule_id=rule_id,
            code=code,
            surface=surface,
            count=count,
        )
        for (rule_id, code, surface), count in sorted(
            counts.items(),
            key=lambda item: (
                item[0][0],
                item[0][1].value,
                item[0][2].value,
            ),
        )
    ]


def load_exposure_baseline_link(
    repository_root: Path,
    policy: PublicBoundaryPolicy,
) -> ExposureBaselineLink:
    """Verify and reduce the immutable exposure receipt to a safe typed link."""
    baseline_path = repository_root / policy.baseline.locator
    baseline_bytes = baseline_path.read_bytes()
    baseline_sha256 = hashlib.sha256(baseline_bytes).hexdigest()
    if baseline_sha256 != policy.baseline.sha256:
        raise ValueError("baseline hash mismatch")

    receipt = ExposureInventoryReceipt.model_validate_json(baseline_bytes)
    if receipt.scan_status.value != policy.baseline.scan_status.value:
        raise ValueError("baseline scan status mismatch")
    if receipt.policy_sha256 != policy.baseline.policy_sha256:
        raise ValueError("baseline policy hash mismatch")
    if receipt.verifier_source_commit != policy.baseline.verifier_source_commit:
        raise ValueError("baseline verifier commit mismatch")

    raw_findings = [
        finding
        for finding in receipt.findings
        if finding.rule_id == policy.baseline.raw_rule_id
    ]
    expected_surfaces = {
        ExposureSurface.WORKTREE,
        ExposureSurface.GIT_HEAD,
        ExposureSurface.GIT_HISTORY,
    }
    if len(raw_findings) != len(expected_surfaces):
        raise ValueError("baseline raw surface count mismatch")
    if {finding.surface for finding in raw_findings} != expected_surfaces:
        raise ValueError("baseline raw surfaces mismatch")
    if len({finding.locator for finding in raw_findings}) != 1:
        raise ValueError("baseline raw locator mismatch")
    raw_locator = raw_findings[0].locator
    if classify_public_path(policy, raw_locator) is not PublicPathDisposition.DENIED:
        raise ValueError("baseline raw locator is not denied")

    observed = {finding.surface: finding.presence for finding in raw_findings}
    expected = policy.baseline.raw_surface_states
    if observed != {
        ExposureSurface.WORKTREE: ExposurePresence(expected.worktree.value),
        ExposureSurface.GIT_HEAD: ExposurePresence(expected.git_head.value),
        ExposureSurface.GIT_HISTORY: ExposurePresence(expected.git_history.value),
    }:
        raise ValueError("baseline raw surface state mismatch")

    return ExposureBaselineLink(
        baseline_sha256=baseline_sha256,
        scan_status=policy.baseline.scan_status,
        policy_sha256=receipt.policy_sha256,
        verifier_source_commit=policy.baseline.verifier_source_commit,
        raw_surface_states=expected,
    )


def _validate_rule_id(value: str) -> str:
    if _RULE_ID_PATTERN.fullmatch(value) is None:
        raise ValueError("unsafe rule ID")
    return value


def _validate_relative_path(value: str) -> str:
    if not value or value != value.strip() or "\\" in value:
        raise ValueError("unsafe relative path")
    if _contains_control_character(value):
        raise ValueError("unsafe relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith("./") or ".." in path.parts:
        raise ValueError("unsafe relative path")
    if path.as_posix() != value or value.endswith("/"):
        raise ValueError("unsafe relative path")
    return value


def _validate_safe_glob(value: str) -> str:
    if not value or value != value.strip() or "\\" in value:
        raise ValueError("unsafe path glob")
    if _contains_control_character(value) or value.startswith(("/", "./")):
        raise ValueError("unsafe path glob")
    if ".." in PurePosixPath(value).parts or value.endswith("/"):
        raise ValueError("unsafe path glob")
    if any(character in value for character in "*?["):
        if not value.endswith("/**"):
            raise ValueError("only explicit recursive-root globs are supported")
        root = value[:-3]
        if any(character in root for character in "*?["):
            raise ValueError("unsafe recursive-root glob")
        _validate_relative_path(root)
    else:
        _validate_relative_path(value)
    return value


def _validate_safe_term(value: str) -> str:
    if not 2 <= len(value) <= 256 or value != value.strip():
        raise ValueError("unsafe vocabulary term")
    if _contains_control_character(value):
        raise ValueError("unsafe vocabulary term")
    return value


def _contains_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _reject_duplicates(values: Iterable[object], label: str) -> None:
    materialized = list(values)
    if len(set(materialized)) != len(materialized):
        raise ValueError(f"{label} must not contain duplicates")


def _reject_same_disposition_overlaps(rules: list[PublicPathRule]) -> None:
    for index, first in enumerate(rules):
        for second in rules[index + 1 :]:
            if first.disposition is not second.disposition:
                continue
            if any(
                _globs_overlap(first_glob, second_glob)
                for first_glob in first.globs
                for second_glob in second.globs
            ):
                raise ValueError("same-disposition path rules must not overlap")


def _globs_overlap(first: str, second: str) -> bool:
    first_root = first[:-3] if first.endswith("/**") else None
    second_root = second[:-3] if second.endswith("/**") else None
    if first_root is None and second_root is None:
        return first == second
    if first_root is not None and second_root is not None:
        return (
            first_root == second_root
            or first_root.startswith(f"{second_root}/")
            or second_root.startswith(f"{first_root}/")
        )
    if first_root is not None:
        return second.startswith(f"{first_root}/")
    assert second_root is not None
    return first.startswith(f"{second_root}/")
