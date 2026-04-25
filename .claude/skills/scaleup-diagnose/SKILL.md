---
description: 'Diagnóstico completo de la empresa en las 4 decisiones de Scaling Up
  (People, Strategy, Execution, Cash). Master agent que evalúa y ruta al sub-agente
  correcto.'
name: scaleup-diagnose
---

# ScaleUp Diagnose

## Purpose

Evaluar el estado actual de la empresa en las 4 decisiones de Scaling Up mediante preguntas guiadas. Generar un reporte de diagnóstico y recomendar por dónde empezar.

## Context

**When to use:** Al inicio del journey con ScaleUp, o cuando el usuario quiere re-evaluar su progreso.

**When to skip:** Si el usuario ya sabe exactamente en qué decisión quiere trabajar → ir directo al sub-agente.

**Inputs:** `.scaleup/agent/memory/company-profile.yaml` debe tener datos de la empresa.

## Steps

### Step 1: Load Context

Leer `.scaleup/agent/memory/company-profile.yaml` y `.scaleup/agent/identity/core.md`.

Si company profile está vacío → redirigir a `/scaleup-welcome` primero.

### Step 2: People Assessment

Leer `.scaleup/agent/sub-agents/people.md` para las preguntas clave.

Hacer 5 preguntas sobre People. Escuchar respuestas. Asignar score 1-5.

Escala:
- 1 = No existe proceso formal
- 2 = Ad hoc, algo de conciencia
- 3 = Frameworks básicos en lugar
- 4 = Sistemático y medido
- 5 = Optimizado, ventaja competitiva

### Step 3: Strategy Assessment

Leer `.scaleup/agent/sub-agents/strategy.md`.

Hacer 5 preguntas sobre Strategy. Score 1-5.

### Step 4: Execution Assessment

Leer `.scaleup/agent/sub-agents/execution.md`.

Hacer 5 preguntas sobre Execution. Score 1-5.

### Step 5: Cash Assessment

Leer `.scaleup/agent/sub-agents/cash.md`.

Hacer 5 preguntas sobre Cash. Score 1-5.

### Step 6: Generate Report

Usar template `templates/diagnosis-report.md` para generar el reporte.

Guardar en `work/diagnosis/{date}-report.md`.

Actualizar scores en `.scaleup/agent/memory/company-profile.yaml`.

### Step 7: Route to Priority

Aplicar routing logic del master agent:

```
if all scores < 2 → People (fundacional)
elif people < 3 → /scaleup-people
elif strategy < 3 → /scaleup-strategy
elif execution < 3 → /scaleup-execution
elif cash < 3 → /scaleup-cash
else → mostrar dashboard, usuario elige
```

Presentar recomendación con razón clara.

<verification>
Reporte guardado. Scores actualizados. Recomendación presentada.
</verification>

## Output

| Item | Destination |
|------|-------------|
| Diagnosis report | `work/diagnosis/{date}-report.md` |
| Updated scores | `.scaleup/agent/memory/company-profile.yaml` |
| Next | Sub-agente recomendado |

## Quality Checklist

- [ ] Company profile cargado antes de preguntar
- [ ] 5 preguntas por decisión (20 total)
- [ ] Scores basados en respuestas, no inventados
- [ ] Reporte usa template estándar
- [ ] Routing sigue la secuencia del libro (People → Strategy → Execution → Cash)
- [ ] Razón clara de por qué se recomienda esa decisión primero
