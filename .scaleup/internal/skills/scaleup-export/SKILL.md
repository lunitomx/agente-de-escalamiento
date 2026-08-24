---
description: 'Genera un Action Plan Export — documento markdown con las 5 secciones clave: diagnóstico, meta anual, prioridades, tareas y próximos pasos.'
name: scaleup-export
---

# ScaleUp Export

## Purpose

Exportar el estado actual de tu empresa en un documento markdown fechado y compartible.
El documento incluye scores de diagnóstico, meta anual, prioridades del trimestre, tareas abiertas y próximos pasos recomendados.

## Architecture

Este skill es un **adapter delgado**. La lógica de lectura de datos, ensamblado y escritura del archivo vive en Python.

## Steps

### Step 1: Load Context

```bash
test -f .scaleup/agent/memory/company-profile.yaml && echo "EXISTS" || echo "NO_PROFILE"
```

| Result | Action |
|--------|--------|
| NO_PROFILE | Redirect to `/scaleup-welcome` — company must be initialized first |
| EXISTS | Continue |

### Step 2: Invoke Core Module

```bash
echo '{"base_path": "."}' | python3 -c "
import sys, json
sys.path.insert(0, '.')
from coaching.export import run
ctx = json.loads(sys.stdin.read())
result = run(ctx)
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

Or as module:

```bash
echo '{"base_path": "."}' | python3 -m coaching.export
```

### Step 3: Quality Gate

```bash
python3 .scaleup/agent/validators/export.py <export_path>
```

Where `<export_path>` is `result["artifacts"]["export_path"]` from Step 2.

### Step 4: Present Results

- Show `result["output"]` to the user — the path where the export was saved
- If `result["errors"]` is non-empty, show errors and stop
- If `result["artifacts"]["missing_optional"]` is non-empty, mention which files were not configured (not an error — graceful degradation)
- Confirm the export path and invite the user to share it with their leadership team

### Step 5: Handle Errors

If `result["errors"]` is non-empty:
1. Show each error
2. Suggest running `/scaleup-diagnose` or `/scaleup-welcome` as appropriate

## Output

| Item | Destination |
|------|-------------|
| Export file | `.scaleup/my-company/exports/YYYY-MM-DD-action-plan.md` |
| Sections | 1. Diagnosis Scores, 2. Annual Goal, 3. Active Priorities, 4. Open Tasks, 5. Next Steps |
