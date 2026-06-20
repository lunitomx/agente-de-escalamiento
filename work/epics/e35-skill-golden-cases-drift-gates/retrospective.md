# E35 Retrospective: Skill Golden Cases & Drift Gates

## Outcome

E35 is complete. The old E22 validation/drift idea has been revived in a
narrower, implemented form focused on selected core ScaleUp skill behavior.

## Delivered Stories

| Story | Status | Evidence |
|---|---|---|
| S35.1 Golden case fixture contract | Complete | `validators/skill_golden_cases.py`, `tests/test_skill_golden_cases.py` |
| S35.2 Core skill golden cases | Complete | `tests/fixtures/skill_golden_cases/core/*.yaml` |
| S35.3 Drift check implementation | Complete | `tests/test_skill_golden_case_drift.py` |
| S35.4 Prompt/version changelog | Complete | `.raise/skill-golden-cases/changelog.yaml` |
| S35.5 Release check integration | Complete | `scripts/check_skill_golden_cases.py`, `.raise/release/skill-golden-cases.md` |

## What Worked

- The implementation stayed deterministic and avoided brittle full-response
  snapshots.
- Changelog hashes made fixture expectation changes auditable.
- Release review now has a single versioned command and checklist to cite.

## Risks And Limits

- Coverage is intentionally limited to Strategy, Cash, People, and Execution.
- The checker is string/property based and does not judge semantics or live
  model behavior.
- Native `rai gate` registration was not added because no project-local gate
  registry was available; the release check is a versioned script.
- The tracked skill catalog validated by the release check is `.claude/skills`;
  `.agents/skills` is treated as a local runtime mirror when present.
- Aggregate `rai gate check --all -f json` is not fully green because
  `gate-sync` reports `no keys provided`; scoped quality gates and full pytest
  passed.

## Follow-Ups

- Add more core cases only when there is real drift risk.
- If a local gate registry becomes available, wrap
  `scripts/check_skill_golden_cases.py` as a native `rai gate`.
- Consider live model evals only after deterministic gates prove insufficient.
