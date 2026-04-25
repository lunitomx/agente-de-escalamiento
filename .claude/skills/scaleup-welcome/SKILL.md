---
description: 'Onboarding para ScaleUp Agent AI. Recoge perfil de la empresa y prepara
  el framework para su primera sesión de diagnóstico.'
name: scaleup-welcome
---

# ScaleUp Welcome

## Purpose

Dar la bienvenida al usuario, recoger información de su empresa y preparar el contexto para el diagnóstico inicial. Primera interacción con el framework.

## Context

**When to use:** Primera vez que un usuario interactúa con ScaleUp Agent AI.

**When to skip:** Si `.scaleup/agent/memory/company-profile.yaml` ya tiene datos (empresa ya registrada).

## Steps

### Step 1: Verify Framework

```bash
ls .scaleup/agent/identity/core.md 2>/dev/null && echo "FRAMEWORK_EXISTS" || echo "NO_FRAMEWORK"
```

| Result | Action |
|--------|--------|
| FRAMEWORK_EXISTS | Continue |
| NO_FRAMEWORK | Stop: "Instala ScaleUp Agent AI primero." |

### Step 2: Company Intake

Preguntar de forma conversacional (no formulario):

1. **Nombre de la empresa**
2. **Industria / sector**
3. **Número de empleados** (aproximado)
4. **Rango de ingresos anuales** (opcional)
5. **Años en operación**
6. **Etapa de crecimiento:** startup | scaleup | establecida | enterprise
7. **Principales retos actuales** (en sus palabras)

<verification>
Toda la información básica de la empresa recolectada.
</verification>

### Step 3: Save Company Profile

Guardar en `.scaleup/agent/memory/company-profile.yaml` con los datos recolectados.

<verification>
company-profile.yaml actualizado con datos reales.
</verification>

### Step 4: Welcome Message

```
¡Bienvenido a ScaleUp Agent AI, {company_name}!

Tu empresa: {employees} empleados en {industry}, etapa {stage}

ScaleUp te guiará a escalar tu empresa usando la metodología Scaling Up
de Verne Harnish, enfocándose en 4 decisiones críticas:

  1. People — Las personas correctas en los asientos correctos
  2. Strategy — Estrategia clara en una página
  3. Execution — Ejecución disciplinada con ritmos y datos
  4. Cash — Cash flow como combustible del crecimiento

Siguiente paso: /scaleup-diagnose
→ Evaluaremos tu empresa en las 4 decisiones para saber por dónde empezar.
```

## Output

| Item | Destination |
|------|-------------|
| Company profile | `.scaleup/agent/memory/company-profile.yaml` |
| Next | `/scaleup-diagnose` |
