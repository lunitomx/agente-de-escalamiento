---
epic_id: "E31"
title: "ScaleUp Pipeline Runtime / Runner"
status: "complete"
created: "2026-06-16"
completed: "2026-06-18"
---

# E31: ScaleUp Pipeline Runtime / Runner

## Objective
Make `.raise/pipelines/scaleup.yaml` operational through a lightweight guided runner that can list pipelines, explain phases/gates/stop conditions, and record execution evidence.

## In Scope
- Pipeline discovery and detail views from the existing YAML registry.
- A first guided run flow for selecting a ScaleUp pipeline and stepping through its declared phases.
- Durable evidence artifacts for run selection, phase review, gate decisions, and stop/completion state.
- Focused tests for CLI behavior, registry compatibility, and evidence serialization.

## Out of Scope
- A generic workflow engine for arbitrary non-ScaleUp registries.
- Automated execution of every skill phase without human review.
- Scheduler, daemon, background jobs, or remote orchestration.
- Pushing to GitLab while `gitlab/main` remains behind local development history.

## Planned Stories
- [x] **S31.1 Guided ScaleUp pipeline runner:** list pipelines, inspect phases/gates/stop conditions, guide a selected run, and write evidence. ✓
- [x] **S31.2 Evidence and resume hardening:** make run evidence easy to inspect and resilient enough for interrupted sessions. ✓
- [x] **S31.3 Integration review:** validate the runner against the canonical ScaleUp pipelines and document any pattern candidates. ✓

## Progress
| Story | Status | Notes |
| --- | --- | --- |
| S31.1 | Complete | Guided runner implemented, reviewed, and gates repaired/passed. |
| S31.2 | Complete | Evidence inspect/resume hardening implemented with append-only events and focused gates passed. |
| S31.3 | Complete | Integration test covers every canonical pipeline and review documents pattern candidates. |

## Done Criteria
- [x] Users can run the first guided pipeline workflow from the CLI.
- [x] Tests cover happy path, unknown pipeline, malformed registry data, stop conditions, and evidence output.
- [x] Evidence artifacts are deterministic enough to support session close and later audits.
- [x] The implementation remains smaller than a generic orchestration framework and uses the existing registry contract.

## Closure Guardrail

E31 is active. S31.1 and S31.2 are complete as stories, but S31.3 remains
pending. Do not create or rely on an E31 complete tag until S31.3 is implemented,
reviewed, and the epic Done Criteria are checked with evidence.

Update after S31.3: S31.3 is now complete. E31 may proceed to epic close once
the Done Criteria are verified against tests and story retrospectives.

## Final Status

Complete. E31 delivers a lightweight guided runner for the canonical ScaleUp
pipeline registry: list, inspect, guided evidence recording, evidence inspect,
resume, and integration coverage across every canonical pipeline. It does not
execute skills automatically or become a generic workflow engine.
