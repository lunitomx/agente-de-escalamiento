---
epic_id: "E36"
title: "Product Truth, IP Boundary & Governance"
status: "draft"
created: "2026-07-21"
mission: "escala-local-v2-plan-maestro-2607202112"
---

# Epic Brief: Product Truth, IP Boundary & Governance

## Hypothesis

For business owners who need to trust ESCALA with sensitive company data, the
product needs one verifiable source of truth and a clean intellectual-property
boundary before new functionality is added. Unlike the current repository,
which mixes historical experiments, legacy identifiers, runtime code, and
distribution candidates, E36 will make every future release traceable to an
explicit private canonical source and a deny-by-default public export contract.

## Success Metrics

- **Leading:** repository, remote, legacy-ID, reference-source, credential, and
  distributable-surface inventories are generated with named owners and no
  unresolved critical finding.
- **Lagging:** a clean-export dry run contains no prohibited reference source,
  embedded credential, private company data, or ambiguous governance state;
  the knowledge graph builds without duplicate epic IDs.

## Appetite

M — 6 stories. This epic establishes the trust boundary; it does not rebuild
the business runtime.

## Scope Boundaries

### In (MUST)

- Establish `origin/main` as the canonical private development truth and remove
  unsafe or obsolete local remote configuration.
- Remove the raw reference-book asset from the current canonical tree and
  inventory derived/reference-facing material without rewriting history.
- Define public-facing ESCALA vocabulary and a deny-by-default clean-export
  manifest.
- Eliminate ambiguous legacy epic identity and create one typed governance
  disposition contract.
- Record the acceptance ledger and architectural invariants for E37-E42.
- Preserve the product rule: execution and authoritative data live only on the
  installer's machine; team exchange uses a user-controlled synced folder.

### In (SHOULD)

- Produce license and third-party-source inventories ready for legal review.
- Add deterministic scanners and regression gates for prohibited references,
  credentials, private paths, and ambiguous public artifacts.

### No-Gos

- No hosted application, hosted database, telemetry service, or cloud runtime.
- No Google Drive/OneDrive API or OAuth integration; only local synced folders.
- No publication or public-repository push during E36.
- No destructive Git-history rewrite without a separate backup, impact report,
  and explicit human authorization.
- No unsupported legal conclusion; license decisions remain marked for counsel
  where required.
- No ingestion, cockpit, meeting automation, or installer implementation; those
  belong to E37-E41.

### Rabbit Holes

- Rewriting every historical internal document merely to change terminology.
- Treating a private history scan as equivalent to a clean public export.
- Building a generalized policy engine when a typed manifest and deterministic
  verifier satisfy the boundary.
- Mixing product repairs into the governance baseline before their owning epic.
