---
name: escala-close-capture
description: 'Collect session activity data from user. Sub-skill del procedimiento interno `escala-close`.'
---

# Capture Session Activity

## Purpose

Ask the user what was accomplished during the session and collect structured data. Sub-skill del procedimiento interno `escala-close`.

## Steps

### Step 1: Ask About Decision Focus

Ask conversationally:

> "¿En qué parte de tu negocio trabajamos hoy: tu equipo, tus clientes y tu estrategia, tu día a día o tu dinero?"

Accept the answer and store it with its internal id (people, strategy, execution or cash). If unclear, infer from the tools/worksheets used during the session.

### Step 2: Ask About Worksheets

> "¿Trabajamos algún worksheet o herramienta específica?"

Examples: Core Values, Plan Estratégico de Una Página (OPSP), CCC, Hábitos de Ejecución, etc.

### Step 3: Ask About Tasks

> "¿Creamos tareas nuevas? ¿Completamos alguna existente?"

Collect task descriptions for created and completed tasks.

### Step 4: Ask About Duration

> "¿Cuánto tiempo llevó la sesión aproximadamente? (en minutos)"

If the user doesn't know, estimate based on conversation length.

### Step 5: Produce Structured Output

Compile into structured data:

```yaml
decision_focus: people
duration_minutes: 45
worksheets_completed: [core-values-worksheet]
tasks_created: [validar-valores-con-equipo]
tasks_completed: []
notes:
  - Discussed core values candidates
  - Identified 3 potential values
```

## Output

Structured capture data for the session log writer.

---
