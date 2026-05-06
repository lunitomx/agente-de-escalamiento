---
description: 'Dashboard de progreso mostrando scores, worksheets completados y próxima acción sugerida. Core Python cross-platform.'
name: scaleup-progress
---

# ScaleUp Progress

## Purpose

Mostrar el progreso del usuario en las 4 decisiones: scores actuales, worksheets completados vs pendientes, y sugerencia del siguiente paso.

## Architecture

Adapter delgado. Core logic en `.scaleup/coaching/progress/`.

## Steps

### Step 1: Invoke Core Module

```bash
echo '{"base_path": "."}' | python3 -c "
import sys, json; sys.path.insert(0, '.')
from scaleup.coaching.progress import run
print(json.dumps(run(json.loads(sys.stdin.read())), indent=2, ensure_ascii=False))
"
```

### Step 2: Quality Gate

```bash
python3 .scaleup/agent/validators/progress.py
```

### Step 3: Present Dashboard

Mostrar el `output` del core module al usuario. Si hay un siguiente worksheet sugerido, ofrecer `/scaleup-worksheet {id}`.

## Output

| Item | Description |
|------|-------------|
| Scores table | Scores actuales por decisión con nivel |
| Worksheet progress | Completados vs pendientes por decisión |
| Next suggestion | Siguiente worksheet recomendado |
