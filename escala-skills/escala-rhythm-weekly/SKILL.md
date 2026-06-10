---
description: 'Cada viernes, Escala analiza los 5 daily huddles de la semana y prepara la agenda del weekly: qué obstáculos siguen abiertos, qué KPIs se movieron, qué merece discusión.'
name: escala-rhythm-weekly
---

# Escalamiento Execution — Weekly Meeting Prep

## Purpose

El weekly meeting no debería empezar con "¿de qué hablamos hoy?". Debería empezar con un pre-análisis de lo que pasó en la semana. Este skill analiza los 5 daily huddles de la semana (o las fotos de pizarrón) y entrega una agenda enfocada para el weekly.

## Steps

### Step 1: Recolectar los dailies de la semana

"¿Tienes los transcripts/fotos de los dailies de esta semana?"

Si el usuario ya configuró ritmos (escala-rhythm-setup), cargar la fuente automáticamente.

Si no tiene todos: "No importa. Trabajemos con los que tengas. ¿Cuántos dailies hubo esta semana?"

### Step 2: Analizar la semana

De cada daily extraer:

**WWWs acumulados:**
- Total de compromisos asumidos
- Completados vs pendientes
- Tasa de cumplimiento: "Esta semana: 12/15 WWWs completados (80%)"

**Obstáculos:**
- Obstáculos nuevos esta semana
- Obstáculos que siguen abiertos de semanas anteriores
- "Obstáculo 'máquina 3' lleva 8 días abierto. ¿Escalamos?"

**KPIs:**
- Tendencia semanal (subiendo/bajando/plano)
- Comparación vs meta del trimestre
- "Ventas: $45K → $42K → $48K → $44K → $46K. Promedio: $45K. Meta: $50K. Estás 10% abajo."

**Prioridad #1:**
- ¿Se mencionó en los dailies?
- Si no: "Tu Prioridad #1 (reducir CCC) no se mencionó en NINGÚN daily esta semana. Eso explica por qué no avanza."

### Step 3: Preparar agenda del weekly

Generar agenda enfocada:

```
📋 Agenda — Weekly Meeting {fecha}

1. Good News (5 min)
   - ¿Qué celebrar esta semana?

2. KPIs (10 min)
   - Ventas: $45K promedio (meta $50K) ⚠️
   - Cobranza: 82% (mejor que 78% semana pasada) ✅
   - Producción: 340 unidades/día (estable)

3. Prioridad #1 (30 min)
   - Tema: Reducir CCC
   - Avance: Sin progreso esta semana
   - Bloqueo: Clientes pagan lento (DSO 67 días)
   - Decisión necesaria: ¿Implementamos penalización por pago tardío?

4. Obstáculos abiertos (15 min)
   - 🔴 Máquina 3 — 8 días abierto. ¿Quién lo resuelve?
   - 🟡 Proveedor materia prima — 3 días. ¿Hay plan B?

5. WWW — Who, What, When (15 min)
   - Asignar dueños y fechas para cada decisión

6. Cierre (5 min)
   - ¿El weekly de HOY fue productivo? (1-5)
```

### Step 4: Facilitar la reunión

"Esta es la agenda. ¿Quieres que te guíe sección por sección durante el weekly?"

El skill puede funcionar como facilitador en tiempo real si el usuario lo desea.

### Step 5: Guardar

Guardar en `work/execution/weekly-{fecha}.md`.

"Después del weekly, súbeme las notas y actualizo tu scorecard trimestral."

## Output

- Agenda del weekly generada desde datos reales
- WWWs con tasa de cumplimiento
- Obstáculos priorizados por antigüedad
- KPIs con tendencia semanal
- Alerta si Prioridad #1 no se mencionó

## Notas

- Si no hubo dailies esta semana, el skill igual genera agenda: "Sin datos de daily. Hagamos el weekly con lo que recuerdes. Prioridad #1: ¿avanzó?"
- Si detecta que los KPIs están planos 3+ semanas: "Tus KPIs están estables pero no mejorando. ¿La Prioridad #1 es la correcta?"
