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

Ofrece el siguiente paso como pregunta en español llano. No muestres el nombre
del procedimiento ni un comando; si el dueño acepta, ejecuta el procedimiento
interno indicado.

| Estado | Recomendación |
|--------|--------------|
| Sin Core Values | procedimiento interno `escala-people-values` primero (prerequisito). Al dueño: "Antes de tu plan, ¿ponemos en palabras lo que en tu empresa no se negocia?" |
| Core Values listos, sin Plan Estratégico de Una Página (OPSP) | procedimiento interno `escala-strategy-opsp`. Al dueño: "¿Armamos tu plan del negocio en una sola página?" |
| Plan Estratégico de Una Página (OPSP) básico listo | procedimiento interno `escala-strategy-7strata`. Al dueño: "¿Vemos qué te hace distinto de tu competencia?" |
| Todo hecho | SWOT/SWT para refinar |
| Pregunta por su competencia, su mercado o las tendencias de su sector (sin prerequisito) | `escala-strategy-research` — investigar afuera antes de decidir |
| Habla de ventas, marketing, prospectos o clientes que no compran o no regresan (sin prerequisito) | `escala-strategy-journey` — cómo llega un cliente hasta que le compra, sólo si el módulo dice que se pregunte |

El Plan Estratégico de Una Página (OPSP) es la pieza central de Strategy. Todo lo demás alimenta al Plan Estratégico de Una Página (OPSP).

### Step 4: Guide

Siempre conectar: "La estrategia debe caber en una página. Si no puedes explicarla simple, no está clara."

## Output

| Item | Destination |
|------|-------------|
| Work artifacts | `work/strategy/` |
| Next | Skill específico de Strategy |

---
