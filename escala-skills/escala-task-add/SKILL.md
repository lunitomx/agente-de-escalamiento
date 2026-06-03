---
name: escala-task-add
description: 'Add a task to the Agente de Escalamiento task board with decision and ontology links.'
---

# Add Task

## Purpose

Create a new task in the task board linked to a Escalamiento de Negocios decision and optionally to an ontology node.

## Steps

### Step 1: Collect Task Info

Ask or infer:
- **Description:** What needs to be done
- **Decision:** people / strategy / execution / cash
- **Due date:** YYYY-MM-DD (optional)
- **Ontology node:** worksheet or tool ID (optional, e.g. `core-values-worksheet`)

### Step 2: Format Task Entry

```markdown
- [ ] {description} <!-- decision:{decision} node:{node} due:{date} -->
```

If no node or date, omit those fields from the comment.

### Step 3: Append to Task Board

Read `.scaleup/my-company/tasks.md`. Append the new task under `## En Progreso` section.

### Step 4: Confirm

Report: "Tarea agregada: {description} (decision: {decision})"

## Output

Updated `.scaleup/my-company/tasks.md` with new task.
