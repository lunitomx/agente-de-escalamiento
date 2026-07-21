"""Typed, deterministic contracts for local exposure inventory."""

from __future__ import annotations

from enum import Enum
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


_RULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_REMOTE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


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


ExposureRule.model_rebuild()
ExposureInventoryPolicy.model_rebuild()
ExposureFinding.model_rebuild()


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
    return sorted(
        findings,
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
