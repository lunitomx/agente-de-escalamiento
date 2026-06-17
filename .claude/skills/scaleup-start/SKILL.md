---
name: scaleup-start
description: 'Session start orchestrator. Loads company context, recent sessions, and open tasks. Presents summary and proposes focus.'
---

# ScaleUp Start — Session Orchestrator

## Purpose

Load company context at the start of a coaching session. Presents a summary of the company's current state, recent sessions, and open tasks. Proposes a focus for the session.

## Pipeline

This skill orchestrates 4 phases inline (file reads are simple enough to not require subagents). Quality gate validates profile completeness before proceeding.

Canonical pipeline ID: `scaleup-session-start`. Registry: `.raise/pipelines/scaleup.yaml`.

## Steps

### Step 1: Load Company Profile

Read `.scaleup/agent/memory/company-profile.yaml`.

Extract:
- `company.name`, `company.growth_stage`, `company.employees`, `company.industry`
- `scores.people`, `scores.strategy`, `scores.execution`, `scores.cash`
- `scores.last_diagnosis`
- `focus.current_decision`, `focus.last_session`

### Step 2: Quality Gate — Profile Completeness

Check if `company.name` has a value.

| Condition | Action |
|-----------|--------|
| `company.name` is filled | Continue to Step 3 |
| `company.name` is empty or missing | **HALT** — display message and redirect |

If halted, present:

```
No tengo información de tu empresa todavía.
Ejecuta /scaleup-welcome para crear tu perfil.
```

Do NOT proceed past this point without a valid profile.

### Step 3: Load Recent Sessions

```bash
ls -1 .scaleup/my-company/sessions/*.md 2>/dev/null | sort | tail -3
```

For each file found, read the YAML frontmatter and extract: `date`, `decision_focus`, `duration_minutes`.

If no sessions exist, note "Sin sesiones previas" and continue.

### Step 4: Load Open Tasks

Read `.scaleup/my-company/tasks.md`.

Parse the three sections:
- **En Progreso** — count items, list each with description
- **Próximo** — count items
- **Completado** — count items

If all sections are empty, note "Sin tareas registradas".

### Step 4b: Accountability Check

Run the overdue detection gate:

```bash
python3 -c "
import sys, pathlib
sys.path.insert(0, str(pathlib.Path('.scaleup/agent')))
from validators.tasks import find_overdue
overdue = find_overdue(pathlib.Path('.scaleup/my-company/tasks.md'))
for t in overdue:
    print(f'OVERDUE: {t[\"description\"]} (due: {t[\"due\"]})')
if not overdue:
    print('NO_OVERDUE')
"
```

If overdue tasks exist, flag them prominently in the presentation:

```
⚠️ Tareas vencidas:
- {task} (vencida desde {due_date})
```

For each overdue task, ask:
- "¿La completaste? → mover a Completado"
- "¿Sigue en progreso? → actualizar fecha"
- "¿Ya no aplica? → eliminar"

This is the accountability loop — the agent follows up on commitments from previous sessions.

### Step 5: Present Context & Propose Focus

Display:

```
══════════════════════════════════════════════════════
  {company_name} — Sesión {today's date}
══════════════════════════════════════════════════════

  Scores:  People {N} │ Strategy {N} │ Execution {N} │ Cash {N}
  Último diagnóstico: {date or "pendiente"}

  Últimas sesiones:
  - {date}: {focus} ({duration} min)
  - {date}: {focus} ({duration} min)
  - {date}: {focus} ({duration} min)

  Tareas en progreso: {count}
  {- task description}
  {- task description}

──────────────────────────────────────────────────────
  Recomendación: {proposed focus}
══════════════════════════════════════════════════════
```

**Focus recommendation logic:**
1. If there are in-progress tasks → "Revisar tareas en progreso"
2. If any score is 1 → recommend that decision (lowest first)
3. If last session had a decision focus → "Continuar con {decision}"
4. If all scores >= 3 → "Revisión general — considera /scaleup-diagnose"

## Output

| Item | Destination |
|------|-------------|
| Context summary | Displayed to user |
| Focus recommendation | Displayed to user |

## Design Notes

Sub-skills exist at `scaleup-start-load-*` for documentation and future use when complexity grows. Currently inlined because each phase is a simple file read (< 20 lines of logic). Per ADR-0: "If a step is < 20 lines of logic, inline it in orchestrator."
