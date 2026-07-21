"""Typed, deterministic contracts for local exposure inventory."""

from __future__ import annotations

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

from validators.repository_truth import (
    RepositoryFingerprint,
    _has_embedded_http_credentials,
    _read_only_git_environment,
    fingerprint_repository,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


_RULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_REMOTE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_COMMIT_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_ASSIGNMENT_PATTERN = re.compile(
    rb"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\b"
    rb"\s*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{12,}"
)
_BEARER_PATTERN = re.compile(
    rb"(?i)\bauthorization\s*:\s*bearer\s+[A-Za-z0-9._~+/=-]{12,}"
)
_PRIVATE_KEY_PATTERN = re.compile(rb"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ExposureSurface(str, Enum):
    WORKTREE = "worktree"
    GIT_HEAD = "git_head"
    GIT_HISTORY = "git_history"
    LOCAL_GIT_CONFIG = "local_git_config"
    DISTRIBUTION_CANDIDATE = "distribution_candidate"
    PUBLIC_CANDIDATE = "public_candidate"


class ExposureClassification(str, Enum):
    RAW_REFERENCE = "raw_reference"
    DERIVED_REFERENCE = "derived_reference"
    PUBLIC_VOCABULARY = "public_vocabulary"
    SECRET_CANDIDATE = "secret_candidate"
    CREDENTIAL_RISK = "credential_risk"
    PRIVATE_DATA = "private_data"
    INTERNAL_PATH = "internal_path"
    NOT_ELIGIBLE = "not_eligible"


class ExposureSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ExposureDisposition(str, Enum):
    REMOVE_IN_S36_3 = "remove_in_s36_3"
    REVIEW_IN_S36_3 = "review_in_s36_3"
    REVIEW_SECURITY = "review_security"
    BLOCK_IN_S36_5 = "block_in_s36_5"


class LocatorKind(str, Enum):
    RELATIVE_PATH = "relative_path"
    SHA256 = "sha256"
    REMOTE_NAME = "remote_name"


class SecretShape(str, Enum):
    ASSIGNMENT = "assignment"
    BEARER_TOKEN = "bearer_token"
    PRIVATE_KEY = "private_key"
    AUTHENTICATED_URL = "authenticated_url"


class DistributionEligibility(str, Enum):
    NOT_ELIGIBLE = "not_eligible"


class GeneratedStagingState(str, Enum):
    NOT_BUILT = "not_built"


class ExposurePresence(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    HISTORICAL = "historical"


class ScanStatus(str, Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"


class InventoryErrorCode(str, Enum):
    MISSING_REPOSITORY = "missing_repository"
    GIT_COMMAND_FAILED = "git_command_failed"
    UNSAFE_PATH = "unsafe_path"
    UNREADABLE_REQUIRED_SURFACE = "unreadable_required_surface"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"


class InventorySubject(str, Enum):
    PRIVATE_REPOSITORY = "private_repository"
    PUBLIC_CANDIDATE = "public_candidate"
    WORKTREE = "worktree"
    GIT_HEAD = "git_head"
    GIT_HISTORY = "git_history"
    LOCAL_GIT_CONFIG = "local_git_config"


class DistributionPolicy(_StrictModel):
    default_eligibility: Literal[DistributionEligibility.NOT_ELIGIBLE]
    generated_staging: Literal[GeneratedStagingState.NOT_BUILT]


class RuleMatchers(_StrictModel):
    path_globs: list[str] = Field(default_factory=list)
    content_terms: list[str] = Field(default_factory=list)
    secret_shapes: list[SecretShape] = Field(default_factory=list)

    @field_validator("path_globs")
    @classmethod
    def validate_path_globs(cls, values: list[str]) -> list[str]:
        validated = [_validate_safe_glob(value) for value in values]
        _reject_duplicates(validated, "path globs")
        return sorted(validated)

    @field_validator("content_terms")
    @classmethod
    def validate_content_terms(cls, values: list[str]) -> list[str]:
        validated = [_validate_safe_term(value) for value in values]
        _reject_duplicates(validated, "content terms")
        return sorted(validated, key=str.casefold)

    @field_validator("secret_shapes")
    @classmethod
    def validate_secret_shapes(cls, values: list[SecretShape]) -> list[SecretShape]:
        _reject_duplicates(values, "secret shapes")
        order = {shape: index for index, shape in enumerate(SecretShape)}
        return sorted(values, key=order.__getitem__)

    @model_validator(mode="after")
    def require_matcher(self) -> RuleMatchers:
        if not (self.path_globs or self.content_terms or self.secret_shapes):
            raise ValueError("at least one matcher is required")
        return self


class ExposureRule(_StrictModel):
    id: str = Field(min_length=3, max_length=128)
    surfaces: list[ExposureSurface] = Field(min_length=1)
    classification: ExposureClassification
    severity: ExposureSeverity
    locator_kind: LocatorKind
    disposition: ExposureDisposition
    matchers: RuleMatchers

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_rule_id(value)

    @field_validator("surfaces")
    @classmethod
    def validate_surfaces(
        cls,
        values: list[ExposureSurface],
    ) -> list[ExposureSurface]:
        _reject_duplicates(values, "rule surfaces")
        order = {surface: index for index, surface in enumerate(ExposureSurface)}
        return sorted(values, key=order.__getitem__)

    @model_validator(mode="after")
    def validate_boundary(self) -> ExposureRule:
        _validate_classification_boundary(
            classification=self.classification,
            disposition=self.disposition,
            locator_kind=self.locator_kind,
            surface=None,
        )
        if self.classification is ExposureClassification.SECRET_CANDIDATE:
            if not self.matchers.secret_shapes:
                raise ValueError("secret candidate rules require secret shapes")
            if self.matchers.content_terms:
                raise ValueError("secret candidate rules cannot contain terms")
        elif self.classification is ExposureClassification.CREDENTIAL_RISK:
            if self.surfaces != [ExposureSurface.LOCAL_GIT_CONFIG]:
                raise ValueError("credential rules are local-config only")
            if self.matchers.secret_shapes != [SecretShape.AUTHENTICATED_URL]:
                raise ValueError("credential rules require authenticated_url")
        elif self.matchers.secret_shapes:
            raise ValueError("non-secret rules cannot contain secret shapes")
        return self


class ExposureInventoryPolicy(_StrictModel):
    schema_version: Literal[1]
    bounded_surfaces: list[ExposureSurface]
    max_text_bytes: int = Field(ge=1, le=104_857_600)
    distribution: DistributionPolicy
    rules: list[ExposureRule] = Field(min_length=1)

    @field_validator("bounded_surfaces")
    @classmethod
    def validate_bounded_surfaces(
        cls,
        values: list[ExposureSurface],
    ) -> list[ExposureSurface]:
        _reject_duplicates(values, "bounded surfaces")
        if set(values) != set(ExposureSurface):
            raise ValueError("all bounded surfaces are required")
        return list(ExposureSurface)

    @field_validator("rules")
    @classmethod
    def validate_rules(cls, values: list[ExposureRule]) -> list[ExposureRule]:
        identifiers = [rule.id for rule in values]
        _reject_duplicates(identifiers, "rule IDs")
        return sorted(values, key=lambda rule: rule.id)

    @model_validator(mode="after")
    def validate_rule_surfaces(self) -> ExposureInventoryPolicy:
        bounded = set(self.bounded_surfaces)
        if any(not set(rule.surfaces) <= bounded for rule in self.rules):
            raise ValueError("rule surface must be bounded")
        return self


class ExposureFinding(_StrictModel):
    rule_id: str = Field(min_length=3, max_length=128)
    surface: ExposureSurface
    classification: ExposureClassification
    severity: ExposureSeverity
    locator_kind: LocatorKind
    locator: str = Field(min_length=1, max_length=1024)
    disposition: ExposureDisposition
    presence: ExposurePresence

    @field_validator("rule_id")
    @classmethod
    def validate_rule_id(cls, value: str) -> str:
        return _validate_rule_id(value)

    @model_validator(mode="after")
    def validate_safe_boundary(self) -> ExposureFinding:
        if self.locator_kind is LocatorKind.RELATIVE_PATH:
            _validate_relative_path(self.locator)
        elif self.locator_kind is LocatorKind.SHA256:
            if _SHA256_PATTERN.fullmatch(self.locator) is None:
                raise ValueError("invalid SHA-256 locator")
        elif _REMOTE_NAME_PATTERN.fullmatch(self.locator) is None:
            raise ValueError("invalid remote-name locator")
        _validate_classification_boundary(
            classification=self.classification,
            disposition=self.disposition,
            locator_kind=self.locator_kind,
            surface=self.surface,
        )
        return self


class RiskSummary(_StrictModel):
    critical: int = Field(ge=0)
    high: int = Field(ge=0)
    medium: int = Field(ge=0)
    low: int = Field(ge=0)
    info: int = Field(ge=0)


class DistributionSummary(_StrictModel):
    default_eligibility: Literal[DistributionEligibility.NOT_ELIGIBLE]
    generated_staging: Literal[GeneratedStagingState.NOT_BUILT]
    tracked_path_count: int = Field(ge=0)
    tracked_path_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class SurfaceSummary(_StrictModel):
    surface: ExposureSurface
    inspected: bool
    item_count: int = Field(ge=0)
    unscanned_count: int = Field(ge=0)


class InventoryError(_StrictModel):
    code: InventoryErrorCode
    subject: InventorySubject


class RepositoryMutationProof(_StrictModel):
    before: RepositoryFingerprint
    after: RepositoryFingerprint
    unchanged: bool

    @model_validator(mode="after")
    def validate_unchanged(self) -> RepositoryMutationProof:
        if self.unchanged != (self.before == self.after):
            raise ValueError("mutation proof does not match fingerprints")
        return self


class ExposureInventoryReceipt(_StrictModel):
    schema_version: Literal[1] = 1
    scan_status: ScanStatus
    policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    verifier_source_commit: str | None = Field(
        default=None,
        pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$",
    )
    distribution: DistributionSummary
    surfaces: list[SurfaceSummary]
    risk_summary: RiskSummary
    findings: list[ExposureFinding]
    errors: list[InventoryError]
    private_repository: RepositoryMutationProof | None
    public_candidate: RepositoryMutationProof | None

    @model_validator(mode="after")
    def validate_receipt(self) -> ExposureInventoryReceipt:
        if self.findings != ordered_findings(self.findings):
            raise ValueError("findings must be deterministically ordered")
        if self.risk_summary != build_risk_summary(self.findings):
            raise ValueError("risk summary does not match findings")
        expected_surfaces = list(ExposureSurface)
        if [summary.surface for summary in self.surfaces] != expected_surfaces:
            raise ValueError("surface summaries must be complete and ordered")
        if self.errors != _ordered_errors(self.errors):
            raise ValueError("errors must be deterministically ordered")
        complete = (
            not self.errors
            and self.private_repository is not None
            and self.private_repository.unchanged
            and self.public_candidate is not None
            and self.public_candidate.unchanged
            and all(summary.inspected for summary in self.surfaces)
        )
        expected_status = ScanStatus.COMPLETE if complete else ScanStatus.INCOMPLETE
        if self.scan_status is not expected_status:
            raise ValueError("scan status does not match observed completeness")
        return self


ExposureRule.model_rebuild()
ExposureInventoryPolicy.model_rebuild()
ExposureFinding.model_rebuild()
ExposureInventoryReceipt.model_rebuild()


def load_exposure_policy(policy_path: Path) -> ExposureInventoryPolicy:
    """Load and strictly validate a local exposure-inventory policy."""
    data: Any = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    return ExposureInventoryPolicy.model_validate(data)


def exposure_policy_hash(policy: ExposureInventoryPolicy) -> str:
    """Return a stable SHA-256 for normalized policy semantics."""
    payload = json.dumps(
        policy.model_dump(mode="json"),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ordered_findings(findings: Iterable[ExposureFinding]) -> list[ExposureFinding]:
    """Return findings in stable surface and domain order."""
    surface_order = {surface: index for index, surface in enumerate(ExposureSurface)}
    classification_order = {
        classification: index
        for index, classification in enumerate(ExposureClassification)
    }
    unique = {
        (
            finding.rule_id,
            finding.surface,
            finding.classification,
            finding.severity,
            finding.locator_kind,
            finding.locator,
            finding.disposition,
            finding.presence,
        ): finding
        for finding in findings
    }
    return sorted(
        unique.values(),
        key=lambda finding: (
            surface_order[finding.surface],
            classification_order[finding.classification],
            finding.rule_id,
            finding.locator,
        ),
    )


def build_risk_summary(findings: Iterable[ExposureFinding]) -> RiskSummary:
    """Count findings by every supported severity."""
    counts = {severity: 0 for severity in ExposureSeverity}
    for finding in findings:
        counts[finding.severity] += 1
    return RiskSummary(
        critical=counts[ExposureSeverity.CRITICAL],
        high=counts[ExposureSeverity.HIGH],
        medium=counts[ExposureSeverity.MEDIUM],
        low=counts[ExposureSeverity.LOW],
        info=counts[ExposureSeverity.INFO],
    )


def scan_exposure_inventory(
    repository_root: Path,
    public_candidate_root: Path,
    policy: ExposureInventoryPolicy,
) -> ExposureInventoryReceipt:
    """Inspect bounded local repository surfaces without mutation or disclosure."""
    errors: list[InventoryError] = []
    private_before = _safe_fingerprint(
        repository_root,
        label="private_repository",
        subject=InventorySubject.PRIVATE_REPOSITORY,
        errors=errors,
    )
    public_before = _safe_fingerprint(
        public_candidate_root,
        label="public_candidate",
        subject=InventorySubject.PUBLIC_CANDIDATE,
        errors=errors,
    )

    findings: list[ExposureFinding] = []
    surfaces = _empty_surface_summaries()
    distribution = _distribution_summary([], policy)
    if private_before is not None and public_before is not None:
        try:
            findings, surfaces, distribution = _scan_all_surfaces(
                repository_root,
                public_candidate_root,
                policy,
            )
        except _SafeScanFailure as failure:
            errors.append(InventoryError(code=failure.code, subject=failure.subject))

    private_after = _safe_fingerprint(
        repository_root,
        label="private_repository",
        subject=InventorySubject.PRIVATE_REPOSITORY,
        errors=errors,
    )
    public_after = _safe_fingerprint(
        public_candidate_root,
        label="public_candidate",
        subject=InventorySubject.PUBLIC_CANDIDATE,
        errors=errors,
    )
    private_proof = _mutation_proof(private_before, private_after)
    public_proof = _mutation_proof(public_before, public_after)
    if private_proof is not None and not private_proof.unchanged:
        errors.append(
            InventoryError(
                code=InventoryErrorCode.FINGERPRINT_MISMATCH,
                subject=InventorySubject.PRIVATE_REPOSITORY,
            )
        )
    if public_proof is not None and not public_proof.unchanged:
        errors.append(
            InventoryError(
                code=InventoryErrorCode.FINGERPRINT_MISMATCH,
                subject=InventorySubject.PUBLIC_CANDIDATE,
            )
        )

    ordered = ordered_findings(findings)
    safe_errors = _ordered_errors(errors)
    complete = (
        not safe_errors
        and private_proof is not None
        and private_proof.unchanged
        and public_proof is not None
        and public_proof.unchanged
        and all(summary.inspected for summary in surfaces)
    )
    return ExposureInventoryReceipt(
        scan_status=ScanStatus.COMPLETE if complete else ScanStatus.INCOMPLETE,
        policy_sha256=exposure_policy_hash(policy),
        verifier_source_commit=private_before.head if private_before else None,
        distribution=distribution,
        surfaces=surfaces,
        risk_summary=build_risk_summary(ordered),
        findings=ordered,
        errors=safe_errors,
        private_repository=private_proof,
        public_candidate=public_proof,
    )


def render_exposure_inventory_json(receipt: ExposureInventoryReceipt) -> str:
    """Render a deterministic JSON receipt from sanitized typed fields only."""
    return (
        json.dumps(
            receipt.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def render_exposure_inventory_markdown(receipt: ExposureInventoryReceipt) -> str:
    """Render a deterministic human-readable exposure summary without excerpts."""
    lines = [
        "# Exposure Inventory Receipt",
        "",
        f"- Scan status: `{receipt.scan_status.value}`",
        f"- Policy SHA-256: `{receipt.policy_sha256}`",
        "- Verifier source commit: "
        f"`{receipt.verifier_source_commit or 'unavailable'}`",
        f"- Distribution default: `{receipt.distribution.default_eligibility.value}`",
        f"- Generated staging: `{receipt.distribution.generated_staging.value}`",
        f"- Tracked path count: `{receipt.distribution.tracked_path_count}`",
        f"- Tracked path set SHA-256: `{receipt.distribution.tracked_path_set_sha256}`",
        "- Private repository mutation check: "
        f"`{_mutation_label(receipt.private_repository)}`",
        "- Public candidate mutation check: "
        f"`{_mutation_label(receipt.public_candidate)}`",
        "",
        "## Risk summary",
        "",
        f"- `critical`: `{receipt.risk_summary.critical}`",
        f"- `high`: `{receipt.risk_summary.high}`",
        f"- `medium`: `{receipt.risk_summary.medium}`",
        f"- `low`: `{receipt.risk_summary.low}`",
        f"- `info`: `{receipt.risk_summary.info}`",
        "",
        "## Surfaces",
        "",
    ]
    lines.extend(
        f"- `{summary.surface.value}`: inspected=`{str(summary.inspected).lower()}`, "
        f"items=`{summary.item_count}`, unscanned=`{summary.unscanned_count}`"
        for summary in receipt.surfaces
    )
    lines.extend(["", "## Finding groups", ""])
    if receipt.findings:
        lines.extend(
            f"- `{rule_id}` | `{surface.value}` | `{classification.value}` | "
            f"`{severity.value}` | `{presence.value}` | "
            f"`{disposition.value}` | count=`{count}`"
            for (
                rule_id,
                surface,
                classification,
                severity,
                presence,
                disposition,
                count,
            ) in _finding_groups(receipt.findings)
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


def write_exposure_inventory_receipts(
    receipt: ExposureInventoryReceipt,
    *,
    json_output: Path | None = None,
    markdown_output: Path | None = None,
) -> None:
    """Write explicitly requested receipts only after a complete safe scan."""
    if receipt.scan_status is not ScanStatus.COMPLETE:
        raise ValueError("incomplete receipt cannot be written")
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            render_exposure_inventory_json(receipt),
            encoding="utf-8",
        )
    if markdown_output is not None:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(
            render_exposure_inventory_markdown(receipt),
            encoding="utf-8",
        )


def _scan_all_surfaces(
    repository_root: Path,
    public_candidate_root: Path,
    policy: ExposureInventoryPolicy,
) -> tuple[list[ExposureFinding], list[SurfaceSummary], DistributionSummary]:
    head_paths = _git_paths(
        repository_root,
        InventorySubject.GIT_HEAD,
        "ls-tree",
        "-r",
        "-z",
        "--name-only",
        "HEAD",
    )
    worktree_paths = _git_paths(
        repository_root,
        InventorySubject.WORKTREE,
        "ls-files",
        "-z",
    )
    history_paths = _history_paths(repository_root)
    public_paths = _git_paths(
        public_candidate_root,
        InventorySubject.PUBLIC_CANDIDATE,
        "ls-tree",
        "-r",
        "-z",
        "--name-only",
        "HEAD",
    )
    remote_entries = _remote_url_entries(repository_root)

    findings: list[ExposureFinding] = []
    worktree_unscanned = 0
    for path in worktree_paths:
        filesystem_path = repository_root / path
        present = os.path.lexists(filesystem_path)
        presence = ExposurePresence.PRESENT if present else ExposurePresence.ABSENT
        findings.extend(
            _path_findings(path, ExposureSurface.WORKTREE, presence, policy)
        )
        if present:
            content = _read_worktree_content(
                filesystem_path,
                policy.max_text_bytes,
            )
            if content is None:
                worktree_unscanned += 1
            else:
                findings.extend(
                    _content_findings(
                        path,
                        content,
                        ExposureSurface.WORKTREE,
                        policy,
                    )
                )

    head_unscanned, head_findings = _scan_git_blobs(
        repository_root,
        head_paths,
        ExposureSurface.GIT_HEAD,
        policy,
    )
    findings.extend(head_findings)

    for path in history_paths:
        findings.extend(
            _path_findings(
                path,
                ExposureSurface.GIT_HISTORY,
                ExposurePresence.HISTORICAL,
                policy,
            )
        )

    for remote_name, remote_url in remote_entries:
        if _has_embedded_http_credentials(remote_url):
            findings.extend(_credential_findings(remote_name, policy))

    public_unscanned, public_findings = _scan_git_blobs(
        public_candidate_root,
        public_paths,
        ExposureSurface.PUBLIC_CANDIDATE,
        policy,
    )
    findings.extend(public_findings)

    surfaces = [
        SurfaceSummary(
            surface=ExposureSurface.WORKTREE,
            inspected=True,
            item_count=len(worktree_paths),
            unscanned_count=worktree_unscanned,
        ),
        SurfaceSummary(
            surface=ExposureSurface.GIT_HEAD,
            inspected=True,
            item_count=len(head_paths),
            unscanned_count=head_unscanned,
        ),
        SurfaceSummary(
            surface=ExposureSurface.GIT_HISTORY,
            inspected=True,
            item_count=len(history_paths),
            unscanned_count=0,
        ),
        SurfaceSummary(
            surface=ExposureSurface.LOCAL_GIT_CONFIG,
            inspected=True,
            item_count=len(remote_entries),
            unscanned_count=0,
        ),
        SurfaceSummary(
            surface=ExposureSurface.DISTRIBUTION_CANDIDATE,
            inspected=True,
            item_count=len(head_paths),
            unscanned_count=0,
        ),
        SurfaceSummary(
            surface=ExposureSurface.PUBLIC_CANDIDATE,
            inspected=True,
            item_count=len(public_paths),
            unscanned_count=public_unscanned,
        ),
    ]
    return (
        ordered_findings(findings),
        surfaces,
        _distribution_summary(
            head_paths,
            policy,
        ),
    )


def _scan_git_blobs(
    repository_root: Path,
    paths: list[str],
    surface: ExposureSurface,
    policy: ExposureInventoryPolicy,
) -> tuple[int, list[ExposureFinding]]:
    findings: list[ExposureFinding] = []
    unscanned = 0
    for path in paths:
        findings.extend(_path_findings(path, surface, ExposurePresence.PRESENT, policy))
        result = _run_git(repository_root, "show", f"HEAD:{path}")
        if result is None:
            raise _SafeScanFailure(
                InventoryErrorCode.GIT_COMMAND_FAILED,
                _subject_for_surface(surface),
            )
        return_code, content = result
        if return_code != 0:
            raise _SafeScanFailure(
                InventoryErrorCode.GIT_COMMAND_FAILED,
                _subject_for_surface(surface),
            )
        if _bounded_text(content, policy.max_text_bytes) is None:
            unscanned += 1
            continue
        findings.extend(_content_findings(path, content, surface, policy))
    return unscanned, findings


def _path_findings(
    path: str,
    surface: ExposureSurface,
    presence: ExposurePresence,
    policy: ExposureInventoryPolicy,
) -> list[ExposureFinding]:
    findings: list[ExposureFinding] = []
    folded_path = path.casefold()
    for rule in policy.rules:
        if surface not in rule.surfaces or not rule.matchers.path_globs:
            continue
        if not any(
            fnmatch.fnmatchcase(folded_path, pattern.casefold())
            for pattern in rule.matchers.path_globs
        ):
            continue
        findings.append(_finding_from_rule(rule, surface, path, presence))
    return findings


def _content_findings(
    path: str,
    content: bytes,
    surface: ExposureSurface,
    policy: ExposureInventoryPolicy,
) -> list[ExposureFinding]:
    text = content.decode("utf-8")
    folded_text = text.casefold()
    findings: list[ExposureFinding] = []
    for rule in policy.rules:
        if surface not in rule.surfaces:
            continue
        matched = any(
            term.casefold() in folded_text for term in rule.matchers.content_terms
        ) or any(
            _secret_shape_matches(shape, content)
            for shape in rule.matchers.secret_shapes
            if shape is not SecretShape.AUTHENTICATED_URL
        )
        if not matched:
            continue
        locator = (
            path
            if rule.locator_kind is LocatorKind.RELATIVE_PATH
            else _sensitive_locator(rule.id, surface, path)
        )
        findings.append(
            _finding_from_rule(
                rule,
                surface,
                locator,
                ExposurePresence.PRESENT,
            )
        )
    return findings


def _credential_findings(
    remote_name: str,
    policy: ExposureInventoryPolicy,
) -> list[ExposureFinding]:
    return [
        _finding_from_rule(
            rule,
            ExposureSurface.LOCAL_GIT_CONFIG,
            remote_name,
            ExposurePresence.PRESENT,
        )
        for rule in policy.rules
        if rule.classification is ExposureClassification.CREDENTIAL_RISK
        and ExposureSurface.LOCAL_GIT_CONFIG in rule.surfaces
    ]


def _finding_from_rule(
    rule: ExposureRule,
    surface: ExposureSurface,
    locator: str,
    presence: ExposurePresence,
) -> ExposureFinding:
    return ExposureFinding(
        rule_id=rule.id,
        surface=surface,
        classification=rule.classification,
        severity=rule.severity,
        locator_kind=rule.locator_kind,
        locator=locator,
        disposition=rule.disposition,
        presence=presence,
    )


def _read_worktree_content(path: Path, max_text_bytes: int) -> bytes | None:
    try:
        metadata = path.lstat()
        if path.is_symlink() or not path.is_file() or metadata.st_size > max_text_bytes:
            return None
        return _bounded_text(path.read_bytes(), max_text_bytes)
    except OSError:
        return None


def _bounded_text(content: bytes, max_text_bytes: int) -> bytes | None:
    if len(content) > max_text_bytes or b"\0" in content:
        return None
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return content


def _git_paths(
    repository_root: Path,
    subject: InventorySubject,
    *arguments: str,
) -> list[str]:
    result = _run_git(repository_root, *arguments)
    if result is None or result[0] != 0:
        raise _SafeScanFailure(InventoryErrorCode.GIT_COMMAND_FAILED, subject)
    paths: list[str] = []
    for item in result[1].split(b"\0"):
        if not item:
            continue
        try:
            path = item.decode("utf-8")
            paths.append(_validate_relative_path(path))
        except (UnicodeDecodeError, ValueError):
            raise _SafeScanFailure(InventoryErrorCode.UNSAFE_PATH, subject) from None
    return sorted(set(paths))


def _history_paths(repository_root: Path) -> list[str]:
    result = _run_git(
        repository_root,
        "log",
        "--all",
        "--format=",
        "--name-only",
        "-z",
        "--",
    )
    if result is None or result[0] != 0:
        raise _SafeScanFailure(
            InventoryErrorCode.GIT_COMMAND_FAILED,
            InventorySubject.GIT_HISTORY,
        )
    paths: list[str] = []
    for item in result[1].split(b"\0"):
        candidate = item.strip(b"\n")
        if not candidate:
            continue
        try:
            path = candidate.decode("utf-8")
            paths.append(_validate_relative_path(path))
        except (UnicodeDecodeError, ValueError):
            raise _SafeScanFailure(
                InventoryErrorCode.UNSAFE_PATH,
                InventorySubject.GIT_HISTORY,
            ) from None
    return sorted(set(paths))


def _remote_url_entries(repository_root: Path) -> list[tuple[str, str]]:
    result = _run_git(
        repository_root,
        "config",
        "--get-regexp",
        r"^remote\..*\.url$",
    )
    if result is None:
        raise _SafeScanFailure(
            InventoryErrorCode.GIT_COMMAND_FAILED,
            InventorySubject.LOCAL_GIT_CONFIG,
        )
    return_code, output = result
    if return_code == 1:
        return []
    if return_code != 0:
        raise _SafeScanFailure(
            InventoryErrorCode.GIT_COMMAND_FAILED,
            InventorySubject.LOCAL_GIT_CONFIG,
        )
    entries: list[tuple[str, str]] = []
    try:
        text = output.decode("utf-8")
        for line in text.splitlines():
            key, remote_url = line.split(maxsplit=1)
            match = re.fullmatch(r"remote\.(.+)\.url", key)
            if match is None or _REMOTE_NAME_PATTERN.fullmatch(match.group(1)) is None:
                raise ValueError
            entries.append((match.group(1), remote_url))
    except (UnicodeDecodeError, ValueError):
        raise _SafeScanFailure(
            InventoryErrorCode.GIT_COMMAND_FAILED,
            InventorySubject.LOCAL_GIT_CONFIG,
        ) from None
    return sorted(entries, key=lambda entry: entry[0])


def _run_git(
    repository_root: Path,
    *arguments: str,
) -> tuple[int, bytes] | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository_root), *arguments],
            check=False,
            capture_output=True,
            env=_read_only_git_environment(),
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.returncode, result.stdout


def _safe_fingerprint(
    repository_root: Path,
    *,
    label: str,
    subject: InventorySubject,
    errors: list[InventoryError],
) -> RepositoryFingerprint | None:
    if not repository_root.is_dir():
        errors.append(
            InventoryError(
                code=InventoryErrorCode.MISSING_REPOSITORY,
                subject=subject,
            )
        )
        return None
    try:
        return fingerprint_repository(repository_root, label=label)
    except ValueError:
        errors.append(
            InventoryError(
                code=InventoryErrorCode.GIT_COMMAND_FAILED,
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


def _mutation_label(proof: RepositoryMutationProof | None) -> str:
    if proof is None:
        return "unavailable"
    return "pass" if proof.unchanged else "fail"


def _distribution_summary(
    paths: list[str],
    policy: ExposureInventoryPolicy,
) -> DistributionSummary:
    payload = "".join(f"{path}\n" for path in sorted(paths))
    return DistributionSummary(
        default_eligibility=policy.distribution.default_eligibility,
        generated_staging=policy.distribution.generated_staging,
        tracked_path_count=len(paths),
        tracked_path_set_sha256=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    )


def _empty_surface_summaries() -> list[SurfaceSummary]:
    return [
        SurfaceSummary(
            surface=surface,
            inspected=False,
            item_count=0,
            unscanned_count=0,
        )
        for surface in ExposureSurface
    ]


def _ordered_errors(errors: Iterable[InventoryError]) -> list[InventoryError]:
    unique = {(error.code, error.subject): error for error in errors}
    return sorted(
        unique.values(),
        key=lambda error: (error.code.value, error.subject.value),
    )


def _finding_groups(
    findings: Iterable[ExposureFinding],
) -> list[
    tuple[
        str,
        ExposureSurface,
        ExposureClassification,
        ExposureSeverity,
        ExposurePresence,
        ExposureDisposition,
        int,
    ]
]:
    counts: dict[
        tuple[
            str,
            ExposureSurface,
            ExposureClassification,
            ExposureSeverity,
            ExposurePresence,
            ExposureDisposition,
        ],
        int,
    ] = {}
    for finding in ordered_findings(findings):
        key = (
            finding.rule_id,
            finding.surface,
            finding.classification,
            finding.severity,
            finding.presence,
            finding.disposition,
        )
        counts[key] = counts.get(key, 0) + 1
    return [(*key, count) for key, count in counts.items()]


def _secret_shape_matches(shape: SecretShape, content: bytes) -> bool:
    patterns = {
        SecretShape.ASSIGNMENT: _ASSIGNMENT_PATTERN,
        SecretShape.BEARER_TOKEN: _BEARER_PATTERN,
        SecretShape.PRIVATE_KEY: _PRIVATE_KEY_PATTERN,
    }
    pattern = patterns.get(shape)
    return pattern is not None and pattern.search(content) is not None


def _sensitive_locator(rule_id: str, surface: ExposureSurface, path: str) -> str:
    payload = f"{rule_id}\0{surface.value}\0{path}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _subject_for_surface(surface: ExposureSurface) -> InventorySubject:
    subjects = {
        ExposureSurface.WORKTREE: InventorySubject.WORKTREE,
        ExposureSurface.GIT_HEAD: InventorySubject.GIT_HEAD,
        ExposureSurface.GIT_HISTORY: InventorySubject.GIT_HISTORY,
        ExposureSurface.LOCAL_GIT_CONFIG: InventorySubject.LOCAL_GIT_CONFIG,
        ExposureSurface.DISTRIBUTION_CANDIDATE: InventorySubject.GIT_HEAD,
        ExposureSurface.PUBLIC_CANDIDATE: InventorySubject.PUBLIC_CANDIDATE,
    }
    return subjects[surface]


class _SafeScanFailure(Exception):
    def __init__(
        self,
        code: InventoryErrorCode,
        subject: InventorySubject,
    ) -> None:
        super().__init__(code.value)
        self.code = code
        self.subject = subject


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
    return value


def _validate_safe_term(value: str) -> str:
    if not 2 <= len(value) <= 256 or value != value.strip():
        raise ValueError("unsafe content term")
    if _contains_control_character(value):
        raise ValueError("unsafe content term")
    return value


def _contains_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _reject_duplicates(values: Iterable[Any], label: str) -> None:
    materialized = list(values)
    if len(set(materialized)) != len(materialized):
        raise ValueError(f"{label} must not contain duplicates")


def _validate_classification_boundary(
    *,
    classification: ExposureClassification,
    disposition: ExposureDisposition,
    locator_kind: LocatorKind,
    surface: ExposureSurface | None,
) -> None:
    expected = {
        ExposureClassification.RAW_REFERENCE: (
            LocatorKind.RELATIVE_PATH,
            ExposureDisposition.REMOVE_IN_S36_3,
        ),
        ExposureClassification.DERIVED_REFERENCE: (
            LocatorKind.RELATIVE_PATH,
            ExposureDisposition.REVIEW_IN_S36_3,
        ),
        ExposureClassification.PUBLIC_VOCABULARY: (
            LocatorKind.RELATIVE_PATH,
            ExposureDisposition.REVIEW_IN_S36_3,
        ),
        ExposureClassification.SECRET_CANDIDATE: (
            LocatorKind.SHA256,
            ExposureDisposition.REVIEW_SECURITY,
        ),
        ExposureClassification.CREDENTIAL_RISK: (
            LocatorKind.REMOTE_NAME,
            ExposureDisposition.REVIEW_SECURITY,
        ),
        ExposureClassification.PRIVATE_DATA: (
            LocatorKind.RELATIVE_PATH,
            ExposureDisposition.BLOCK_IN_S36_5,
        ),
        ExposureClassification.INTERNAL_PATH: (
            LocatorKind.RELATIVE_PATH,
            ExposureDisposition.BLOCK_IN_S36_5,
        ),
        ExposureClassification.NOT_ELIGIBLE: (
            LocatorKind.RELATIVE_PATH,
            ExposureDisposition.BLOCK_IN_S36_5,
        ),
    }
    if (locator_kind, disposition) != expected[classification]:
        raise ValueError("incoherent classification boundary")
    if (
        classification is ExposureClassification.CREDENTIAL_RISK
        and surface is not None
        and surface is not ExposureSurface.LOCAL_GIT_CONFIG
    ):
        raise ValueError("credential findings are local-config only")
