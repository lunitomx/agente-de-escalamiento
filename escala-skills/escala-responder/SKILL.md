---
description: 'Generar la respuesta ejecutiva de cinco bloques para una decisión revisada.'
name: escala-responder
---

# ESCALA — Entregar la respuesta ejecutiva

## Purpose

Convierte la decisión, evidencia, selección y revisión en una respuesta
ejecutiva de cinco bloques que el empresario pueda leer en menos de cinco
minutos:

1. Qué veo
2. Por qué importa
3. Evidencia relevante
4. Qué no sé todavía
5. Acción recomendada o siguiente pregunta

## Architecture

Skill adapter delgado. La lógica de ensamblaje vive en `coaching.responder`.

## Flow

### Step 1: Confirmar entradas

Requiere:

- `decision` (S43.1)
- `package` (S43.2)
- `selection` (S43.3)
- `review` (S43.4)

### Step 2: Invocar el core module

```bash
echo '{
  "base_path": ".",
  "decision": { ... },
  "package": { ... },
  "selection": { "receipt": { ... } },
  "review": { "report": { "can_proceed": true, ... } }
}' | python3 -c "
import sys, json
sys.path.insert(0, '.')
from coaching.responder import run
ctx = json.loads(sys.stdin.read())
result = run(ctx)
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

### Step 3: Interpretar la respuesta

| `artifacts.action` | Significado | Próximo paso |
|--------------------|-------------|--------------|
| `responded` | Respuesta generada | Mostrar `output` al empresario |
| `blocked` | La revisión no autoriza responder | Mostrar `output` con el límite y la pregunta siguiente |
| (error) | Faltan entradas | Ejecutar las skills anteriores primero |

## Output

| Item | Destination |
|------|-------------|
| Markdown ejecutivo | `output` |
| Respuesta estructurada | `artifacts.response` |

## Notes

- No inventa datos para llenar bloques.
- Si la revisión bloquea, el bloque 5 pide resolver el problema.
