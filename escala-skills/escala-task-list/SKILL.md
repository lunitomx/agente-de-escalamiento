---
name: escala-task-list
description: 'Display the current Agente de Escalamiento task board with counts and metadata.'
---

# List Tasks

## Purpose

Show the current state of the task board with counts per section and metadata.

## Steps

### Step 1: Read Board

Read `.escala/my-company/tasks.md`.

### Step 2: Parse and Count

For each section (En Progreso, Próximo, Completado):
- Count tasks
- Extract metadata from HTML comments (decision, node, due date)
- Flag overdue tasks (due date < today)

### Step 3: Present

```
═══════════════════════════════════════
  Task Board
═══════════════════════════════════════

  En Progreso ({count}):
  - {task} [decision] {due date or ""}
  - {task} [decision] ⚠️ OVERDUE

  Próximo ({count}):
  - {task} [decision]

  Completado ({count}):
  - {task} ✓

═══════════════════════════════════════
```

## Output

Formatted task board displayed to user.
