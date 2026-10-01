---
description: 'Realiza el Quarterly Pulse Check — registra el estado de cada decisión (People, Strategy, Execution, Cash, Overall) como mejorando, estancado o regresando, genera correcciones de curso para decisiones en regresión y persiste el historial en pulse-history.yaml.'
name: escala-pulse
---

# Escalamiento Pulse

## Purpose

Capturar el pulso trimestral del negocio: por cada una de las 4 decisiones (más una evaluación general), el usuario indica si la empresa está mejorando (+1), estancada (0) o retrocediendo (-1). El skill registra la entrada en `pulse-history.yaml` y sugiere acciones para las decisiones en regresión.

## Architecture

Este skill es un **adapter delgado**. La lógica de trend mapping, persistencia YAML y generación de correcciones vive en Python (`coaching/pulse/`).

## Steps

### Step 1: Load Context

```bash
test -f .escala/agent/memory/company-profile.yaml && echo "EXISTS" || echo "NO_PROFILE"
```

| Result | Action |
|--------|--------|
| NO_PROFILE | Ejecuta el procedimiento interno `escala-welcome` — la empresa debe existir primero. Al dueño: "Antes de tu registro semanal necesito conocer tu empresa. ¿Empezamos?" |
| EXISTS | Continue |

### Step 2: Collect Answers

Ask the user to rate each of the following decisions as:
- **+1** — improving (making clear progress this quarter)
- **0** — stalling (no meaningful change)
- **-1** — regressing (moving backwards or losing ground)

Decisions to rate:
- People — right people in right seats, accountability
- Strategy — clarity of direction, brand promise, competitive differentiation
- Execution — meeting rhythms, priorities, Hábitos de Ejecución
- Cash — cash flow health, CCC, runway
- Overall — holistic assessment of the quarter

Assemble the answers into JSON:
```json
{"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}}
```

### Step 3: Invoke Core Module

```bash
echo '{"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}}' | python3 -m coaching.pulse
```

Or as inline import:
```bash
echo '{"answers": {...}}' | python3 -c "
import sys, json
sys.path.insert(0, '.')
from coaching.pulse import run
ctx = json.loads(sys.stdin.read())
result = run(ctx)
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

### Step 4: Handle Errors

If `result["errors"]` is non-empty:
1. Show each error to the user
2. For invalid answer values, ask the user to correct them (must be -1, 0, or 1)
3. Re-run Step 3 with corrected answers

### Step 5: Run Quality Gate

```bash
python3 .escala/agent/validators/pulse.py .escala/my-company/pulse-history.yaml
```

If the gate exits 1, report the error and do not present results as successful.

### Step 6: Present Results

- Show `result["output"]` to the user — the formatted pulse report with trends table
- If `result["artifacts"]["prior_pulse_date"]` is not null, mention: "Last pulse was on {prior_pulse_date}"
- If `result["artifacts"]["course_corrections"]` is non-empty:
  - Highlight the corrections as action items
  - For each correction, offer to dive deeper with the suggested command
- Confirm that the pulse has been saved to `result["artifacts"]["history_path"]`

## Output

| Item | Destination |
|------|-------------|
| Pulse history | `.escala/my-company/pulse-history.yaml` |
| History schema | `{pulses: [{date, answers, trends, course_corrections}]}` |
| Valid answer values | -1 (regressing), 0 (stalling), +1 (improving) |
| Valid trend values | regressing, stalling, improving |

---
