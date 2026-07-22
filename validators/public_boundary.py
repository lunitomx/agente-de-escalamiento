"""Strict, source-neutral contracts for a local public-content boundary."""

from __future__ import annotations

from collections import Counter
from enum import Enum
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.exposure_inventory import (
    ExposureInventoryReceipt,
    ExposurePresence,
    ExposureSurface,
    RepositoryMutationProof,
)
from validators.repository_truth import (
    RepositoryFingerprint,
    _read_only_git_environment,
    fingerprint_repository,
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
    SHA256 = "sha256"


class BoundaryStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INCOMPLETE = "incomplete"


class PublicCandidateStatus(str, Enum):
    OBSERVED = "observed"
    LEGACY_FINDINGS_UNRESOLVED = "legacy_findings_unresolved"
    INCOMPLETE = "incomplete"


class BoundaryErrorCode(str, Enum):
    MISSING_REPOSITORY = "missing_repository"
    GIT_COMMAND_FAILED = "git_command_failed"
    UNSAFE_PATH = "unsafe_path"
    UNREADABLE_REQUIRED = "unreadable_required"
    BASELINE_MISMATCH = "baseline_mismatch"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"


class BoundarySubject(str, Enum):
    BASELINE = "baseline"
    PRIVATE_REPOSITORY = "private_repository"
    PRIVATE_WORKTREE = "private_worktree"
    PRIVATE_HEAD = "private_head"
    PRIVATE_HISTORY = "private_history"
    PUBLIC_CANDIDATE = "public_candidate"


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
    locator_kind: BoundaryLocatorKind
    locator: str = Field(min_length=1, max_length=1024)

    @field_validator("rule_id")
    @classmethod
    def validate_rule_id(cls, value: str) -> str:
        return _validate_rule_id(value)

    @model_validator(mode="after")
    def validate_locator(self) -> PublicBoundaryFinding:
        if self.locator_kind is BoundaryLocatorKind.RELATIVE_PATH:
            _validate_relative_path(self.locator)
        elif _SHA256_PATTERN.fullmatch(self.locator) is None:
            raise ValueError("invalid SHA-256 locator")
        return self


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


class BoundaryError(_StrictModel):
    code: BoundaryErrorCode
    subject: BoundarySubject


class BoundarySurfaceSummary(_StrictModel):
    surface: BoundarySurface
    inspected: bool
    tracked_count: int = Field(ge=0)
    candidate_public_count: int = Field(ge=0)
    unscanned_required_count: int = Field(ge=0)


class BoundaryPathSummary(_StrictModel):
    candidate_public_count: int = Field(ge=0)
    candidate_public_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    denied_count: int = Field(ge=0)
    denied_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    not_eligible_count: int = Field(ge=0)
    not_eligible_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class RawAssetObservation(_StrictModel):
    worktree: BaselinePresence
    git_head: BaselinePresence
    git_history: BaselinePresence

    @model_validator(mode="after")
    def validate_states(self) -> RawAssetObservation:
        current_states = {BaselinePresence.ABSENT, BaselinePresence.PRESENT}
        if self.worktree not in current_states or self.git_head not in current_states:
            raise ValueError("current raw states must be present or absent")
        if self.git_history not in {
            BaselinePresence.ABSENT,
            BaselinePresence.HISTORICAL,
        }:
            raise ValueError("history raw state must be absent or historical")
        return self


class PublicBoundaryReceipt(_StrictModel):
    schema_version: Literal[1] = 1
    status: BoundaryStatus
    policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    verifier_source_commit: str | None = Field(
        default=None,
        pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$",
    )
    baseline: ExposureBaselineLink | None
    raw_asset: RawAssetObservation | None
    path_summary: BoundaryPathSummary | None
    surfaces: list[BoundarySurfaceSummary]
    findings: list[PublicBoundaryFinding]
    finding_groups: list[BoundaryFindingGroup]
    errors: list[BoundaryError]
    private_repository: RepositoryMutationProof | None
    public_candidate: RepositoryMutationProof | None
    public_candidate_status: PublicCandidateStatus
    public_candidate_finding_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_receipt(self) -> PublicBoundaryReceipt:
        if self.findings != _ordered_findings(self.findings):
            raise ValueError("findings must be deterministically ordered")
        if self.finding_groups != group_boundary_findings(self.findings):
            raise ValueError("finding groups do not match findings")
        if self.errors != _ordered_errors(self.errors):
            raise ValueError("errors must be deterministically ordered")
        if [summary.surface for summary in self.surfaces] != list(BoundarySurface):
            raise ValueError("surface summaries must be complete and ordered")
        public_count = sum(
            finding.surface is BoundarySurface.PUBLIC_CANDIDATE_HEAD
            for finding in self.findings
        )
        if self.public_candidate_finding_count != public_count:
            raise ValueError("public candidate finding count mismatch")

        infrastructure_complete = (
            not self.errors
            and self.baseline is not None
            and self.raw_asset is not None
            and self.path_summary is not None
            and self.private_repository is not None
            and self.private_repository.unchanged
            and self.public_candidate is not None
            and self.public_candidate.unchanged
            and all(summary.inspected for summary in self.surfaces)
            and all(summary.unscanned_required_count == 0 for summary in self.surfaces)
        )
        private_findings = [
            finding
            for finding in self.findings
            if finding.surface is not BoundarySurface.PUBLIC_CANDIDATE_HEAD
        ]
        if not infrastructure_complete:
            expected_status = BoundaryStatus.INCOMPLETE
        elif (
            self.raw_asset is not None
            and self.raw_asset.git_head is BaselinePresence.ABSENT
            and self.raw_asset.git_history is BaselinePresence.HISTORICAL
            and not private_findings
        ):
            expected_status = BoundaryStatus.PASS
        else:
            expected_status = BoundaryStatus.FAIL
        if self.status is not expected_status:
            raise ValueError("boundary status does not match observations")

        public_summary = self.surfaces[-1]
        if (
            self.public_candidate is None
            or not self.public_candidate.unchanged
            or not public_summary.inspected
            or public_summary.unscanned_required_count
            or any(
                error.subject is BoundarySubject.PUBLIC_CANDIDATE
                for error in self.errors
            )
        ):
            expected_public_status = PublicCandidateStatus.INCOMPLETE
        elif public_count:
            expected_public_status = PublicCandidateStatus.LEGACY_FINDINGS_UNRESOLVED
        else:
            expected_public_status = PublicCandidateStatus.OBSERVED
        if self.public_candidate_status is not expected_public_status:
            raise ValueError("public candidate status does not match observations")
        return self


class _TrackedEntry(_StrictModel):
    path: str = Field(min_length=1, max_length=4096)
    mode: str = Field(pattern=r"^[0-9]{6}$")

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _validate_relative_path(value)


PublicPathRule.model_rebuild()
VocabularyRule.model_rebuild()
ExposureBaselineContract.model_rebuild()
PublicBoundaryPolicy.model_rebuild()
PublicBoundaryFinding.model_rebuild()
BoundaryFindingGroup.model_rebuild()
ExposureBaselineLink.model_rebuild()
BoundaryError.model_rebuild()
BoundarySurfaceSummary.model_rebuild()
BoundaryPathSummary.model_rebuild()
RawAssetObservation.model_rebuild()
PublicBoundaryReceipt.model_rebuild()
_TrackedEntry.model_rebuild()


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
    *,
    baseline_path: Path | None = None,
) -> ExposureBaselineLink:
    """Verify and reduce the immutable exposure receipt to a safe typed link."""
    resolved_baseline = baseline_path or repository_root / policy.baseline.locator
    baseline_bytes = resolved_baseline.read_bytes()
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


def scan_public_boundary(
    repository_root: Path,
    public_candidate_root: Path,
    policy: PublicBoundaryPolicy,
    *,
    baseline_path: Path | None = None,
) -> PublicBoundaryReceipt:
    """Inspect committed and worktree boundaries without mutating either repo."""
    errors: list[BoundaryError] = []
    baseline = _safe_baseline_link(
        repository_root,
        policy,
        baseline_path=baseline_path,
        errors=errors,
    )
    private_before = _safe_fingerprint(
        repository_root,
        label="private_repository",
        subject=BoundarySubject.PRIVATE_REPOSITORY,
        errors=errors,
    )
    public_before = _safe_fingerprint(
        public_candidate_root,
        label="public_candidate",
        subject=BoundarySubject.PUBLIC_CANDIDATE,
        errors=errors,
    )

    findings: list[PublicBoundaryFinding] = []
    surfaces = _empty_surface_summaries()
    raw_asset: RawAssetObservation | None = None
    path_summary: BoundaryPathSummary | None = None
    if private_before is not None:
        try:
            (
                private_findings,
                private_surfaces,
                raw_asset,
                path_summary,
            ) = _scan_private_repository(repository_root, policy)
            findings.extend(private_findings)
            surfaces[:3] = private_surfaces
            for summary in private_surfaces:
                if summary.unscanned_required_count:
                    errors.append(
                        BoundaryError(
                            code=BoundaryErrorCode.UNREADABLE_REQUIRED,
                            subject=_subject_for_surface(summary.surface),
                        )
                    )
        except _SafeBoundaryFailure as failure:
            errors.append(BoundaryError(code=failure.code, subject=failure.subject))

    if public_before is not None:
        try:
            public_findings, public_summary = _scan_public_candidate(
                public_candidate_root,
                policy,
            )
            findings.extend(public_findings)
            surfaces[3] = public_summary
            if public_summary.unscanned_required_count:
                errors.append(
                    BoundaryError(
                        code=BoundaryErrorCode.UNREADABLE_REQUIRED,
                        subject=BoundarySubject.PUBLIC_CANDIDATE,
                    )
                )
        except _SafeBoundaryFailure as failure:
            errors.append(BoundaryError(code=failure.code, subject=failure.subject))

    private_after = _safe_fingerprint(
        repository_root,
        label="private_repository",
        subject=BoundarySubject.PRIVATE_REPOSITORY,
        errors=errors,
    )
    public_after = _safe_fingerprint(
        public_candidate_root,
        label="public_candidate",
        subject=BoundarySubject.PUBLIC_CANDIDATE,
        errors=errors,
    )
    private_proof = _mutation_proof(private_before, private_after)
    public_proof = _mutation_proof(public_before, public_after)
    if private_proof is not None and not private_proof.unchanged:
        errors.append(
            BoundaryError(
                code=BoundaryErrorCode.FINGERPRINT_MISMATCH,
                subject=BoundarySubject.PRIVATE_REPOSITORY,
            )
        )
    if public_proof is not None and not public_proof.unchanged:
        errors.append(
            BoundaryError(
                code=BoundaryErrorCode.FINGERPRINT_MISMATCH,
                subject=BoundarySubject.PUBLIC_CANDIDATE,
            )
        )

    ordered_findings = _ordered_findings(findings)
    ordered_errors = _ordered_errors(errors)
    public_count = sum(
        finding.surface is BoundarySurface.PUBLIC_CANDIDATE_HEAD
        for finding in ordered_findings
    )
    infrastructure_complete = (
        not ordered_errors
        and baseline is not None
        and raw_asset is not None
        and path_summary is not None
        and private_proof is not None
        and private_proof.unchanged
        and public_proof is not None
        and public_proof.unchanged
        and all(summary.inspected for summary in surfaces)
        and all(summary.unscanned_required_count == 0 for summary in surfaces)
    )
    private_findings = [
        finding
        for finding in ordered_findings
        if finding.surface is not BoundarySurface.PUBLIC_CANDIDATE_HEAD
    ]
    if not infrastructure_complete:
        status = BoundaryStatus.INCOMPLETE
    elif (
        raw_asset is not None
        and raw_asset.git_head is BaselinePresence.ABSENT
        and raw_asset.git_history is BaselinePresence.HISTORICAL
        and not private_findings
    ):
        status = BoundaryStatus.PASS
    else:
        status = BoundaryStatus.FAIL

    if (
        public_proof is None
        or not public_proof.unchanged
        or not surfaces[3].inspected
        or surfaces[3].unscanned_required_count
        or any(
            error.subject is BoundarySubject.PUBLIC_CANDIDATE
            for error in ordered_errors
        )
    ):
        public_status = PublicCandidateStatus.INCOMPLETE
    elif public_count:
        public_status = PublicCandidateStatus.LEGACY_FINDINGS_UNRESOLVED
    else:
        public_status = PublicCandidateStatus.OBSERVED

    return PublicBoundaryReceipt(
        status=status,
        policy_sha256=public_boundary_policy_hash(policy),
        verifier_source_commit=private_before.head if private_before else None,
        baseline=baseline,
        raw_asset=raw_asset,
        path_summary=path_summary,
        surfaces=surfaces,
        findings=ordered_findings,
        finding_groups=group_boundary_findings(ordered_findings),
        errors=ordered_errors,
        private_repository=private_proof,
        public_candidate=public_proof,
        public_candidate_status=public_status,
        public_candidate_finding_count=public_count,
    )


def render_public_boundary_json(receipt: PublicBoundaryReceipt) -> str:
    """Render deterministic machine evidence from safe typed fields only."""
    return (
        json.dumps(
            receipt.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def render_public_boundary_markdown(receipt: PublicBoundaryReceipt) -> str:
    """Render a bounded grouped summary without detailed locators."""
    lines = [
        "# Public Boundary Receipt",
        "",
        f"- Status: `{receipt.status.value}`",
        f"- Policy SHA-256: `{receipt.policy_sha256}`",
        "- Verifier source commit: "
        f"`{receipt.verifier_source_commit or 'unavailable'}`",
        "- Baseline SHA-256: "
        f"`{receipt.baseline.baseline_sha256 if receipt.baseline else 'unavailable'}`",
        f"- Public candidate: `{receipt.public_candidate_status.value}`",
        f"- Public candidate finding count: `{receipt.public_candidate_finding_count}`",
        "- Private repository unchanged: "
        f"`{_mutation_label(receipt.private_repository)}`",
        f"- Public candidate unchanged: `{_mutation_label(receipt.public_candidate)}`",
        "",
        "## Raw reference state",
        "",
    ]
    if receipt.raw_asset is None:
        lines.append("- Unavailable")
    else:
        lines.extend(
            [
                f"- Worktree: `{receipt.raw_asset.worktree.value}`",
                f"- Git HEAD: `{receipt.raw_asset.git_head.value}`",
                f"- Git history: `{receipt.raw_asset.git_history.value}`",
            ]
        )
    lines.extend(["", "## Path classifications", ""])
    if receipt.path_summary is None:
        lines.append("- Unavailable")
    else:
        lines.extend(
            [
                "- Candidate public: "
                f"`{receipt.path_summary.candidate_public_count}` "
                f"(`{receipt.path_summary.candidate_public_set_sha256}`)",
                f"- Denied: `{receipt.path_summary.denied_count}` "
                f"(`{receipt.path_summary.denied_set_sha256}`)",
                "- Not eligible: "
                f"`{receipt.path_summary.not_eligible_count}` "
                f"(`{receipt.path_summary.not_eligible_set_sha256}`)",
            ]
        )
    lines.extend(["", "## Surfaces", ""])
    lines.extend(
        f"- `{summary.surface.value}`: inspected=`{str(summary.inspected).lower()}`, "
        f"tracked=`{summary.tracked_count}`, "
        f"candidate_public=`{summary.candidate_public_count}`, "
        f"unscanned_required=`{summary.unscanned_required_count}`"
        for summary in receipt.surfaces
    )
    lines.extend(["", "## Finding groups", ""])
    if receipt.finding_groups:
        lines.extend(
            f"- `{group.rule_id}` | `{group.surface.value}` | "
            f"`{group.code.value}` | count=`{group.count}`"
            for group in receipt.finding_groups
        )
    else:
        lines.append("- None")
    lines.extend(["", "## Errors", ""])
    if receipt.errors:
        lines.extend(
            f"- `{error.code.value}`: `{error.subject.value}`"
            for error in receipt.errors
        )
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def write_public_boundary_receipts(
    receipt: PublicBoundaryReceipt,
    *,
    json_output: Path | None = None,
    markdown_output: Path | None = None,
) -> None:
    """Write only explicitly requested, passing private-boundary receipts."""
    if receipt.status is not BoundaryStatus.PASS:
        raise ValueError("only a passing receipt may be written")
    json_content = render_public_boundary_json(receipt)
    markdown_content = render_public_boundary_markdown(receipt)
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json_content, encoding="utf-8")
    if markdown_output is not None:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(markdown_content, encoding="utf-8")


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


def _scan_private_repository(
    repository_root: Path,
    policy: PublicBoundaryPolicy,
) -> tuple[
    list[PublicBoundaryFinding],
    list[BoundarySurfaceSummary],
    RawAssetObservation,
    BoundaryPathSummary,
]:
    worktree_entries = _index_entries(repository_root)
    head_entries = _head_entries(repository_root, BoundarySubject.PRIVATE_HEAD)
    history_paths = _history_paths(repository_root)
    raw_rule, raw_path = _raw_rule_and_path(policy)
    raw_asset = RawAssetObservation(
        worktree=(
            BaselinePresence.PRESENT
            if os.path.lexists(repository_root / raw_path)
            else BaselinePresence.ABSENT
        ),
        git_head=(
            BaselinePresence.PRESENT
            if raw_path in {entry.path for entry in head_entries}
            else BaselinePresence.ABSENT
        ),
        git_history=(
            BaselinePresence.HISTORICAL
            if raw_path in set(history_paths)
            else BaselinePresence.ABSENT
        ),
    )

    worktree_findings, worktree_unscanned, worktree_candidates = _scan_required_entries(
        repository_root,
        worktree_entries,
        BoundarySurface.PRIVATE_WORKTREE,
        policy,
        worktree=True,
        candidate_only=True,
    )
    head_findings, head_unscanned, head_candidates = _scan_required_entries(
        repository_root,
        head_entries,
        BoundarySurface.PRIVATE_HEAD,
        policy,
        worktree=False,
        candidate_only=True,
    )
    findings = worktree_findings + head_findings
    for surface, state in (
        (BoundarySurface.PRIVATE_WORKTREE, raw_asset.worktree),
        (BoundarySurface.PRIVATE_HEAD, raw_asset.git_head),
    ):
        if state is BaselinePresence.PRESENT:
            findings.append(
                PublicBoundaryFinding(
                    rule_id=raw_rule.id,
                    code=BoundaryFindingCode.RAW_ASSET_TRACKED,
                    surface=surface,
                    locator_kind=BoundaryLocatorKind.SHA256,
                    locator=_sensitive_locator(raw_rule.id, surface, raw_path),
                )
            )

    surfaces = [
        BoundarySurfaceSummary(
            surface=BoundarySurface.PRIVATE_WORKTREE,
            inspected=True,
            tracked_count=len(worktree_entries),
            candidate_public_count=worktree_candidates,
            unscanned_required_count=worktree_unscanned,
        ),
        BoundarySurfaceSummary(
            surface=BoundarySurface.PRIVATE_HEAD,
            inspected=True,
            tracked_count=len(head_entries),
            candidate_public_count=head_candidates,
            unscanned_required_count=head_unscanned,
        ),
        BoundarySurfaceSummary(
            surface=BoundarySurface.PRIVATE_HISTORY,
            inspected=True,
            tracked_count=len(history_paths),
            candidate_public_count=0,
            unscanned_required_count=0,
        ),
    ]
    return findings, surfaces, raw_asset, _build_path_summary(head_entries, policy)


def _scan_public_candidate(
    repository_root: Path,
    policy: PublicBoundaryPolicy,
) -> tuple[list[PublicBoundaryFinding], BoundarySurfaceSummary]:
    entries = _head_entries(repository_root, BoundarySubject.PUBLIC_CANDIDATE)
    findings, unscanned, candidates = _scan_required_entries(
        repository_root,
        entries,
        BoundarySurface.PUBLIC_CANDIDATE_HEAD,
        policy,
        worktree=False,
        candidate_only=False,
    )
    return findings, BoundarySurfaceSummary(
        surface=BoundarySurface.PUBLIC_CANDIDATE_HEAD,
        inspected=True,
        tracked_count=len(entries),
        candidate_public_count=candidates,
        unscanned_required_count=unscanned,
    )


def _scan_required_entries(
    repository_root: Path,
    entries: list[_TrackedEntry],
    surface: BoundarySurface,
    policy: PublicBoundaryPolicy,
    *,
    worktree: bool,
    candidate_only: bool,
) -> tuple[list[PublicBoundaryFinding], int, int]:
    findings: list[PublicBoundaryFinding] = []
    unscanned = 0
    candidate_count = 0
    for entry in entries:
        if candidate_only:
            disposition = classify_public_path(policy, entry.path)
            if disposition is not PublicPathDisposition.CANDIDATE_PUBLIC:
                continue
        candidate_count += 1
        findings.extend(_path_vocabulary_findings(entry.path, surface, policy))
        content = (
            _read_worktree_content(repository_root / entry.path, entry.mode)
            if worktree
            else _read_head_content(repository_root, entry, surface)
        )
        text = _bounded_text(content, policy.max_text_bytes)
        if text is None:
            unscanned += 1
            findings.append(_unsafe_content_finding(entry.path, surface, policy))
            continue
        content_findings, valid_yaml = _content_vocabulary_findings(
            entry.path,
            text,
            surface,
            policy,
        )
        findings.extend(content_findings)
        if not valid_yaml:
            unscanned += 1
            findings.append(_unsafe_content_finding(entry.path, surface, policy))
    return findings, unscanned, candidate_count


def _path_vocabulary_findings(
    path: str,
    surface: BoundarySurface,
    policy: PublicBoundaryPolicy,
) -> list[PublicBoundaryFinding]:
    folded_path = path.casefold()
    return [
        PublicBoundaryFinding(
            rule_id=rule.id,
            code=BoundaryFindingCode.PROHIBITED_PATH,
            surface=surface,
            locator_kind=BoundaryLocatorKind.SHA256,
            locator=_sensitive_locator(rule.id, surface, path),
        )
        for rule in policy.vocabulary_rules
        if VocabularyTarget.PATH in rule.targets
        and any(term.casefold() in folded_path for term in rule.terms)
    ]


def _content_vocabulary_findings(
    path: str,
    text: str,
    surface: BoundarySurface,
    policy: PublicBoundaryPolicy,
) -> tuple[list[PublicBoundaryFinding], bool]:
    folded_text = text.casefold()
    findings = [
        PublicBoundaryFinding(
            rule_id=rule.id,
            code=BoundaryFindingCode.PROHIBITED_TEXT,
            surface=surface,
            locator_kind=_locator_kind_for_path(path, policy),
            locator=_locator_for_path(rule.id, surface, path, policy),
        )
        for rule in policy.vocabulary_rules
        if VocabularyTarget.TEXT in rule.targets
        and any(term.casefold() in folded_text for term in rule.terms)
    ]
    if not path.casefold().endswith((".yaml", ".yml")):
        return findings, True
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError:
        return findings, False
    if isinstance(document, dict):
        for key in policy.forbidden_yaml_root_keys:
            if key in document:
                findings.append(
                    PublicBoundaryFinding(
                        rule_id="public.provenance",
                        code=BoundaryFindingCode.PROHIBITED_YAML_KEY,
                        surface=surface,
                        locator_kind=_locator_kind_for_path(path, policy),
                        locator=_locator_for_path(
                            "public.provenance",
                            surface,
                            path,
                            policy,
                        ),
                    )
                )
    return findings, True


def _unsafe_content_finding(
    path: str,
    surface: BoundarySurface,
    policy: PublicBoundaryPolicy,
) -> PublicBoundaryFinding:
    return PublicBoundaryFinding(
        rule_id="boundary.required_content",
        code=BoundaryFindingCode.UNSAFE_OR_UNREADABLE,
        surface=surface,
        locator_kind=_locator_kind_for_path(path, policy),
        locator=_locator_for_path(
            "boundary.required_content",
            surface,
            path,
            policy,
        ),
    )


def _locator_kind_for_path(
    path: str,
    policy: PublicBoundaryPolicy,
) -> BoundaryLocatorKind:
    if _path_has_prohibited_term(path, policy):
        return BoundaryLocatorKind.SHA256
    return BoundaryLocatorKind.RELATIVE_PATH


def _locator_for_path(
    rule_id: str,
    surface: BoundarySurface,
    path: str,
    policy: PublicBoundaryPolicy,
) -> str:
    if _path_has_prohibited_term(path, policy):
        return _sensitive_locator(rule_id, surface, path)
    return path


def _path_has_prohibited_term(path: str, policy: PublicBoundaryPolicy) -> bool:
    folded_path = path.casefold()
    return any(
        term.casefold() in folded_path
        for rule in policy.vocabulary_rules
        if VocabularyTarget.PATH in rule.targets
        for term in rule.terms
    )


def _read_worktree_content(path: Path, mode: str) -> bytes | None:
    if mode not in {"100644", "100755"}:
        return None
    try:
        metadata = path.lstat()
        if path.is_symlink() or not path.is_file():
            return None
        if metadata.st_size < 0:
            return None
        return path.read_bytes()
    except OSError:
        return None


def _read_head_content(
    repository_root: Path,
    entry: _TrackedEntry,
    surface: BoundarySurface,
) -> bytes | None:
    if entry.mode not in {"100644", "100755"}:
        return None
    subject = _subject_for_surface(surface)
    return _run_git(repository_root, subject, "show", f"HEAD:{entry.path}")


def _bounded_text(content: bytes | None, max_text_bytes: int) -> str | None:
    if content is None or len(content) > max_text_bytes or b"\0" in content:
        return None
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _index_entries(repository_root: Path) -> list[_TrackedEntry]:
    output = _run_git(
        repository_root,
        BoundarySubject.PRIVATE_WORKTREE,
        "ls-files",
        "--stage",
        "-z",
    )
    entries: list[_TrackedEntry] = []
    for record in output.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", maxsplit=1)
            mode, _object_id, stage = metadata.decode("ascii").split()
            if stage != "0":
                raise ValueError
            path = raw_path.decode("utf-8")
            entries.append(_TrackedEntry(path=path, mode=mode))
        except (UnicodeDecodeError, ValueError):
            raise _SafeBoundaryFailure(
                BoundaryErrorCode.UNSAFE_PATH,
                BoundarySubject.PRIVATE_WORKTREE,
            ) from None
    return _ordered_entries(entries)


def _head_entries(
    repository_root: Path,
    subject: BoundarySubject,
) -> list[_TrackedEntry]:
    output = _run_git(repository_root, subject, "ls-tree", "-r", "-z", "HEAD")
    entries: list[_TrackedEntry] = []
    for record in output.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", maxsplit=1)
            mode, _object_type, _object_id = metadata.decode("ascii").split()
            path = raw_path.decode("utf-8")
            entries.append(_TrackedEntry(path=path, mode=mode))
        except (UnicodeDecodeError, ValueError):
            raise _SafeBoundaryFailure(
                BoundaryErrorCode.UNSAFE_PATH,
                subject,
            ) from None
    return _ordered_entries(entries)


def _ordered_entries(entries: Iterable[_TrackedEntry]) -> list[_TrackedEntry]:
    unique = {(entry.path, entry.mode): entry for entry in entries}
    return sorted(unique.values(), key=lambda entry: (entry.path, entry.mode))


def _history_paths(repository_root: Path) -> list[str]:
    output = _run_git(
        repository_root,
        BoundarySubject.PRIVATE_HISTORY,
        "log",
        "--all",
        "--format=",
        "--name-only",
        "-z",
        "--",
    )
    paths: list[str] = []
    for item in output.split(b"\0"):
        candidate = item.strip(b"\n")
        if not candidate:
            continue
        try:
            paths.append(_validate_relative_path(candidate.decode("utf-8")))
        except (UnicodeDecodeError, ValueError):
            raise _SafeBoundaryFailure(
                BoundaryErrorCode.UNSAFE_PATH,
                BoundarySubject.PRIVATE_HISTORY,
            ) from None
    return sorted(set(paths))


def _raw_rule_and_path(
    policy: PublicBoundaryPolicy,
) -> tuple[PublicPathRule, str]:
    rules = [rule for rule in policy.path_rules if rule.deny_class is DenyClass.RAW]
    if len(rules) != 1 or len(rules[0].globs) != 1:
        raise _SafeBoundaryFailure(
            BoundaryErrorCode.BASELINE_MISMATCH,
            BoundarySubject.BASELINE,
        )
    path = rules[0].globs[0]
    if any(character in path for character in "*?["):
        raise _SafeBoundaryFailure(
            BoundaryErrorCode.BASELINE_MISMATCH,
            BoundarySubject.BASELINE,
        )
    return rules[0], _validate_relative_path(path)


def _build_path_summary(
    entries: list[_TrackedEntry],
    policy: PublicBoundaryPolicy,
) -> BoundaryPathSummary:
    groups = {disposition: [] for disposition in PublicPathDisposition}
    for entry in entries:
        groups[classify_public_path(policy, entry.path)].append(entry.path)
    return BoundaryPathSummary(
        candidate_public_count=len(groups[PublicPathDisposition.CANDIDATE_PUBLIC]),
        candidate_public_set_sha256=_path_set_hash(
            groups[PublicPathDisposition.CANDIDATE_PUBLIC]
        ),
        denied_count=len(groups[PublicPathDisposition.DENIED]),
        denied_set_sha256=_path_set_hash(groups[PublicPathDisposition.DENIED]),
        not_eligible_count=len(groups[PublicPathDisposition.NOT_ELIGIBLE]),
        not_eligible_set_sha256=_path_set_hash(
            groups[PublicPathDisposition.NOT_ELIGIBLE]
        ),
    )


def _path_set_hash(paths: Iterable[str]) -> str:
    payload = "".join(f"{path}\n" for path in sorted(set(paths)))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _safe_baseline_link(
    repository_root: Path,
    policy: PublicBoundaryPolicy,
    *,
    baseline_path: Path | None,
    errors: list[BoundaryError],
) -> ExposureBaselineLink | None:
    try:
        return load_exposure_baseline_link(
            repository_root,
            policy,
            baseline_path=baseline_path,
        )
    except Exception:
        errors.append(
            BoundaryError(
                code=BoundaryErrorCode.BASELINE_MISMATCH,
                subject=BoundarySubject.BASELINE,
            )
        )
        return None


def _safe_fingerprint(
    repository_root: Path,
    *,
    label: str,
    subject: BoundarySubject,
    errors: list[BoundaryError],
) -> RepositoryFingerprint | None:
    if not repository_root.exists() or not (repository_root / ".git").exists():
        errors.append(
            BoundaryError(
                code=BoundaryErrorCode.MISSING_REPOSITORY,
                subject=subject,
            )
        )
        return None
    try:
        return fingerprint_repository(repository_root, label=label)
    except Exception:
        errors.append(
            BoundaryError(
                code=BoundaryErrorCode.GIT_COMMAND_FAILED,
                subject=subject,
            )
        )
        return None


def _mutation_proof(
    before: RepositoryFingerprint | None,
    after: RepositoryFingerprint | None,
) -> RepositoryMutationProof | None:
    if before is None or after is None:
        return None
    return RepositoryMutationProof(
        before=before,
        after=after,
        unchanged=before == after,
    )


def _run_git(
    repository_root: Path,
    subject: BoundarySubject,
    *arguments: str,
) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository_root), *arguments],
            check=False,
            capture_output=True,
            env=_read_only_git_environment(),
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        raise _SafeBoundaryFailure(
            BoundaryErrorCode.GIT_COMMAND_FAILED,
            subject,
        ) from None
    if result.returncode != 0:
        raise _SafeBoundaryFailure(
            BoundaryErrorCode.GIT_COMMAND_FAILED,
            subject,
        )
    return result.stdout


def _ordered_findings(
    findings: Iterable[PublicBoundaryFinding],
) -> list[PublicBoundaryFinding]:
    surface_order = {surface: index for index, surface in enumerate(BoundarySurface)}
    unique = {
        (
            finding.rule_id,
            finding.code,
            finding.surface,
            finding.locator_kind,
            finding.locator,
        ): finding
        for finding in findings
    }
    return sorted(
        unique.values(),
        key=lambda finding: (
            surface_order[finding.surface],
            finding.rule_id,
            finding.code.value,
            finding.locator_kind.value,
            finding.locator,
        ),
    )


def _ordered_errors(errors: Iterable[BoundaryError]) -> list[BoundaryError]:
    unique = {(error.code, error.subject): error for error in errors}
    return sorted(
        unique.values(),
        key=lambda error: (error.code.value, error.subject.value),
    )


def _empty_surface_summaries() -> list[BoundarySurfaceSummary]:
    return [
        BoundarySurfaceSummary(
            surface=surface,
            inspected=False,
            tracked_count=0,
            candidate_public_count=0,
            unscanned_required_count=0,
        )
        for surface in BoundarySurface
    ]


def _sensitive_locator(rule_id: str, surface: BoundarySurface, path: str) -> str:
    payload = f"{rule_id}\0{surface.value}\0{path}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _subject_for_surface(surface: BoundarySurface) -> BoundarySubject:
    subjects = {
        BoundarySurface.PRIVATE_WORKTREE: BoundarySubject.PRIVATE_WORKTREE,
        BoundarySurface.PRIVATE_HEAD: BoundarySubject.PRIVATE_HEAD,
        BoundarySurface.PRIVATE_HISTORY: BoundarySubject.PRIVATE_HISTORY,
        BoundarySurface.PUBLIC_CANDIDATE_HEAD: BoundarySubject.PUBLIC_CANDIDATE,
    }
    return subjects[surface]


def _mutation_label(proof: RepositoryMutationProof | None) -> str:
    if proof is None:
        return "unavailable"
    return "yes" if proof.unchanged else "no"


class _SafeBoundaryFailure(Exception):
    def __init__(self, code: BoundaryErrorCode, subject: BoundarySubject) -> None:
        super().__init__(code.value)
        self.code = code
        self.subject = subject
