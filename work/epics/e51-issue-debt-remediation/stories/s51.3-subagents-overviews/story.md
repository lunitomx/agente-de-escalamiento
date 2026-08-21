# S51.3: Sub-Agents and Decision Overviews

## Problem
GitHub issue #3 reports that 4 decision skills (`escala-strategy`, `escala-people`, `escala-execution`, `escala-cash`) reference missing files: 4 sub-agent personas and 3 decision overviews. Without them, the skills load degraded.

## Root Cause
The files were never created. The content exists scattered in `conocimiento/decisions/*.yaml` and related concept/tool/metric nodes, but there is no consolidated persona or overview document for the agent to read.

## Goal
Create the 7 missing files based on the existing ontology, giving each decision skill a persona and a domain overview.

## Acceptance Criteria
- [ ] `.escala/agent/sub-agents/{strategy,people,execution,cash}.md` exist and define the coaching persona for that decision.
- [ ] `.escala/knowledge/{strategy,people,execution}/overview.md` exist and summarize the domain, tool routing, and maturity signals.
- [ ] Content is derived from `conocimiento/decisions/*.yaml` and existing nodes; no invented IP.
- [ ] A test verifies the 7 files exist and are non-empty.
- [ ] All existing tests pass.

## Tasks
1. Read `conocimiento/decisions/*.yaml` and related nodes.
2. Draft the 4 sub-agent personas.
3. Draft the 3 decision overviews.
4. Add a regression test.
5. Run gates.

## Related
- GitHub issue #3
