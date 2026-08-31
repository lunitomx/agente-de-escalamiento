"""Fail-closed local custody contracts for private course sources.

This module intentionally handles metadata and fingerprints only. It reads raw
bytes solely to verify a declared hash; it never returns, logs, or stores course
text in the repository.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


COURSE_LIBRARY_ROOT = Path(".scaleup") / "course-library"

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

_NORMATIVE_ACTIONS = [
    "citation",
    "formula",
    "installable_pack",
    "normative_rule",
]
_ALL_ACTIONS = ["curate_candidates", *_NORMATIVE_ACTIONS]


class CourseSourceError(ValueError):
    """Safe failure that never includes course content or local paths."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CourseFormat(str, Enum):
    AUDIO = "audio"
    NOTES = "notes"
    OCR = "ocr"
    SLIDES = "slides"
    TRANSCRIPT = "transcript"
    VIDEO = "video"
    WORKBOOK = "workbook"


class DistributionStatus(str, Enum):
    NOT_AUTHORIZED = "not_authorized"


class RightsStatus(str, Enum):
    DOCUMENTED_LOCAL_USE = "documented_local_use"
    REVIEW_REQUIRED = "review_required"
    UNKNOWN = "unknown"


class CaptureQuality(str, Enum):
    ORIGINAL = "original"
    OCR = "ocr"
    NOISY_TRANSCRIPT = "noisy_transcript"
    REVIEWED_TRANSCRIPT = "reviewed_transcript"


class ReviewStatus(str, Enum):
    HUMAN_APPROVED = "human_approved"
    PENDING = "pending"
    REJECTED = "rejected"


class RetentionPolicy(str, Enum):
    LOCAL_ONLY = "local_only"


class LifecycleStatus(str, Enum):
    APPROVED_LOCAL = "approved_local"
    BLOCKED = "blocked"
    CANDIDATE = "candidate"
    RETIRED = "retired"


class RightsEvidence(_StrictModel):
    kind: str = Field(min_length=3, max_length=80)
    locator: str = Field(min_length=1, max_length=512)

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe rights evidence kind")
        return value

    @field_validator("locator")
    @classmethod
    def validate_locator(cls, value: str) -> str:
        if "\x00" in value or "\n" in value or "\r" in value:
            raise ValueError("unsafe rights evidence locator")
        return value


class CourseArtifact(_StrictModel):
    relative_path: str = Field(min_length=1, max_length=512)
    sha256: str = Field(pattern=_SHA256_PATTERN.pattern)
    byte_count: int = Field(ge=1)

    @field_validator("relative_path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if (
            path.is_absolute()
            or "\\" in value
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise ValueError("unsafe course artifact path")
        return path.as_posix()


class CourseSourceManifest(_StrictModel):
    schema_version: Literal[1]
    course_id: str = Field(min_length=3, max_length=128)
    title: str = Field(min_length=1, max_length=512)
    instructor: str = Field(min_length=1, max_length=256)
    acquired_on: date
    format: CourseFormat
    owner_id: str = Field(min_length=3, max_length=128)
    distribution_status: DistributionStatus
    rights_status: RightsStatus
    rights_evidence: list[RightsEvidence] = Field(default_factory=list)
    capture_quality: CaptureQuality
    timestamps_available: bool
    review_status: ReviewStatus
    retention: RetentionPolicy
    lifecycle_status: LifecycleStatus
    artifact: CourseArtifact

    @field_validator("course_id", "owner_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe course identifier")
        return value

    @field_validator("title", "instructor")
    @classmethod
    def validate_private_label(cls, value: str) -> str:
        if "\x00" in value or "\n" in value or "\r" in value:
            raise ValueError("unsafe private label")
        return value

    @field_validator("rights_evidence")
    @classmethod
    def validate_evidence(cls, values: list[RightsEvidence]) -> list[RightsEvidence]:
        identities = [(item.kind, item.locator) for item in values]
        if len(identities) != len(set(identities)):
            raise ValueError("duplicate rights evidence")
        return sorted(values, key=lambda item: (item.kind, item.locator))

    @model_validator(mode="after")
    def validate_rights(self) -> CourseSourceManifest:
        if (
            self.rights_status is RightsStatus.DOCUMENTED_LOCAL_USE
            and not self.rights_evidence
        ):
            raise ValueError("documented local use requires evidence")
        if (
            self.rights_status is not RightsStatus.DOCUMENTED_LOCAL_USE
            and self.rights_evidence
        ):
            raise ValueError("unresolved rights cannot claim permission evidence")
        return self


class PromotionDecision(_StrictModel):
    status: Literal["blocked", "candidate_only"]
    reason: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    allowed_actions: list[str]
    blocked_actions: list[str]

    @model_validator(mode="after")
    def validate_action_partition(self) -> PromotionDecision:
        if self.allowed_actions != sorted(set(self.allowed_actions)):
            raise ValueError("allowed actions must be unique and sorted")
        if self.blocked_actions != sorted(set(self.blocked_actions)):
            raise ValueError("blocked actions must be unique and sorted")
        if set(self.allowed_actions) | set(self.blocked_actions) != set(_ALL_ACTIONS):
            raise ValueError("promotion decision must classify every action")
        if set(self.allowed_actions) & set(self.blocked_actions):
            raise ValueError("promotion decision actions overlap")
        if self.status == "blocked" and self.allowed_actions:
            raise ValueError("blocked decision cannot allow actions")
        if self.status == "candidate_only" and self.allowed_actions != [
            "curate_candidates"
        ]:
            raise ValueError("candidate decision may only allow curation")
        return self


class CourseSourceReceipt(_StrictModel):
    schema_version: Literal[1]
    status: Literal["pass"]
    course_id: str
    source_sha256: str = Field(pattern=_SHA256_PATTERN.pattern)
    decision: PromotionDecision
    local_only: Literal[True]
    publication_authorized: Literal[False]


def _course_library(repository: Path) -> Path:
    return (repository.resolve() / COURSE_LIBRARY_ROOT).resolve()


def _require_in_course_library(repository: Path, path: Path) -> Path:
    library = _course_library(repository)
    candidate = path.resolve()
    try:
        candidate.relative_to(library)
    except ValueError as exc:
        raise CourseSourceError("manifest outside local course library") from exc
    return candidate


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CourseSourceError("manifest unreadable") from exc


def load_course_source_manifest(
    repository: Path, manifest_path: Path
) -> CourseSourceManifest:
    manifest_path = _require_in_course_library(repository, manifest_path)
    if manifest_path.name != "manifest.json":
        raise CourseSourceError("manifest filename invalid")
    try:
        return CourseSourceManifest.model_validate(_load_json(manifest_path))
    except CourseSourceError:
        raise
    except Exception as exc:
        raise CourseSourceError("manifest contract invalid") from exc


def _artifact_path(manifest_path: Path, manifest: CourseSourceManifest) -> Path:
    course_root = manifest_path.parent.resolve()
    artifact = (course_root / manifest.artifact.relative_path).resolve()
    try:
        artifact.relative_to(course_root)
    except ValueError as exc:
        raise CourseSourceError("artifact outside course directory") from exc
    return artifact


def validate_course_source_manifest(
    repository: Path, manifest_path: Path, manifest: CourseSourceManifest
) -> None:
    manifest_path = _require_in_course_library(repository, manifest_path)
    artifact = _artifact_path(manifest_path, manifest)
    try:
        content = artifact.read_bytes()
    except OSError as exc:
        raise CourseSourceError("course artifact unreadable") from exc
    if len(content) != manifest.artifact.byte_count:
        raise CourseSourceError("artifact byte count mismatch")
    if hashlib.sha256(content).hexdigest() != manifest.artifact.sha256:
        raise CourseSourceError("artifact hash mismatch")


def promotion_decision(manifest: CourseSourceManifest) -> PromotionDecision:
    blocked_normative = sorted(_NORMATIVE_ACTIONS)
    if manifest.lifecycle_status in {LifecycleStatus.BLOCKED, LifecycleStatus.RETIRED}:
        return PromotionDecision(
            status="blocked",
            reason="source_not_active",
            allowed_actions=[],
            blocked_actions=sorted(_ALL_ACTIONS),
        )
    if manifest.rights_status is not RightsStatus.DOCUMENTED_LOCAL_USE:
        return PromotionDecision(
            status="blocked",
            reason="rights_not_documented",
            allowed_actions=[],
            blocked_actions=sorted(_ALL_ACTIONS),
        )
    if manifest.review_status is ReviewStatus.REJECTED:
        return PromotionDecision(
            status="blocked",
            reason="human_review_rejected",
            allowed_actions=[],
            blocked_actions=sorted(_ALL_ACTIONS),
        )
    if manifest.capture_quality is CaptureQuality.NOISY_TRANSCRIPT or (
        manifest.format
        in {CourseFormat.AUDIO, CourseFormat.TRANSCRIPT, CourseFormat.VIDEO}
        and not manifest.timestamps_available
    ):
        reason = "capture_not_reviewed"
    elif manifest.review_status is not ReviewStatus.HUMAN_APPROVED:
        reason = "human_review_required"
    else:
        reason = "candidate_requires_procedure_review"
    return PromotionDecision(
        status="candidate_only",
        reason=reason,
        allowed_actions=["curate_candidates"],
        blocked_actions=blocked_normative,
    )


def build_course_source_receipt(
    manifest: CourseSourceManifest, decision: PromotionDecision
) -> CourseSourceReceipt:
    return CourseSourceReceipt(
        schema_version=1,
        status="pass",
        course_id=manifest.course_id,
        source_sha256=manifest.artifact.sha256,
        decision=decision,
        local_only=True,
        publication_authorized=False,
    )
