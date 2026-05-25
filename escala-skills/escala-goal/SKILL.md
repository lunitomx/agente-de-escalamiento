     1|---
     2|name: escala-goal
     3|description: 'Set or view the Meta SMART anual. All recommendations filter through this goal.'
     4|---
     5|
     6|# Escalamiento Goal — SMART Annual Goal
     7|
     8|## Purpose
     9|
    10|Set or view the company's annual Meta SMART. This goal acts as a strategic filter — every recommendation the agent makes is evaluated against: "Does this advance the annual goal?"
    11|
    12|## Steps
    13|
    14|### Step 1: Check Current Goal
    15|
    16|Read `.escala/my-company/annual-goal.md`. If the goal fields are filled, display current goal. If empty, proceed to goal creation.
    17|
    18|### Step 2: Goal Creation (if needed)
    19|
    20|Guide the user through Meta SMART setting:
    21|
    22|1. **Meta:** "¿Cuál es tu meta principal del año?" (one sentence)
    23|2. **Específica:** "¿Qué exactamente quieres lograr?"
    24|3. **Medible:** "¿Cómo sabrás que lo lograste? ¿Qué número?"
    25|4. **Alcanzable:** "¿Es realista con tus recursos actuales?"
    26|5. **Relevante:** "¿Por qué esta meta y no otra?"
    27|6. **Temporal:** "¿Para cuándo?"
    28|
    29|### Step 3: Define KPI
    30|
    31|Ask:
    32|- **Métrica principal:** What number tracks progress?
    33|- **Valor actual:** Where are you now?
    34|- **Valor meta:** Where do you need to be?
    35|- **Fecha límite:** By when?
    36|
    37|### Step 4: Connect to 4 Decisions
    38|
    39|For each decision, ask how the goal connects:
    40|- **People:** "¿Qué necesitas de tu equipo?"
    41|- **Strategy:** "¿Qué cambio estratégico requiere?"
    42|- **Execution:** "¿Qué disciplina necesitas?"
    43|- **Cash:** "¿Cuánto cash necesitas?"
    44|
    45|### Step 5: Save Goal
    46|
    47|Write the responses to `.escala/my-company/annual-goal.md` filling in the template fields.
    48|
    49|### Step 6: Confirm
    50|
    51|Display the complete goal and confirm:
    52|
    53|```
    54|Meta SMART: {goal}
    55|KPI: {metric} — de {current} a {target} para {deadline}
    56|Filtro activo: toda recomendación se evalúa contra esta meta.
    57|```
    58|
    59|## Output
    60|
    61|| Item | Destination |
    62||------|-------------|
    63|| Annual goal | `.escala/my-company/annual-goal.md` |
    64|| Filter | Active in all coaching skills |
    65|

---
*> El marco de metas SMART fue desarrollado por George T. Doran. Ver [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) para la referencia completa.
