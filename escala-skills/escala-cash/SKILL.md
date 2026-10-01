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
Lee también `.escala/knowledge/cash/overview.md` (en un paquete:
`references/knowledge/cash/overview.md`) y abre la ficha del curso de Cash
que corresponda a lo que preguntó el dueño.

### Step 2: Check Existing Work

```bash
ls work/cash/ 2>/dev/null
```

### Step 3: Recommend Next Tool

Ofrece el siguiente paso como pregunta en español llano. No muestres el nombre
del procedimiento ni un comando; si el dueño acepta, ejecuta el procedimiento
interno indicado.

| Estado | Procedimiento interno | Cómo se lo ofreces al dueño |
|--------|-----------------------|-----------------------------|
| Sin trabajo previo | procedimiento interno `escala-cash-ccc` | "¿Vemos cuántos días pasan desde que pagas a tu proveedor hasta que tu cliente te paga?" |
| CCC mapeado | procedimiento interno `escala-cash-power1` | "¿Vemos cuánto dinero liberas si cobras 10 días antes?" |
| Power of One hecho | procedimiento interno `escala-cash-acceleration` | "¿Buscamos formas de que el dinero te llegue más rápido?" |
| Te pasa sus estados financieros o su estado de resultados (sin prerequisito) | procedimiento interno `escala-cash-finanzas` | "¿Me pasas tus estados financieros como los tengas, en PDF, Excel o foto, y yo saco los números?" |
| Todo hecho | — | "¿Volvemos a medir para ver cuánto mejoró tu efectivo?" |

### Step 4: Use Backend Engine

Para cálculos precisos, usar `POST /api/cash/power-of-one` con financials + adjustments.
El motor está en `escala_server/cash/__init__.py` (PowerOfOneEngine).

## Language Rules

- NO usar jerga financiera sin tooltip: "días en cobrar" en vez de "DSO"
- Benchmarks por industria en `escala-cash-power1`
- Dar crédito: Alan Miltz (metodología)
- Cuando una ficha de `.escala/knowledge/cash/` aplique, explica la idea con
  ella y cita su frase una vez por tema:
  "Según el curso de cash que vimos, recuerda: …".
  Nunca digas quién dio el curso. Si no está en una ficha, no se la atribuyas
  al curso.
- El asesor debe recomendar después de cada cálculo

## Output

| Item | Destination |
|------|-------------|
| Work artifacts | `work/cash/` |
| Next | Skill específico de Cash |
| Backend engine | `escala_server/cash/__init__.py` |

---

*Metodología: Alan Miltz. Adaptación: Kokoro.*
