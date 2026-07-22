from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys

import pytest
from pydantic import ValidationError

import validators.exposure_inventory as exposure_module
from validators.exposure_inventory import (
    ExposureClassification,
    ExposureDisposition,
    ExposureFinding,
    ExposurePresence,
    ExposureSeverity,
    ExposureSurface,
    InventoryErrorCode,
    LocatorKind,
    ScanStatus,
    SecretShape,
    build_risk_summary,
    detect_secret_shapes,
    exposure_policy_hash,
    load_exposure_policy,
    ordered_findings,
    render_exposure_inventory_json,
    render_exposure_inventory_markdown,
    scan_exposure_inventory,
    write_exposure_inventory_receipts,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_exposure_inventory.py"


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
    presence: ExposurePresence = ExposurePresence.PRESENT,
) -> ExposureFinding:
    return ExposureFinding(
        rule_id=rule_id,
        surface=surface,
        classification=classification,
        severity=severity,
        locator_kind=locator_kind,
        locator=locator,
        disposition=disposition,
        presence=presence,
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
    ("content", "expected"),
    [
        (b"plain local configuration", []),
        (b"api_key=S36SECRETASSIGNMENT123", [SecretShape.ASSIGNMENT]),
        (
            b"Authorization: Bearer S36.SECRET.BEARER.TOKEN",
            [SecretShape.BEARER_TOKEN],
        ),
        (
            b"-----BEGIN PRIVATE KEY-----\nS36PRIVATEKEYVALUE\n",
            [SecretShape.PRIVATE_KEY],
        ),
        (
            b"password=S36SECRETASSIGNMENT123\n"
            b"Authorization: Bearer S36.SECRET.BEARER.TOKEN\n"
            b"-----BEGIN PRIVATE KEY-----\nS36PRIVATEKEYVALUE\n",
            [
                SecretShape.ASSIGNMENT,
                SecretShape.BEARER_TOKEN,
                SecretShape.PRIVATE_KEY,
            ],
        ),
    ],
)
def test_detect_secret_shapes_returns_only_sorted_shape_ids(
    content: bytes,
    expected: list[SecretShape],
) -> None:
    detected = detect_secret_shapes(content)

    assert detected == expected
    serialized = repr(detected)
    for private_value in (
        "S36SECRETASSIGNMENT123",
        "S36.SECRET.BEARER.TOKEN",
        "S36PRIVATEKEYVALUE",
    ):
        assert private_value not in serialized


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
            "presence": "present",
        },
        {
            "rule_id": "config.authenticated_remote",
            "surface": "local_git_config",
            "classification": "credential_risk",
            "severity": "critical",
            "locator_kind": "sha256",
            "locator": "a" * 64,
            "disposition": "review_security",
            "presence": "present",
        },
        {
            "rule_id": "reference.raw_asset",
            "surface": "git_head",
            "classification": "raw_reference",
            "severity": "critical",
            "locator_kind": "relative_path",
            "locator": "reference.pdf",
            "disposition": "review_security",
            "presence": "present",
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

    assert ordered_findings([higher, lower, lower]) == [lower, higher]
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


def _git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _initialize_repository(repository: Path) -> None:
    repository.mkdir(parents=True)
    subprocess.run(
        ["git", "init", "--initial-branch=main", str(repository)],
        check=True,
        capture_output=True,
        text=True,
    )
    _git(repository, "config", "user.email", "tests@example.invalid")
    _git(repository, "config", "user.name", "Exposure Inventory Tests")


def _create_inventory_repositories(
    tmp_path: Path,
) -> tuple[Path, Path, str, str]:
    private = tmp_path / "private-repository"
    public = tmp_path / "public-candidate"
    sentinel = "S36-EXPOSURE-SECRET-123456789"
    sensitive_url = f"https://{sentinel}@example.invalid/private.git"

    _initialize_repository(private)
    (private / "README.md").write_text("local product\n", encoding="utf-8")
    (private / "reference-asset.pdf").write_bytes(b"%PDF-binary-reference\x00")
    (private / "secret.env").write_text(
        f'api_key = "{sentinel}"\n',
        encoding="utf-8",
    )
    (private / "old-reference.pdf").write_bytes(b"%PDF-historical\x00")
    _git(private, "add", ".")
    _git(private, "commit", "-m", "baseline")
    (private / "old-reference.pdf").unlink()
    _git(private, "add", "-u")
    _git(private, "commit", "-m", "remove historical reference")
    (private / "reference-asset.pdf").unlink()
    _git(private, "remote", "add", "gitlab", sensitive_url)

    _initialize_repository(public)
    (public / "README.md").write_text("public candidate\n", encoding="utf-8")
    _git(public, "add", "README.md")
    _git(public, "commit", "-m", "public baseline")
    (public / "dirty-private-name.txt").write_text(sentinel, encoding="utf-8")

    return private, public, sentinel, sensitive_url


def _findings_for(
    receipt: object,
    *,
    rule_id: str,
    surface: ExposureSurface,
) -> list[ExposureFinding]:
    findings = getattr(receipt, "findings")
    return [
        finding
        for finding in findings
        if finding.rule_id == rule_id and finding.surface is surface
    ]


def test_real_git_inventory_keeps_surfaces_distinct_and_complete(
    tmp_path: Path,
) -> None:
    private, public, sentinel, sensitive_url = _create_inventory_repositories(tmp_path)
    policy = load_exposure_policy(_write_policy(tmp_path))

    receipt = scan_exposure_inventory(private, public, policy)
    serialized = receipt.model_dump_json()

    worktree_raw = _findings_for(
        receipt,
        rule_id="reference.raw_asset",
        surface=ExposureSurface.WORKTREE,
    )
    head_raw = _findings_for(
        receipt,
        rule_id="reference.raw_asset",
        surface=ExposureSurface.GIT_HEAD,
    )
    history_raw = _findings_for(
        receipt,
        rule_id="reference.raw_asset",
        surface=ExposureSurface.GIT_HISTORY,
    )
    secret_findings = _findings_for(
        receipt,
        rule_id="secret.assignment",
        surface=ExposureSurface.GIT_HEAD,
    )
    credential_findings = _findings_for(
        receipt,
        rule_id="config.authenticated_remote",
        surface=ExposureSurface.LOCAL_GIT_CONFIG,
    )

    assert receipt.scan_status is ScanStatus.COMPLETE
    assert receipt.errors == []
    assert receipt.verifier_source_commit == _git(private, "rev-parse", "HEAD")
    assert [(finding.locator, finding.presence) for finding in worktree_raw] == [
        ("reference-asset.pdf", ExposurePresence.ABSENT)
    ]
    assert [(finding.locator, finding.presence) for finding in head_raw] == [
        ("reference-asset.pdf", ExposurePresence.PRESENT)
    ]
    assert {(finding.locator, finding.presence) for finding in history_raw} == {
        ("old-reference.pdf", ExposurePresence.HISTORICAL),
        ("reference-asset.pdf", ExposurePresence.HISTORICAL),
    }
    assert len(secret_findings) == 1
    assert secret_findings[0].locator_kind is LocatorKind.SHA256
    assert len(secret_findings[0].locator) == 64
    assert [(finding.locator, finding.presence) for finding in credential_findings] == [
        ("gitlab", ExposurePresence.PRESENT)
    ]
    assert receipt.distribution.default_eligibility == "not_eligible"
    assert receipt.distribution.generated_staging == "not_built"
    assert receipt.distribution.tracked_path_count == 3
    expected_paths = "README.md\nreference-asset.pdf\nsecret.env\n"
    assert (
        receipt.distribution.tracked_path_set_sha256
        == hashlib.sha256(expected_paths.encode("utf-8")).hexdigest()
    )
    assert receipt.private_repository is not None
    assert receipt.private_repository.unchanged is True
    assert receipt.public_candidate is not None
    assert receipt.public_candidate.unchanged is True
    assert (public / "dirty-private-name.txt").read_text(encoding="utf-8") == sentinel
    for forbidden in (
        sentinel,
        sensitive_url,
        str(private),
        str(public),
        "dirty-private-name.txt",
        "secret.env",
    ):
        assert forbidden not in serialized


def test_inventory_ignores_inherited_git_environment_overrides(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private, public, sentinel, _ = _create_inventory_repositories(tmp_path / "target")
    decoy, _, _, _ = _create_inventory_repositories(tmp_path / "decoy")
    policy = load_exposure_policy(_write_policy(tmp_path))
    injected = "S36-INJECTED-GIT-CONFIG-SECRET"
    expected_commit = _git(private, "rev-parse", "HEAD")

    monkeypatch.setenv("GIT_DIR", str(decoy / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(decoy))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "remote.injected.url")
    monkeypatch.setenv(
        "GIT_CONFIG_VALUE_0",
        f"https://{injected}@example.invalid/private.git",
    )

    receipt = scan_exposure_inventory(private, public, policy)
    serialized = receipt.model_dump_json()

    assert receipt.scan_status is ScanStatus.COMPLETE
    assert receipt.verifier_source_commit == expected_commit
    assert injected not in serialized
    assert sentinel not in serialized
    assert "injected" not in {
        finding.locator
        for finding in receipt.findings
        if finding.locator_kind is LocatorKind.REMOTE_NAME
    }


def test_missing_repository_returns_sanitized_incomplete_receipt(
    tmp_path: Path,
) -> None:
    public = tmp_path / "public"
    _initialize_repository(public)
    (public / "README.md").write_text("public\n", encoding="utf-8")
    _git(public, "add", "README.md")
    _git(public, "commit", "-m", "public")
    missing = tmp_path / "private-customer-name"
    policy = load_exposure_policy(_write_policy(tmp_path))

    receipt = scan_exposure_inventory(missing, public, policy)
    serialized = receipt.model_dump_json()

    assert receipt.scan_status is ScanStatus.INCOMPLETE
    assert receipt.private_repository is None
    assert InventoryErrorCode.MISSING_REPOSITORY in {
        error.code for error in receipt.errors
    }
    assert str(missing) not in serialized
    assert "private-customer-name" not in serialized


def test_fingerprint_mismatch_fails_closed_without_mutating_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private, public, _, _ = _create_inventory_repositories(tmp_path)
    policy = load_exposure_policy(_write_policy(tmp_path))
    original = exposure_module.fingerprint_repository
    call_count = 0

    def mismatching_fingerprint(
        repository_root: Path,
        *,
        label: str,
    ) -> object:
        nonlocal call_count
        call_count += 1
        fingerprint = original(repository_root, label=label)
        if call_count == 3:
            return fingerprint.model_copy(update={"status_sha256": "f" * 64})
        return fingerprint

    monkeypatch.setattr(
        exposure_module,
        "fingerprint_repository",
        mismatching_fingerprint,
    )

    receipt = scan_exposure_inventory(private, public, policy)

    assert receipt.scan_status is ScanStatus.INCOMPLETE
    assert InventoryErrorCode.FINGERPRINT_MISMATCH in {
        error.code for error in receipt.errors
    }
    assert receipt.private_repository is not None
    assert receipt.private_repository.unchanged is False


def test_receipt_renderers_and_explicit_writes_are_deterministic_and_safe(
    tmp_path: Path,
) -> None:
    private, public, sentinel, sensitive_url = _create_inventory_repositories(tmp_path)
    policy = load_exposure_policy(_write_policy(tmp_path))
    receipt = scan_exposure_inventory(private, public, policy)
    json_output = tmp_path / "evidence" / "baseline.json"
    markdown_output = tmp_path / "evidence" / "baseline.md"

    first_json = render_exposure_inventory_json(receipt)
    first_markdown = render_exposure_inventory_markdown(receipt)
    write_exposure_inventory_receipts(
        receipt,
        json_output=json_output,
        markdown_output=markdown_output,
    )

    assert first_json == render_exposure_inventory_json(receipt)
    assert first_markdown == render_exposure_inventory_markdown(receipt)
    assert first_json.endswith("\n")
    assert first_markdown.endswith("\n")
    assert json_output.read_text(encoding="utf-8") == first_json
    assert markdown_output.read_text(encoding="utf-8") == first_markdown
    assert "# Exposure Inventory Receipt" in first_markdown
    assert "- Scan status: `complete`" in first_markdown
    assert "## Finding groups" in first_markdown
    assert "reference-asset.pdf" not in first_markdown
    assert len(first_markdown) < len(first_json)
    combined = first_json + first_markdown
    for forbidden in (
        sentinel,
        sensitive_url,
        str(private),
        str(public),
        "dirty-private-name.txt",
        "secret.env",
    ):
        assert forbidden not in combined


def test_incomplete_receipt_is_not_written(tmp_path: Path) -> None:
    public = tmp_path / "public"
    _initialize_repository(public)
    (public / "README.md").write_text("public\n", encoding="utf-8")
    _git(public, "add", "README.md")
    _git(public, "commit", "-m", "public")
    policy = load_exposure_policy(_write_policy(tmp_path))
    receipt = scan_exposure_inventory(tmp_path / "missing-private", public, policy)
    json_output = tmp_path / "must-not-exist.json"
    markdown_output = tmp_path / "must-not-exist.md"

    with pytest.raises(ValueError, match="incomplete receipt"):
        write_exposure_inventory_receipts(
            receipt,
            json_output=json_output,
            markdown_output=markdown_output,
        )

    assert not json_output.exists()
    assert not markdown_output.exists()


def test_cli_complete_scan_writes_byte_identical_safe_receipts(
    tmp_path: Path,
) -> None:
    private, public, sentinel, sensitive_url = _create_inventory_repositories(tmp_path)
    policy_path = _write_policy(tmp_path)
    json_output = tmp_path / "evidence" / "baseline.json"
    markdown_output = tmp_path / "evidence" / "baseline.md"
    command = [
        sys.executable,
        str(SCRIPT),
        "--repo",
        str(private),
        "--public-candidate",
        str(public),
        "--policy",
        str(policy_path),
        "--format",
        "json",
        "--json-output",
        str(json_output),
        "--markdown-output",
        str(markdown_output),
    ]

    first = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    first_json = json_output.read_bytes()
    first_markdown = markdown_output.read_bytes()
    second = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert first.returncode == 0
    assert second.returncode == 0
    assert first.stderr == ""
    assert second.stderr == ""
    assert first.stdout == second.stdout
    assert first_json == json_output.read_bytes()
    assert first_markdown == markdown_output.read_bytes()
    combined = first.stdout + first.stderr + second.stdout + second.stderr
    combined += json_output.read_text(encoding="utf-8")
    combined += markdown_output.read_text(encoding="utf-8")
    for forbidden in (
        sentinel,
        sensitive_url,
        str(private),
        str(public),
        "dirty-private-name.txt",
        "secret.env",
    ):
        assert forbidden not in combined


def test_cli_incomplete_or_unsafe_scan_prints_only_fixed_error(
    tmp_path: Path,
) -> None:
    public = tmp_path / "public"
    _initialize_repository(public)
    (public / "README.md").write_text("public\n", encoding="utf-8")
    _git(public, "add", "README.md")
    _git(public, "commit", "-m", "public")
    secret_path_fragment = "S36-CLI-PRIVATE-CUSTOMER"
    missing = tmp_path / secret_path_fragment
    policy_path = _write_policy(tmp_path)
    json_output = tmp_path / "must-not-exist.json"
    markdown_output = tmp_path / "must-not-exist.md"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(missing),
            "--public-candidate",
            str(public),
            "--policy",
            str(policy_path),
            "--json-output",
            str(json_output),
            "--markdown-output",
            str(markdown_output),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "exposure inventory: unable to produce a safe receipt\n"
    assert secret_path_fragment not in result.stderr
    assert str(public) not in result.stderr
    assert not json_output.exists()
    assert not markdown_output.exists()
