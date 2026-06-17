---
epic_id: "E31"
title: "ScaleUp Pipeline Runtime / Runner"
status: "draft"
created: "2026-06-16"
---

# Epic Brief: ScaleUp Pipeline Runtime / Runner

## Hypothesis
For operators using the ScaleUp skills who need repeatable execution guidance,
the pipeline runner is a lightweight CLI and evidence workflow
that makes `.raise/pipelines/scaleup.yaml` operational without turning it into a full orchestration engine.
Unlike a static registry, the runner exposes available pipelines, walks phases and gates, stops at declared conditions, and records execution evidence.

## Success Metrics
- **Leading:** A user can list ScaleUp pipelines and inspect phases, gates, stop conditions, and entrypoints from the registry.
- **Lagging:** A guided run produces durable evidence that shows which pipeline was selected, which phases were reviewed, and where execution stopped or completed.

## Appetite
M — 3-5 stories. Keep the first version guided and observable; defer generic execution machinery until the workflow proves value.

## Scope Boundaries
### In (MUST)
- Read `.raise/pipelines/scaleup.yaml` through the existing registry contract.
- Provide a guided runner that lists pipelines, shows phase/gate/stop-condition detail, and records evidence.
- Add focused tests around registry loading, CLI behavior, stop conditions, and evidence output.

### In (SHOULD)
- Reuse existing ScaleUp skill entrypoint references and validation helpers.
- Keep output useful for session close, audits, and later pipeline retrospectives.

### No-Gos
- No full generic workflow engine in the first pass; execution remains guided.
- No mutation of existing ScaleUp skill contracts unless a failing test proves it is necessary.
- No GitLab push as part of the epic; GitLab is known to be far behind local main.

### Rabbit Holes
- Building async job orchestration, retries, scheduling, or parallel phase execution before the guided runner has real usage evidence.
