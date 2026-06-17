---
epic_id: "E31"
title: "ScaleUp Pipeline Runtime / Runner"
status: "draft"
created: "2026-06-16"
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
- **S31.1 Guided ScaleUp pipeline runner:** list pipelines, inspect phases/gates/stop conditions, guide a selected run, and write evidence.
- **S31.2 Evidence and resume hardening:** make run evidence easy to inspect and resilient enough for interrupted sessions.
- **S31.3 Integration review:** validate the runner against the canonical ScaleUp pipelines and document any pattern candidates.

## Done Criteria
- Users can run the first guided pipeline workflow from the CLI.
- Tests cover happy path, unknown pipeline, malformed registry data, stop conditions, and evidence output.
- Evidence artifacts are deterministic enough to support session close and later audits.
- The implementation remains smaller than a generic orchestration framework and uses the existing registry contract.
