---
name: escala-start-present
description: 'Present session context summary to user. Sub-skill del procedimiento interno `escala-start`.'
---

# Present Session Context

## Purpose

Format and present the loaded context to the user. Sub-skill del procedimiento interno `escala-start`.

## Steps

### Step 1: Receive Context

The orchestrator passes:
- Company profile data (name, stage, scores)
- Recent sessions summary (last 3)
- Open tasks summary (counts + in-progress items)

### Step 2: Format Presentation

Present in this format:

```
══════════════════════════════════════════════
  {company_name} — Sesión {date}
══════════════════════════════════════════════

  Scores:  People {N} │ Strategy {N} │ Execution {N} │ Cash {N}

  Últimas sesiones:
  - {date}: {focus} ({duration} min)
  - {date}: {focus} ({duration} min)

  Tareas en progreso: {count}
  {list each in-progress task}

──────────────────────────────────────────────
  Recomendación: {proposed focus}
══════════════════════════════════════════════
```

### Step 3: Propose Focus

Determine recommended focus using this priority:
1. If there are overdue tasks → "Revisar tareas pendientes"
2. If a decision has score 1 → recommend that decision (lowest first)
3. If previous session had unfinished work → "Continuar con {decision}"
4. If all scores >= 3 → "Revisión general o re-diagnóstico"

## Output

Formatted context summary displayed to user with focus recommendation.
