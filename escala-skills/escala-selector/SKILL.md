---
description: 'Elegir la herramienta de análisis ESCALA más adecuada para una decisión confirmada y su paquete de evidencia.'
name: escala-selector
---

# ESCALA — Elegir la herramienta adecuada

## Purpose

Una vez que S43.1 aclaró la decisión y S43.2 armó el paquete de evidencia, este
skill selecciona la herramienta de análisis ESCALA que mejor calza con la
pregunta del empresario y los datos disponibles. Si falta el dato mínimo, no
fuerza una herramienta: pide la información faltante.

## Architecture

Skill adapter delgado. La lógica de mapeo área + evidencia, validación de mínimo
y generación de recibo vive en `coaching.selector`.

## Flow

### Step 1: Confirmar decisión y evidencia

El skill requiere:

- Una decisión confirmada en `.escala/agent/memory/company-profile.yaml`
  (`focus.current_decision`), o un objeto `decision` en el contexto.
- Un `EvidencePackage` en `context.package` (output del procedimiento interno `escala-evidence`).

### Step 2: Invocar el core module

Enviar JSON con `base_path` y `package`:

```bash
echo '{
  "base_path": ".",
  "package": {
    "decision_ref": {
      "decision": "¿Cuánto cash tengo disponible para agosto?",
      "area": "cash",
      "horizon": "inmediato",
      "outcome": "evitar sorpresas de liquidez"
    },
    "sources": [
      {
        "source_id": "worksheet-cash-ccc",
        "source_type": "worksheet",
        "title": "Cash Conversion Cycle Worksheet",
        "decision": "cash",
        "status": "available",
        "period": "2026-07",
        "confidence": "high",
        "reason": "Worksheet completo y reciente."
      }
    ],
    "missing": [],
    "not_trustworthy": [],
    "questions": []
  }
}' | python3 -c "
import sys, json
sys.path.insert(0, '.')
from coaching.selector import run
ctx = json.loads(sys.stdin.read())
result = run(ctx)
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

También se puede pasar la decisión explícita para pruebas:

```bash
echo '{
  "base_path": ".",
  "decision": {
    "decision": "¿Por qué no avanzan las prioridades del trimestre?",
    "area": "execution",
    "horizon": "corto",
    "outcome": "recuperar ritmo de ejecución"
  },
  "package": { ... }
}' | python3 -c "
import sys, json
sys.path.insert(0, '.')
from coaching.selector import run
ctx = json.loads(sys.stdin.read())
result = run(ctx)
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

### Step 3: Interpretar la respuesta

| `artifacts.action` | Significado | Próximo paso |
|--------------------|-------------|--------------|
| `tool_selected` | Se eligió una herramienta basada en evidencia | Mostrar el markdown al empresario; invocar la skill principal indicada en `receipt.skills` |
| `clarify` | Falta el dato mínimo para el área | Hacer la pregunta en `output` (o `artifacts.questions`) antes de continuar |
| (error) | No hay decisión confirmada o no se recibió paquete | Ejecuta antes el procedimiento interno `escala-decision` o `escala-evidence` |

Ejemplo de herramienta seleccionada (`action: tool_selected`):

```json
{
  "output": "## Herramienta seleccionada: Cash Analysis\n\n**Área:** Cash...",
  "artifacts": {
    "action": "tool_selected",
    "receipt": {
      "area": "cash",
      "decision": "¿Cuánto cash tengo disponible para agosto?",
      "tool": "cash_analysis",
      "label": "Cash Analysis",
      "skills": ["<ids internos de procedimientos; nunca se muestran al dueño>"],
      "evidence_used": ["worksheet-cash-ccc"],
      "reason": "Área Cash con workbook financiero disponible.",
      "missing_minimum": false
    },
    "questions": []
  },
  "errors": []
}
```

Ejemplo de clarificación (`action: clarify`):

```json
{
  "output": "## Falta información para elegir una herramienta\n\nPara analizar...",
  "artifacts": {
    "action": "clarify",
    "receipt": {
      "area": "cash",
      "decision": "¿Cuánto cash tengo disponible?",
      "tool": null,
      "label": null,
      "skills": [],
      "evidence_used": [],
      "reason": "No hay evidencia mínima disponible para el área Cash.",
      "missing_minimum": true
    },
    "questions": ["¿Tienes disponible 'Cash Conversion Cycle Worksheet'?"]
  },
  "errors": []
}
```

## Output

| Item | Destination |
|------|-------------|
| Recibo de selección | `artifacts.receipt` para S43.4 y trazabilidad |
| Markdown legible | `output` para mostrar al empresario |
| Preguntas de aclaración | `artifacts.questions` cuando `action: clarify` |
| Skill recomendada | `receipt.skills[0]` como siguiente paso |

## Notes

- El módulo no selecciona ninguna herramienta cuando falta el dato mínimo.
- No inventa ni simula evidencia para forzar un análisis.
- El catálogo de herramientas es extensible a `people` y `strategy` sin cambiar
  la firma pública de `run`.
