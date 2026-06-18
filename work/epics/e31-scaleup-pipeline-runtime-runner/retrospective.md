# E31 Retrospective — ScaleUp Pipeline Runtime / Runner

**Date:** 2026-06-18
**Status:** Complete
**Stories:** 3/3 complete
**Tag:** `epic/e31-scaleup-pipeline-runtime-runner-complete`

## Summary

E31 made `.raise/pipelines/scaleup.yaml` operational without overbuilding. The
result is a lightweight guided runner that lists pipelines, renders deterministic
pipeline detail, records run evidence, inspects evidence, resumes interrupted
runs, and proves compatibility with every canonical ScaleUp pipeline.

## Delivered

- S31.1: Guided runner for list, inspect, run, and evidence writing.
- S31.2: Evidence inspect/resume hardening with append-only events.
- S31.3: Integration review across all canonical ScaleUp pipelines.

## Scope Verification

| Commitment | Result | Evidence |
|---|---|---|
| Pipeline discovery and detail views | Fulfilled | `list_pipeline_summaries`, `render_pipeline_detail`, CLI tests |
| First guided run flow | Fulfilled | `run_guided_pipeline`, CLI `run`, stopped/completed evidence tests |
| Durable evidence artifacts | Fulfilled | Pydantic evidence model, YAML round-trip tests, inspect/resume tests |
| Focused tests | Fulfilled | `tests/test_pipeline_runner.py` and registry compatibility tests |
| Avoid generic workflow engine | Fulfilled | Runner records guided evidence only; no automated skill execution |

## Verification

- `uv run pytest tests/test_pipeline_runner.py --tb=short` — 12 passed
- `uv run pytest --tb=short` — 486 passed, 2 skipped
- `uv run ruff check` — pass
- `uv run ruff format --check` — pass
- `uv run pyright` — pass
- `rai gate check gate-tests -f json` — pass
- `rai gate check gate-lint -f json` — pass
- `rai gate check gate-format -f json` — pass
- `rai gate check gate-types -f json` — pass

## Patterns

- **Guided evidence recorder:** a first runtime layer should preserve registry
  intent and record review evidence before attempting automated execution.
- **Registry round-trip test:** canonical pipelines should be loadable,
  renderable, runnable to evidence, and reloadable from evidence.
- **Explicit human gates:** unresolved gates stay visible as `not_checked`
  rather than silently passing.

## Follow-up

- Add real gate evaluation only after there is a clear owner for manual and
  code-gate decisions.
- Keep automated skill execution out of scope until guided evidence proves
  enough repeated usage to justify a runtime engine.
