---
description: 'Mapea el Ciclo de Conversión de Efectivo (CCC) completo: sales cycle, delivery cycle
  y collection cycle en días.'
name: escala-cash-ccc
---

# Escalamiento Cash — Ciclo de Conversión de Efectivo (CCC)

## Purpose

Mapear el CCC completo de la empresa: cuántos días tarda un peso invertido en regresar como cash cobrado.

## Steps

### Step 1: Load Context

Leer `.escala/knowledge/cash/tools/cash-conversion-cycle.md`.
Cargar template `templates/cash-conversion-cycle.md`.

### Step 2: Map Sales Cycle

Cuántos días desde primer contacto hasta contrato firmado. Desglosar etapas.

### Step 3: Map Delivery Cycle

Cuántos días desde contrato hasta entrega completada.

### Step 4: Map Collection Cycle

Cuántos días desde facturación hasta dinero en banco.

### Step 5: Calculate & Identify Opportunities

CCC = Sales + Delivery + Collection. Identificar qué componente es más largo y dónde hay oportunidades de reducción.

### Step 6: Save

Guardar en `work/cash/ccc-analysis.md`.

## Output

| Item | Destination |
|------|-------------|
| CCC Analysis | `work/cash/ccc-analysis.md` |
| Next | `/escala-cash-power1` |

---
