# ESCALA-001 — Closure governance gates block all commits

Issue Type: Bug

WHAT: `tests/test_epic_closure_governance.py` reports 10 governance consistency errors across audited closures and backlog draft dispositions.
WHEN: The closure-governance test module runs from the current canonical `main` snapshot `c9b119d`.
WHERE: `tests/test_epic_closure_governance.py`, `validators/epic_closure.py`, the seven affected epic scope files, `work/epics/e33-backlog-draft-closure/audit-matrix.md`, and `work/epics/legacy-disposition-index.md`.
EXPECTED: Canonical audit and backlog artifacts satisfy the validator contract without weakening the assertions or manufacturing completion evidence.
Done when: The focused module and full test suite pass; Ruff and Pyright pass; canonical statuses remain fail-closed and explain the terminal disposition of every affected item.

## Reproduction

```text
uv run pytest tests/test_epic_closure_governance.py -q
2 failed, 2 passed
```

The failure is a prerequisite gate for the ESCALA Local V2 master mission because repository policy forbids commits while tests are red.

TRIAGE:
  Bug Type:    Regression
  Severity:    S1-High
  Origin:      Integration
  Qualifier:   Incorrect
  Jira fields: not set — local RaiSE bug with no Jira adapter/ticket
