from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

import pytest
from pydantic import ValidationError
import yaml

import validators.public_boundary as boundary_module
from validators.public_boundary import (
    BoundaryFindingCode,
    BoundaryLocatorKind,
    BoundaryStatus,
    BoundarySurface,
    PublicCandidateStatus,
    PublicBoundaryFinding,
    PublicPathDisposition,
    classify_public_path,
    group_boundary_findings,
    load_exposure_baseline_link,
    load_public_boundary_policy,
    public_boundary_policy_hash,
    render_public_boundary_json,
    render_public_boundary_markdown,
    scan_public_boundary,
    write_public_boundary_receipts,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "governance/public-boundary.yaml"
BASELINE_PATH = (
    ROOT
    / "work/epics/e36-product-truth-ip-governance/stories"
    / "s36.2-evidence/baseline.json"
)
BASELINE_SHA256 = "3ae688c34b8cb13dcf96bd72198aeee6e4eace0a432b413cc654d1c279943dce"
SCRIPT = ROOT / "scripts/check_public_boundary.py"
RAW_ASSET_PATH = (
    "Verne Harnish - Scaling Up_ How a Few Companies Make It...and Why the Rest "
    "Don't (Rockefeller Habits 2.0)-Gazelles, Inc. (2014).pdf"
)


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
    _git(repository, "config", "user.email", "boundary@example.invalid")
    _git(repository, "config", "user.name", "Boundary Tests")


def _create_boundary_repositories(
    tmp_path: Path,
    *,
    raw_in_head: bool,
) -> tuple[Path, Path, str]:
    private = tmp_path / "private-repository"
    public = tmp_path / "public-candidate"
    sentinel = "S36-PUBLIC-BOUNDARY-SENTINEL-123456789"

    _initialize_repository(private)
    (private / "README.md").write_text(
        "Local business operating system\n",
        encoding="utf-8",
    )
    (private / RAW_ASSET_PATH).write_bytes(b"%PDF-private-reference\x00")
    _git(private, "add", "README.md", RAW_ASSET_PATH)
    _git(private, "commit", "-m", "private baseline")
    (private / RAW_ASSET_PATH).unlink()
    if not raw_in_head:
        _git(private, "add", "-u")
        _git(private, "commit", "-m", "remove current raw asset")

    _initialize_repository(public)
    (public / "README.md").write_text(
        "Gazelles legacy public candidate\n",
        encoding="utf-8",
    )
    _git(public, "add", "README.md")
    _git(public, "commit", "-m", "public baseline")
    (public / "dirty-private-name.txt").write_text(sentinel, encoding="utf-8")

    return private, public, sentinel


def test_real_git_scan_keeps_current_history_and_public_candidate_distinct(
    tmp_path: Path,
) -> None:
    private, public, sentinel = _create_boundary_repositories(
        tmp_path,
        raw_in_head=True,
    )
    policy = load_public_boundary_policy(POLICY_PATH)

    receipt = scan_public_boundary(
        private,
        public,
        policy,
        baseline_path=BASELINE_PATH,
    )
    serialized = receipt.model_dump_json()

    assert receipt.status is BoundaryStatus.FAIL
    assert receipt.errors == []
    assert receipt.verifier_source_commit == _git(private, "rev-parse", "HEAD")
    assert receipt.raw_asset is not None
    assert receipt.raw_asset.model_dump(mode="json") == {
        "worktree": "absent",
        "git_head": "present",
        "git_history": "historical",
    }
    assert receipt.public_candidate_status is (
        PublicCandidateStatus.LEGACY_FINDINGS_UNRESOLVED
    )
    assert receipt.public_candidate_finding_count == 1
    assert receipt.path_summary is not None
    assert receipt.path_summary.candidate_public_count == 1
    assert receipt.path_summary.denied_count == 1
    assert receipt.path_summary.not_eligible_count == 0
    assert receipt.private_repository is not None
    assert receipt.private_repository.unchanged is True
    assert receipt.public_candidate is not None
    assert receipt.public_candidate.unchanged is True
    assert (public / "dirty-private-name.txt").read_text(encoding="utf-8") == sentinel
    assert any(
        finding.code is BoundaryFindingCode.RAW_ASSET_TRACKED
        and finding.locator_kind is BoundaryLocatorKind.SHA256
        for finding in receipt.findings
    )
    for forbidden in (
        sentinel,
        "Gazelles",
        RAW_ASSET_PATH,
        str(private),
        str(public),
        "dirty-private-name.txt",
    ):
        assert forbidden not in serialized


def test_scan_ignores_inherited_git_environment_and_dirty_public_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private, public, sentinel = _create_boundary_repositories(
        tmp_path / "target",
        raw_in_head=False,
    )
    decoy, _, _ = _create_boundary_repositories(
        tmp_path / "decoy",
        raw_in_head=True,
    )
    injected = "S36-INJECTED-GIT-SECRET"
    expected_head = _git(private, "rev-parse", "HEAD")
    monkeypatch.setenv("GIT_DIR", str(decoy / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(decoy))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "remote.injected.url")
    monkeypatch.setenv(
        "GIT_CONFIG_VALUE_0",
        f"https://{injected}@example.invalid/private.git",
    )

    receipt = scan_public_boundary(
        private,
        public,
        load_public_boundary_policy(POLICY_PATH),
        baseline_path=BASELINE_PATH,
    )
    serialized = receipt.model_dump_json()

    assert receipt.status is BoundaryStatus.PASS
    assert receipt.verifier_source_commit == expected_head
    assert injected not in serialized
    assert sentinel not in serialized


def test_worktree_and_head_content_are_scanned_as_independent_surfaces(
    tmp_path: Path,
) -> None:
    private, public, _ = _create_boundary_repositories(
        tmp_path,
        raw_in_head=False,
    )
    (private / "README.md").write_text(
        "Gazelles appears only in the dirty worktree\n",
        encoding="utf-8",
    )

    receipt = scan_public_boundary(
        private,
        public,
        load_public_boundary_policy(POLICY_PATH),
        baseline_path=BASELINE_PATH,
    )

    assert receipt.status is BoundaryStatus.FAIL
    private_source_findings = [
        finding
        for finding in receipt.findings
        if finding.rule_id == "public.company_identity"
        and finding.surface is not BoundarySurface.PUBLIC_CANDIDATE_HEAD
    ]
    assert [finding.surface for finding in private_source_findings] == [
        BoundarySurface.PRIVATE_WORKTREE
    ]


def test_candidate_path_text_and_yaml_provenance_are_detected_without_values(
    tmp_path: Path,
) -> None:
    private, public, _ = _create_boundary_repositories(
        tmp_path,
        raw_in_head=False,
    )
    named_path = private / "coaching/scaling_up-guide.md"
    named_path.parent.mkdir(parents=True)
    named_path.write_text("Use VerneHandler here\n", encoding="utf-8")
    yaml_path = private / "conocimiento/node.yaml"
    yaml_path.parent.mkdir(parents=True)
    yaml_path.write_text(
        "id: node\nsource: S36-PRIVATE-PROVENANCE-VALUE\n",
        encoding="utf-8",
    )
    _git(
        private,
        "add",
        named_path.relative_to(private).as_posix(),
        yaml_path.relative_to(private).as_posix(),
    )
    _git(private, "commit", "-m", "add prohibited candidate fixtures")

    receipt = scan_public_boundary(
        private,
        public,
        load_public_boundary_policy(POLICY_PATH),
        baseline_path=BASELINE_PATH,
    )
    serialized = receipt.model_dump_json()

    assert receipt.status is BoundaryStatus.FAIL
    assert {
        BoundaryFindingCode.PROHIBITED_PATH,
        BoundaryFindingCode.PROHIBITED_TEXT,
        BoundaryFindingCode.PROHIBITED_YAML_KEY,
    } <= {finding.code for finding in receipt.findings}
    assert all(
        finding.locator_kind is BoundaryLocatorKind.SHA256
        for finding in receipt.findings
        if finding.code is BoundaryFindingCode.PROHIBITED_PATH
    )
    assert "S36-PRIVATE-PROVENANCE-VALUE" not in serialized
    assert "scaling_up-guide" not in serialized


def test_missing_repository_returns_sanitized_incomplete_receipt(
    tmp_path: Path,
) -> None:
    _, public, _ = _create_boundary_repositories(
        tmp_path / "valid",
        raw_in_head=False,
    )
    secret_fragment = "S36-PRIVATE-MISSING-CUSTOMER"
    missing = tmp_path / secret_fragment

    receipt = scan_public_boundary(
        missing,
        public,
        load_public_boundary_policy(POLICY_PATH),
        baseline_path=BASELINE_PATH,
    )

    assert receipt.status is BoundaryStatus.INCOMPLETE
    assert receipt.private_repository is None
    assert secret_fragment not in receipt.model_dump_json()
    assert str(missing) not in repr(receipt)


def test_fingerprint_mismatch_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private, public, _ = _create_boundary_repositories(
        tmp_path,
        raw_in_head=False,
    )
    original = boundary_module.fingerprint_repository
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
        boundary_module,
        "fingerprint_repository",
        mismatching_fingerprint,
    )

    receipt = scan_public_boundary(
        private,
        public,
        load_public_boundary_policy(POLICY_PATH),
        baseline_path=BASELINE_PATH,
    )

    assert receipt.status is BoundaryStatus.INCOMPLETE
    assert receipt.private_repository is not None
    assert receipt.private_repository.unchanged is False
    assert any(error.code.value == "fingerprint_mismatch" for error in receipt.errors)


def test_denied_and_unknown_binary_content_is_not_promoted_or_scanned(
    tmp_path: Path,
) -> None:
    private, public, _ = _create_boundary_repositories(
        tmp_path,
        raw_in_head=False,
    )
    denied = private / "escala_server/data/private.bin"
    denied.parent.mkdir(parents=True)
    denied.write_bytes(b"Gazelles\x00private")
    unknown = private / "customer-private.bin"
    unknown.write_bytes(b"Gazelles\x00private")
    _git(private, "add", denied.relative_to(private).as_posix(), unknown.name)
    _git(private, "commit", "-m", "private denied and unknown content")

    receipt = scan_public_boundary(
        private,
        public,
        load_public_boundary_policy(POLICY_PATH),
        baseline_path=BASELINE_PATH,
    )

    assert receipt.status is BoundaryStatus.PASS
    assert receipt.path_summary is not None
    assert receipt.path_summary.denied_count == 1
    assert receipt.path_summary.not_eligible_count == 1
    assert all(
        finding.locator not in {denied.relative_to(private).as_posix(), unknown.name}
        for finding in receipt.findings
    )


@pytest.mark.parametrize("unsafe_kind", ["binary", "non_utf8", "oversized", "symlink"])
def test_required_worktree_or_head_content_fails_closed(
    tmp_path: Path,
    unsafe_kind: str,
) -> None:
    private, public, _ = _create_boundary_repositories(
        tmp_path,
        raw_in_head=False,
    )
    required = private / "coaching/required.md"
    required.parent.mkdir(parents=True)
    if unsafe_kind == "binary":
        required.write_bytes(b"required\x00binary")
    elif unsafe_kind == "non_utf8":
        required.write_bytes(b"required\xfftext")
    elif unsafe_kind == "oversized":
        required.write_bytes(b"x" * 1_048_577)
    else:
        target = private / "private-target.txt"
        target.write_text("private", encoding="utf-8")
        required.symlink_to(target)
    _git(private, "add", required.relative_to(private).as_posix())
    _git(private, "commit", "-m", f"add {unsafe_kind} required content")

    receipt = scan_public_boundary(
        private,
        public,
        load_public_boundary_policy(POLICY_PATH),
        baseline_path=BASELINE_PATH,
    )

    assert receipt.status is BoundaryStatus.INCOMPLETE
    assert any(
        finding.code is BoundaryFindingCode.UNSAFE_OR_UNREADABLE
        for finding in receipt.findings
    )


def test_malformed_required_yaml_fails_closed_without_serializing_values(
    tmp_path: Path,
) -> None:
    private, public, _ = _create_boundary_repositories(
        tmp_path,
        raw_in_head=False,
    )
    sentinel = "S36-MALFORMED-YAML-PRIVATE-VALUE"
    malformed = private / "conocimiento/bad.yaml"
    malformed.parent.mkdir(parents=True)
    malformed.write_text(f"source: [{sentinel}\n", encoding="utf-8")
    _git(private, "add", malformed.relative_to(private).as_posix())
    _git(private, "commit", "-m", "add malformed required yaml")

    receipt = scan_public_boundary(
        private,
        public,
        load_public_boundary_policy(POLICY_PATH),
        baseline_path=BASELINE_PATH,
    )

    assert receipt.status is BoundaryStatus.INCOMPLETE
    assert sentinel not in receipt.model_dump_json()


def test_renderers_and_writers_are_deterministic_bounded_and_safe(
    tmp_path: Path,
) -> None:
    private, public, sentinel = _create_boundary_repositories(
        tmp_path,
        raw_in_head=False,
    )
    receipt = scan_public_boundary(
        private,
        public,
        load_public_boundary_policy(POLICY_PATH),
        baseline_path=BASELINE_PATH,
    )
    json_output = tmp_path / "evidence/boundary.json"
    markdown_output = tmp_path / "evidence/boundary.md"

    first_json = render_public_boundary_json(receipt)
    first_markdown = render_public_boundary_markdown(receipt)
    write_public_boundary_receipts(
        receipt,
        json_output=json_output,
        markdown_output=markdown_output,
    )

    assert receipt.status is BoundaryStatus.PASS
    assert first_json == render_public_boundary_json(receipt)
    assert first_markdown == render_public_boundary_markdown(receipt)
    assert first_json == json_output.read_text(encoding="utf-8")
    assert first_markdown == markdown_output.read_text(encoding="utf-8")
    assert len(first_markdown.encode()) < 32 * 1024
    combined = first_json + first_markdown
    for forbidden in (
        sentinel,
        "Gazelles",
        RAW_ASSET_PATH,
        str(private),
        str(public),
        "dirty-private-name.txt",
    ):
        assert forbidden not in combined


def test_nonpassing_receipt_is_not_written(tmp_path: Path) -> None:
    private, public, _ = _create_boundary_repositories(
        tmp_path,
        raw_in_head=True,
    )
    receipt = scan_public_boundary(
        private,
        public,
        load_public_boundary_policy(POLICY_PATH),
        baseline_path=BASELINE_PATH,
    )
    json_output = tmp_path / "must-not-exist.json"
    markdown_output = tmp_path / "must-not-exist.md"

    with pytest.raises(ValueError, match="passing receipt"):
        write_public_boundary_receipts(
            receipt,
            json_output=json_output,
            markdown_output=markdown_output,
        )

    assert not json_output.exists()
    assert not markdown_output.exists()


def test_cli_writes_safe_receipts_and_failure_is_fixed(tmp_path: Path) -> None:
    private, public, sentinel = _create_boundary_repositories(
        tmp_path,
        raw_in_head=False,
    )
    json_output = tmp_path / "evidence/boundary.json"
    markdown_output = tmp_path / "evidence/boundary.md"
    command = [
        sys.executable,
        str(SCRIPT),
        "--repo",
        str(private),
        "--public-candidate",
        str(public),
        "--policy",
        str(POLICY_PATH),
        "--baseline",
        str(BASELINE_PATH),
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
    assert first.stderr == second.stderr == ""
    assert first.stdout == second.stdout
    assert first_json == json_output.read_bytes()
    assert first_markdown == markdown_output.read_bytes()
    assert sentinel not in first.stdout

    failed = subprocess.run(
        [
            *command[:2],
            "--repo",
            str(tmp_path / "S36-PRIVATE-MISSING-ROOT"),
            *command[4:],
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert failed.returncode == 1
    assert failed.stdout == ""
    assert (
        failed.stderr == "public boundary: unable to produce a safe passing receipt\n"
    )
    assert "S36-PRIVATE-MISSING-ROOT" not in failed.stderr


def test_runtime_identity_migration_paths_and_handler_are_atomic() -> None:
    tracked = set(_git(ROOT, "ls-files").splitlines())
    migrations = {
        "conocimiento/execution/tools/rockefeller-habits.yaml": (
            "conocimiento/execution/tools/execution-habits.yaml"
        ),
        "conocimiento/execution/worksheets/rockefeller-habits.yaml": (
            "conocimiento/execution/worksheets/execution-habits.yaml"
        ),
        "conocimiento/coaching/verne-templates.yaml": (
            "conocimiento/coaching/advisor-templates.yaml"
        ),
        "escala_server/verne_handler.py": "escala_server/business_advisor.py",
        "escala_server/static/dashboards/execution/rockefeller-habits.html": (
            "escala_server/static/dashboards/execution/execution-habits.html"
        ),
        "templates/rockefeller-habits-checklist.md": (
            "templates/execution-habits-checklist.md"
        ),
        "tests/test_verne_handler.py": "tests/test_business_advisor.py",
    }

    for old_path, new_path in migrations.items():
        assert old_path not in tracked
        assert new_path in tracked

    assert importlib.util.find_spec("escala_server.verne_handler") is None
    module = importlib.import_module("escala_server.business_advisor")
    assert hasattr(module, "BusinessAdvisorHandler")
    assert not hasattr(module, "VerneHandler")


def test_execution_identity_migration_keeps_graph_and_registry_resolvable() -> None:
    tool_path = ROOT / "conocimiento/execution/tools/execution-habits.yaml"
    worksheet_path = ROOT / "conocimiento/execution/worksheets/execution-habits.yaml"
    registry_path = ROOT / "conocimiento/registry/worksheets.yaml"

    tool = yaml.safe_load(tool_path.read_text(encoding="utf-8"))
    worksheet = yaml.safe_load(worksheet_path.read_text(encoding="utf-8"))
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))

    assert tool["id"] == "tool-execution-habits"
    assert worksheet["id"] == "worksheet-execution-habits"
    assert "worksheet-execution-habits" in {
        relation["target"] for relation in tool["relationships"]
    }
    assert "tool-execution-habits" in {
        relation["target"] for relation in worksheet["relationships"]
    }
    registry_entry = next(
        entry
        for entry in registry["worksheets"]
        if entry["id"] == "worksheet-execution-habits"
    )
    assert registry_entry["node_path"] == "execution/worksheets/execution-habits.yaml"
    assert worksheet_path.exists()


def test_runtime_callers_use_only_source_neutral_migration_symbols() -> None:
    runtime_files = [
        ROOT / "coaching/diagnose/__init__.py",
        ROOT / "conocimiento/decisions/execution.yaml",
        ROOT / "conocimiento/execution/metrics/meeting-health-score.yaml",
        ROOT / "conocimiento/registry/worksheets.yaml",
        ROOT / "escala_server/business_advisor.py",
        ROOT / "escala_server/cash/generate_dashboards.py",
        ROOT / "escala_server/cli.py",
        ROOT / "escala_server/server.py",
        ROOT / "escala_server/static/dashboards/execution/execution-habits.html",
        ROOT / "escala_server/static/shared/js/context-panel.js",
    ]
    prohibited_migration_tokens = (
        "VerneHandler",
        "verne_handler",
        "tool-rockefeller-habits",
        "worksheet-rockefeller-habits",
        "rockefeller-habits.html",
        "rockefeller-habits-checklist.md",
    )

    for path in runtime_files:
        content = path.read_text(encoding="utf-8")
        assert all(token not in content for token in prohibited_migration_tokens)

    assert "BusinessAdvisorHandler" in (ROOT / "escala_server/server.py").read_text(
        encoding="utf-8"
    )
    assert "execution-habits" in (
        ROOT / "escala_server/static/shared/js/context-panel.js"
    ).read_text(encoding="utf-8")
