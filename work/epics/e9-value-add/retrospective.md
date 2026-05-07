# Retrospective: E9 — Value-Add Features

**Dates:** 2026-05-06 → 2026-05-06
**Stories:** S9.1 ✓ S9.2 ✓ S9.3 ✓ S9.4 ✓
**Architecture:** Cross-platform pattern (core Python `coaching/` + SKILL.md adapters)

## Deliverables

- `/scaleup-export` — Action Plan Export (S9.1): shareable markdown doc with diagnosis, goals, tasks, next steps
- `/scaleup-pulse` — Quarterly Pulse re-diagnosis (S9.2): 5-question re-diagnosis + trend comparison + history append
- `/scaleup-dashboard` — Progress Dashboard (S9.3): read-only 4-section markdown dashboard with historical score trajectory
- Session Summary auto-generated on `/scaleup-close` Step 3.5 (S9.4): structured `## Session Summary` appended to session logs

## Scope Fulfillment

| Item | Status | Evidence |
|------|--------|----------|
| `/scaleup-export` | **Fulfilled** | `.claude/skills/scaleup-export/SKILL.md` + `.scaleup/coaching/` (export.py) |
| `/scaleup-pulse` | **Fulfilled** | `.claude/skills/scaleup-pulse/SKILL.md` + `.scaleup/coaching/` (pulse.py) |
| `/scaleup-dashboard` | **Fulfilled** | `.claude/skills/scaleup-dashboard/SKILL.md` + `.scaleup/coaching/` (dashboard.py) |
| Session summary auto-generated | **Fulfilled** | `.scaleup/coaching/summary/` (engine.py, formatter.py, __init__.py) + `.claude/skills/scaleup-close/SKILL.md` Step 3.5 |
| Core Python in `coaching/` | **Fulfilled** | `.scaleup/coaching/` — all 4 modules present (export.py, pulse.py, dashboard.py, summary/) |
| Quality gate validators per story | **Fulfilled** | `.scaleup/agent/validators/` — export.py, pulse.py, dashboard.py, summary_validator.py all present |

## What Went Well

- **E8 cross-platform pattern is a proven template.** By S9.3 it was copy-paste — zero structural surprises across 3 consecutive modules. The `run→dict`, `__main__`, `core.run_and_print` composition is genuinely portable.
- **Lessons applied forward, not backward.** S9.1 flagged PRIORITY_ORDER/ROUTING_RULES duplication; S9.2 immediately extracted these to coaching/core. S9.3 flagged YAML null trap; S9.4 applied null-coalesce proactively without needing a QR catch.
- **QR caught real bugs before merge every story.** S9.2: validator schema mismatch (Critical). S9.3: two null-coalesce bugs. S9.4: anchored-regex bug + tautological test. None slipped to main.
- **Test discipline held.** TDD RED→GREEN→REFACTOR followed; 17 → 21 → 23 → 38 unit tests accumulated cleanly. Full suite grew from 20 to 62 without regression.
- **Pure function separation (S9.4)** — `engine.py` / `formatter.py` / `__init__.py` I/O isolator proved clean. Business logic fully unit-testable without filesystem setup.
- **Gemba walk accurate (S9.3):** correctly identified `coaching/progress/` as independent (worksheet tracker, not score tracker), avoiding a wrong dependency.

## What to Improve

- **Schema contract testing in design, not QR.** S9.2's validator schema mismatch was testable from the spec but wasn't caught until QR. Design step should require: "For modules with a validator, write a contract test that passes run() output through the actual validator."
- **YAML null trap should be default-proactive, not QR-caught.** S9.3 caught it in review; S9.4 applied it proactively. This pattern should be codified at the plan/design level, not discovered at QR.
- **Regex anchoring as default.** S9.4's `re.search(r"## Session Summary")` should have been `re.search(r"^## Session Summary", content, re.MULTILINE)` from the start. Add anchoring check to REFACTOR-phase TDD checklist.
- **Tautological assertions.** `assert "X" in "X"` provides zero test value. Add test-review rule: "Every assert must reference the result of a function call, not a hardcoded literal."
- **Pre-story audit of shared utilities.** S9.1 duplicated constants that could have lived in coaching/core. Gemba walk in Story Design should include: "Check coaching/core for existing utilities before creating per-module copies."

## Patterns Crystallized This Epic

| Pattern | Origin | Description |
|---------|--------|-------------|
| PAT-L-1 | S9.1 | Check `coaching/core` for shared utilities before per-module duplication |
| PAT-L-2 | S9.1 | E8 coaching module pattern is a portable template for all E9+ modules |
| PAT-L-6 | S9.2 | Writer/validator schema contract — `run()` output must pass the actual validator in tests |
| PAT-L-7 | S9.2 | `pulse-history.yaml` schema locked post-S9.2 — Dashboard S9.3 unambiguous |
| PAT (S9.3) | S9.3 | YAML null coalescing — `data.get(key) or default` vs `data.get(key, default)` |
| PAT-L-24 | S9.4 | `coaching/summary` engine+formatter+I/O isolator pattern — proven across 3 stories, treat as default coaching module architecture |
| BASE-009 | S9.4 | Retrospective required before story/epic close — followed exactly |

The **engine+formatter+I/O isolator** architecture (PAT-L-24) is now the standard for all future coaching modules.

## Learning Chain Summary

No RAISE server available across all 4 stories. No `.raise/rai/learnings/` records persisted remotely. Patterns captured locally via `rai pattern add` in `raise.db` (project scope). Aggregate metrics (acceptance rate, gap rate, pattern utility) unavailable.

**Notable QR heuristics now codified:**
1. YAML null-coalesce: `.get(key) or default` is not the same as `.get(key, default)` for explicit YAML nulls
2. Section-header regex anchoring: `^` + `re.MULTILINE` required to avoid false positives from embedded text
3. Schema contract test: `run()` output must be passed through the actual validator in unit tests
4. Tautological assertions: `assert literal in literal` provides zero signal — reject in REFACTOR phase

## Epic Health Summary

- **Velocity:** 4 stories in 1 day (2026-05-06), all M-S sized
- **Quality:** 0 bugs escaped to main; QR caught real issues every story
- **Test count:** 17 → 21 → 23 → 38 per story; full suite 20 → 41 → 62 → (S9.4 clean)
- **Pattern debt:** 0 — all retrospective patterns applied forward within the epic
