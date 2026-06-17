# E29 Draft Scope Reclassification

Date: 2026-06-16

These local folders were previously included in the completed-epic audit because their numeric prefixes collided with real completed epic tags. Current evidence shows they are ignored local drafts, not completed epics.

## Reclassification

| Draft folder | Current git evidence | Decision | Rationale |
|---|---|---|---|
| `work/epics/e19-strategy-core-skills/` | `git status --ignored` reports `!!`; `git ls-files` returns no tracked files; `git log -- <path>` returns no implementation commits. | Backlog candidate, not completed. | The only available content is brief/scope planning. No story, implementation, retrospective, or close evidence exists. |
| `work/epics/e20-voice-of-customer-evidence-capture/` | `git status --ignored` reports `!!`; `git ls-files` returns no tracked files; `git log -- <path>` returns no implementation commits. | Backlog candidate, not completed. | The folder is a local draft. The `epic/e20-complete` tag belongs to E20 Contextual Skills. |
| `work/epics/e21-transcript-intelligence-for-escala/` | `git status --ignored` reports `!!`; `git ls-files` returns no tracked files; `git log -- <path>` returns no implementation commits. | Backlog candidate, not completed. | The folder is a local draft. The `epic/e21-complete` tag belongs to E21 Verne Board Member. |
| `work/epics/e22-validation-drift-governance/` | `git status --ignored` reports `!!`; `git ls-files` returns no tracked files; `git log -- <path>` returns no implementation commits. | Backlog candidate, not completed. | The folder is a local draft. The `epic/e22-complete` tag belongs to E22 Full System Audit / Verne Audit. |

## Policy

- Do not close these as completed epics without implementation evidence.
- If any remains useful, renumber it as a future formal epic before starting work.
- Do not delete these drafts without explicit user approval.

