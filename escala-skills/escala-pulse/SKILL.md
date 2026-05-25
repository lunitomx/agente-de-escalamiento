     1|---
     2|description: 'Realiza el Quarterly Pulse Check — registra el estado de cada decisión (People, Strategy, Execution, Cash, Overall) como mejorando, estancado o regresando, genera correcciones de curso para decisiones en regresión y persiste el historial en pulse-history.yaml.'
     3|name: escala-pulse
     4|---
     5|
     6|# Escalamiento Pulse
     7|
     8|## Purpose
     9|
    10|Capturar el pulso trimestral del negocio: por cada una de las 4 decisiones (más una evaluación general), el usuario indica si la empresa está mejorando (+1), estancada (0) o retrocediendo (-1). El skill registra la entrada en `pulse-history.yaml` y sugiere acciones para las decisiones en regresión.
    11|
    12|## Architecture
    13|
    14|Este skill es un **adapter delgado**. La lógica de trend mapping, persistencia YAML y generación de correcciones vive en Python (`coaching/pulse/`).
    15|
    16|## Steps
    17|
    18|### Step 1: Load Context
    19|
    20|```bash
    21|test -f .escala/agent/memory/company-profile.yaml && echo "EXISTS" || echo "NO_PROFILE"
    22|```
    23|
    24|| Result | Action |
    25||--------|--------|
    26|| NO_PROFILE | Redirect to `/escala-welcome` — company must be initialized first |
    27|| EXISTS | Continue |
    28|
    29|### Step 2: Collect Answers
    30|
    31|Ask the user to rate each of the following decisions as:
    32|- **+1** — improving (making clear progress this quarter)
    33|- **0** — stalling (no meaningful change)
    34|- **-1** — regressing (moving backwards or losing ground)
    35|
    36|Decisions to rate:
    37|- People — right people in right seats, accountability
    38|- Strategy — clarity of direction, brand promise, competitive differentiation
    39|- Execution — meeting rhythms, priorities, Hábitos de Ejecución
    40|- Cash — cash flow health, CCC, runway
    41|- Overall — holistic assessment of the quarter
    42|
    43|Assemble the answers into JSON:
    44|```json
    45|{"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}}
    46|```
    47|
    48|### Step 3: Invoke Core Module
    49|
    50|```bash
    51|echo '{"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}}' | python3 -m coaching.pulse
    52|```
    53|
    54|Or as inline import:
    55|```bash
    56|echo '{"answers": {...}}' | python3 -c "
    57|import sys, json
    58|sys.path.insert(0, '.')
    59|from coaching.pulse import run
    60|ctx = json.loads(sys.stdin.read())
    61|result = run(ctx)
    62|print(json.dumps(result, indent=2, ensure_ascii=False))
    63|"
    64|```
    65|
    66|### Step 4: Handle Errors
    67|
    68|If `result["errors"]` is non-empty:
    69|1. Show each error to the user
    70|2. For invalid answer values, ask the user to correct them (must be -1, 0, or 1)
    71|3. Re-run Step 3 with corrected answers
    72|
    73|### Step 5: Run Quality Gate
    74|
    75|```bash
    76|python3 .escala/agent/validators/pulse.py .escala/my-company/pulse-history.yaml
    77|```
    78|
    79|If the gate exits 1, report the error and do not present results as successful.
    80|
    81|### Step 6: Present Results
    82|
    83|- Show `result["output"]` to the user — the formatted pulse report with trends table
    84|- If `result["artifacts"]["prior_pulse_date"]` is not null, mention: "Last pulse was on {prior_pulse_date}"
    85|- If `result["artifacts"]["course_corrections"]` is non-empty:
    86|  - Highlight the corrections as action items
    87|  - For each correction, offer to dive deeper with the suggested command
    88|- Confirm that the pulse has been saved to `result["artifacts"]["history_path"]`
    89|
    90|## Output
    91|
    92|| Item | Destination |
    93||------|-------------|
    94|| Pulse history | `.escala/my-company/pulse-history.yaml` |
    95|| History schema | `{pulses: [{date, answers, trends, course_corrections}]}` |
    96|| Valid answer values | -1 (regressing), 0 (stalling), +1 (improving) |
    97|| Valid trend values | regressing, stalling, improving |
    98|

---
*> Esta herramienta está inspirada en los Hábitos de Ejecución, desarrollados por Verne Harnish como parte de su metodología de escalamiento de negocios. Ver [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) para la referencia completa.
