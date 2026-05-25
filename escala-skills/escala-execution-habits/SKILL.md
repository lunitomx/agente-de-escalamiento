     1|     1|---
     2|     2|description: 'Evaluación de los 10 Hábitos de Ejecución. Diagnóstico de disciplina
     3|     3|  de ejecución con scoring y plan de acción.'
     4|     4|name: escala-execution-habits
     5|     5|---
     6|     6|
     7|     7|# Escalamiento Execution — Hábitos de Ejecución Checklist
     8|     8|
     9|     9|## Purpose
    10|    10|
    11|    11|Evaluar los 10 Hábitos de Ejecución de la empresa, identificar los más débiles y crear plan de acción.
    12|    12|
    13|    13|## Steps
    14|    14|
    15|    15|### Step 1: Load Context
    16|    16|
    17|    17|Leer `.escala/knowledge/execution/tools/ejecucion-habits-checklist.md`.
    18|    18|Cargar template `templates/ejecucion-habits-checklist.md`.
    19|    19|
    20|    20|### Step 2: Evaluate Each Habit
    21|    21|
    22|    22|Para cada uno de los 10 hábitos, preguntar al usuario cómo lo implementan y asignar score 1-5 colaborativamente.
    23|    23|
    24|    24|### Step 3: Score & Prioritize
    25|    25|
    26|    26|Calcular score total (/50). Identificar top 3 hábitos a mejorar.
    27|    27|
    28|    28|### Step 4: Action Plan
    29|    29|
    30|    30|Para los 3 hábitos más débiles, crear plan de acción concreto con timeline.
    31|    31|
    32|    32|### Step 5: Save
    33|    33|
    34|    34|Guardar en `work/execution/ejecucion-habits.md`.
    35|    35|
    36|    36|## Output
    37|    37|
    38|    38|| Item | Destination |
    39|    39||------|-------------|
    40|    40|| Hábitos de Ejecución evaluation | `work/execution/ejecucion-habits.md` |
    41|    41|| Next | `/escala-execution-rhythms` |
    42|    42|

---
*> Esta herramienta está inspirada en los Hábitos de Ejecución, desarrollados por Verne Harnish como parte de su metodología de escalamiento de negocios. Ver [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) para la referencia completa.
