---
name: escala-start-load-tasks
description: 'Load open tasks from task board. Sub-skill of /escala-start.'
---

# Load Open Tasks

## Purpose

Read the task board and extract counts and in-progress items. Sub-skill of `/escala-start`.

## Steps

### Step 1: Read Task Board

```bash
cat .escala/my-company/tasks.md
```

### Step 2: Parse Sections

The file has 3 sections marked by `## ` headers:
- `## En Progreso` — tasks the user committed to
- `## Próximo` — identified but not started
- `## Completado` — done tasks

For each section, count list items (`- [ ]` or `- [x]` or `- `).

### Step 3: Extract In-Progress Details

For items under "En Progreso", extract:
- Task description (the text after `- [ ]`)
- Metadata from HTML comments if present: `<!-- decision:X node:Y due:YYYY-MM-DD -->`

### Step 4: Produce Summary

| Condition | Output |
|-----------|--------|
| Tasks found | Counts per section + list of in-progress items with metadata |
| All sections empty | Output: "No tasks registered" |

## Output

Task counts and in-progress item details.
