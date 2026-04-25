# ScaleUp Agent AI — Product Roadmap

> Master plan for the ScaleUp Coach AI product.
> A GitHub repo any entrepreneur clones, opens in Claude Code, and gets an expert Scaling Up coaching agent running locally. No servers, no databases, no API keys beyond Claude.

---

## Vision

Turn the Scaling Up methodology (Verne Harnish) into an interactive, local-first AI coaching agent. The entrepreneur gets persistent memory, structured guidance through 34 worksheets across 4 Decisions (People, Strategy, Execution, Cash), and measurable progress tracking — all inside Claude Code.

## Architecture Principles

1. **Ontology over RAG** — A curated domain graph (nodes + relationships + pointers), not chunked text in a vector store.
2. **Shared belief system** — Agent and user share the Scaling Up methodology as the common framework. This constrains the LLM toward useful, methodology-aligned outputs.
3. **Skills = processes within the ontology** — Each skill is an observable, measurable, repeatable process grounded in the methodology graph.
4. **Neuro-symbolic memory** — Deterministic retrieval algorithms over structured data. No embedding search.
5. **Level-aware coaching** — Shu/Ha/Ri adaptation: beginners get step-by-step, advanced users get strategic nudges.
6. **Everything local** — Clone repo = get the full brain. Privacy by architecture.

---

## Epic Sequence

```
E3 (Agent Framework) ──► E6 (Knowledge Ontology) ──► E7 (Agent Intelligence)
       DONE                      DONE                       │
                                                            ▼
                                                  E8 (Coaching Engine) ──► E9 (Value-Add)
                                                            │                    │
                                                            ▼                    ▼
                                                  E10 (Skill Refactor)    E4 (Validation) ──► E5 (Distribution)
```

**E7 builds with orchestration pattern from day 1.** E10 adapts the 20 existing skills to the same pattern.

---

## E3 — Agent Framework (In Progress)

**Objective:** Make the repo installable — clone, open Claude Code, get a working ScaleUp agent with zero configuration.

**Status:** 2/5 stories done (S3.2 .gitignore, S3.4 .scaleup/ defaults).

### Stories

| ID | Story | Size | Status |
|----|-------|------|--------|
| S3.1 | CLAUDE.md — Product identity, instructions, routing rules | M | pending |
| S3.2 | .gitignore + repo cleanup | S | done |
| S3.3 | README.md — Quick start for the entrepreneur | M | pending |
| S3.4 | .scaleup/ defaults structure for end user | S | done |
| S3.5 | Skill triggers — Map slash commands in CLAUDE.md | S | pending |

### Dependencies
- None. This is the foundation.

### Done Criteria
- [ ] Cloned directory contains everything needed for Claude Code to function as ScaleUp agent
- [ ] No dev artifacts (RaiSE governance, build/, PDFs) in the product
- [ ] All skills invocable via documented slash commands
- [ ] README explains install + use in under 1 minute of reading

---

## E6 — Knowledge Ontology

**Objective:** Convert the extracted Scaling Up content (68 methodologies, 34 worksheets, 23 coaching prompts) into a structured domain ontology with deterministic retrieval — the agent's "brain."

### Stories

| ID | Story | Size | Description |
|----|-------|------|-------------|
| S6.1 | Ontology schema design | M | Define node types (concept, tool, worksheet, stage, decision, metric), relationship types (belongs-to, requires, feeds-into, measured-by, prerequisite-of), and the YAML/JSON schema for graph storage |
| S6.2 | People decision — ontology population | M | Convert People knowledge files into ontology nodes and relationships. Cover: FACe/PACe, Topgrading, Five Manager Activities, OPPP, hiring checklist |
| S6.3 | Strategy decision — ontology population | M | Convert Strategy knowledge: OPSP, 7 Strata, SWT Analysis, Core Values/Purpose, brand promises |
| S6.4 | Execution decision — ontology population | M | Convert Execution knowledge: Rockefeller Habits checklist, meeting rhythm, priorities/rocks, data/KPIs |
| S6.5 | Cash decision — ontology population | M | Convert Cash knowledge: CCC, Power of One, Simple Numbers framework |
| S6.6 | Cross-decision relationships + worksheet registry | S | Wire inter-decision edges (e.g., OPSP feeds-into priorities, core values feed-into hiring). Create the 34-worksheet registry with completion status tracking schema |
| S6.7 | Deterministic retrieval engine | M | Build the graph query layer: given a context (decision, stage, tool), retrieve relevant nodes and relationships. Symbolic traversal, no vectors. Port from RaiSE's symbolic memory adapter where applicable |

### Dependencies
- E3 complete (repo structure must be stable before populating knowledge)

### Done Criteria
- [ ] All 68 methodologies represented as ontology nodes with relationships
- [ ] All 34 worksheets registered with metadata (decision area, prerequisites, outputs)
- [ ] Graph stored in `.scaleup/knowledge/ontology/` as inspectable YAML/JSON files
- [ ] Retrieval engine returns relevant nodes for any (decision, stage) query
- [ ] Zero external dependencies — pure file-based graph

---

## E7 — Agent Intelligence

**Objective:** Give the agent persistent memory, session continuity, task management, and strategic alignment so it behaves like a real coach across multiple conversations.

### Stories

| ID | Story | Size | Description |
|----|-------|------|-------------|
| S7.1 | Session lifecycle commands | M | `/scaleup-start` and `/scaleup-close` — load company context on open, save state on close. Detect returning vs new user |
| S7.2 | Persistent memory system | M | Store and retrieve: company profile, diagnosis scores, completed worksheets, session history. All in `.scaleup/my-company/`. YAML-based, human-readable |
| S7.3 | SMART annual goal as strategic filter | S | `/scaleup-goal` — set/view the annual SMART goal. All recommendations filtered through: "Does this advance the annual goal?" |
| S7.4 | Task board (kanban in markdown) | M | `/scaleup-tasks` — track commitments as TODO/DOING/DONE in `.scaleup/my-company/tasks.md`. Each task linked to a decision area and the annual goal |
| S7.5 | Accountability loop | M | On session start: review open tasks, ask for status updates, celebrate completions, address blockers. Follow-up on commitments from previous sessions |
| S7.6 | Company knowledge graph | S | Store company-specific facts (org structure, key metrics, competitive landscape) as structured nodes in `.scaleup/my-company/context/`. Agent references these for personalized coaching |

### Dependencies
- E6 complete (memory system references ontology nodes for linking tasks to methodology)

### Done Criteria
- [ ] Agent remembers company context across sessions without re-asking
- [ ] Session start loads full context in under 5 seconds
- [ ] Task board persists between sessions, tracks decision area per task
- [ ] Annual goal is visible in every coaching interaction
- [ ] Accountability loop fires automatically on session start

---

## E8 — Coaching Engine

**Objective:** Turn the ontology and intelligence into an active coaching experience — guide entrepreneurs through worksheets, track methodology progress, and adapt to their mastery level.

### Stories

| ID | Story | Size | Description |
|----|-------|------|-------------|
| S8.1 | Onboarding skill — `/scaleup-welcome` | M | Ask: company name, location, employees, what they sell. Detect business stage (startup/growth/scaling/expansion per Verne's stages). Offer Lean Canvas (starting/reinventing) or BMC (expansion). Save to `.scaleup/my-company/profile.md` |
| S8.2 | Diagnosis skill — `/scaleup-diagnose` | M | Score each of 4 decisions (1-5 scale). Use structured questions mapped to ontology. Generate prioritized recommendation: which decision to tackle first and why |
| S8.3 | Worksheet guidance engine | L | `/scaleup-worksheet [name]` — retrieve worksheet from ontology, walk user through it step by step, validate inputs, save completed worksheet to `.scaleup/my-company/worksheets/`. Track completion status in registry |
| S8.4 | Methodology progress tracker | M | `/scaleup-progress` — show completion percentage per decision area (People/Strategy/Execution/Cash), list completed vs pending worksheets, suggest next worksheet based on diagnosis scores and dependencies |
| S8.5 | Level-aware coaching (Shu/Ha/Ri) | M | Detect mastery level from diagnosis scores and worksheet completion. Shu (beginner): step-by-step with explanations. Ha (intermediate): frameworks with autonomy. Ri (advanced): strategic challenges and edge cases. Adjust tone and depth accordingly |
| S8.6 | Sub-agent routing | S | Route to specialized sub-agents (People, Strategy, Execution, Cash) based on diagnosis scores and user requests. Each sub-agent has deep context on its decision area via ontology traversal |

### Dependencies
- E6 complete (ontology drives worksheet content and relationships)
- E7 complete (memory system stores progress, session continuity enables multi-session coaching)

### Done Criteria
- [ ] New user goes through onboarding in under 10 minutes
- [ ] Diagnosis produces actionable prioritization across 4 decisions
- [ ] All 34 worksheets are guidable and saveable
- [ ] Progress shows accurate completion per decision area
- [ ] Coaching tone adapts visibly based on mastery level
- [ ] Sub-agents activate correctly based on routing rules

---

## E9 — Value-Add Features

**Objective:** Deliver export, pulse diagnostics, and a progress dashboard — features that make the coaching tangible and shareable with the entrepreneur's team.

### Stories

| ID | Story | Size | Description |
|----|-------|------|-------------|
| S9.1 | Action plan export | M | `/scaleup-export` — generate a shareable markdown document with: current diagnosis, annual goal, active priorities, open tasks, next steps. Formatted for sharing with leadership team or board |
| S9.2 | Quarterly pulse | M | `/scaleup-pulse` — 5-question re-diagnosis (one per decision + overall). Compare scores vs previous pulse. Detect trends (improving, stalling, regressing). Suggest course corrections |
| S9.3 | Progress dashboard | M | `/scaleup-dashboard` — visual overview (ASCII/markdown) of scores across 4 decisions over time. Show trajectory, highlight wins, flag areas needing attention. Pull data from session history |
| S9.4 | Coaching session summary | S | At session close, auto-generate a summary: what was discussed, decisions made, tasks created, worksheets completed. Append to `.scaleup/my-company/sessions/` as a log |

### Dependencies
- E8 complete (dashboard and pulse need methodology tracking data; export needs task board and diagnosis data)

### Done Criteria
- [ ] Export produces a clean, shareable markdown document
- [ ] Pulse re-diagnosis completes in under 5 minutes
- [ ] Dashboard shows historical score progression
- [ ] Session summaries are auto-generated and stored

---

## E4 — Validation

**Objective:** End-to-end testing of the complete product flow — from clone to coaching — ensuring reliability before public distribution.

### Stories

| ID | Story | Size | Description |
|----|-------|------|-------------|
| S4.1 | Onboarding flow validation | M | Test: clone repo, open Claude Code, run `/scaleup-welcome`, verify profile creation and diagnosis routing |
| S4.2 | Coaching flow validation | M | Test: full cycle from diagnosis through worksheet completion. Verify memory persistence, progress tracking, sub-agent routing |
| S4.3 | Edge case testing | M | Test: returning user with existing data, user skipping steps, incomplete worksheets, conflicting inputs, session crash recovery |
| S4.4 | Knowledge integrity validation | S | Verify: all 68 methodologies accessible, all 34 worksheets guidable, ontology relationships consistent, no broken references |
| S4.5 | Performance and UX validation | S | Verify: session start under 5 seconds, no excessive context loading, slash commands discoverable, error messages helpful |

### Dependencies
- E9 complete (all features must exist before comprehensive validation)

### Done Criteria
- [ ] Full onboarding-to-coaching flow works without errors
- [ ] Memory persists correctly across 3+ sessions
- [ ] All 34 worksheets complete without errors
- [ ] Edge cases handled gracefully with helpful messages
- [ ] No performance bottlenecks in normal usage

---

## E5 — Distribution

**Objective:** Publish the product to GitHub as a clean, public repo that any entrepreneur can clone and use immediately.

### Stories

| ID | Story | Size | Description |
|----|-------|------|-------------|
| S5.1 | Git history cleanup | M | Clean history of any sensitive data, dev artifacts, or noisy commits. Produce a clean, professional commit history |
| S5.2 | GitHub repo setup | S | Configure repo: description, topics, license (MIT or Apache 2.0), social preview image, branch protection on main |
| S5.3 | Release packaging | S | Tag v1.0.0, create GitHub release with changelog, verify clone-and-run works from the public URL |
| S5.4 | Launch README and examples | M | Final README polish with screenshots/examples. Add a `/examples` directory with sample company profiles showing what a completed coaching journey looks like |

### Dependencies
- E4 complete (product must be validated before public release)

### Done Criteria
- [ ] Public repo is cloneable and functional within 5 minutes
- [ ] No sensitive data in git history
- [ ] README is compelling and clear for non-technical entrepreneurs
- [ ] v1.0.0 release tagged and published
- [ ] At least one example company profile included

---

## Timeline Estimate

| Epic | Estimated Effort | Cumulative | Status |
|------|-----------------|------------|--------|
| E3 — Agent Framework | done | — | DONE |
| E6 — Knowledge Ontology | done | — | DONE |
| E7 — Agent Intelligence | 6 stories (~4-6 sessions) | ~6 sessions | IN PROGRESS |
| E8 — Coaching Engine | 6 stories (~5-7 sessions) | ~13 sessions | planned |
| E9 — Value-Add | 4 stories (~3-4 sessions) | ~17 sessions | planned |
| E10 — Skill Refactor | ~4-6 stories (TBD) | ~21 sessions | planned |
| E4 — Validation | 5 stories (~3-4 sessions) | ~25 sessions | planned |
| E5 — Distribution | 4 stories (~2-3 sessions) | ~28 sessions | planned |

**Total: ~28 sessions to v1.0.0**

## Risk Register

| Risk | Mitigation |
|------|-----------|
| Ontology design too complex | Start with minimal viable graph (just 4 decision nodes + tools). Add relationships incrementally |
| Context window limits with large ontology | Selective loading — only load relevant decision subgraph per session. Never load full ontology at once |
| Worksheet guidance quality varies | Template each worksheet with structured prompts. Test each individually in E4 |
| Session memory corruption | YAML with schema validation. Backup on session close. Human-readable = debuggable |
| Scope creep in coaching features | E8 is the biggest risk. Timebox each story. Ship minimal viable coaching first, refine in post-v1 |

---

*Created: 2026-03-17*
*Status: Active*
*Owner: ScaleUp Agent AI Team*
