---
description: 'Detecta y adapta el nivel de coaching (Shu/Ha/Ri) según scores de diagnóstico. Core Python cross-platform.'
name: escala-level
---

# Escalamiento Level

## Purpose

Detectar automáticamente el nivel de coaching del usuario (Shu/Ha/Ri) basado en scores de diagnóstico, y permitir override manual.

## Architecture

Adapter delgado. Core logic en `.scaleup/coaching/level/`.

## Steps

### Detect Level

```bash
echo '{"action": "detect", "base_path": "."}' | python3 -c "
import sys, json; sys.path.insert(0, '.')
from coaching.level import run
print(json.dumps(run(json.loads(sys.stdin.read())), indent=2, ensure_ascii=False))
"
```

### Set Level (Override)

```bash
echo '{"action": "set", "level": "ha", "base_path": "."}' | python3 -c "
import sys, json; sys.path.insert(0, '.')
from coaching.level import run
print(json.dumps(run(json.loads(sys.stdin.read())), indent=2, ensure_ascii=False))
"
```

### Get Current Level

```bash
echo '{"action": "get", "base_path": "."}' | python3 -c "
import sys, json; sys.path.insert(0, '.')
from coaching.level import run
print(json.dumps(run(json.loads(sys.stdin.read())), indent=2, ensure_ascii=False))
"
```

## Integration

El nivel se carga automáticamente en `/escala-start` y se pasa como contexto a todos los skills de coaching.

El SKILL.md de cada skill debe incluir:
```
- coaching.level: shu|ha|ri
- coaching.level_source: auto|manual
```

## Output

| Item | Destination |
|------|-------------|
| Level | `.scaleup/agent/memory/company-profile.yaml` → coaching.level |
| Auto-detect | Basado en promedio de scores |
