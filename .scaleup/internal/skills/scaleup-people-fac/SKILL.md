---
description: 'Guía para crear el Function Accountability Chart (FACChart). Clarifica
  estructura organizacional, roles y accountability.'
name: scaleup-people-fac
---

# ScaleUp People — Function Accountability Chart

## Purpose

Guiar al usuario para crear su FACChart: identificar todas las funciones del negocio, asignar UN accountable por función, y definir KPIs.

## Steps

### Step 1: Load Context

Leer `.scaleup/agent/memory/company-profile.yaml` y `.scaleup/knowledge/people/tools/function-accountability-chart.md`.
Cargar template `templates/function-accountability-chart.md`.

### Step 2: Identify Functions

Preguntar: "¿Cuáles son las funciones principales de tu empresa?" Guiar con las funciones estándar como base y adaptar a su industria.

### Step 3: Assign Accountability

Para cada función, preguntar quién es accountable. Reglas:
- Exactamente 1 persona por función
- Máximo 2-3 funciones por persona
- El CEO no puede ser accountable de todo

### Step 4: Define KPIs

Para cada función, definir 1-2 KPIs medibles semanalmente.

### Step 5: Validate & Save

Correr checklist de validación. Guardar en `work/people/fac-chart.md`.

## Output

| Item | Destination |
|------|-------------|
| FACChart | `work/people/fac-chart.md` |
| Next | `/scaleup-people-values` o `/scaleup-people` |
