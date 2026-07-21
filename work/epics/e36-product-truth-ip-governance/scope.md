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
