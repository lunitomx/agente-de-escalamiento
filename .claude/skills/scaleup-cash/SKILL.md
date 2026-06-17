---
description: 'Sub-agente Cash. Guía la decisión de Cash: Cash Conversion Cycle, Power
  of One, cash acceleration strategies.'
name: scaleup-cash
---

# ScaleUp Cash

## Purpose

Entry point del sub-agente de Cash. Evalúa salud financiera operativa y guía optimización del flujo de efectivo.

## Context

**When to use:** Cuando el diagnóstico ruta a Cash, o el usuario quiere optimizar flujo de efectivo.

## Canonical Pipeline

Pipeline ID: `scaleup-cash-acceleration-system`

Este entrypoint no reemplaza los skills de Cash. Orquesta el flujo recomendado:

1. `/scaleup-cash-ccc` — mapear Cash Conversion Cycle
2. `/scaleup-cash-power1` — calcular impacto de las 7 palancas
3. `/scaleup-cash-acceleration` — elegir movimientos de aceleración
4. `/scaleup-task-add` — convertir movimientos aprobados en tareas

Stop conditions: faltan datos base de cash, o el usuario no puede elegir movimientos prioritarios.
Quality gates: `ccc_inputs_complete`, `acceleration_moves_are_prioritized`.
Registry: `.raise/pipelines/scaleup.yaml`.

## Steps

### Step 1: Load Context

Leer:
- `.scaleup/agent/sub-agents/cash.md`
- `.scaleup/agent/memory/company-profile.yaml`
- `.scaleup/knowledge/cash/overview.md`

### Step 2: Check Existing Work

```bash
ls work/cash/ 2>/dev/null
```

### Step 3: Recommend Next Tool

| Estado | Recomendación |
|--------|--------------|
| Sin trabajo previo | `/scaleup-cash-ccc` — mapear Cash Conversion Cycle |
| CCC mapeado | `/scaleup-cash-power1` — análisis Power of One |
| Power of One hecho | `/scaleup-cash-acceleration` — estrategias de aceleración |
| Todo hecho | Re-mapear CCC, medir mejoras |

### Step 4: Guide

Enfatizar: "El cash es el oxígeno del crecimiento. El crecimiento chupa cash — si no lo gestionas, el éxito mismo puede matarte."

Nota: Este sub-agente NO da asesoría financiera. Guía el análisis operativo del ciclo de cash usando las herramientas de Scaling Up.

## Output

| Item | Destination |
|------|-------------|
| Work artifacts | `work/cash/` |
| Next | Skill específico de Cash |
