---
name: scaleup-goal
description: 'Set or view the SMART annual goal. All recommendations filter through this goal.'
---

# ScaleUp Goal — SMART Annual Goal

## Purpose

Set or view the company's annual SMART goal. This goal acts as a strategic filter — every recommendation the agent makes is evaluated against: "Does this advance the annual goal?"

## Steps

### Step 1: Check Current Goal

Read `.scaleup/my-company/annual-goal.md`. If the goal fields are filled, display current goal. If empty, proceed to goal creation.

### Step 2: Goal Creation (if needed)

Guide the user through SMART goal setting:

1. **Meta:** "¿Cuál es tu meta principal del año?" (one sentence)
2. **Específica:** "¿Qué exactamente quieres lograr?"
3. **Medible:** "¿Cómo sabrás que lo lograste? ¿Qué número?"
4. **Alcanzable:** "¿Es realista con tus recursos actuales?"
5. **Relevante:** "¿Por qué esta meta y no otra?"
6. **Temporal:** "¿Para cuándo?"

### Step 3: Define KPI

Ask:
- **Métrica principal:** What number tracks progress?
- **Valor actual:** Where are you now?
- **Valor meta:** Where do you need to be?
- **Fecha límite:** By when?

### Step 4: Connect to 4 Decisions

For each decision, ask how the goal connects:
- **People:** "¿Qué necesitas de tu equipo?"
- **Strategy:** "¿Qué cambio estratégico requiere?"
- **Execution:** "¿Qué disciplina necesitas?"
- **Cash:** "¿Cuánto cash necesitas?"

### Step 5: Save Goal

Write the responses to `.scaleup/my-company/annual-goal.md` filling in the template fields.

### Step 6: Confirm

Display the complete goal and confirm:

```
Meta SMART: {goal}
KPI: {metric} — de {current} a {target} para {deadline}
Filtro activo: toda recomendación se evalúa contra esta meta.
```

## Output

| Item | Destination |
|------|-------------|
| Annual goal | `.scaleup/my-company/annual-goal.md` |
| Filter | Active in all coaching skills |
