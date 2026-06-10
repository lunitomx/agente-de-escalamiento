---
description: 'Me acuerdo de ti. Escala mantiene un timeline trimestral de tu negocio: KPIs, decisiones, crisis, contrataciones. "Tu CCC en Q1 2025: 45 días. Q1 2026: 62 días."'
name: escala-memory
---

# Escalamiento — Memoria Longitudinal

## Purpose

Un coach que no se acuerda de ti no es coach. Escala recuerda todo: tus KPIs por trimestre, las decisiones que tomaste, las crisis que superaste, las personas que contrataste. Este skill consulta esa memoria y te da perspectiva que ningún consultor externo podría darte sin 6 meses de contexto.

## Steps

### Step 1: Cargar el archivo del negocio

Leer todo el historial disponible:
- `.escala/agent/memory/` — facts y decisiones guardadas
- `work/people/`, `work/strategy/`, `work/execution/`, `work/cash/` — entregables
- Sesiones pasadas (work/epics/) — retrospectivas y aprendizajes
- Worksheets completados

Si no hay historial suficiente: "Todavía estamos construyendo tu memoria. Necesito al menos 2 trimestres de datos para darte perspectiva longitudinal."

### Step 2: Construir el timeline trimestral

Organizar por trimestre:

```
📅 Timeline — {Empresa}

Q1 2025:
  People:   FACe inicial con 5 funciones. VP Ventas vacío.
  Strategy: OPSP creado. Core Customer identificado.
  Execution: Daily huddle iniciado. 8/10 Rockefeller Habits.
  Cash:     CCC 45 días. Margen bruto 32%.
  Eventos:  Contrataste a María como Controller.

Q2 2025:
  People:   María renunció. VP Ventas sigue vacío.
  Strategy: BHAG revisado. Nuevo: $50M para 2030.
  Execution: Daily huddle consistencia bajó a 60%.
  Cash:     CCC subió a 52 días. Margen bajó a 28%.
  Eventos:  Perdiste tu cliente más grande (-$200K).

Q3 2025:
  People:   Contrataste VP Ventas (Carlos).
  Strategy: Brand Promise actualizada.
  Execution: Volviste a 85% consistencia en daily.
  Cash:     CCC 48 días. Power of One: palanca precio +$32K.
  Eventos:  Nuevo producto lanzado.

Q4 2025:
  People:   Carlos (VP Ventas) renunció. Otra vez vacío.
  Strategy: Sin cambios.
  Execution: Daily huddle 90%. Prioridad #1: Cash.
  Cash:     CCC 62 días. Crisis de efectivo en diciembre.
  Eventos:  Casi te quedas sin cash. Préstamo de emergencia.

Q1 2026:
  ...
```

### Step 3: Identificar patrones

Analizar el timeline y detectar:

**Patrones de ciclo:**
- "Tus problemas de cash siempre empiezan en Q3 y explotan en Q4. Ya pasó en 2024, 2025..."
- "Cada vez que contratas un VP Ventas, renuncia en menos de 6 meses. Van 3 en 2 años."

**Patrones de decisión:**
- "En Q2 de cada año revisas el BHAG. Es tu ritual."
- "Siempre postergas las decisiones de People hasta que hay crisis."

**Patrones de mejora:**
- "Tu daily huddle mejoró de 60% a 90% en 2 trimestres. Eso es disciplina."
- "Tu margen bruto pasó de 32% a 35% en un año. Consistente."

### Step 4: Presentar perspectiva

"Mirando tus últimos [N] trimestres:

**Lo que mejoró:**
- [Métrica] subió/bajó de [X] a [Y]
- [Hábito] se volvió consistente

**Lo que empeoró:**
- [Métrica] empeoró de [X] a [Y]
- [Problema recurrente]

**Patrón que debes ver:**
- [Patrón detectado con datos]

**Si la tendencia continúa:**
- En [N] trimestres, [proyección]."

### Step 5: Guardar y actuar

Guardar perfil longitudinal en `work/memory/company-timeline.md`.

"¿Quieres que active alertas para que te avise cuando un patrón se repita?"

## Output

- Timeline trimestral del negocio
- Patrones detectados con evidencia
- Proyección de tendencias
- Perfil guardado en work/memory/

## Notas

- Si faltan datos de algún trimestre, el espacio queda en blanco: "Q2 2025: sin datos."
- Los patrones se detectan con mínimo 3 ocurrencias. Con 2 es "posible patrón".
- La memoria es acumulativa: cada sesión, cada decisión, cada KPI suma.
