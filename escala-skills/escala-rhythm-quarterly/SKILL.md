---
description: '2 semanas antes del cierre de trimestre, Escala prepara tu off-site: SWT, Prioridad #1 propuesta, agenda completa. Tú solo llegas a decidir.'
name: escala-rhythm-quarterly
---

# Escalamiento Execution — Quarterly Off-site Automation

## Purpose

El off-site trimestral es el momento más importante del trimestre. Pero prepararlo toma horas que el CEO no tiene. Este skill automatiza toda la preparación: 2 semanas antes del cierre, Escala prepara el SWT, la propuesta de Prioridad #1, y la agenda completa del off-site.

## Steps

### Step 1: Timing — 2 semanas antes

"Tu trimestre cierra en [fecha]. Estamos a [días] del off-site."

Si faltan más de 2 semanas: "Perfecto. Te avisaré 2 semanas antes para preparar todo."
Si faltan menos de 2 semanas: "OK, estamos cerca. Empecemos ya la preparación."

### Step 2: Ejecutar Board Proactivo

Invocar escala-board para tener el análisis completo de las 4 decisiones.

El board genera:
- SWT actualizado
- Propuesta de Prioridad #1
- Acta de board meeting
- Carta al CEO

Esto toma ~2-3 minutos de procesamiento.

### Step 3: Preparar agenda del off-site

```
📋 Agenda — Quarterly Off-site Q{trimestre} {año}

Duración: 1 día completo (9am-5pm)

Mañana (9am-1pm):
  09:00 — Bienvenida y encuadre (15 min)
  09:15 — Revisión del trimestre: ¿qué logramos? (30 min)
  09:45 — SWT: Strengths, Weaknesses, Trends (60 min)
  10:45 — Break (15 min)
  11:00 — People Review: FACe, A-players, rotación (60 min)
  12:00 — Cash Review: CCC, Power of One, proyecciones (60 min)

Almuerzo (1pm-2pm)

Tarde (2pm-5pm):
  14:00 — Prioridad #1 próximo trimestre (60 min)
  15:00 — KPIs y Critical Number (30 min)
  15:30 — Break (15 min)
  15:45 — Tema del trimestre (30 min)
  16:15 — WWW: compromisos y próximos pasos (30 min)
  16:45 — Cierre y evaluación del off-site (15 min)
```

### Step 4: Preparar datos de respaldo

Para cada sección de la agenda, preparar datos:

**Revisión del trimestre:**
- KPIs trimestrales con tendencia
- WWWs cumplidos vs total
- Obstáculos resueltos vs abiertos

**SWT:**
- Ya generado por el board (escala-board)

**People Review:**
- FACe actual (de escala-people-organigrama si existe)
- Rotación, hiring pipeline

**Cash Review:**
- CCC actual vs trimestre anterior
- Power of One calculado (de escala-cash-finanzas si existe)

**Prioridad #1:**
- Propuesta del board con justificación numérica

### Step 5: Entregar paquete al CEO

"Tu off-site está listo. Esto es lo que tengo para ti:

- ✅ Agenda completa (1 día)
- ✅ SWT actualizado con datos reales
- ✅ Propuesta de Prioridad #1
- ✅ Datos de respaldo para cada sección
- ✅ Carta del board

Solo necesitas:
- Reservar el espacio (fuera de la oficina)
- Invitar al equipo clave
- Llegar y facilitar (yo te guío sección por sección si quieres)

¿Quieres que te recuerde 1 semana antes y 1 día antes?"

### Post Off-site

Después del off-site: "¿Cómo fue? Súbeme las notas o la grabación y actualizo todo para el siguiente trimestre."

## Output

- Agenda del off-site (horario detallado)
- SWT trimestral
- Datos de respaldo para cada sección
- Propuesta de Prioridad #1 con justificación
- Paquete guardado en `work/execution/offsite-Q{trimestre}-{año}/`

## Notas

- Si no hay suficientes datos para generar todo, el skill lo dice y sugiere qué falta.
- El CEO siempre tiene la última palabra: "Esto es lo que el board y los datos sugieren. Tú decides."
- La agenda es una plantilla — el CEO puede ajustar tiempos y secciones.
