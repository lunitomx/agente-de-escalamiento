---
adr_id: "E36-ADR-001"
title: "Private Canonical Source and Verified Clean Export"
status: "accepted"
date: "2026-07-21"
owners:
  - "ESCALA product owner"
  - "E36 implementation"
---

# E36-ADR-001: Private Canonical Source and Verified Clean Export

## Context

The current private repository contains product code, historical experiments,
governance artifacts, derived knowledge, private paths, and raw reference
material. A separate public-like local repository also exists, but it has
diverged and contains intentional uncommitted work. Manually synchronizing the
two cannot prove which source produced a release or prevent private material
from crossing the distribution boundary.

The product must run only on the installer's machine. Company data and the
authoritative SQLite database remain local. A team may exchange inbox files and
scoped reports through a locally mounted Google Drive or OneDrive folder, but
ESCALA does not host a service or synchronize its database.

## Decision

1. The private repository is the only canonical development source.
2. The private repository will not be made public and will not be mirrored as a
   release mechanism.
3. A distributable artifact is generated from an explicit, versioned allowlist.
   Everything not allowlisted is private by default.
4. The staged artifact is independently verified for prohibited references,
   credential patterns, private data/paths, unexpected files, license/notices,
   third-party inventory, provenance, and file hashes.
5. Governance manifests are parsed into strict typed models and fail closed on
   unknown or incomplete values.
6. The export process creates a local artifact and receipt. Publication, push,
   or replacement of an existing public repository is a separate human-reviewed
   action.
7. The local-only runtime, local data authority, no shared SQLite, and
   filesystem-only synced-folder rules are release invariants.

## Alternatives Considered

### Make the private repository public

Rejected. The current tree and history contain material that is not eligible for
public distribution. Removing selected current files would not make the private
history or future additions safe.

### Maintain a second public repository manually

Rejected. Manual copying creates two sources of truth, hides provenance, and
cannot deterministically prove that every release received the same checks.

### Export by blacklist

Rejected. A newly added private file would be exported until someone remembered
to deny it. The safe default is non-distribution.

### Rewrite private Git history now

Rejected for E36. It is destructive, affects every clone and reference, and is
not required to produce a clean current artifact. Historical exposure remains
reported truthfully and can be handled as a separately authorized operation.

### Build a hosted collaboration service

Rejected. It contradicts the product requirement and would expand security,
privacy, operations, and multi-writer scope before local product acceptance.

## Consequences

### Positive

- One traceable source produces every candidate artifact.
- New private files are excluded automatically until reviewed and allowlisted.
- The exact staged artifact, not an approximation, receives verification.
- The dirty public candidate repository is preserved untouched.
- Local data ownership is an architectural constraint that later epics must
  prove rather than an informal promise.

### Costs and Constraints

- Public additions require an explicit manifest change and review.
- Private history may still contain historical material; reports must not claim
  it was purged.
- License posture still requires human legal review before release.
- Windows installation evidence is deferred to E41 but remains a release gate.

## Compliance Evidence

- sanitized remote/upstream audit;
- typed product-boundary and governance manifests;
- exposure report separated by surface;
- negative and positive policy tests;
- collision-free graph-build receipt;
- clean-export dry-run manifest and verification receipt;
- E37-E42 acceptance ledger with no-host requirements.

## Revisit Conditions

Revisit only if the product owner intentionally changes the product from
local-only to hosted/multi-writer, or if a future distribution channel cannot
consume deterministic local artifacts. Either change requires a new ADR and
must not silently amend this decision.
