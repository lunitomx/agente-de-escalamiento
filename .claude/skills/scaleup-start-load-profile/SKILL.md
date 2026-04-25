---
name: scaleup-start-load-profile
description: 'Load company profile from YAML. Sub-skill of /scaleup-start.'
---

# Load Company Profile

## Purpose

Read the company profile YAML and extract context for the session. Sub-skill of `/scaleup-start`.

## Steps

### Step 1: Read Profile

```bash
cat .scaleup/agent/memory/company-profile.yaml
```

### Step 2: Extract Context

From the YAML, extract:
- `company.name` — company name
- `company.growth_stage` — startup / scaleup / established / enterprise
- `company.employees` — employee count
- `company.industry` — sector
- `scores.people`, `scores.strategy`, `scores.execution`, `scores.cash` — diagnosis scores (1-5)
- `scores.last_diagnosis` — date of last diagnosis
- `focus.current_decision` — what decision they're working on
- `focus.last_session` — date of last session

### Step 3: Check Profile Completeness

| Condition | Output |
|-----------|--------|
| `company.name` is filled | Output structured context with all fields |
| `company.name` is empty or missing | Output signal: `PROFILE_EMPTY` |

## Output

Structured context block with company data, or `PROFILE_EMPTY` signal.
