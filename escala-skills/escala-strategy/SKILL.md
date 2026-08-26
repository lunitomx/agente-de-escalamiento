---
description: 'Sub-agente Strategy. Guía la decisión de Estrategia: core values, BHAG,
  brand promise, Plan Estratégico de Una Página (OPSP), 7 Estratos de Estrategia.'
name: escala-strategy
---

# Escalamiento Strategy

## Purpose

Entry point del sub-agente de Strategy. Evalúa madurez estratégica, verifica prerequisitos y guía hacia la herramienta correcta.

## Context

**When to use:** Cuando el diagnóstico ruta a Strategy, o el usuario quiere trabajar en estrategia.

## Steps

### Step 1: Load Context

Leer:
- `.escala/agent/sub-agents/strategy.md`
- `.escala/agent/memory/company-profile.yaml`
- `.escala/knowledge/strategy/overview.md`

### Step 2: Check Existing Work & Prerequisites

```bash
ls work/strategy/ 2>/dev/null
ls work/people/ 2>/dev/null
```

Verificar que People tiene base mínima (score >= 2). Si no, sugerir volver a People primero.

### Gate de evidencia de clientes

Antes de definir cliente central, promesa de marca, posicionamiento o plan:

- Revisar evidencia de clientes con fuente, fecha, confianza y contradicciones.
- Citar los identificadores de evidencia que sostienen cada recomendación.
- Si falta evidencia, hacer una sola pregunta de evidencia faltante por turno.
- No inventar diferenciación, promesa o posicionamiento cuando haya huecos.

### Step 3: Recommend Next Tool

| Estado | Recomendación |
|--------|--------------|
| Sin Core Values | `/escala-people-values` primero (prerequisito) |
| Core Values listos, sin Plan Estratégico de Una Página (OPSP) | `/escala-strategy-opsp` — Plan Estratégico de Una Página (OPSP) |
| Plan Estratégico de Una Página (OPSP) básico listo | `/escala-strategy-7strata` — profundizar diferenciación |
| Todo hecho | SWOT/SWT para refinar |

El Plan Estratégico de Una Página (OPSP) es la pieza central de Strategy. Todo lo demás alimenta al Plan Estratégico de Una Página (OPSP).

### Step 4: Guide

Siempre conectar: "La estrategia debe caber en una página. Si no puedes explicarla simple, no está clara."

## Output

| Item | Destination |
|------|-------------|
| Work artifacts | `work/strategy/` |
| Next | Skill específico de Strategy |

---
