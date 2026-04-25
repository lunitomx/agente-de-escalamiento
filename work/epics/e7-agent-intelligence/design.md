# Epic Design: E7 — Agent Intelligence

## Gemba Findings

### Current State

1. **Dual profile storage (conflict):**
   - `.scaleup/my-company/profile.md` — markdown template, user-facing, empty
   - `.scaleup/agent/memory/company-profile.yaml` — YAML with scores, agent-facing, empty
   - `/scaleup-welcome` writes to YAML only. User never sees their data in readable format.
   - **Decision:** Unify. YAML is source of truth (agent reads). Markdown is generated view (human reads). One write, two outputs.

2. **Existing templates (reuse):**
   - `my-company/profile.md` — company info (needs filling logic)
   - `my-company/annual-goal.md` — SMART goal with 4-decision connection
   - `my-company/quarterly-focus.md` — rocks, critical number, theme
   - `my-company/tasks.md` — kanban board (En Progreso / Próximo / Completado)
   - All have HTML comment placeholders — good structure, just need a write mechanism.

3. **No session infrastructure:**
   - No `my-company/sessions/` directory
   - No session log format
   - No "last session" tracking beyond `company-profile.yaml.focus.last_session`

4. **KnowledgeGraph ready (E6):**
   - `retrieval.py` with query/traverse/path/worksheets API
   - 70 nodes, 301 edges, worksheet registry
   - Ready to link tasks → methodology nodes

5. **Skills don't load context on start:**
   - Each skill reads its own files independently
   - No shared "context loader" across skills

### Patterns to Follow

- YAML for machine data, markdown for human-readable views
- HTML comments as placeholder instructions (PAT-L-001)
- Keep everything in `.scaleup/my-company/` — user's data stays in user's space
- Agent config in `.scaleup/agent/` — separated concerns (PAT-L-002)

## Architecture Decisions

### ADR-1: Single Source of Truth for Company Data

**Context:** Two files store company info. Skills write to different ones.

**Decision:** `company-profile.yaml` is the single source. Skills read/write YAML. On session close, generate markdown views into `my-company/*.md` for human readability.

**Rationale:** YAML is parseable, merge-friendly, queryable. Markdown is for the entrepreneur to read in GitHub/editor.

### ADR-2: Session Log Format

**Context:** Need to track what happened across sessions for accountability loop.

**Decision:** One file per session: `.scaleup/my-company/sessions/YYYY-MM-DD.md` with structured frontmatter (YAML) + free-form notes.

```yaml
---
date: 2026-04-25
duration_minutes: 45
decision_focus: people
worksheets_completed: [core-values-worksheet]
tasks_created: [task-1, task-2]
tasks_completed: [task-0]
score_changes: {people: "2→3"}
---
## Session Notes
- Discussed core values exercise
- Identified 3 candidate values
- Next: validate with leadership team
```

**Rationale:** File-per-session = easy to list, sort, and load recent. YAML frontmatter = machine-parseable. Markdown body = human-readable.

### ADR-3: Task Identity and Linking

**Context:** Tasks need to link to decisions and methodology nodes.

**Decision:** Tasks live in `my-company/tasks.md` as markdown list items with inline metadata:

```markdown
## En Progreso
- [ ] Completar ejercicio de Core Values <!-- decision:people node:core-values-worksheet due:2026-05-01 -->
```

**Rationale:** Readable in any editor. HTML comments carry metadata without cluttering the view. Matches PAT-L-001.

### ADR-4: Context Loading Strategy

**Context:** Multiple skills need company context. Loading is scattered.

**Decision:** Create a shared context loader function in the session start skill that reads: company-profile.yaml + annual-goal + quarterly-focus + last 3 sessions + open tasks. Present as structured context block.

**Rationale:** One load path = consistent context. Skills reference loaded context, don't reload independently.

## Story Refinement (post-gemba)

| ID | Story | Size | Gemba Impact |
|----|-------|------|-------------|
| S7.1 | Session lifecycle | M | Must unify profile storage. Session log format (ADR-2). Context loader (ADR-4). |
| S7.2 | Persistent memory | M | YAML source of truth (ADR-1). Generate markdown views. Diagnosis history tracking. |
| S7.3 | SMART annual goal | S | Template exists. Add read/write logic to skills. Filter mechanism in recommendations. |
| S7.4 | Task board | M | Template exists. Add metadata format (ADR-3). Link to ontology nodes. CRUD operations. |
| S7.5 | Accountability loop | M | Depends on S7.1 (sessions) + S7.4 (tasks). Auto-review on session start. |
| S7.6 | Company knowledge graph | S | Extend company-profile.yaml with structured facts. Org chart, key metrics, competitive notes. |

## Dependency Graph

```
S7.1 Session lifecycle
  ↓
S7.2 Persistent memory ──→ S7.3 SMART goal (parallel with S7.4)
  ↓                              ↓
S7.4 Task board ←────────────────┘
  ↓
S7.5 Accountability loop
  ↓
S7.6 Company knowledge graph (can start after S7.2)
```

Critical path: S7.1 → S7.2 → S7.4 → S7.5

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Context loading too slow with many sessions | Low | Medium | Only load last 3 sessions + summary of older ones |
| Task board gets cluttered | Medium | Low | Auto-archive completed tasks older than 30 days |
| YAML/markdown sync drift | Medium | Medium | Generate markdown on session close only, never edit markdown directly |
