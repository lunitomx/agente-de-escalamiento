---
description: 'Calificar el ciclo de coaching confiable con casos positivos y negativos para People, Strategy, Execution y Cash.'
name: escala-qualifier
---

# ESCALA — Calificar las cuatro decisiones

## Purpose

Ejecuta el ciclo completo de coaching confiable (S43.1-S43.5) contra ocho casos
de prueba: dos por cada decisión (People, Strategy, Execution, Cash). Cuatro
positivos deben llegar a una respuesta ejecutiva; cuatro negativos deben ser
bloqueados o pedir aclaración antes de responder.

## Architecture

Skill adapter delgado. Los casos y el runner viven en `coaching.qualifier`.

## Flow

### Step 1: Invocar el qualifier

```bash
python -m coaching.qualifier
```

### Step 2: Interpretar la respuesta

| `artifacts.action` | Significado | Próximo paso |
|--------------------|-------------|--------------|
| `qualification_complete` | Todos los casos se ejecutaron | Verificar `failed` == 0 |

## Output

| Item | Destination |
|------|-------------|
| Resumen markdown | `output` |
| Resultados detallados | `artifacts.results` |
| Conteo | `artifacts.passed` / `artifacts.failed` |

## Notes

- No modifica módulos de producción.
- Los casos negativos incluyen evidencia faltante, no confiable o contradictoria.
