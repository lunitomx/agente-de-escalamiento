---
description: 'Diagnóstico completo de la empresa en las 4 decisiones (People, Strategy, Execution, Cash) usando el core Python cross-platform.'
name: escala-diagnose
---

# Escalamiento Diagnose

## Purpose

Evaluar el estado de la empresa en las 4 decisiones mediante preguntas guiadas. Generar reporte con scores y priorización. Usa el core module en `.scaleup/coaching/diagnose/`.

## Architecture

Este skill es un **adapter delgado**. La lógica de scoring, priorización y persistencia vive en Python.

## Steps

### Step 1: Load Context

```bash
test -f .scaleup/agent/memory/company-profile.yaml && echo "EXISTS" || echo "NO_PROFILE"
```

| Result | Action |
|--------|--------|
| NO_PROFILE | Redirect to `/escala-welcome` |
| EXISTS | Continue |

Leer el perfil actual para ver si ya hay scores.

### Step 2: Assess Each Decision

Hacer 5 preguntas por decisión (20 total). Usar escala 1-5:

| Score | Nivel |
|-------|-------|
| 1 | No iniciado |
| 2 | Ad hoc |
| 3 | Emergente |
| 4 | Establecido |
| 5 | Optimizado |

Para cada respuesta, anotar el score como entero 1-5.

### Step 3: Invoke Core Module

Construir JSON con answers y ejecutar:

```bash
echo '{"answers": {"people_q1": 3, "people_q2": 2, "people_q3": 4, "people_q4": 2, "people_q5": 3, "strategy_q1": 2, "strategy_q2": 3, "strategy_q3": 1, "strategy_q4": 2, "strategy_q5": 3, "execution_q1": 4, "execution_q2": 3, "execution_q3": 2, "execution_q4": 3, "execution_q5": 2, "cash_q1": 1, "cash_q2": 2, "cash_q3": 1, "cash_q4": 3, "cash_q5": 2}, "base_path": ".", "mode": "full"}' | python3 -c "
import sys, json
sys.path.insert(0, '.')
from coaching.diagnose import run
ctx = json.loads(sys.stdin.read())
result = run(ctx)
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

### Step 4: Quality Gate

```bash
python3 .scaleup/agent/validators/diagnose.py .scaleup/agent/memory/company-profile.yaml
```

### Step 5: Present Results

Mostrar el `output` del core module. Si hay routing a sub-agente, preguntar si el usuario quiere ir ahora.

### Step 6: Partial Re-diagnosis

Para re-evaluar solo una decisión:

```bash
echo '{"answers": {"people_q1": 4, "people_q2": 3, "people_q3": 4, "people_q4": 3, "people_q5": 4}, "decisions": ["people"], "mode": "partial", "base_path": "."}' | python3 -c "
import sys, json; sys.path.insert(0, '.')
from coaching.diagnose import run
print(json.dumps(run(json.loads(sys.stdin.read())), indent=2, ensure_ascii=False))
"
```

## Output

| Item | Destination |
|------|-------------|
| Scores actualizados | `.scaleup/agent/memory/company-profile.yaml` |
| Próximo paso | Sub-agente recomendado |
