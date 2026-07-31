---
description: 'Revisar la decisión, evidencia y selección de herramienta antes de generar una respuesta ejecutiva.'
name: escala-reviewer
---

# ESCALA — Revisar antes de responder

## Purpose

Antes de entregar una recomendación al empresario, este skill revisa la decisión
confirmada, el paquete de evidencia y la herramienta seleccionada para detectar:

- afirmaciones sin fuente,
- fuentes no confiables,
- contradicciones entre fuentes,
- números de periodos distintos,
- desalineación entre la acción y el objetivo inicial.

Si todo está bien, autoriza la respuesta ejecutiva (S43.5). Si no, pide
aclaración o bloquea la respuesta.

## Architecture

Skill adapter delgado. La lógica de revisión vive en `coaching.reviewer`.

## Flow

### Step 1: Confirmar entradas

El skill requiere:

- Una decisión confirmada (`focus.current_decision` en el perfil) o un objeto
  `decision` en el contexto.
- Un paquete de evidencia en `context.package` (output de `/escala-evidence`).
- Un recibo de selección en `context.selection` (output de `/escala-selector`).

### Step 2: Invocar el core module

```bash
echo '{
  "base_path": ".",
  "decision": {
    "decision": "¿Cuánto cash tengo disponible para agosto?",
    "area": "cash",
    "horizon": "inmediato",
    "outcome": "evitar sorpresas de liquidez"
  },
  "package": { ... },
  "selection": {
    "action": "tool_selected",
    "receipt": {
      "area": "cash",
      "decision": "¿Cuánto cash tengo disponible para agosto?",
      "tool": "cash_analysis",
      "label": "Cash Analysis",
      "skills": ["/escala-cash", "/escala-cash-ccc", "/escala-cash-power1"],
      "evidence_used": ["worksheet-cash-ccc"],
      "reason": "Área Cash con workbook financiero disponible.",
      "missing_minimum": false
    }
  }
}' | python3 -c "
import sys, json
sys.path.insert(0, '.')
from coaching.reviewer import run
ctx = json.loads(sys.stdin.read())
result = run(ctx)
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

### Step 3: Interpretar la respuesta

| `artifacts.action` | Significado | Próximo paso |
|--------------------|-------------|--------------|
| `reviewed` | La respuesta puede generarse | Pasar a S43.5 para entregar la respuesta ejecutiva |
| `clarify` | Falta información o hay advertencias | Hacer la pregunta en `output` o `artifacts.questions` antes de responder |
| `blocked` | Contradicción crítica o desalineación | No generar recomendación; resolver el problema señalado en `output` |
| (error) | Faltan entradas | Ejecutar `/escala-decision`, `/escala-evidence` o `/escala-selector` primero |

Ejemplo de respuesta `reviewed`:

```json
{
  "output": "## Revisión de calidad\n\nLa recomendación puede avanzar...",
  "artifacts": {
    "action": "reviewed",
    "report": {
      "decision": "¿Cuánto cash tengo disponible para agosto?",
      "area": "cash",
      "tool": "cash_analysis",
      "findings": [],
      "critical_questions": [],
      "action_aligned": true,
      "can_proceed": true
    },
    "questions": []
  },
  "errors": []
}
```

## Output

| Item | Destination |
|------|-------------|
| Informe de revisión | `artifacts.report` para S43.5 |
| Markdown legible | `output` para mostrar al empresario |
| Preguntas de aclaración | `artifacts.questions` cuando `action: clarify` |
| Acción final | `artifacts.action` (`reviewed` / `clarify` / `blocked`) |

## Notes

- Nunca genera la respuesta ejecutiva; solo autoriza o bloquea el paso a S43.5.
- No silencia findings críticos.
- Reutiliza los modelos de `coaching.evidence` y `coaching.selector`.
