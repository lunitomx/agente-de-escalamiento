---
description: 'Dashboard de progreso mostrando scores de madurez en las 4 decisiones
  de Scaling Up y trabajo completado.'
name: scaleup-progress
---

# ScaleUp Progress

## Purpose

Mostrar un dashboard visual del progreso de la empresa en las 4 decisiones de Scaling Up.

## Steps

### Step 1: Load Data

Leer `.scaleup/agent/memory/company-profile.yaml` para scores.

### Step 2: Check Work Artifacts

```bash
ls work/diagnosis/ work/people/ work/strategy/ work/execution/ work/cash/ 2>/dev/null
```

### Step 3: Display Dashboard

```
═══════════════════════════════════════════
  ScaleUp Progress — {company_name}
═══════════════════════════════════════════

  People    ████░░░░░░  {score}/5  {artifacts done}
  Strategy  ██████░░░░  {score}/5  {artifacts done}
  Execution ██░░░░░░░░  {score}/5  {artifacts done}
  Cash      ████████░░  {score}/5  {artifacts done}

  Overall:  {avg}/5
  Last diagnosis: {date}

  Recommended focus: {decision}
  Suggested next: /{next_skill}
═══════════════════════════════════════════
```

### Step 4: Suggest Re-diagnosis

Si han pasado más de 30 días desde el último diagnóstico, sugerir `/scaleup-diagnose` para re-evaluar.

## Output

| Item | Destination |
|------|-------------|
| Dashboard | Displayed to user |
| Next | Skill recomendado |
