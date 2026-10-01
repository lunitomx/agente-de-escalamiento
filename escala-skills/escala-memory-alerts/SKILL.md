---
description: 'Escala detecta patrones repetidos y te alerta antes de que sea tarde. "Tus problemas de cash siempre empiezan en Q3. Estamos en junio — ¿preparamos?"'
name: escala-memory-alerts
---

# Escalamiento — Detección de Patrones y Alertas

## Purpose

Los patrones se repiten. El problema es que los humanos los vemos demasiado tarde. Escala los detecta temprano y te alerta cuando algo se está cocinando que ya pasó antes.

## Steps

### Step 1: Cargar memoria

Leer el timeline longitudinal (escala-memory) y todas las sesiones pasadas.

### Step 2: Detectar patrones por categoría

**Patrones de Cash:**
- CCC subiendo 2+ trimestres → "Los días que tarda en regresar tu dinero (CCC) subieron Q2→Q3→Q4. Si no actúas, en 2 trimestres llegas a 90 días."
- Crisis de efectivo en meses específicos → "Diciembre y enero siempre son meses críticos. Estamos en octubre — ¿empezamos a preparar?"
- Margen bajando → "Tu margen bruto bajó 3 trimestres seguidos. 32% → 30% → 28% → 26%."

**Patrones de People:**
- Rotación en misma posición → "Van 3 VPs de Ventas en 2 años. El problema no es la persona — es el rol, la compensación, o el onboarding."
- FACe con el mismo hueco 2+ trimestres → "VP Ventas lleva 4 trimestres vacío. ¿Cuándo lo vas a llenar?"
- A-players saliendo → "María (Controller, A-player) y Carlos (VP Ventas, A-player) se fueron en menos de 12 meses. ¿Patrón?"

**Patrones de Strategy:**
- Core Customer no definido por 3+ trimestres → "Llevas un año sin decidir quién es tu Core Customer. Cada trimestre que pasa, tu estrategia es más difusa."
- BHAG cambiado 2+ veces → "Cambiaste tu gran meta de largo plazo (BHAG) 3 veces en 18 meses. ¿Es ajuste o indecisión?"

**Patrones de Execution:**
- Prioridad #1 cambiada a mitad de trimestre → "En 3 de los últimos 4 trimestres cambiaste la Prioridad #1 a los 45 días. El problema no es la prioridad — es mantener el foco."
- Daily huddle perdiendo consistencia → "Tu daily pasó de 90% a 60% en 2 meses. ¿Se está desmoronando el ritmo?"
- Obstáculos recurrentes sin resolver → "El obstáculo 'máquina 3' apareció en 8 dailies este trimestre. ¿Quién es accountable de resolverlo?"

### Step 3: Generar alertas

Para cada patrón detectado, generar alerta con:

```
🚨 ALERTA: [Patrón detectado]

Evidencia:
- [Dato 1 con fuente y fecha]
- [Dato 2 con fuente y fecha]
- [Dato 3 con fuente y fecha]

Qué pasó la última vez:
- [Consecuencia histórica]

Recomendación:
- [Acción concreta]

Si no actúas:
- [Proyección a 3-6 meses]
```

Ejemplo:

```
🚨 ALERTA: Tu CCC está repitiendo el patrón de 2025

Evidencia:
- Q1 2026: CCC 52 días (work/cash/ccc.md — ene 2026)
- Q2 2026: CCC 58 días (work/cash/ccc.md — abr 2026)
- Q3 2026: CCC 67 días (work/cash/ccc.md — jul 2026)

Qué pasó la última vez:
- En Q4 2025, CCC llegó a 82 días. Tuviste que pedir préstamo de emergencia.

Recomendación:
- Prioridad #1 este trimestre: bajar CCC a 50 días.
- Empieza por DSO: tus clientes pagan a 67 días. Meta: 45 días.
- Skill sugerido: escala-cash-finanzas para actualizar Power of One.

Si no actúas:
- En Q4 2026, CCC proyectado: 76 días. Efectivo insuficiente para nómina de diciembre.
```

### Step 4: Priorizar y entregar

Ordenar alertas por severidad:
- 🔴 Crítica: amenaza la supervivencia (cash insuficiente, rotación de posición clave)
- 🟠 Alta: frena el crecimiento (hueco en FACe crítico, Prioridad #1 cambiante)
- 🟡 Media: reduce eficiencia (margen bajando, daily inconsistente)

"Tienes 5 alertas activas. 1 crítica, 2 altas, 2 medias. ¿Empezamos por la crítica?"

### Step 5: Activar monitoreo continuo

"Cada vez que cierres una sesión o subas un daily, reviso si hay patrones nuevos. Si detecto algo, te aviso. ¿Activo el monitoreo?"

Guardar configuración en `work/memory/alerts-config.md`.

## Output

- Alertas clasificadas por severidad con evidencia
- Recomendaciones accionables con skills sugeridos
- Proyección de consecuencias si no se actúa
- Monitoreo continuo configurado

## Notas

- Mínimo 3 ocurrencias para confirmar un patrón. Con 2 es "posible patrón — monitoreando."
- Las alertas citan fuentes reales (archivos, fechas, sesiones).
- Si no hay datos suficientes: "Todavía no tengo suficiente historia para detectar patrones confiables. Sigue registrando tus sesiones."
- El tono no es alarmista — es preventivo. "Mejor verlo ahora que en diciembre."
