# Legacy Epic Disposition Index

Date: 2026-06-20

This index prevents legacy incomplete scopes from being counted as active open
epics or false completes.

The executable authorities are `governance/closure-dispositions.yaml` and
`governance/epic-identities.yaml`. This page is only their human-readable
derived view; old folder names below are exact aliases, not current paths.

## Terminal Dispositions

| Canonical folder | Legacy alias | Disposition | Trusted successor / action |
|---|---|---|---|
| `e1902-strategy-core-skills` | `e19-strategy-core-skills` | Superseded/Discarded | Absorbed by E34 S34.4; no active epic remains. |
| `e2002-voice-of-customer-evidence-capture` | `e20-voice-of-customer-evidence-capture` | Superseded/Discarded | Superseded by E34; no active epic remains. |
| `e2101-transcript-intelligence-for-escala` | `e21-transcript-intelligence-for-escala` | Deprecated/Discarded | Do not revive as full epic; optional future E1801 story only. |
| `e2201-validation-drift-governance` | `e22-validation-drift-governance` | Superseded/Discarded | Superseded by E35; no active epic remains. |

## Deferred Backlog, Not Active

| Canonical folder | Legacy alias | Disposition | Rule |
|---|---|---|---|
| `e1901-book-ingestion` | `e19-book-ingestion` | Deferred/Backlog | Do not count as complete; reopen only with new proof scope. |
| `e23-kokoro-agent` | — | Deferred/Backlog | Do not count as complete; reopen only for memory proof if needed. |
| `e24-escala-evolve` | — | Deferred/Backlog | Do not count as complete; reopen only as new automation/auto-patch stories. |

## Current Board Interpretation

There is no active legacy epic pending from these folders. Bare E18–E22 are
ambiguous aliases and never select a first folder. The project is up to date
for the E34/E35 repair/revival decision. Future work requires an explicit new
scope, not inference from old numeric tags.
