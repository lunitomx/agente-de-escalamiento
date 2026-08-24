---
description: 'Genera el Progress Dashboard — vista consolidada con scores actuales, historial de pulso, victorias y áreas de atención.'
name: scaleup-dashboard
---

# ScaleUp Dashboard

## Purpose

Mostrar el estado de progreso de la empresa en un dashboard de 4 secciones:
1. **Current Scores** — diagnóstico actual por decisión
2. **Pulse History** — historial de pulsos en orden cronológico inverso
3. **Wins** — decisiones con tendencia improving en el último pulso
4. **Attention Areas** — decisiones con tendencia regressing o stalling 2+ pulsos

## Architecture

Este skill es un **adapter delgado**. Toda la lógica vive en Python. No contiene lógica de negocio.

## Steps

### Step 1: Prerequisite Check

```bash
test -f .scaleup/agent/memory/company-profile.yaml && echo "EXISTS" || echo "NO_PROFILE"
```

| Result | Action |
|--------|--------|
| NO_PROFILE | Redirect to `/scaleup-welcome` — company must be initialized first |
| EXISTS | Continue |

### Step 2: Invoke Core Module

```bash
echo '{"base_path": "."}' | python3 -m coaching.dashboard
```

Capture the JSON result. The dashboard output is in `result["output"]`.

### Step 3: Quality Gate

Save the dashboard output to a temp file and validate:

```bash
echo '{"base_path": "."}' | python3 -m coaching.dashboard | python3 -c "
import sys, json
result = json.loads(sys.stdin.read())
with open('/tmp/dashboard-output.md', 'w') as f:
    f.write(result['output'])
print(json.dumps(result, indent=2, ensure_ascii=False))
" > /tmp/dashboard-result.json && python3 .scaleup/agent/validators/dashboard.py /tmp/dashboard-output.md
```

Exit 0 = validation passed. Exit 1 = missing sections (show errors).

### Step 4: Present Dashboard

- Show `result["output"]` to the user directly — it's formatted markdown
- If `result["errors"]` is non-empty, show errors and suggest remediation
- If `artifacts["pulse_count"]` is 0, invite the user to run `/scaleup-pulse` to start tracking

### Step 5: Handle Errors

If `result["errors"]` is non-empty:
1. Show each error
2. Suggest running `/scaleup-diagnose` for score issues or `/scaleup-pulse` for pulse issues

## Output Sections

| Section | Data Source | Behavior When Empty |
|---------|-------------|---------------------|
| Current Scores | `company-profile.yaml` → `scores` | "No diagnosis yet. Run /scaleup-diagnose first." |
| Pulse History | `pulse-history.yaml` → `pulses` | "No pulse data yet. Run /scaleup-pulse to start tracking." |
| Wins | Last pulse `trends` where improving | "No improving trends in the latest pulse." |
| Attention Areas | Last pulse `trends` where regressing or 2+ stalling | "No attention areas detected. Keep up the momentum!" |
