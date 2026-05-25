     1|---
     2|description: 'Evaluación de los 10 Hábitos de Ejecución. Diagnóstico de disciplina
     3|  de ejecución con scoring y plan de acción.'
     4|name: escala-execution-habits
     5|---
     6|
     7|# Escalamiento Execution — Hábitos de Ejecución Checklist
     8|
     9|## Purpose
    10|
    11|Evaluar los 10 Hábitos de Ejecución de la empresa, identificar los más débiles y crear plan de acción.
    12|
    13|## Steps
    14|
    15|### Step 1: Load Context
    16|
    17|Leer `.escala/knowledge/execution/tools/ejecucion-habits-checklist.md`.
    18|Cargar template `templates/ejecucion-habits-checklist.md`.
    19|
    20|### Step 2: Evaluate Each Habit
    21|
    22|Para cada uno de los 10 hábitos, preguntar al usuario cómo lo implementan y asignar score 1-5 colaborativamente.
    23|
    24|### Step 3: Score & Prioritize
    25|
    26|Calcular score total (/50). Identificar top 3 hábitos a mejorar.
    27|
    28|### Step 4: Action Plan
    29|
    30|Para los 3 hábitos más débiles, crear plan de acción concreto con timeline.
    31|
    32|### Step 5: Save
    33|
    34|Guardar en `work/execution/ejecucion-habits.md`.
    35|
    36|## Output
    37|
    38|| Item | Destination |
    39||------|-------------|
    40|| Hábitos de Ejecución evaluation | `work/execution/ejecucion-habits.md` |
    41|| Next | `/escala-execution-rhythms` |
    42|