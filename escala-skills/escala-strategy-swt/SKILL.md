---
description: 'SWT automático: Strengths, Weaknesses, Trends generados desde datos reales de tus sesiones, no desde opiniones. Cada afirmación cita evidencia.'
name: escala-strategy-swt
---

# Escalamiento Strategy — SWT Automático

## Purpose

El SWT (Strengths, Weaknesses, Trends) es el corazón de la estrategia trimestral. Pero la mayoría de los empresarios lo llenan desde sus creencias, no desde sus datos. Este skill genera un SWT basado en evidencia real: lo que PASÓ en tus sesiones, worksheets, y KPIs. No lo que crees que pasó.

## Steps

### Step 1: Recolectar evidencia

De las sesiones pasadas extraer:
- Decisiones tomadas (work/cash/, work/strategy/, etc.)
- Patrones detectados por E34 (memoria longitudinal)
- KPIs y su tendencia (mejorando/empeorando)
- Obstáculos recurrentes mencionados en daily huddles
- Logros celebrados

### Step 2: Clasificar en SWT

**Strengths (Fortalezas) — Lo que está funcionando:**
- KPIs que mejoraron 2+ trimestres seguidos
- Decisiones ejecutadas con éxito
- Áreas donde los daily huddles muestran consistencia
- "Tu equipo de operaciones resolvió 85% de obstáculos en <48h este trimestre."

**Weaknesses (Debilidades) — Lo que está frenando:**
- KPIs que empeoraron
- Obstáculos recurrentes (3+ menciones sin resolver)
- Funciones del FACe vacías
- "Los días que tarda en regresar tu dinero (CCC) subieron 17. La causa: cuentas por cobrar pasaron de 45 a 67 días."

**Trends (Tendencias) — Lo que viene:**
- Patrones estacionales (siempre hay problemas de cash en Q3)
- Cambios en el mercado mencionados en sesiones
- Competidores mencionados
- "Tus clientes están pidiendo más digitalización. En las últimas 5 sesiones apareció 8 veces."

### Step 3: Validar con el CEO

"Esto es lo que los DATOS dicen. ¿Hay algo que los datos no capturen?"

El CEO puede ajustar — pero el punto de partida ya no es una hoja en blanco.

### Step 4: Qué dicen fuera de tu empresa (Evidencia externa)

Pregunta: "¿Quieres que revise qué dicen fuera de tu empresa antes de cerrar tu análisis de fortalezas, debilidades y tendencias (SWT)?"

Si dice que sí, trae lo guardado:

```bash
echo '{"action": "swt", "base_path": "."}' | python3 -m coaching.research
```

- Con `swt_evidence`: di el `message`. Cada hallazgo ya viene marcado
  ("Según fuentes externas, [mes]") y calificado (confirmado /
  por confirmar). Si dice que sí, agrégalos en una sección **Evidencia externa**
  del mismo archivo, aparte de la evidencia interna, sin URLs y citando el
  reporte local (`saved_to`). Nunca los mezcles con lo que salió de sus datos.
- Sin nada guardado, o con una investigación vencida: di el `message` y, si
  quiere, sigue con `escala-strategy-research` en modo
  `fortalezas-tendencias`; al terminar vuelves a este paso.
- Si no quiere, cierra el SWT sólo con su evidencia interna.

Es el mismo SWT: no escribas otro SWT ni otro archivo.

### Step 5: Guardar

`work/strategy/swt-{año}-Q{trimestre}.md`

## Output

- SWT con 3-5 items por categoría
- Cada item cita fuente (sesión, KPI, worksheet)
- Evidencia externa (si la hubo) en su propia sección, marcada y calificada
- Resumen ejecutivo: "Tu fortaleza es operaciones. Tu debilidad es cash. La tendencia que no estás viendo es digitalización."

## Notas

- Si no hay suficientes sesiones para generar tendencias, lo dice: "Solo tengo 3 sesiones. Necesito al menos 8 para detectar patrones confiables."
- El SWT es input para el board proactivo (escala-board) — no reemplaza la conversación.
