---
name: escala-close-log
description: 'Write session log file with YAML frontmatter. Sub-skill del procedimiento interno `escala-close`.'
---

# Write Session Log

## Purpose

Take captured session data and write a structured log file. Sub-skill del procedimiento interno `escala-close`.

## Steps

### Step 1: Determine Filename

Base filename: `YYYY-MM-DD.md` using today's date.

Check if file already exists:

```bash
ls .escala/my-company/sessions/YYYY-MM-DD*.md 2>/dev/null
```

| Condition | Filename |
|-----------|----------|
| No existing file | `YYYY-MM-DD.md` |
| `YYYY-MM-DD.md` exists | `YYYY-MM-DD-2.md` |
| `YYYY-MM-DD-2.md` also exists | `YYYY-MM-DD-3.md` |

### Step 2: Ensure Directory Exists

```bash
mkdir -p .escala/my-company/sessions
```

### Step 3: Write Session Log

Write to `.escala/my-company/sessions/{filename}`:

```markdown
---
date: {YYYY-MM-DD}
duration_minutes: {N}
decision_focus: {people|strategy|execution|cash}
worksheets_completed: [{list}]
tasks_created: [{list}]
tasks_completed: [{list}]
---
## Session Notes
- {note 1}
- {note 2}
- {note 3}
```

**Required fields:** `date`, `duration_minutes`, `decision_focus`
**Optional fields:** `worksheets_completed`, `tasks_created`, `tasks_completed`, `score_changes`

### Step 4: Confirm Write

Report the file path and contents written.

## Output

Session log file at `.escala/my-company/sessions/{filename}`.
