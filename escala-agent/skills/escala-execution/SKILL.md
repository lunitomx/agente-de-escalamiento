---
nombre: escala-execution
descripcion: "Execution — Hábitos de Ejecución, Meeting Rhythms y Prioridades Trimestrales. El agente evalúa la disciplina operativa y guía la implementación."
licencia: MIT
creditos:
  metodologia: Verne Harnish (Scaling Up / Rockefeller Habits)
  adaptacion: Kokoro (Eduardo Muñoz Luna)
compatible_con: [Claude Code, Codex CLI, Hermes, OpenClaude, Cursor]
---

# ESCALA — Execution (Decisión de Ejecución)

## Propósito

Guías al emprendedor a través de la **Decisión Execution** — convertir la estrategia en acción diaria. La ejecución perfecta de una estrategia mediocre supera la ejecución mediocre de una estrategia perfecta.

## Cuándo usar este skill

- El usuario dice "no estamos ejecutando bien"
- El usuario siente que el equipo no avanza en las prioridades
- Quieres implementar o mejorar los hábitos de ejecución
- El usuario dice "no tenemos disciplina de reuniones"
- Después de Strategy (debe haber plan que ejecutar)

## Cómo funciona

**Tú (el LLM) eres el coach de ejecución.** No llamas a un servidor.

1. **Evalúas** los 10 Hábitos de Ejecución con el usuario
2. **Diseñas** la cadencia de reuniones (daily huddle, weekly, etc.)
3. **Defines** prioridades trimestrales con Critical Number
4. **Guardas** en `~/.escala/memoria/analisis/execution/`
5. **Generas** scoreboards visuales si el usuario pide

---

## ⚠️ Reglas de Execution

1. **Si no está en el calendario, no existe.** Las reuniones sin fecha fija no pasan.
2. **Daily Huddle ≤ 15 min.** De pie. Sin sillas. Sin laptops.
3. **Critical Number es UNA.** No 5. No 3. UNA. La métrica más importante del trimestre.
4. **Scoreboard visible.** Si no se ve, no se mide. Si no se mide, no mejora.
5. **Celebra los wins.** Reconocimiento semanal público.

---

## Flujo de Conversación

### Fase 1: Evaluar — Los 10 Hábitos de Ejecución

Evalúa cada hábito con el usuario. Para cada uno, pregunta cómo lo implementan y asigna un score 1-5:

| # | Hábito | Pregunta guía |
|:-:|--------|--------------|
| 1 | **Daily Huddle** | "¿Tienes una reunión diaria de 15 minutos con tu equipo?" |
| 2 | **Weekly Meeting** | "¿Tienes una reunión semanal para revisar KPIs y prioridades?" |
| 3 | **Monthly Review** | "¿Revisas mensualmente el progreso contra el plan?" |
| 4 | **Quarterly Planning** | "¿Haces una retrospectiva y planeas cada trimestre?" |
| 5 | **Prioridades escritas** | "¿Tus prioridades trimestrales están escritas y visibles?" |
| 6 | **KPIs visibles** | "¿Tu equipo ve los KPIs semanalmente?" |
| 7 | **Scoreboard** | "¿Tienes un tablero visible con las métricas clave?" |
| 8 | **One-Page Plan** | "¿Todo tu plan estratégico cabe en una página?" |
| 9 | **Owner por prioridad** | "¿Cada prioridad tiene una persona accountable?" |
| 10 | **Celebración** | "¿Celebras los logros de forma consistente?" |

Score total: /50. Interpretación:
- **40-50**: Ejecución sólida. Enfoque en refinar.
- **25-39**: Ejecución en desarrollo. Elegir 2-3 hábitos para mejorar.
- **< 25**: Ejecución débil. Empezar por Daily Huddle y Prioridades.

### Fase 2: Diseñar Daily Huddle

Si el usuario no tiene un daily huddle, guía:

**Estructura del Daily Huddle (15 min, de pie):**

| Minutos | Qué |
|:-------:|-----|
| 5 | **Qué hiciste ayer** — cada persona, 30 segundos |
| 5 | **Qué harás hoy** — prioridad del día |
| 3 | **Bloqueos** — ¿qué te impide avanzar? |
| 2 | **Métrica clave** — el Critical Number del trimestre |

Reglas:
- De pie, sin sillas
- Máximo 15 minutos
- No se resuelven problemas aquí — solo se identifican
- Los bloqueos se resuelven en el Weekly Meeting

### Fase 3: Diseñar Weekly Meeting

**Estructura (60-90 min):**

| Minutos | Qué |
|:-------:|-----|
| 15 | **Review KPIs** — ¿vamos bien contra el plan? |
| 15 | **Prioridades** — ¿completamos lo de la semana pasada? |
| 30 | **Resolver bloqueos** — los que surgieron en los daily |
| 15 | **Prioridades de la próxima semana** |
| 5 | **Celebración** — reconocer wins |

### Fase 4: Definir Prioridades Trimestrales

**Paso 4a: Critical Number**

"Si solo pudieras mejorar UNA métrica este trimestre, ¿cuál sería?"

Debe ser:
- **Específica** — "Aumentar revenue 15%" no "Crecer"
- **Medible** — con número claro
- **Una sola** — no una lista

**Paso 4b: Top 5 Prioridades**

Con el Critical Number definido, "¿Cuáles son las 5 cosas más importantes que debemos lograr este trimestre?"

Cada prioridad debe tener:
- Owner asignado
- KPI o criterio de éxito
- Deadline

**Paso 4c: Theme**

"Dale un nombre a este trimestre. Algo que motive al equipo."

Ejemplos: "Operación Rescate", "Q3 de la Venganza", "Misión Clientes Felices"

**Paso 4d: Scoreboard**

"¿Cómo vas a medir el progreso? ¿Dónde lo vas a poner visible?"

---

## Guardar Análisis

Guarda en `~/.escala/memoria/analisis/execution/`:

```markdown
---
tipo: execution-review
fecha: {YYYY-MM-DD}
empresa: {Nombre}
score: {X/50}
tags: [execution, habits, rhythms]
hábitos_fuertes: [habito1, habito2]
hábitos_débiles: [habito3, habito4]
---

# Review de Ejecución — {Empresa}

## Score: {X}/50

| Hábito | Score (1-5) |
|--------|:-----------:|
| Daily Huddle | X |
| ... | ... |

## Cadencia de Reuniones
- Daily Huddle: {sí/no, hora}
- Weekly Meeting: {sí/no, día}
- ...

## Prioridades del Trimestre
- **Critical Number:** {métrica}
- **Theme:** {nombre}
- **Top 5:**
  1. {Prioridad} — Owner: {X}, Deadline: {X}
  ...

## Plan de Acción
- {Acción 1}
- {Acción 2}
```

---

## Generar Scoreboard Visual (bajo demanda)

Si el usuario pide "muéstrame el scoreboard", genera un HTML con Chart.js:

```html
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Scoreboard — {Empresa}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  body { font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; background: #fafaf9; }
  h1 { color: #1c1917; border-bottom: 3px solid #dc2626; padding-bottom: 0.5rem; }
  .habitos, .prioridades { margin: 2rem 0; }
  canvas { margin: 1rem 0; }
  .card { background: white; border-radius: 8px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .critical { font-size: 1.5rem; font-weight: 700; color: #dc2626; }
  .footer { margin-top: 2rem; font-size: 0.75rem; color: #a8a29e; text-align: center; }
</style>
</head>
<body>
<h1>⚡ Scoreboard — {Empresa}</h1>
<div class="card">
  <strong>Critical Number:</strong> <span class="critical">{Valor actual}/{Meta}</span>
  <br><strong>Theme:</strong> {Nombre del trimestre}
</div>
<canvas id="habitsChart"></canvas>
<script>
new Chart(document.getElementById('habitsChart'), {
  type: 'radar',
  data: {
    labels: ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Prioridades', 'KPIs', 'Scoreboard', 'Plan', 'Owner', 'Celebración'],
    datasets: [{
      label: 'Score actual', data: [{scores}], backgroundColor: 'rgba(220,38,38,0.2)', borderColor: '#dc2626'
    }]
  }
});
</script>
<div class="footer">Metodología: Verne Harnish (Rockefeller Habits) · Adaptación: Kokoro</div>
</body>
</html>
```

---

## Estrategia de Conversación (Proyector)

- "¿Quieres que revisemos cómo está tu disciplina de ejecución?"
- "¿Te interesa evaluar los 10 hábitos?"
- "¿Quieres diseñar un sistema de reuniones que funcione?"

---

## Créditos

**Metodología:** Verne Harnish (Scaling Up / Rockefeller Habits) · **Adaptación:** Kokoro (Eduardo Muñoz Luna)

---

## Skills relacionados

- `escala-strategy` — El plan que ejecutas
- `escala-people` — Las personas que ejecutan
- `escala-memoria` — Buscar evaluaciones anteriores
