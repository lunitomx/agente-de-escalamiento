---
story_id: "S36.2"
evidence_type: "live-exposure-baseline"
created: "2026-07-21"
scan_status: "complete"
---

# S36.2 Live Exposure Baseline

## Receipt

- Verifier source commit: `e863f781600a99c476e0f1182ddcc8552983b7e3`
- Policy SHA-256: `7eec173c0b2a132b15a3a1dfda8cfdeeac36e27621a1bf5a70a0fe37b61c7b0c`
- Scan status: `complete`
- Scan errors: `0`
- Detailed findings: `2126`
- Machine ledger: `baseline.json` (`729130` bytes)
- Human summary: `baseline.md` (`3040` bytes)

The scan completed every bounded surface. Content that could not be decoded or
was outside configured size limits remains counted as unscanned; therefore this
receipt does not claim that the repositories are secret-free or distribution
eligible.

## Risk and disposition

| Dimension | Value | Count |
|---|---|---:|
| Severity | `critical` | 27 |
| Severity | `high` | 598 |
| Severity | `medium` | 1501 |
| Classification | `raw_reference` | 3 |
| Classification | `derived_reference` | 36 |
| Classification | `public_vocabulary` | 562 |
| Classification | `private_data` | 24 |
| Classification | `internal_path` | 1501 |
| Disposition | `remove_in_s36_3` | 3 |
| Disposition | `review_in_s36_3` | 598 |
| Disposition | `block_in_s36_5` | 1525 |

No credential-risk finding was emitted. This means no configured rule produced
a credential finding on the successfully inspected content; it is not a claim
about the unscanned content.

## Surface coverage

| Surface | Items | Unscanned | Result |
|---|---:|---:|---|
| `worktree` | 1175 | 7 | inspected |
| `git_head` | 1175 | 8 | inspected |
| `git_history` | 1304 | 0 | inspected metadata |
| `local_git_config` | 1 | 0 | inspected safely |
| `distribution_candidate` | 1175 | 0 | inventoried |
| `public_candidate` | 173 | 0 | canonical HEAD inspected |

The raw reference is absent from the worktree, present in canonical `HEAD`, and
historical in Git metadata. Its intentional worktree deletion remained
unstaged; S36.3 owns the auditable canonical-tree removal.

## Distribution boundary

- Default eligibility: `not_eligible`
- Generated staging: `not_built`
- Tracked path count: `1175`
- Tracked path-set SHA-256:
  `12f6baae02073f005bd26efa5901ae19582ee0863fc04bb48a4e8772ee84feca`

These findings are inventory inputs for S36.3 and S36.5. They are not proof of
remediation, export cleanliness, or public-release readiness.

## Non-mutation proof

The private repository fingerprint was byte-identical before and after the
scan: branch, `HEAD`, dirty-entry count, status hash, worktree hash, Git-config
hash, index hash, and refs hash all matched. Its dirty-entry count remained `1`.

The public candidate fingerprint was also byte-identical before and after the
scan across the same dimensions. Its dirty-entry count remained `17`, and the
scanner made no changes to that repository.

## Human-summary correction

The first complete scan produced a `359376`-byte Markdown file because it
repeated every machine finding. The renderer was corrected before this receipt:
the JSON retains the detailed remediation ledger while Markdown groups findings
by safe dimensions and omits locators. The final Markdown is `3040` bytes.

Focused tests, lint, format, and type gates passed after that correction and
after the final live-baseline generation.
