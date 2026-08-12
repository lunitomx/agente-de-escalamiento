---
description: 'Aclarar una pregunta abierta del empresario y convertirla en una ficha de decisión concreta (área People/Strategy/Execution/Cash, horizonte y resultado esperado).'
name: escala-decision
---

# ESCALA — Aclarar la decisión

## Purpose

Antes de analizar o recomendar, ESCALA necesita entender qué decisión quiere tomar el empresario. Este skill convierte una pregunta abierta en una ficha clara y, una vez confirmada, la guarda para que el resto del ciclo de coaching la use.

## Architecture

Skill adapter delgado. La lógica de extracción, clasificación y persistencia vive en `coaching.decision`.

## Flow

### Step 1: Recibir pregunta

El empresario hace una pregunta abierta. Ejemplos:

- "¿Debería contratar a María para ventas?"
- "Necesito mejorar el cash"
- "¿Cuál es el próximo paso?"

### Step 2: Invocar el core module

Enviar JSON con `action: question`:

```bash
echo '{"action": "question", "question": "¿Debería contratar a María para ventas?", "base_path": "."}' | python3 -c "
import sys, json
sys.path.insert(0, '.')
from coaching.decision import run
ctx = json.loads(sys.stdin.read())
result = run(ctx)
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

### Step 3: Interpretar la respuesta

| `artifacts.action` | Significado | Próximo paso |
|--------------------|-------------|--------------|
| `propose` | Ficha completa propuesta | Mostrar la ficha y pedir confirmación/corrección |
| `clarify` | Falta información crítica | Hacer la pregunta de aclaración en `output` |

Ejemplo de ficha propuesta (`action: propose`):

```json
{
  "output": "## Ficha de decisión propuesta...",
  "artifacts": {
    "action": "propose",
    "draft": {
      "decision": "contratar a María en ventas",
      "area": "people",
      "horizon": "inmediato",
      "outcome": "cubrir la vacante y mejorar cobertura comercial"
    }
  },
  "errors": []
}
```

### Step 4: Confirmar la ficha

Cuando el empresario confirma, enviar `action: confirm` con el `draft`:

```bash
echo '{
  "action": "confirm",
  "draft": {
    "decision": "contratar a María en ventas",
    "area": "people",
    "horizon": "inmediato",
    "outcome": "cubrir la vacante y mejorar cobertura comercial"
  },
  "base_path": "."
}' | python3 -c "
import sys, json
sys.path.insert(0, '.')
from coaching.decision import run
ctx = json.loads(sys.stdin.read())
result = run(ctx)
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

### Step 5: Corregir un campo

Si el empresario corrige un campo, enviar `action: correct`:

```bash
echo '{
  "action": "correct",
  "draft": {
    "decision": "contratar a María en ventas",
    "area": "people",
    "horizon": "inmediato",
    "outcome": "cubrir la vacante y mejorar cobertura comercial"
  },
  "corrections": {"area": "execution"},
  "base_path": "."
}' | python3 -c "
import sys, json
sys.path.insert(0, '.')
from coaching.decision import run
ctx = json.loads(sys.stdin.read())
result = run(ctx)
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

## Output

| Item | Destination |
|------|-------------|
| Ficha confirmada | `.escala/agent/memory/company-profile.yaml` → `focus.current_decision` |
| Siguiente paso | S43.2 arma el paquete de evidencia |

## Notes

- Una pregunta ambigua nunca debe disparar análisis ni recomendación.
- Si faltan datos, hacer **una** pregunta de aclaración a la vez.
- El área se clasifica como `people`, `strategy`, `execution` o `cash`.
