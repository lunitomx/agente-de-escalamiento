# Skill Golden Cases Release Check

## Command

```bash
uv run python scripts/check_skill_golden_cases.py --format json
```

## Evidence To Cite

- `status`
- `checks[].name`
- `checks[].status`
- `errors`

## What This Covers

- Core golden-case fixture validity.
- Golden-case changelog evidence for expectation hashes.
- Deterministic output drift for release output fixtures.

## What This Does Not Cover

- E30 pipeline registry validation.
- E31 guided runner integration.
- E32 closure evidence governance.
- Live model behavior or semantic scoring.

## Release Rule

Before release, cite the JSON report. A release reviewer should treat
`status: fail` as blocking until failed case names and errors are resolved or
explicitly accepted in a new changelog entry.
