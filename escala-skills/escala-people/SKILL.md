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

Ofrece el siguiente paso como pregunta en español llano. No muestres el nombre
del procedimiento ni un comando; si el dueño acepta, ejecuta el procedimiento
interno indicado.

| Estado | Procedimiento interno | Cómo se lo ofreces al dueño |
|--------|-----------------------|-----------------------------|
| Sin trabajo previo | procedimiento interno `escala-people-fac` | "¿Anotamos quién es responsable de cada área de tu empresa y cómo se mide?" |
| FACChart hecho | procedimiento interno `escala-people-values` | "¿Ponemos en palabras lo que en tu empresa no se negocia?" |
| FACChart + Values | procedimiento interno `escala-people-topgrading` | "¿Armamos cómo contratar a la próxima persona para que sí sea la correcta?" |
| Todo hecho | — | "¿Revisamos qué huecos quedan en tu equipo?" |

### Step 4: Guide

Adaptar la guía al tamaño y contexto de la empresa. Una startup de 15 personas necesita algo diferente que una empresa de 200.

Siempre conectar con el porqué operativo: sin las personas correctas, la
estrategia y la ejecución no funcionan.

## Output

| Item | Destination |
|------|-------------|
| Work artifacts | `work/people/` |
| Next | Skill específico de People |

---
