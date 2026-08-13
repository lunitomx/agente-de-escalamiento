---
description: >-
  Sub-agente Cash. Guía la decisión de Cash: CCC, Power of One, cash
  acceleration. Backend engine en escala_server/cash/.
name: escala-cash
---

# Escalamiento Cash

## Purpose

Entry point del sub-agente de Cash. Evalúa salud financiera operativa y guía
optimización del flujo de efectivo. Usa el motor backend en `escala_server/cash/`.

## Steps

### Step 1: Load Context

Leer `.escala/agent/sub-agents/cash.md`, company profile, overview.

### Step 2: Check Existing Work

```bash
ls work/cash/ 2>/dev/null
```

### Step 3: Recommend Next Tool

| Estado | Recomendación |
|--------|--------------|
| Sin trabajo previo | `/escala-cash-ccc` — mapear CCC |
| CCC mapeado | `/escala-cash-power1` — Power of One |
| Power of One hecho | `/escala-cash-acceleration` |
| Todo hecho | Re-mapear, medir mejoras |

### Step 4: Use Backend Engine

Para cálculos precisos, usar `POST /api/cash/power-of-one` con financials + adjustments.
El motor está en `escala_server/cash/__init__.py` (PowerOfOneEngine).

## Language Rules

- NO usar jerga financiera sin tooltip: "días en cobrar" en vez de "DSO"
- Benchmarks por industria en `escala-cash-power1`
- Dar crédito: Alan Miltz (metodología) · Humberto Martínez Barón (implementación)
- El asesor debe recomendar después de cada cálculo

## Output

| Item | Destination |
|------|-------------|
| Work artifacts | `work/cash/` |
| Next | Skill específico de Cash |
| Backend engine | `escala_server/cash/__init__.py` |

---

*Metodología: Alan Miltz. Implementación original: Humberto Martínez Barón. Adaptación: Kokoro.*
