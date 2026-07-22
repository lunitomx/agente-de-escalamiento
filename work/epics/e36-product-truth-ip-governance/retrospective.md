# Epic Retrospective: E36 Product Truth, IP Boundary & Governance

**Completed:** 2026-07-21
**Duration:** 10h 18m 53s at the closure-audit snapshot
**Stories:** 6 stories delivered

---

## Summary

E36 established the trustworthy foundation for ESCALA Local V2: one canonical
private source, sanitized exposure evidence, a current-tree reference boundary,
typed fail-closed governance, unique epic identities, an independently verified
allowlisted local artifact, and a 42-requirement acceptance control plane for
E37-E42. The epic closes without claiming future product functionality, legal
approval, or publication: the current master ledger remains correctly `0/42`,
human legal review remains required, and publication authorization is false.

The final private synchronization was performed only after explicit owner
authorization. A new untracked repository-truth receipt proves local `main` and
private `origin/main` are `0/0` at
`1d6a977f468ab38f3ca6c37d5af47025af9e8371`, all seven repository checks pass,
and there are zero findings. Its JSON SHA-256 is
`30299e095544aebd02203dd81b674a8cfeecc8d1ea8cae7be83e92923ca9a1c6`; the
Markdown SHA-256 is
`dc03a25a9d1625b18ee4447f882f329fd4f1ec064ef2138d1f5dde352aaa13e5`.

## Metrics

| Metric | Value | Notes |
|---|---:|---|
| Stories delivered | 6 | 2 S, 3 M, 1 L |
| Story points | N/A | E36 did not define a point scale; none is invented here |
| Test functions added | 140 | Git comparison: 64 before E36, 204 before the close commit |
| Recorded story-cycle sum | 6h 41m 27s | Sum of the six scope-tracking actuals |
| Mean observed story cycle | 1h 06m 55s | Descriptive only; sizes are not interchangeable |
| Epic elapsed time | 10h 18m 53s | `81561eb` at 12:51:16 to the closure-audit snapshot at 23:10:09 |
| Commits in epic snapshot | 81 | From `81561eb` through pre-close `1d6a977` |
| Repository delta | 407 files | 49,484 insertions and 1,339 deletions before close docs |

### Story Breakdown

| Story | Size | Actual | Key learning |
|---|:---:|---:|---|
| S36.1 Canonical Repository & Remote Truth | S | 44m 06s | Tracking configuration is not synchronization; equality requires an authorized push and a fresh sanitized receipt. |
| S36.2 Exposure Inventory | M | 47m 32s | Machine completeness and bounded human evidence need separate renderers. |
| S36.3 Reference & Public Vocabulary Boundary | M | 1h 53m 12s | Candidate-public is a canary, not an allowlist; module provenance must be asserted when roots collide. |
| S36.4 Typed Governance & Unique IDs | M | 1h 05m 33s | Filesystem-derived identities require atomic collision repair and a real installed graph build. |
| S36.5 Clean Export Contract | L | 1h 21m 21s | Exact staged bytes and an independent verifier expose defects that fixtures miss. |
| S36.6 Master Acceptance Ledger | S | 49m 43s | Contract validity, mission readiness, legal state, and publication authority are separate facts. |

## Scope and Done-Criteria Audit

### Mandatory scope

| Commitment | Verdict | Observable evidence |
|---|---|---|
| Establish private `origin/main` truth and remove unsafe local remote configuration | Fulfilled | Policy and verifier pass; only `origin` remains; `main` tracks `origin/main`; final receipt is `0/0` with zero findings. |
| Remove the raw reference asset from the current tree without rewriting history | Fulfilled | Deletion commit `e31914e`; absent from HEAD and present in its parent; reachable history retained. |
| Define public vocabulary and deny-by-default export | Fulfilled | Strict public-boundary and public-export policies; current boundary receipt PASS; generated artifact is allowlist-only. |
| Eliminate ambiguous canonical epic identity and create one typed closure contract | Fulfilled | Ten unique E1801-E2202 identities, explicit legacy ambiguities, one closure-disposition authority, and strict graph PASS. |
| Record E37-E42 acceptance ledger and invariants | Fulfilled | 42 unique requirements across six epics with owners, evidence declarations, gates, platforms, blockers, and human/machine parity. |
| Preserve installer-machine execution and filesystem-only team exchange | Fulfilled | Export and ledger authorities forbid hosted service, cloud database, Drive/OneDrive APIs, OAuth, telemetry, and synchronized authoritative SQLite. |

The two SHOULD commitments are also fulfilled technically: a 13-entry
third-party/license inventory is ready for human legal review, and deterministic
scanners/gates cover references, credentials, private paths, public artifacts,
and governance ambiguity. This is not a legal conclusion.

### Done Criteria

| # | Criterion | Verdict | Evidence |
|:--:|---|---|---|
| 1 | Local and private canonical branch identical | Proved | Final repository-truth receipt: 7/7 checks, `0/0`, zero findings, empty stderr. |
| 2 | Raw asset absent current tree with auditable deletion | Proved | `e31914e`; current-tree count zero; parent/history evidence retained. |
| 3 | Exposure distinguishes current, history, and export | Proved | S36.2 baseline plus current public-boundary receipt: current absent, history historical, export independently classified. |
| 4 | No embedded real credential in tracked/distributable content | Proved | Current exposure scan completed with zero errors and no remote credential. Four unique secret-shaped hits were synthetic detector/verifier fixtures in two tests; independent artifact check `credentials` passes. |
| 5 | Public export rejects prohibited/private/non-allowlisted material | Proved | Current private boundary PASS; existing public candidate remains unresolved and unchanged; artifact `public_boundary` and `path_set` checks pass. |
| 6 | One typed closure contract | Proved | Canonical YAML, typed consumer, positive/negative gates, and no permissive normalization fallback. |
| 7 | No duplicate canonical legacy epic IDs | Proved | Strict current graph build: 38 epics, 226 concepts, zero duplicate failure. |
| 8 | Real clean-export dry run passes | Proved | Current-HEAD 264-file build and independent verifier: 10/10 checks, zero violations. |
| 9 | E37-E42 ledger complete | Proved | Contract PASS, six epics, 42 requirements, all correctly unproved until downstream evidence exists. |
| 10 | Quality gates pass | Proved | Focused gates before task commits and 15/15 story-close gates for every story; final epic-close gates run again before final push. |

### Elimination commitments

- **Raw asset removal — fulfilled:** the current tree no longer contains the
  asset; history is intentionally not rewritten.
- **Ambiguous canonical IDs — fulfilled:** all ten colliding folders have unique
  identities; bare legacy IDs fail closed as declared ambiguities.
- **Obsolete remote removal — fulfilled:** only the canonical private remote is
  configured and its upstream is explicit.
- **No destructive cleanup claimed:** private history and the existing public
  candidate remain separate observed surfaces, not silently rewritten.

## What Went Well

- Risk-first sequencing preserved the original exposure baseline before
  remediation and converged repository/content/governance work only at the real
  artifact gate.
- TDD plus live integration found issues that green isolated fixtures missed:
  evidence volume, inherited Git environment, tracked bytecode, receipt
  self-reference, package metadata, duplicate module provenance, incomplete
  human rendering, and broken symlink outputs.
- Every external or dirty subject was fingerprinted before and after. The
  existing public candidate remained unchanged throughout E36.
- Builder and verifier stayed independent. The final current-HEAD artifact has
  264 files and passes artifact root, credentials, dependencies, integrity,
  license posture, local-only, manifest, metadata, path-set, and public-boundary
  checks.
- The acceptance ledger prevents plans, old DONE labels, code presence, or
  reviewable non-complete states from becoming false delivery claims.

## What Could Be Improved

- All 20 expected lifecycle learning records were absent: epic design/plan plus
  design/plan/implement for six stories. Retrospectives had to report formal
  acceptance, gap, and utility metrics as `N/A`.
- Graph retrieval was weak for the actual governance/export domain. Two epic
  PRIME queries returned 15 result instances and three JIT queries returned 17,
  but none covered the exact closure topics.
- The gate runner repeatedly generated unowned `.coverage`/`uv.lock` artifacts.
  An explicit local drift-baseline command completed but scanned `0` modules,
  so it is recorded as unusable rather than presented as architecture evidence.
- Session-filtered signal queries appear stale when the active session ID is not
  exported, even when the latest unfiltered event is correct.
- CLI help for the clean-export builder should state that `--repo` must be
  absolute. A relative-path audit invocation failed safely although the same
  current commit built and verified successfully with the documented internal
  contract.

## Patterns Discovered

| ID | Pattern | Context |
|---|---|---|
| PAT-L-1280 | Generate remote-equality evidence only after an authorized private push. | Canonical repository closure |
| PAT-L-1281 | Dirty-repository non-mutation needs worktree, config, index, refs, HEAD, and status hashes. | External/local evidence subjects |
| PAT-L-1291 | Candidate-public is a canary, never an implicit allowlist. | Public-boundary and export work |
| PAT-L-1295 | Bind evidence to the preceding green source and prove later determinism separately. | Non-self-referential receipts |
| PAT-L-1296 | Clean-export PASS requires exact staged bytes plus an independent verifier and tamper proof. | Distribution qualification |
| PAT-L-1298 | Technical PASS, legal review, and publication authorization are distinct typed states. | Release governance |
| PAT-L-1300 | A valid `0/N` ledger can pass contract validation but cannot pass readiness. | Master-plan control |
| PAT-L-1301 | Human acceptance views must preserve all decision-bearing machine facts. | Review and audit artifacts |

E36 produced 20 reusable project patterns across its six story reviews. Formal
lifecycle learning metrics remain `N/A` because their source records are
missing; review-local votes are not substituted for absent denominators.

## Process Insights

- RaiSE's lifecycle gates worked best when plans declared the exact real-world
  integration checkpoint, not merely unit-test completion.
- Jidoka prevented four false closes: excessive evidence output, a Python
  provenance defect, incomplete human ledger truth, and remote divergence.
- Exact staging preserved intentional dirty work across 81 commits and avoided
  accidental inclusion of generated lock/coverage files.
- Human authorization was needed only at the material external boundary. Once
  granted, the private push and `0/0` receipt were executed directly without a
  public release or repeated routine prompts.

## Artifacts

- **Scope:** `work/epics/e36-product-truth-ip-governance/scope.md`
- **Brief:** `work/epics/e36-product-truth-ip-governance/brief.md`
- **ADR:** `work/epics/e36-product-truth-ip-governance/adr-private-canonical-source-and-clean-export.md`
- **Stories:** `work/epics/e36-product-truth-ip-governance/stories/`
- **Acceptance ledger:** `work/epics/e36-product-truth-ip-governance/master-acceptance-ledger.yaml`
- **Governance:** repository truth, exposure, public boundary/export, closure dispositions, epic identities, and third-party inventory under `governance/`
- **Tests:** 140 additional test functions in the E36 Git snapshot
- **Final remote receipt:** untracked by design; hashes recorded above and in session journal `JRN-138`

## Closure Boundaries

- Human legal/IP review is still required; approval evidence is absent.
- Publication authorization is false and no public release or public-repository
  push occurred.
- The existing public candidate retains 209 legacy policy findings and remains
  an unchanged evidence canary, not the generated artifact.
- The product and authoritative data remain local to the installer machine;
  Drive/OneDrive are ordinary filesystem exchange only and authoritative SQLite
  is never synchronized.
- E36 completes the trust foundation only. E37-E42 remain `0/42` until their
  exact functionality and qualification evidence are delivered.

## Next Steps

- Start E37 Local Workspace & Flexible Ingestion under the master ledger.
- Prove each E37 requirement with source-bound receipts instead of changing
  ledger state from plans or code presence.
- Preserve the local-only, filesystem-sharing, no-synced-SQLite, legal, and
  publication authorities through E37-E42.
