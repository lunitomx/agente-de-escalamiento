---
description: 'Acta de board meeting + Carta al CEO generadas automáticamente. El board documenta sus decisiones y te escribe como un board de verdad.'
name: escala-board-acta
---

# Escalamiento — Acta de Board + Carta al CEO

## Purpose

Un board de verdad documenta sus decisiones. Y un buen board member te escribe una carta que a veces es incómoda pero siempre es útil. Este skill genera ambos artefactos automáticamente después de una sesión de board proactivo.

## Steps

### Step 1: Acta de Board Meeting

Generar un acta estructurada con:

```
# Acta de Board Meeting — {fecha}

**Presentes:**
- ESCALA (estratega)
- COO (operaciones)
- CFO (finanzas)

**Decisiones tomadas:**
1. [Decisión 1] — Votos: 3-0
2. [Decisión 2] — Votos: 2-1 (CFO disiente)

**Dissents:**
- CFO: "La decisión 2 consume $50K de efectivo que necesitamos para el CCC."

**Prioridad #1 aprobada:**
- [Prioridad] con Critical Number [métrica] y meta [número]

**Próximos pasos:**
- CEO: [acción] para [fecha]
- Equipo: [acción] para [fecha]

**Próxima reunión de board:** {fecha + 90 días}
```

### Step 2: Carta al CEO

Una carta en voz del asesor de negocio, directa y sin paja.

```
{ciudad}, {fecha}

{cercanía},

{diagnóstico honesto — lo bueno primero, luego lo que preocupa}

{recomendación concreta}

{cierre — a veces motivacional, a veces incómodo}

— Asesor ESCALA
```

Ejemplo:

```
Cancún, 15 de junio 2026

Eduardo,

Tu equipo está bien. Tus A-players están en los asientos correctos y tu
cultura de daily huddle es sólida. Eso no es poca cosa — la mayoría de
las empresas nunca llegan ahí.

Pero tu cash me preocupa. Tu CCC subió 17 días este trimestre. Si no lo
arreglas, en 6 meses el crecimiento te va a comer el oxígeno. Ya vimos
esto en Q3 2025 — no dejemos que se repita.

Mi recomendación: Prioridad #1 este trimestre es Cash. Punto. Nada de
"estrategia" ni "contrataciones" hasta que tu CCC baje de 60 días. El
Power of One te dice que mejorando 1% en cobranza liberas $45,000. 
Empieza por ahí.

No es glamoroso. Pero es lo que necesitas.

— Asesor ESCALA
```

### Step 3: Guardar

- `work/board/acta-{año}-Q{trimestre}.md`
- `work/board/carta-ceo-{año}-Q{trimestre}.md`

## Output

- Acta de board con decisiones, votos, dissents
- Carta al CEO en voz del asesor de negocio
- Próximos pasos con responsables y fechas

## Notas

- El tono de la carta se adapta a la situación: urgente si hay crisis, motivacional si las cosas van bien.
- Si no hay suficiente contexto, el skill pide más datos antes de generar la carta.
- El board documenta dissents. Si el CFO no está de acuerdo con algo, queda registrado. Eso es un board de verdad.
