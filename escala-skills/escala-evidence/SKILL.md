---
description: 'Armar el paquete de evidencia local para una decisión confirmada: descubre fuentes disponibles, ausentes y no confiables, sin exponer rutas internas.'
name: escala-evidence
---

# ESCALA — Armar el paquete de evidencia

## Purpose

Una vez que S43.1 aclaró y confirmó una decisión, este skill recopila las
fuentes locales que ESCALA puede usar antes de elegir una herramienta de
análisis (S43.3). El empresario ve qué evidencia alimenta la recomendación,
qué falta y qué datos no son confiables todavía.

## Architecture

Skill adapter delgado. La lógica de descubrimiento, clasificación y privacidad
vive en `coaching.evidence`.

## Flow

### Step 1: Confirmar que existe una decisión

El skill se invoca automáticamente después del procedimiento interno `escala-decision` o cuando el
empresario pide "arma el paquete de evidencia". Requiere que
`.escala/agent/memory/company-profile.yaml` contenga `focus.current_decision`.

### Step 2: Invocar el core module

Enviar JSON con `base_path`:

```bash
echo '{"base_path": "."}' | python3 -c "
import sys, json
sys.path.insert(0, '.')
from coaching.evidence import run
ctx = json.loads(sys.stdin.read())
result = run(ctx)
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

Opcionalmente se puede ajustar el umbral de frescura:

```bash
echo '{"base_path": ".", "freshness_days": 60}' | python3 -c "
import sys, json
sys.path.insert(0, '.')
from coaching.evidence import run
ctx = json.loads(sys.stdin.read())
result = run(ctx)
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

### Step 3: Interpretar la respuesta

| `artifacts.action` | Significado | Próximo paso |
|--------------------|-------------|--------------|
| `evidence_package` | Paquete generado correctamente | Mostrar el markdown al empresario y pasar a S43.3 |
| (error) | No hay decisión confirmada | Ejecuta antes el procedimiento interno `escala-decision`. Al dueño: "¿Qué decisión quieres tomar primero?" |

Ejemplo de paquete generado:

```json
{
  "output": "## Paquete de evidencia para: contratar a María en ventas...",
  "artifacts": {
    "action": "evidence_package",
    "decision_ref": {
      "decision": "contratar a María en ventas",
      "area": "people",
      "horizon": "inmediato",
      "outcome": "cubrir la vacante y mejorar cobertura comercial"
    },
    "package": {
      "sources": [...],
      "missing": [...],
      "not_trustworthy": [...],
      "questions": [...]
    },
    "summary": {
      "source_count": 2,
      "missing_count": 1,
      "not_trustworthy_count": 0,
      "ready_for_analysis": false
    }
  },
  "errors": []
}
```

## Output

| Item | Destination |
|------|-------------|
| Paquete de evidencia | `artifacts.package` para S43.3 |
| Markdown legible | `output` para mostrar al empresario |
| Resumen estructurado | `artifacts.summary` para el orchestrador |

## Notes

- Nunca se exponen rutas absolutas, URLs ni datos de otra empresa.
- Las fuentes se clasifican como `available`, `missing` o `not_trustworthy`.
- Cada fuente incluye tipo, título, periodo, confianza (`high`/`medium`/`low`) y razón.
- Si falta información crítica, el paquete lista la evidencia ausente y formula
  una pregunta de aclaración antes de concluir.
