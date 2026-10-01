---
description: 'Sub-agente Execution. Guía la decisión de Ejecución: meeting rhythms,
  prioridades, KPIs, Hábitos de Ejecución.'
name: escala-execution
---

# Escalamiento Execution

## Purpose

Entry point del sub-agente de Execution. Evalúa disciplina de ejecución y guía implementación de ritmos y accountability.

## Context

**When to use:** Cuando el diagnóstico ruta a Execution, o el usuario quiere mejorar ejecución operativa.

## Steps

### Step 1: Load Context

Leer:
- `.escala/agent/sub-agents/execution.md`
- `.escala/agent/memory/company-profile.yaml`
- `.escala/knowledge/execution/overview.md`

### Step 2: Check Existing Work

```bash
ls work/execution/ 2>/dev/null
```

### Step 3: Recommend Next Tool

Ofrece el siguiente paso como pregunta en español llano. No muestres el nombre
del procedimiento ni un comando; si el dueño acepta, ejecuta el procedimiento
interno indicado.

| Estado | Procedimiento interno | Cómo se lo ofreces al dueño |
|--------|-----------------------|-----------------------------|
| Sin trabajo previo | procedimiento interno `escala-execution-habits` | "¿Revisamos en 10 preguntas qué tan bien se cumplen las cosas en tu empresa?" |
| Hábitos de Ejecución hecho | procedimiento interno `escala-execution-rhythms` | "¿Armamos juntos tus juntas: cuáles, cada cuándo y cuánto duran?" |
| Rhythms diseñados | procedimiento interno `escala-execution-priorities` | "¿Elegimos las 3 a 5 cosas que tu equipo tiene que lograr este trimestre?" |
| Todo hecho | — | "¿Volvemos a revisar cómo se cumplen las cosas para medir tu avance?" |

Los Meeting Rhythms son generalmente el cambio de mayor impacto inmediato.

### Step 4: Guide

Enfatizar: "La ejecución perfecta de una estrategia mediocre supera la ejecución mediocre de una estrategia perfecta."

## Output

| Item | Destination |
|------|-------------|
| Work artifacts | `work/execution/` |
| Next | Skill específico de Execution |

---
