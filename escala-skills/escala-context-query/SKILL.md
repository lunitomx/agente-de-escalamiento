---
name: escala-context-query
description: 'Query company facts by category from the knowledge graph.'
---

# Query Company Context

## Purpose

Retrieve stored facts about the company by category.

## Steps

### Step 1: Determine Query

Accept a category filter: org, metrics, competitive, custom, or "all".

### Step 2: Read Files

Read the appropriate YAML file(s) from `.scaleup/my-company/context/`.

### Step 3: Present

Display facts grouped by category:

```
Company Context:

  Org ({count}):
  - {fact} (added: {date})

  Metrics ({count}):
  - {fact} (added: {date})
```

If no facts exist, report: "No hay hechos registrados. Usa /escala-context-add para agregar."

## Output

Formatted list of company facts.
