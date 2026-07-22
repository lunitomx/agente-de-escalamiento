---
description: 'El board se reúne solo. Revisa toda la data de la empresa en memoria/ y knowledge graph, y produce un análisis completo sin que el CEO pregunte nada.'
name: escala-board
---

# Escalamiento — Board Proactivo Trimestral

## Purpose

El board no espera a que el CEO pregunte. Cada trimestre (o cuando el CEO lo active), el board se "reúne" — revisa TODA la data acumulada en las sesiones de Escala, analiza tendencias, y produce un paquete completo de decisiones. El CEO solo revisa y ajusta.

## Steps

### Step 1: Cargar contexto de la empresa

Leer todo lo disponible en:
- `.escala/agent/memory/` — perfil, hechos, decisiones
- `.escala/knowledge/` — worksheets completados
- `work/people/`, `work/strategy/`, `work/execution/`, `work/cash/` — entregables
- `work/epics/` — retrospectivas de sesiones anteriores

"Esto es lo que sé de tu empresa hasta hoy. ¿Hay algo más que deba saber antes de la reunión de board?"

### Step 2: Revisar las 4 Decisiones

Para cada decisión, generar un diagnóstico:

**People:**
- FACe actual: ¿huecos? ¿personas overloaded?
- A-players identificados vs rotación
- Core Values: ¿se viven o son póster?

**Strategy:**
- OPSP: ¿sigue vigente? ¿BHAG en camino?
- Brand Promises: ¿se cumplen? (check vs reseñas/NPS si hay)
- SWT preliminar basado en datos, no en opiniones

**Execution:**
- Prioridad #1 actual: ¿avance? ¿bloqueos?
- Ritmo de reuniones: ¿se sostienen?
- KPIs: tendencias (mejorando/empeorando/planos)

**Cash:**
- CCC actual vs trimestre anterior
- Power of One: palancas con mayor impacto potencial
- Alertas: ¿oxígeno suficiente para 12 meses?

### Step 3: Síntesis — Board Discussion

Simular un debate de board entre el asesor de negocio (estrategia/cash), COO
(ejecución/operaciones) y CFO (finanzas).

"No esperes un informe tibio. Esto es un board de verdad."

Roles:
- **Asesor de negocio:** "¿Esto acerca o aleja del BHAG?"
- **COO:** "¿Hay ritmo para ejecutar esto?"
- **CFO:** "¿Cuánto oxígeno consume?"

### Step 4: Output — Paquete de Board

Generar 4 artefactos:

1. **SWT actualizado** (Strengths, Weaknesses, Trends) con evidencia citada
2. **Propuesta de Prioridad #1** para el siguiente trimestre con justificación
3. **Acta de board meeting** con decisiones, dissents, y próximos pasos
4. **Carta al CEO** — directa, basada en evidencia y a veces incómoda

### Step 5: El CEO solo revisa

"Esto es lo que el board propone. Tú decides. ¿Qué ajustas?"

El board no impone — recomienda. El CEO tiene la última palabra. Pero ya no empieza de cero.

## Output

- `work/strategy/swt-{trimestre}.md` — SWT actualizado
- `work/strategy/prioridad-{trimestre}.md` — Prioridad #1 propuesta
- `work/board/acta-{trimestre}.md` — Acta de board meeting
- `work/board/carta-ceo-{trimestre}.md` — Carta al CEO

## Notas

- El board usa TODA la data disponible. Si no hay datos suficientes, lo dice: "No tengo suficiente información para evaluar People. ¿Quieres que hagamos un diagnóstico primero?"
- Las recomendaciones citan evidencia: "Tu CCC subió 17 días (ver sesión S-X-260315)."
- La carta al CEO no endulza: "Eduardo, tu equipo está bien, tu cash está bien. El problema es que no has decidido quién es tu Core Customer. Y sin eso, todo lo demás es un parche."
