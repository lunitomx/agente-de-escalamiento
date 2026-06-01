---
description: 'Guía paso a paso de worksheets de Escalamiento de Negocios desde la ontología. Usa core Python cross-platform.'
name: escala-worksheet
---

# Escalamiento Worksheet

## Purpose

Guiar al usuario a través de cualquier worksheet de Escalamiento de Negocios, cargado desde la ontología (E6). Validar campos, guardar progreso, marcar completados.

## Architecture

Adapter delgado. Core logic en `.escala/coaching/worksheet/`.

## Steps

### Step 1: List Worksheets

```bash
echo '{"action": "list", "base_path": "."}' | python3 -c "
import sys, json; sys.path.insert(0, '.')
from coaching.worksheet import run
print(json.dumps(run(json.loads(sys.stdin.read())), indent=2, ensure_ascii=False))
"
```

### Step 2: Start Worksheet

```bash
echo '{"action": "start", "worksheet_name": "face", "base_path": "."}' | python3 -c "
import sys, json; sys.path.insert(0, '.')
from coaching.worksheet import run
print(json.dumps(run(json.loads(sys.stdin.read())), indent=2, ensure_ascii=False))
"
```

### Step 3: Advance Step

Después de cada respuesta del usuario:

```bash
echo '{"action": "step", "worksheet_name": "face", "fields": {"funciones": "CEO, Ventas, Operaciones, Finanzas"}, "base_path": "."}' | python3 -c "
import sys, json; sys.path.insert(0, '.')
from coaching.worksheet import run
print(json.dumps(run(json.loads(sys.stdin.read())), indent=2, ensure_ascii=False))
"
```

### Step 4: Complete & Save

```bash
echo '{"action": "save", "worksheet_name": "face", "base_path": "."}' | python3 -c "
import sys, json; sys.path.insert(0, '.')
from coaching.worksheet import run
print(json.dumps(run(json.loads(sys.stdin.read())), indent=2, ensure_ascii=False))
"
```

### Step 5: Quality Gate

```bash
python3 .escala/agent/validators/worksheet.py .escala/my-company/worksheets/face.yaml
```

## Resume Flow

Si el usuario vuelve a un worksheet en progreso:

```bash
echo '{"action": "resume", "worksheet_name": "face", "base_path": "."}' | python3 -c "
import sys, json; sys.path.insert(0, '.')
from coaching.worksheet import run
print(json.dumps(run(json.loads(sys.stdin.read())), indent=2, ensure_ascii=False))
"
```

## Output

| Item | Destination |
|------|-------------|
| Worksheet state | `.escala/my-company/worksheets/{id}.yaml` |
| Completed worksheets | Mismo archivo con status: completed |
