---
description: 'Sub-agente Execution. Guía la decisión de Ejecución: meeting rhythms,
  prioridades, KPIs, Rockefeller Habits.'
name: scaleup-execution
---

# ScaleUp Execution

## Purpose

Entry point del sub-agente de Execution. Evalúa disciplina de ejecución y guía implementación de ritmos y accountability.

## Context

**When to use:** Cuando el diagnóstico ruta a Execution, o el usuario quiere mejorar ejecución operativa.

## Steps

### Step 1: Load Context

Leer:
- `.scaleup/agent/sub-agents/execution.md`
- `.scaleup/agent/memory/company-profile.yaml`
- `.scaleup/knowledge/execution/overview.md`

### Step 2: Check Existing Work

```bash
ls work/execution/ 2>/dev/null
```

### Step 3: Recommend Next Tool

| Estado | Recomendación |
|--------|--------------|
| Sin trabajo previo | `/scaleup-execution-rockefeller` — evaluar 10 hábitos |
| Rockefeller hecho | `/scaleup-execution-rhythms` — diseñar meeting rhythm |
| Rhythms diseñados | `/scaleup-execution-priorities` — prioridades trimestrales |
| Todo hecho | Re-evaluar Rockefeller, medir progreso |

Los Meeting Rhythms son generalmente el cambio de mayor impacto inmediato.

### Step 4: Guide

Enfatizar: "La ejecución perfecta de una estrategia mediocre supera la ejecución mediocre de una estrategia perfecta."

## Output

| Item | Destination |
|------|-------------|
| Work artifacts | `work/execution/` |
| Next | Skill específico de Execution |
