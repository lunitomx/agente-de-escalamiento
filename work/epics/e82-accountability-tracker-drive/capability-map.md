# Capability map E82 (ESCALA-48)

Evidence reused, not redone: `stories/s82.1-spike-drive-connectors.md`, `stories/s82.2-story.md`, `stories/s82.2-retrospective.md`.

## Part 1 - Gemba findings
| Capability | State | Where | Disposition |
|---|---|---|---|
| Find file, read sheets (formulas resolved) | Works, Claude Drive connector | S82.1 | reuse |
| Write cells | Not possible with this connector (`update_file` = title/parent only) | S82.1 | new (blocked on S82.6) |
| Parse participant sheet, 7 variations, unparsed side blocks | Done, 11 synthetic tests | `coaching/tracker/` (parser.py, models.py) | reuse |
| Confirm identity / own sheet | Missing; name cell can be an unfilled formula ("Name 6") | S82.2 retro | extend (S82.3) |
| Revenue/custom blocks | Reported, not read | S82.2 retro | out unless E84 needs it |

Gaps: G1 write path; G2 ChatGPT/Codex behavior; G3 identity confirmation; G4 custom blocks.

## Part 2 - Backlog scan
Verified via `rai backlog get --adapter jira`: ESCALA-48 (epic), ESCALA-53 (S82.3), -54 (S82.4), -55 (S82.5), -56 (S82.6), all "Tareas por hacer". No duplicate work found in this scan; related epics E45, E68, E79, E85 listed in scope.md were not re-scanned.

## Part 3 - Scope validation
- MVP read-only flow (S82.3, S82.5 read side) is supported today in Claude.
- S82.4 write step depends on S82.6; order in scope (S82.6 before S82.4) is correct.
- Open unknowns for S82.6, not asserted here: ChatGPT Work Drive/Sheets write, any Google Sheets MCP with per-cell write (install viability, file-scoped permission), Codex with a user-configured Sheets MCP.
