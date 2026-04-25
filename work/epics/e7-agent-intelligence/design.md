# Epic Design: E7 — Agent Intelligence

## Orchestration Pattern (ADR-0)

**Context:** Emilio Osorio (2026-04-25) — un skill grande con muchas fases produce baja calidad. El LLM "hace patito para cumplir" cuando tiene demasiadas responsabilidades en un solo contexto.

**Decision:** Toda funcionalidad de E7 se construye con el patrón:

```
Orchestrator Skill (secuencial)
  ├── subagent: step-1  → artefacto verificable
  │     └── quality gate (código, no LLM)
  ├── subagent: step-2  → artefacto verificable
  │     └── quality gate
  └── resultado final
```

**Reglas:**
1. Cada skill hace UNA cosa, produce UN artefacto
2. Quality gates son validadores en código (Python), NO el LLM evaluándose a sí mismo
3. Cada fase se lanza como subagente con su propio contexto de inferencia
4. El orquestador solo secuencia, valida artefactos y pasa contexto mínimo al siguiente paso
5. Primero skill de orquestación (probar ~1 semana), después convertir a YAML config para engine

**Implicación para skills existentes:** Los 20 skills actuales (welcome, diagnose, etc.) NO se tocan en E7. Se adaptan en una épica futura (E10) una vez que el patrón esté probado.

## Gemba Findings

### Current State

1. **Dual profile storage (conflict):**
   - `.scaleup/my-company/profile.md` — markdown template, user-facing, empty
   - `.scaleup/agent/memory/company-profile.yaml` — YAML with scores, agent-facing, empty
   - **Decision:** YAML es source of truth. Markdown se genera como vista.

2. **Existing templates (reuse):**
   - `my-company/profile.md`, `annual-goal.md`, `quarterly-focus.md`, `tasks.md`
   - Todos con HTML comment placeholders — buena estructura, falta write mechanism.

3. **No session infrastructure:**
   - No `my-company/sessions/` directory
   - No session log format
   - No "last session" tracking

4. **KnowledgeGraph ready (E6):**
   - `retrieval.py` — query/traverse/path/worksheets API
   - 70 nodes, 301 edges, worksheet registry

5. **Skills don't share context:**
   - Each skill loads its own files independently
   - No shared context loader

## Architecture Decisions

### ADR-1: Single Source of Truth for Company Data

`company-profile.yaml` is the single source. Skills read/write YAML. On session close, generate markdown views for human readability.

### ADR-2: Session Log Format

One file per session: `.scaleup/my-company/sessions/YYYY-MM-DD.md`

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
- Next: validate with leadership team
```

### ADR-3: Task Identity and Linking

Tasks in `my-company/tasks.md` with inline HTML comment metadata:

```markdown
## En Progreso
- [ ] Completar Core Values <!-- decision:people node:core-values-worksheet due:2026-05-01 -->
```

### ADR-4: Context Loading as Pipeline

Context loading is itself a pipeline of subagents:

```
/scaleup-start (orchestrator)
  ├── load-profile     → context.yaml (company data + scores)
  ├── load-sessions    → recent-sessions.yaml (last 3)
  ├── load-tasks       → open-tasks.yaml (pending items)
  ├── quality gate     → ¿profile exists? ¿tasks parseable?
  └── present-context  → formatted summary to user
```

### ADR-5: Validators in Code

Quality gates are Python functions, not LLM prompts:

```python
def validate_profile(profile_path: Path) -> bool:
    """Check company-profile.yaml has required fields filled."""
    data = yaml.safe_load(profile_path.read_text())
    return bool(data.get("company", {}).get("name"))

def validate_session_log(log_path: Path) -> bool:
    """Check session log has valid frontmatter."""
    # parse YAML frontmatter, verify required keys
    ...
```

## Story Decomposition (orchestration-aware)

### S7.1 — Session Lifecycle Pipeline

**Orchestrator:** `/scaleup-start` and `/scaleup-close`
**Sub-skills:**
- `scaleup-start-load` — read YAML files, build context bundle
- `scaleup-start-review` — analyze context, detect signals (stale tasks, score changes, time since last session)
- `scaleup-start-present` — present summary to user, propose focus
- `scaleup-close-capture` — collect session artifacts
- `scaleup-close-log` — write session log file
- `scaleup-close-sync` — generate markdown views from YAML

**Validators:** profile exists, session log format valid, context bundle complete

### S7.2 — Persistent Memory

**Sub-skills:**
- `scaleup-memory-write` — write structured data to YAML
- `scaleup-memory-read` — read and merge company data sources
- `scaleup-memory-render` — generate markdown views from YAML

**Validators:** YAML schema validation, required fields check

### S7.3 — SMART Annual Goal

**Sub-skills:**
- `scaleup-goal-set` — guided goal creation, write to annual-goal.yaml
- `scaleup-goal-filter` — given a recommendation, evaluate against goal alignment

**Validators:** goal has all SMART components, KPI has numeric target

### S7.4 — Task Board

**Sub-skills:**
- `scaleup-task-add` — create task with decision/node metadata
- `scaleup-task-update` — move task between states
- `scaleup-task-list` — render current board

**Validators:** task has decision tag, no duplicate IDs, dates parseable

### S7.5 — Accountability Loop

**Orchestrator:** runs inside `scaleup-start-review`
**Sub-skills:**
- `scaleup-accountability-scan` — find overdue/stale tasks
- `scaleup-accountability-prompt` — generate follow-up questions

**Validators:** all open tasks have dates, overdue detection is date-math not LLM

### S7.6 — Company Knowledge Graph

**Sub-skills:**
- `scaleup-context-add` — add structured fact (org, metric, competitor)
- `scaleup-context-query` — retrieve facts by category

**Validators:** fact has category tag, no contradicting facts

## Dependency Graph

```
S7.1 Session lifecycle (orchestrator + 6 sub-skills)
  ↓
S7.2 Persistent memory (3 sub-skills)
  ├──→ S7.3 SMART goal (2 sub-skills)
  └──→ S7.4 Task board (3 sub-skills)
         ↓
       S7.5 Accountability loop (2 sub-skills, embedded in S7.1)
  ↓
S7.6 Company knowledge graph (2 sub-skills)
```

Critical path: S7.1 → S7.2 → S7.4 → S7.5

## Parking Lot

- **E10 (future):** Adapt existing 20 skills to orchestration pattern
  - `/scaleup-welcome` → pipeline: intake → validate → save → present
  - `/scaleup-diagnose` → pipeline: load-context → assess-people → assess-strategy → assess-execution → assess-cash → generate-report → route
  - Each assessment as its own subagent with focused context
  - Quality gates: score validation, routing logic in code

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Over-engineering sub-skills for simple operations | Medium | Medium | If a step is < 20 lines of logic, inline it in orchestrator |
| Context loading too slow with many sessions | Low | Medium | Only load last 3 sessions |
| Subagent overhead for trivial tasks | Medium | Low | Only use subagents when context isolation improves quality |
| YAML/markdown sync drift | Medium | Medium | Generate markdown on session close only |
