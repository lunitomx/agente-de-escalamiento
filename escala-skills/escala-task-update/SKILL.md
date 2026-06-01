---
name: escala-task-update
description: 'Move a task between states on the Agente de Escalamiento task board.'
---

# Update Task

## Purpose

Move a task between board states: En Progreso → Completado, or Próximo → En Progreso.

## Steps

### Step 1: Identify Task

Ask which task to update, or identify by description match.

### Step 2: Determine New State

| Current | Target | Action |
|---------|--------|--------|
| En Progreso | Completado | Move to `## Completado`, mark `[x]` |
| Próximo | En Progreso | Move to `## En Progreso` |
| En Progreso | Próximo | Move back to `## Próximo` (deprioritize) |

### Step 3: Update Task Board

Read `.escala/my-company/tasks.md`. Remove the task from its current section. Add it to the target section.

If moving to Completado, change `- [ ]` to `- [x]` and append completion date: `<!-- completed:YYYY-MM-DD -->`.

### Step 4: Confirm

Report the move: "{task} moved from {old} to {new}"

## Output

Updated `.escala/my-company/tasks.md` with task in new state.
