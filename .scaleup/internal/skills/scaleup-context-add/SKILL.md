---
name: scaleup-context-add
description: 'Add a structured fact to the company knowledge graph.'
---

# Add Company Context

## Purpose

Store a structured fact about the company for use in personalized coaching.

## Steps

### Step 1: Determine Category

| Category | File | When |
|----------|------|------|
| org | `context/org.yaml` | Team structure, roles, reporting |
| metrics | `context/metrics.yaml` | Revenue, margins, KPIs |
| competitive | `context/competitive.yaml` | Competitors, market position |
| custom | `context/custom.yaml` | Anything else |

### Step 2: Collect Fact

Ask or infer: "What fact should I remember about your company?"

### Step 3: Append to File

Read the appropriate YAML file in `.scaleup/my-company/context/`. Append to the `facts` list:

```yaml
- description: "{the fact}"
  added: "{today's date}"
  source: "session"
```

### Step 4: Confirm

Report: "Registrado: {fact} (categoría: {category})"

## Output

Updated context file in `.scaleup/my-company/context/`.
