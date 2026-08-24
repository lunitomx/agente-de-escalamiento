---
name: scaleup-start-load-sessions
description: 'Load last 3 session logs. Sub-skill of /scaleup-start.'
---

# Load Recent Sessions

## Purpose

Read the most recent session logs and produce a summary. Sub-skill of `/scaleup-start`.

## Steps

### Step 1: List Session Files

```bash
ls -1 .scaleup/my-company/sessions/*.md 2>/dev/null | sort | tail -3
```

Filenames are `YYYY-MM-DD.md` — lexicographic sort equals chronological order.

### Step 2: Read Each Session

For each of the last 3 files, read the YAML frontmatter and extract:
- `date` — session date
- `decision_focus` — which decision was worked on
- `duration_minutes` — how long
- `worksheets_completed` — if any
- `tasks_created` — if any

### Step 3: Produce Summary

| Condition | Output |
|-----------|--------|
| Sessions found | Summary table: date, focus, duration, key outcomes |
| No sessions directory or empty | Output: "No previous sessions found" |

## Output

Summary of last 3 sessions, or empty summary message.
