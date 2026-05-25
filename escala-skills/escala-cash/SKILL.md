---
description: 'Sub-agente Cash. Guía la decisión de Cash: Ciclo de Conversión de Efectivo (CCC), Power
  of One, cash acceleration strategies.'
name: escala-cash
---

# Escalamiento Cash

## Purpose

Entry point del sub-agente de Cash. Evalúa salud financiera operativa y guía optimización del flujo de efectivo.

## Context

**When to use:** Cuando el diagnóstico ruta a Cash, o el usuario quiere optimizar flujo de efectivo.

## Steps

### Step 1: Load Context

Leer:
- `.escala/agent/sub-agents/cash.md`
- `.escala/agent/memory/company-profile.yaml`
- `.escala/knowledge/cash/overview.md`

### Step 2: Check Existing Work

```bash
ls work/cash/ 2>/dev/null
```

### Step 3: Recommend Next Tool

| Estado | Recomendación |
|--------|--------------|
| Sin trabajo previo | `/escala-cash-ccc` — mapear Ciclo de Conversión de Efectivo (CCC) |
| CCC mapeado | `/escala-cash-power1` — análisis Análisis Power of One |
| Análisis Power of One hecho | `/escala-cash-acceleration` — estrategias de aceleración |
| Todo hecho | Re-mapear CCC, medir mejoras |

### Step 4: Guide

Enfatizar: "El cash es el oxígeno del crecimiento. El crecimiento chupa cash — si no lo gestionas, el éxito mismo puede matarte."

Nota: Este sub-agente NO da asesoría financiera. Guía el análisis operativo del ciclo de cash usando las herramientas de Escalamiento de Negocios.

## Output

| Item | Destination |
|------|-------------|
| Work artifacts | `work/cash/` |
| Next | Skill específico de Cash |

---
*> Esta herramienta está inspirada en los Hábitos de Ejecución, desarrollados por Verne Harnish como parte de su metodología de escalamiento de negocios. Ver [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) para la referencia completa.
