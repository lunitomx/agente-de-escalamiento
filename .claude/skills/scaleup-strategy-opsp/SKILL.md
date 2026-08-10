---
description: 'Guía paso a paso para llenar el One-Page Strategic Plan (OPSP), la herramienta
  central de Scaling Up para Strategy.'
name: scaleup-strategy-opsp
---

# ScaleUp Strategy — OPSP

## Purpose

Guiar al usuario paso a paso para completar su One-Page Strategic Plan. El OPSP es LA herramienta central de Scaling Up — toda la estrategia de la empresa en una sola página.

## Context

**When to use:** Cuando el usuario está listo para crear o actualizar su OPSP.

**Prerequisites:** Core Values identificados (al menos borrador). Si no existen, guiar su descubrimiento primero.

## Steps

### Step 1: Load Verified Context

Leer las fuentes instaladas que sí existen:
- `.scaleup/knowledge/strategy/tools/opsp.yaml`
- `.scaleup/knowledge/strategy/worksheets/opsp.yaml`
- evidencia y perfil de empresa disponibles, sólo si el usuario los confirma.

No declares que existe una plantilla, un archivo previo ni un plan guardado si
no se ha confirmado. S47.4 incorporará persistencia, reanudación y exportación
local; esta guía sólo construye y revisa el modelo.

### Step 2: Establish the One-Page Structure

- Columns 1-3 contienen pensamiento estratégico; Columns 4-7 contienen
  ejecución anual y trimestral.
- Las tres filas son Actions / Goals / Targets, con una celda por columna.
- Cada celda de ejecución debe nombrar Your Accountability.
- Column 2 incluye Key Capabilities para el horizonte de 3-5 años.

### Step 3: Voice of Customer Evidence Gate

Antes de completar Sandbox, Brand Promise, posicionamiento o Strategy Canvas:

- Cargar evidencia Voice of Customer como `CustomerEvidenceRecord`.
- Usar `map_evidence_to_strategy` para revisar inputs, gaps y contradicciones.
- Sandbox/Core Customer y Brand Promise requieren evidence ids citados.
- Si falta evidencia aprobada para customer segment, promised value, proof u
  objection, ask one missing-evidence question at a time.
- Si hay gaps, do not invent Brand Promise, Sandbox, positioning, OPSP, or
  Strategy Canvas claims. Marcar el gap y pedir evidencia.

### Step 4: Core Values (si no existen)

Facilitar ejercicio de descubrimiento:
1. "¿Qué comportamientos premias o castigas sin importar el resultado?"
2. "¿Qué valores tiene la persona que más admiras en tu equipo?"
3. "¿Qué no negociarías aunque te costara dinero?"

Llegar a 3-5 Core Values. Guardar.

### Step 5: Purpose & BHAG

- **Purpose:** "¿Por qué existe tu empresa más allá de hacer dinero?"
- **BHAG:** "¿Cuál es tu meta audaz a 10-25 años que inspira a todo el equipo?"

### Step 6: Sandbox (3-5 años)

Definir la "arena competitiva":
- Revenue y profit target a 3-5 años
- Geografía / mercado
- Segmento de clientes
- Producto/servicio foco

### Step 7: Brand Promise & Profit per X

- **Brand Promise:** "¿Qué promesa medible le haces a tu cliente?"
- **KPI de la promesa:** "¿Cómo la mides?"
- **Profit per X:** "¿Cuál es tu motor económico? ¿Profit per qué?"

### Step 8: Annual Goals

Metas anuales: revenue, profit, top 5 prioridades del año.

### Step 9: Quarterly Plan

- **Critical Number:** la métrica #1 del trimestre
- **Top 5 prioridades** con owner y KPI
- **Theme:** nombre creativo + celebración + deadline + scoreboard

### Step 10: Review Without False Persistence

Revisar completitud: ¿Cabe en una página? ¿Es claro? ¿Lo entendería un empleado nuevo?
Si falta un dato, declararlo pendiente y pedir una sola aclaración. No afirmar
que el OPSP se guardó: esa capacidad pertenece a S47.4.

<verification>
Estructura OPSP revisada; pendientes explícitos y sin promesa de persistencia.
</verification>

## Output

| Item | Destination |
|------|-------------|
| Estructura OPSP revisada | Conversación actual; S47.4 añadirá persistencia local |
| Next | `/scaleup-execution` o `/scaleup-progress` |

## Quality Checklist

- [ ] Core Values verificados antes de empezar
- [ ] Cada sección completada con datos específicos (no genéricos)
- [ ] BHAG es realmente audaz (10-25 años, no 1-2 años)
- [ ] Brand Promise es medible, diferenciadora y citada con evidence ids
- [ ] Prioridades tienen Owner asignado
- [ ] Actions / Goals / Targets cubren las siete columnas
- [ ] Cada celda de ejecución tiene Your Accountability
- [ ] Key Capabilities cubren 3-5 años
- [ ] Critical Number es UNA sola métrica
- [ ] El OPSP completo cabe en una página conceptualmente
