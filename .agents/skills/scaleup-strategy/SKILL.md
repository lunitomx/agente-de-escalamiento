---
description: 'Sub-agente Strategy. Guía la decisión de Estrategia: core values, BHAG,
  brand promise, OPSP, 7 Strata.'
name: scaleup-strategy
---

# ScaleUp Strategy

## Purpose

Entry point del sub-agente de Strategy. Evalúa madurez estratégica, verifica prerequisitos y guía hacia la herramienta correcta.

## Context

**When to use:** Cuando el diagnóstico ruta a Strategy, o el usuario quiere trabajar en estrategia.

## Canonical Pipeline

Pipeline ID: `scaleup-strategy-development`

Este entrypoint no reemplaza los skills de Strategy. Orquesta el flujo recomendado:

1. `/scaleup-strategy-swot` — sintetizar SWT/SWOT
2. `/scaleup-strategy-opsp` — construir One-Page Strategic Plan
3. `/scaleup-strategy-7strata` — profundizar diferenciación
4. `/scaleup-context-add` — guardar decisiones aprobadas

Stop conditions: faltan prerequisitos de estrategia, o el OPSP no puede quedar internamente consistente.
Quality gates: `strategy_prerequisites_present`, `opsp_internal_consistency`.
Registry: `.raise/pipelines/scaleup.yaml`.

## Steps

### Step 1: Load Context

Leer:
- `.scaleup/agent/sub-agents/strategy.md`
- `.scaleup/agent/memory/company-profile.yaml`
- `.scaleup/knowledge/strategy/overview.md`

### Step 2: Check Existing Work & Prerequisites

```bash
ls work/strategy/ 2>/dev/null
ls work/people/ 2>/dev/null
```

Verificar que People tiene base mínima (score >= 2). Si no, sugerir volver a People primero.

### Step 3: Voice of Customer Evidence Gate

Antes de formar Core Customer, Brand Promise, posicionamiento o Strategy Canvas,
buscar evidencia Voice of Customer validada:

- Usar registros `CustomerEvidenceRecord` cuando existan.
- Usar `map_evidence_to_strategy` para obtener inputs citados y gaps.
- Las recomendaciones estratégicas deben citar evidence ids.
- Si faltan inputs o hay gaps, ask one missing-evidence question at a time.
- Si no hay evidencia aprobada, do not invent Core Customer, Brand Promise,
  positioning, OPSP, 7 Strata, or Strategy Canvas claims.

### Step 4: Recommend Next Tool

| Estado | Recomendación |
|--------|--------------|
| Sin Core Values | `/scaleup-people-values` primero (prerequisito) |
| Core Values listos, sin OPSP | `/scaleup-strategy-opsp` — One-Page Strategic Plan |
| OPSP básico listo | `/scaleup-strategy-7strata` — profundizar diferenciación |
| Todo hecho | SWOT/SWT para refinar |

El OPSP es la pieza central de Strategy. Todo lo demás alimenta al OPSP.

### Step 5: Guide

Siempre conectar: "La estrategia debe caber en una página. Si no puedes explicarla simple, no está clara."

## Output

| Item | Destination |
|------|-------------|
| Work artifacts | `work/strategy/` |
| Next | Skill específico de Strategy |
