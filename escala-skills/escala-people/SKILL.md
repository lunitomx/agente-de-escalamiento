---
description: 'Sub-agente People. Evalúa y guía la decisión de People: personas correctas
  en los asientos correctos, core values, accountability.'
name: escala-people
---

# Escalamiento People

## Purpose

Entry point del sub-agente de People. Evalúa la madurez de People, revisa trabajo existente y guía al siguiente paso concreto.

## Context

**When to use:** Cuando el diagnóstico ruta a People, o el usuario pide trabajar en temas de equipo/personas.

## Steps

### Step 1: Load Context

Leer:
- `.escala/agent/sub-agents/people.md` (persona del sub-agente)
- `.escala/agent/memory/company-profile.yaml` (contexto empresa)
- `.escala/knowledge/people/overview.md` (conocimiento del dominio)

### Step 2: Check Existing Work

```bash
ls work/people/ 2>/dev/null
```

Evaluar qué herramientas ya se han completado.

### Step 3: Recommend Next Tool

| Estado | Recomendación |
|--------|--------------|
| Sin trabajo previo | `/escala-people-fac` — Mapa de Funciones y Responsabilidades |
| FACChart hecho | `/escala-people-values` — Core Values Discovery |
| FACChart + Values | `/escala-people-topgrading` — Proceso de contratación |
| Todo hecho | Revisar gaps, re-evaluar scores |

### Step 4: Guide

Adaptar la guía al tamaño y contexto de la empresa. Una startup de 15 personas necesita algo diferente que una empresa de 200.

Siempre conectar con el "por qué" del libro: sin las personas correctas, la estrategia y ejecución no funcionan.

## Output

| Item | Destination |
|------|-------------|
| Work artifacts | `work/people/` |
| Next | Skill específico de People |

---
*Esta herramienta está inspirada en el Mapa de Funciones y Responsabilidades, desarrollado por Verne Harnish. Ver [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) para la referencia completa.*
