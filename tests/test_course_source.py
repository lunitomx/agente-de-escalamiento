from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from validators.course_source import (
    COURSE_LIBRARY_ROOT,
    CourseSourceError,
    build_course_source_receipt,
    load_course_source_manifest,
    promotion_decision,
    validate_course_source_manifest,
)


ROOT = Path(__file__).resolve().parents[1]


def _manifest_data(content: bytes, **overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "schema_version": 1,
        "course_id": "sales-foundations",
        "title": "Synthetic sales workshop",
        "instructor": "Synthetic instructor",
        "format": "transcript",
        "owner_id": "local-owner",
        "rights_status": "documented_local_use",
        "rights_evidence": [{"kind": "owner_attestation", "locator": "local-record"}],
        "capture_quality": "reviewed_transcript",
        "timestamps_available": True,
        "review_status": "human_approved",
        "retention": "local_only",
        "lifecycle_status": "candidate",
        "artifact": {
            "relative_path": "raw/session.txt",
            "sha256": hashlib.sha256(content).hexdigest(),
            "byte_count": len(content),
        },
    }
    data.update(overrides)
    return data


def _write_manifest(tmp_path: Path, data: dict[str, object], content: bytes) -> Path:
    course_root = tmp_path / COURSE_LIBRARY_ROOT / "sales-foundations"
    artifact = course_root / "raw/session.txt"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(content)
    manifest = course_root / "manifest.json"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    return manifest


def test_authorized_local_source_yields_bounded_candidate_receipt(
    tmp_path: Path,
) -> None:
    content = b"synthetic source only\n"
    manifest_path = _write_manifest(tmp_path, _manifest_data(content), content)

    manifest = load_course_source_manifest(tmp_path, manifest_path)
    validate_course_source_manifest(tmp_path, manifest_path, manifest)
    decision = promotion_decision(manifest)
    receipt = build_course_source_receipt(manifest, decision)

    assert decision.status == "candidate_only"
    assert decision.allowed_actions == ["curate_candidates"]
    assert decision.blocked_actions == [
        "citation",
        "formula",
        "installable_pack",
        "normative_rule",
    ]
    assert receipt.course_id == "sales-foundations"
    assert receipt.local_only is True
    assert receipt.publication_authorized is False
    rendered = receipt.model_dump_json()
    for secret in (
        "Synthetic sales workshop",
        "Synthetic instructor",
        "local-owner",
        "raw/session.txt",
        "synthetic source only",
    ):
        assert secret not in rendered


@pytest.mark.parametrize(
    ("field", "value", "expected_status"),
    [
        ("review_status", "pending", "candidate_only"),
        ("review_status", "rejected", "blocked"),
        ("lifecycle_status", "blocked", "blocked"),
    ],
)
def test_incomplete_contract_fails_closed(
    tmp_path: Path, field: str, value: str, expected_status: str
) -> None:
    content = b"synthetic source only\\n"
    manifest_path = _write_manifest(
        tmp_path, _manifest_data(content, **{field: value}), content
    )
    manifest = load_course_source_manifest(tmp_path, manifest_path)

    decision = promotion_decision(manifest)

    assert decision.status == expected_status
    assert {"citation", "formula", "installable_pack", "normative_rule"} <= set(
        decision.blocked_actions
    )
    if expected_status == "blocked":
        assert decision.allowed_actions == []
        assert "curate_candidates" in decision.blocked_actions
    else:
        assert decision.allowed_actions == ["curate_candidates"]


def test_manifest_rejects_missing_retention(tmp_path: Path) -> None:
    content = b"synthetic source only\\n"
    manifest_path = _write_manifest(
        tmp_path, _manifest_data(content, retention=""), content
    )

    with pytest.raises(CourseSourceError, match="manifest contract invalid"):
        load_course_source_manifest(tmp_path, manifest_path)


def test_manifest_rejects_unresolved_rights_with_permission(tmp_path: Path) -> None:
    content = b"synthetic source only\\n"
    manifest_path = _write_manifest(
        tmp_path, _manifest_data(content, rights_status="unknown"), content
    )

    with pytest.raises(CourseSourceError, match="manifest contract invalid"):
        load_course_source_manifest(tmp_path, manifest_path)


def test_noisy_transcript_cannot_be_promoted_to_a_rule_or_pack(tmp_path: Path) -> None:
    content = b"synthetic noisy transcript\n"
    manifest_path = _write_manifest(
        tmp_path,
        _manifest_data(
            content,
            capture_quality="noisy_transcript",
            timestamps_available=False,
            review_status="pending",
        ),
        content,
    )
    manifest = load_course_source_manifest(tmp_path, manifest_path)

    decision = promotion_decision(manifest)

    assert decision.status == "candidate_only"
    assert decision.reason == "capture_not_reviewed"
    assert decision.allowed_actions == ["curate_candidates"]
    assert {"normative_rule", "formula", "citation", "installable_pack"} <= set(
        decision.blocked_actions
    )


def test_manifest_requires_local_course_library_and_matching_artifact(
    tmp_path: Path,
) -> None:
    content = b"synthetic source only\\n"
    outside = tmp_path / "outside-manifest.json"
    outside.write_text(json.dumps(_manifest_data(content)), encoding="utf-8")

    with pytest.raises(CourseSourceError, match="outside local course library"):
        load_course_source_manifest(tmp_path, outside)

    manifest_path = _write_manifest(tmp_path, _manifest_data(content), content)
    manifest = load_course_source_manifest(tmp_path, manifest_path)
    (manifest_path.parent / "raw/session.txt").write_bytes(b"altered!! source only\\n")

    with pytest.raises(CourseSourceError, match="artifact hash mismatch"):
        validate_course_source_manifest(tmp_path, manifest_path, manifest)


def test_course_library_is_ignored_by_git() -> None:
    completed = subprocess.run(
        [
            "git",
            "check-ignore",
            "-q",
            f"{COURSE_LIBRARY_ROOT}/sales-foundations/manifest.json",
        ],
        cwd=ROOT,
        check=False,
    )

    assert completed.returncode == 0
