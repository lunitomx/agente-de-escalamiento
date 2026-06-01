---
name: escala-close
description: 'Session close orchestrator. Captures session activity, writes log, validates, and syncs state.'
---

# Escalamiento Close — Session Orchestrator

## Purpose

Close the coaching session by capturing what was accomplished, writing a structured session log, and verifying data integrity.

## Pipeline

This skill orchestrates 3 phases + 1 quality gate + 1 summary generation step.

## Steps

### Step 1: Capture Session Activity

Ask the user conversationally:

1. "¿En qué decisión trabajamos hoy?" (People / Strategy / Execution / Cash)
2. "¿Trabajamos algún worksheet o herramienta?"
3. "¿Creamos tareas nuevas o completamos alguna?"
4. "¿Cuánto duró la sesión aproximadamente? (minutos)"

Collect into structured data:
- `decision_focus` — one of: people, strategy, execution, cash
- `duration_minutes` — positive integer
- `worksheets_completed` — list (can be empty)
- `tasks_created` — list (can be empty)
- `tasks_completed` — list (can be empty)
- `notes` — key points from the session

### Step 2: Write Session Log

Determine filename:

```bash
ls .escala/my-company/sessions/$(date +%Y-%m-%d)*.md 2>/dev/null
```

| Existing files | New filename |
|----------------|-------------|
| None | `YYYY-MM-DD.md` |
| `YYYY-MM-DD.md` exists | `YYYY-MM-DD-2.md` |
| `-2` also exists | `YYYY-MM-DD-3.md` |

Ensure directory exists:

```bash
mkdir -p .escala/my-company/sessions
```

Write session log with YAML frontmatter:

```markdown
---
date: {YYYY-MM-DD}
duration_minutes: {N}
decision_focus: {decision}
worksheets_completed: [{list}]
tasks_created: [{list}]
tasks_completed: [{list}]
---
## Session Notes
- {note 1}
- {note 2}
```

### Step 3: Quality Gate — Validate Session Log

Run the Python validator on the written file:

```bash
python3 -c "
import sys, pathlib
sys.path.insert(0, str(pathlib.Path('.escala/agent')))
from validators.session import validate_session_log
errors = validate_session_log(pathlib.Path('{log_file_path}'))
if errors:
    print('FAIL:', errors)
    sys.exit(1)
print('PASS')
"
```

| Result | Action |
|--------|--------|
| PASS (0 errors) | Continue to Step 4 |
| FAIL | Show errors, ask user to clarify, rewrite the log |

### Step 3.5: Generate Session Summary

After Step 3 quality gate passes, invoke the summary module with the session
data collected in Step 1:

```bash
echo '{
  "base_path": ".",
  "log_file_path": "{log_file_path}",
  "date": "{YYYY-MM-DD}",
  "duration_minutes": {N},
  "decision_focus": "{decision}",
  "worksheets_completed": [{worksheets}],
  "tasks_created": [{tasks_created}],
  "tasks_completed": [{tasks_completed}],
  "notes": [{notes}],
  "scores_before": null
}' | python3 -m coaching.summary
```

- Capture the returned JSON. If `errors` is non-empty, surface errors to user and abort.
- Then run the summary quality gate:
  ```bash
  python3 .escala/agent/validators/summary_validator.py {log_file_path}
  ```
  Must exit 0. If it exits 1, surface the error and abort.
- Continue to Step 4 only when both checks pass.

**Adapter rules:**
- MUST NOT contain business logic — only JSON assembly and subprocess invocation.
- MUST NOT re-ask the user any questions (all data already collected in Step 1).
- Step 4 confirmation text is unchanged.

### Step 4: Sync (Stub)

Verify that the session log file exists and is non-empty.

Present confirmation:

```
Sesión registrada: {date} — {decision_focus}
Duración: {duration_minutes} min
{worksheets_count} worksheet(s), {tasks_created_count} tarea(s) creada(s)

¡Nos vemos en la próxima sesión!
```

## Output

| Item | Destination |
|------|-------------|
| Session log | `.escala/my-company/sessions/YYYY-MM-DD.md` |
| Validation | Python quality gate (pass/fail) |
| Confirmation | Displayed to user |
