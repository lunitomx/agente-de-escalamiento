     1|---
     2|name: escala-close-capture
     3|description: 'Collect session activity data from user. Sub-skill of /escala-close.'
     4|---
     5|
     6|# Capture Session Activity
     7|
     8|## Purpose
     9|
    10|Ask the user what was accomplished during the session and collect structured data. Sub-skill of `/escala-close`.
    11|
    12|## Steps
    13|
    14|### Step 1: Ask About Decision Focus
    15|
    16|Ask conversationally:
    17|
    18|> "¿En qué decisión trabajamos hoy? (People / Strategy / Execution / Cash)"
    19|
    20|Accept the answer. If unclear, infer from the tools/worksheets used during the session.
    21|
    22|### Step 2: Ask About Worksheets
    23|
    24|> "¿Trabajamos algún worksheet o herramienta específica?"
    25|
    26|Examples: Core Values, Plan Estratégico de Una Página (OPSP), CCC, Hábitos de Ejecución, etc.
    27|
    28|### Step 3: Ask About Tasks
    29|
    30|> "¿Creamos tareas nuevas? ¿Completamos alguna existente?"
    31|
    32|Collect task descriptions for created and completed tasks.
    33|
    34|### Step 4: Ask About Duration
    35|
    36|> "¿Cuánto tiempo llevó la sesión aproximadamente? (en minutos)"
    37|
    38|If the user doesn't know, estimate based on conversation length.
    39|
    40|### Step 5: Produce Structured Output
    41|
    42|Compile into structured data:
    43|
    44|```yaml
    45|decision_focus: people
    46|duration_minutes: 45
    47|worksheets_completed: [core-values-worksheet]
    48|tasks_created: [validar-valores-con-equipo]
    49|tasks_completed: []
    50|notes:
    51|  - Discussed core values candidates
    52|  - Identified 3 potential values
    53|```
    54|
    55|## Output
    56|
    57|Structured capture data for the session log writer.
    58|

---
*> Esta herramienta está inspirada en los Hábitos de Ejecución, desarrollados por Verne Harnish como parte de su metodología de escalamiento de negocios. Ver [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) para la referencia completa.
