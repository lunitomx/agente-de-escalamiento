---
epic_id: "E36"
title: "Product Truth, IP Boundary & Governance"
status: "active"
created: "2026-07-21"
mission: "escala-local-v2-plan-maestro-2607202112"
---

# Epic Scope: E36 — Product Truth, IP Boundary & Governance

## Objective

Create the trustworthy foundation for ESCALA Local V2: one canonical private
repository, an explicit intellectual-property and secret boundary, unambiguous
governance identities, and deterministic gates that prevent unsafe material or
false completion claims from entering a distributable product.

## Value

- **For the owner:** company information remains local and every distributable
  artifact has a verifiable origin.
- **For the product team:** one private source replaces manual synchronization
  between divergent repositories.
- **For future epics:** E37-E42 inherit executable no-host, evidence, identity,
  and release contracts instead of prose-only assumptions.

## Architectural Invariants

1. ESCALA runs on the machine of the person who installs it.
2. SQLite and canonical company state remain local to the owner machine.
3. A SQLite database is never synchronized through Drive or OneDrive.
4. Teams exchange inbox files and scoped reports through a user-controlled local
   sync folder; there is no hosted ESCALA service.
5. Public distribution is generated from an allowlisted export, never by making
   the private development repository public.
6. A governance status is fail-closed: unknown, incomplete, unproved, and
   terminal-discarded states cannot be inferred as complete.

## In Scope

- Canonical repository and remote-tracking truth.
- Current-tree removal of prohibited raw reference assets.
- Reference, credential, private-data, and public-surface inventory.
- Public vocabulary rules and distribution denylist.
- Typed closure-disposition taxonomy consumed by validators and tests.
- Unique canonical epic identities plus explicit legacy aliases.
- Clean-export manifest, license posture, third-party inventory, and verifier.
- E37-E42 acceptance ledger with evidence requirements and ownership.

## Out of Scope

- Destructive rewrite of private Git history.
- Public release or migration of a public repository.
- Local database/runtime redesign, file ingestion, OCR, financial calculations,
  dashboards, meeting automation, synced-folder processors, or installers.
- Multi-writer collaboration, SaaS, hosted APIs, or cloud databases.
- Final legal approval of a software license.

## Planned Stories

| ID | Story | Size | Depends on | Outcome |
|---|---|---:|---|---|
| S36.1 | Canonical Repository & Remote Truth | S | — | `origin/main`, branch policy, and private/public roles are explicit and verifiable. |
| S36.2 | IP, Secret & Reference Exposure Inventory | M | S36.1 | Current tree, history, remotes, distributable paths, and generated artifacts have a risk-classified inventory. |
| S36.3 | Reference Removal & Public Vocabulary | M | S36.2 | Raw source deletion is committed and prohibited public-facing references are removed or blocked. |
| S36.4 | Typed Governance Taxonomy & Unique IDs | M | S36.1 | One fail-closed disposition model and collision-free canonical epic identity feed validators and graph build. |
| S36.5 | Clean Export, License & Third-Party Contract | L | S36.2, S36.3, S36.4 | Allowlist, denylist, license posture, notices, and deterministic export verification are executable. |
| S36.6 | Master Acceptance Ledger | S | S36.4, S36.5 | E37-E42 requirements, evidence, gates, owners, and no-host invariants are baselined. |

## Done Criteria

- [ ] Local `main` and canonical private `origin/main` are identical and the
      active upstream cannot silently target the obsolete remote.
- [ ] The raw reference-book file is absent from the current canonical tree and
      the commit preserves an auditable deletion record.
- [ ] A history/exposure report distinguishes current-tree removal, private
      historical presence, and public-export eligibility without claiming an
      unperformed history rewrite.
- [ ] Secret scanning finds no embedded credential in tracked content or
      distributable configuration; unsafe local remote URLs are sanitized.
- [ ] Public-facing export rules reject prohibited source/author/book references,
      private paths, company data, and non-allowlisted files.
- [ ] Closure dispositions come from one typed contract and all positive and
      negative governance tests pass.
- [ ] Knowledge-graph build reports no duplicate canonical epic IDs for legacy
      E18-E22 folders.
- [ ] A clean-export dry run passes its manifest, license, third-party notice,
      reference, secret, and provenance checks without publishing externally.
- [ ] E37-E42 acceptance ledger maps every master-plan requirement to evidence
      and an owning epic/story.
- [ ] Test, lint, format, and type gates pass before every commit.

## Acceptance Evidence

- Repository/remote audit with sanitized output.
- IP/reference/secret exposure report and machine-readable findings.
- Typed governance model plus regression tests.
- Collision-free graph-build receipt.
- Clean-export manifest, dry-run artifact inventory, and verifier receipt.
- Master acceptance ledger linking E37-E42.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Historical source material is confused with current public eligibility | High | Report history truth separately; export from an allowlist. |
| Debranding removes useful business concepts | High | Change public attribution/vocabulary, not verified product capabilities. |
| Legacy ID repair breaks old links | Medium | Preserve explicit aliases and test resolution before renaming. |
| Secret scan exposes a credential in logs | High | Emit redacted metadata only; rotate outside code if a live secret is found. |
| Governance work expands into product rebuild | Medium | Enforce story boundaries and defer runtime work to E37-E41. |

## Implementation Plan

> Added by `/rai-epic-plan` — 2026-07-21. No historical velocity or epic-plan
> learning record was available, so sequence checkpoints replace invented
> calendar estimates. Actual effort will be recorded after each story.

### Sequencing Strategy

E36 uses risk-first and dependency-driven sequencing. Repository truth must be
repaired before evidence is captured; the broad exposure inventory runs before
public vocabulary is changed so the baseline is not lost. Governance taxonomy
can proceed in parallel after S36.1, but both streams must converge before the
clean-export integration story.

The critical path is:

`S36.1 → S36.2 → S36.3 → S36.5 → S36.6`

S36.4 is a required parallel path:

`S36.1 → S36.4 → S36.5 → S36.6`

### Story Sequence

| Order | Story | Size | Dependencies | Milestone | Rationale and what it enables |
|:-----:|-------|:----:|--------------|-----------|-------------------------------|
| 1 | S36.1 Canonical Repository & Remote Truth | S | None | M1 | Removes ambiguity and unsafe upstream configuration; gives every later receipt a trustworthy source commit. |
| 2 | S36.2 IP, Secret & Reference Exposure Inventory | M | S36.1 | M1 | Tackles the largest unknown early and captures current tree/history/export surfaces before remediation changes them. |
| 3 | S36.4 Typed Governance Taxonomy & Unique IDs | M | S36.1 | M2 | Can run independently of content remediation; provides fail-closed contracts needed by export and acceptance evidence. |
| 4 | S36.3 Reference Removal & Public Vocabulary | M | S36.2 | M2 | Uses the classified baseline to commit the intended raw-asset deletion and change/block only the public surface. |
| 5 | S36.5 Clean Export, License & Third-Party Contract | L | S36.2, S36.3, S36.4 | M3 | Integrates repository truth, classifications, governance, metadata, builder, and staged-artifact verifier in one real local flow. |
| 6 | S36.6 Master Acceptance Ledger | S | S36.4, S36.5 | M4 | Binds E37-E42 requirements to evidence after the contracts they reference actually exist. |

### Milestones

| Milestone | Stories | Target checkpoint | Success criteria | Demonstrable capability |
|-----------|---------|-------------------|------------------|--------------------------|
| **M1: Trust Baseline** | S36.1, S36.2 | Before remediation | Canonical upstream is safe; sanitized inventories distinguish current tree, history, local configuration, candidate public tree, and generated staging. | Reproduce where each risk exists without leaking a credential or remote URL. |
| **M2: Enforceable Boundary** | S36.4, S36.3 | Before export integration | One typed fail-closed closure contract; collision-free canonical IDs; raw source absent from current tree; public vocabulary rules executable. | Demonstrate positive/negative governance and public-boundary tests. |
| **M3: E2E Clean Artifact** | S36.5 | Before acceptance ledger | A real temporary staged artifact is built from the allowlist and independently passes manifest, license, notice, reference, secret, provenance, traversal, and unexpected-file checks. | Produce a local clean artifact and redacted receipt without publishing or touching the public candidate repository. |
| **M4: Epic Complete** | S36.6 plus exit audit | Before `/rai-epic-close` | Every E36 done criterion is proved; E37-E42 ledger entries have owners/evidence/gates; retrospective and full quality gates pass. | Trace any master-plan requirement from owner to verification command and current evidence state. |

M3 is the required integration checkpoint. It uses the actual filesystem,
tracked-file enumeration, manifests, a temporary staging directory, and the real
verifier. Mock-only unit tests cannot satisfy it.

### Parallel Work Streams

```text
Critical content path:  S36.1 ──► S36.2 ──► S36.3 ──┐
                       │                            ├──► S36.5 ──► S36.6
Governance path:       └────────► S36.4 ───────────┘
```

**Split point:** after S36.1, exposure classification and governance identity
have no mutual implementation dependency.

**Merge point:** S36.5 starts only when S36.2-S36.4 evidence is complete. Work
may be sequenced on one machine, but the independence remains useful for failure
isolation and commit recovery.

### Progress Tracking

| Story | Size | Status | Actual | Velocity | Notes |
|-------|:----:|:------:|:------:|:--------:|-------|
| S36.1 | S | Complete | 44m 06s | 1 S / 44m 06s | Merged locally at `d56a957`; final `origin/main` `0/0` proof remains an E36 close gate |
| S36.2 | M | Complete | 47m 32s | 1 M / 47m 32s | Merged locally at `195eff6`; sanitized baseline and non-mutation proof committed |
| S36.4 | M | Complete | 1h 05m 33s | 1 M / 1h 05m 33s | Merged locally at `708a1b6`; strict governance contract, 10 canonical identities, and 15/15 close gates passed |
| S36.3 | M | Complete | 1h 53m 12s | 1 M / 1h 53m 12s | Merged locally at `52baa1a`; 15/15 close gates passed after T7 canonical-import repair |
| S36.5 | L | Pending | — | Not calibrated | E2E integration checkpoint |
| S36.6 | S | Pending | — | Not calibrated | Epic-wide acceptance control |

Velocity will be calibrated from completed task evidence, not estimated hours.
Every story records its commit(s), focused tests, full gates, receipts, and any
scope variance before it is marked done.

### Sequencing Risks

| Risk | Likelihood / Impact | Mitigation |
|------|:-------------------:|------------|
| Remote repair accidentally exposes or prints a credential | M / H | Audit exact remote names and booleans; never echo URLs; sanitize configuration before evidence generation. |
| Inventory is changed by remediation before the baseline is captured | M / H | Complete and commit S36.2 evidence before S36.3 content changes. |
| S36.4 hides graph collisions behind prose aliases | M / H | Require executable resolver behavior and a real graph-build receipt with zero duplicate canonical IDs. |
| S36.5 passes unit tests but fails on a real artifact | M / H | Make the real temporary filesystem/staged verifier M3's exit gate. |
| Ledger claims future work is complete from plans | M / H | Default all E37-E42 requirements to unproved/planned and require named evidence for transition. |
| Public candidate repository is modified during integration | L / H | Treat it as read-only evidence and assert no mutation in the S36.5 receipt. |

### Plan Review Record

The product owner instructed the session to continue the full master plan and
explicitly removed repeated approval prompts for routine local PASS gates. This
plan remains inside that authorized scope. E36 still stops for a critical
finding, credential handling, destructive history operation, or external
publication/push.
