---
description: 'Sub-agente People. Evalúa y guía la decisión de People: personas correctas
  en los asientos correctos, core values, accountability.'
name: scaleup-people
---

# ScaleUp People

## Purpose

Entry point del sub-agente de People. Evalúa la madurez de People, revisa trabajo existente y guía al siguiente paso concreto.

## Context

**When to use:** Cuando el diagnóstico ruta a People, o el usuario pide trabajar en temas de equipo/personas.

## Canonical Pipeline

Pipeline ID: `scaleup-people-development`

Este entrypoint no reemplaza los skills de People. Orquesta el flujo recomendado:

1. `/scaleup-people-fac` — construir Function Accountability Chart
2. `/scaleup-people-values` — descubrir Core Values desde evidencia observada
3. `/scaleup-people-topgrading` — diseñar proceso de contratacion A-player

Stop conditions: falta mapa de funciones, o no hay evidencia conductual suficiente para valores.
Quality gates: `facchart_has_single_accountable`, `values_are_observed_not_invented`.
Registry: `.raise/pipelines/scaleup.yaml`.

## Steps

### Step 1: Load Context

Leer:
- `.scaleup/agent/sub-agents/people.md` (persona del sub-agente)
- `.scaleup/agent/memory/company-profile.yaml` (contexto empresa)
- `.scaleup/knowledge/people/overview.md` (conocimiento del dominio)

### Step 2: Check Existing Work

```bash
ls work/people/ 2>/dev/null
```

Evaluar qué herramientas ya se han completado.

### Step 3: Recommend Next Tool

| Estado | Recomendación |
|--------|--------------|
| Sin trabajo previo | `/scaleup-people-fac` — Function Accountability Chart |
| FACChart hecho | `/scaleup-people-values` — Core Values Discovery |
| FACChart + Values | `/scaleup-people-topgrading` — Proceso de contratación |
| Todo hecho | Revisar gaps, re-evaluar scores |

### Step 4: Guide

Adaptar la guía al tamaño y contexto de la empresa. Una startup de 15 personas necesita algo diferente que una empresa de 200.

Siempre conectar con el "por qué" del libro: sin las personas correctas, la estrategia y ejecución no funcionan.

## Output

| Item | Destination |
|------|-------------|
| Work artifacts | `work/people/` |
| Next | Skill específico de People |
