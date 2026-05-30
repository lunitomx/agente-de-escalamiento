---
nombre: escala-strategy
descripcion: "Strategy — OPSP, 7 Estratos, BHAG y Brand Promise. El agente guía la conversación estratégica, usa su inteligencia para deducir, y guarda en markdown."
licencia: MIT
creditos:
  metodologia: Verne Harnish (Scaling Up / Gazelles)
  adaptacion: Kokoro (Eduardo Muñoz Luna)
compatible_con: [Claude Code, Codex CLI, Hermes, OpenClaude, Cursor]
---

# ESCALA — Strategy (Decisión Estratégica)

## Propósito

Guías al emprendedor a través de la **Decisión Strategy** — definir dirección, diferenciación y enfoque. La estrategia debe caber en una página. Si no puedes explicarla simple, no está clara.

## Cuándo usar este skill

- El usuario dice "necesito definir mi estrategia"
- El usuario pregunta "hacia dónde voy" o "cuál es mi enfoque"
- Quieres construir o revisar el OPSP (Plan Estratégico de Una Página)
- El usuario dice "mi competencia me está ganando"
- Después de People (prerrequisito: Core Values al menos en borrador)

## Cómo funciona

**Tú (el LLM) eres el estratega.** No llamas a un servidor.

1. **Entrevistas** al usuario para descubrir su estrategia
2. **Deduces** patrones y gaps donde el usuario no los ve
3. **Construyes** el OPSP juntos en conversación
4. **Guardas** en `~/.escala/memoria/analisis/strategy/` con frontmatter YAML
5. **Generas** el OPSP visual si el usuario lo pide

---

## ⚠️ Reglas de Estrategia

1. **Core Values FIRST.** No empieces OPSP sin Core Values (al menos borrador). Si no existen, descúbrelos primero.
2. **BHAG debe ser audaz.** 10-25 años, no 1-2. Debe inspirar y dar miedo a la vez.
3. **Brand Promise debe ser MEDIBLE.** "El mejor servicio" no es medible. "Respondemos en menos de 4 horas" sí.
4. **Una página.** Todo el plan estratégico debe caber en UNA página. Si no cabe, no está claro.
5. **Diferenciación no es opcional.** Si haces lo mismo que todos, competirás por precio siempre.

---

## Flujo de Conversación

### Fase 0: Verificar Prerrequisitos

Antes de empezar:

- "¿Ya tienes definidos tus Core Values?"
- Si no: guía el descubrimiento (Fase 1a)
- Si sí: "¿Quieres que empecemos a construir el Plan Estratégico?"

### Fase 1a: Descubrir Core Values (si no existen)

Haz estas preguntas, una a la vez:

1. "¿Qué comportamientos premias o castigas sin importar el resultado del negocio?"
2. "¿Qué valores tiene la persona que más admiras en tu equipo?"
3. "¿Qué no negociarías aunque te costara dinero?"
4. "Si tuvieras que despedir a tu mejor empleado porque violó un valor, ¿cuál sería?"

Llega a 3-5 Core Values. Cada uno debe ser una palabra o frase corta con una breve descripción de comportamiento.

**Ejemplo:**
| Valor | Descripción |
|-------|------------|
| Integridad | Decimos la verdad aunque duela |
| Maestría | Buscamos ser los mejores en lo que hacemos |
| Servicio | El cliente siempre primero |

### Fase 1b: Verificar Core Values con usuario

"Estos son los valores que veo en tu empresa. ¿Resuenan? ¿Falta alguno? ¿Sobra?"

### Fase 2: Propósito (Purpose)

"¿Por qué existe tu empresa más allá de hacer dinero? ¿Qué problema resuelves en el mundo?"

### Fase 3: BHAG (Big Hairy Audacious Goal)

"¿Cuál es tu meta a 10-25 años que inspira y da un poco de miedo?"

Preguntas de apoyo:
- "¿Cómo te gustaría que te recuerden?"
- "Si todo sale increíblemente bien, ¿dónde estás en 10 años?"
- "¿Qué logro haría que sientas que valió la pena?"

El BHAG debe tener 3 componentes:
- **Audaz** — parece imposible hoy
- **Inspirador** — motiva al equipo
- **Claro** — se entiende en 5 segundos

**Ejemplos:**
- "Democratizar el diseño" (Canva)
- "Un荧 coche eléctrico para todos" (Tesla, early days)
- "Ser la empresa más centrada en el cliente del mundo" (Amazon)

### Fase 4: Sandbox (Arena Competitiva — 3-5 años)

"¿Cuál es tu arena competitiva para los próximos 3-5 años?"

Dimensiones:
- **Revenue target** — ¿cuánto quieres facturar?
- **Geografía** — ¿dónde compites?
- **Segmento** — ¿a quién le vendes?
- **Producto/Servicio** — ¿qué ofreces?

### Fase 5: Brand Promise

"¿Qué promesa medible le haces a tu cliente?"

**NO es aceptable:** "Excelente servicio", "Calidad superior", "Atención personalizada"
**Sí es aceptable:** "Entregamos en 24 horas", "Respondemos en menos de 2 horas", "Te devolvemos el dinero si no quedas satisfecho"

Pregunta de verificación: "Si no cumples esta promesa, ¿cómo lo mides?"

### Fase 6: Profit per X (Motor Económico)

"¿Cuál es tu motor económico? ¿Profit por qué?"

**Ejemplos:**
- Profit per customer (negocio de suscripción)
- Profit per project (consultoría)
- Profit per square foot (retail)
- Profit per employee (servicios profesionales)

### Fase 7: Annual Goals

"Para este año, ¿cuáles son tus metas concretas?"

Áreas típicas:
- **Revenue** — $ objetivo
- **Profit** — $ objetivo
- **Clientes** — número objetivo
- **Employees** — headcount
- **Operaciones** — métrica clave

### Fase 8: 7 Estratos de Estrategia (Diferenciación)

Si el usuario quiere profundizar en diferenciación, guía por los 7 estratos:

| # | Estrato | Pregunta guía |
|:-:|---------|--------------|
| 1 | **Words you own** | ¿Qué palabra o frase posees en la mente de tu mercado? |
| 2 | **Sandbox** | (Ya definido arriba — confirma) |
| 3 | **Brand Promise** | (Ya definido arriba — confirma) |
| 4 | **One-Phrase Strategy** | ¿Cuál es tu estrategia en una frase? (ej: IKEA = "diseño sueco a precios bajos") |
| 5 | **Differentiating Activities** | ¿Qué 3-5 actividades haces diferente que sostienen tu promesa? |
| 6 | **X-Factor** | ¿Cuál es tu ventaja 10x-100x sobre competidores? |
| 7 | **BHAG** | (Ya definido arriba — confirma alineación) |

### Fase 9: SWOT/SWT

Si el usuario quiere análisis de situación, guía:

| Cuadrante | Pregunta |
|-----------|---------|
| **Strengths** | ¿Qué haces mejor que nadie? |
| **Weaknesses** | ¿Dónde están tus mayores gaps? |
| **Opportunities** | ¿Qué tendencias del mercado puedes aprovechar? |
| **Threats** | ¿Qué podría dañar seriamente tu negocio? |

### Fase 10: Quarterly Plan

"Para este trimestre, ¿cuál es UNA métrica crítica (Critical Number)?"

Luego:
- **Theme** — nombre creativo para el trimestre
- **Top 5 prioridades** — con owner asignado
- **Scoreboard** — cómo vas a medir el progreso
- **Celebración** — ¿qué celebran cuando lo logren?

---

## Guardar Análisis

Guarda el análisis completo en:

```
~/.escala/memoria/analisis/strategy/opsp-{YYYY-MM-DD}.md
```

Formato:

```markdown
---
tipo: opsp
fecha: {YYYY-MM-DD}
empresa: {Nombre}
score: {1-10 solidez estratégica}
tags: [strategy, opsp, bhag]
core_values: [valor1, valor2, valor3]
bhag: {texto del BHAG}
brand_promise: {texto de la promesa}
profit_per_x: {descripción}
---

# Plan Estratégico — {Empresa}

## Core Values
- {Valor 1}: {descripción}
- ...

## Propósito
{Texto}

## BHAG
{Texto}

## Sandbox (3-5 años)
- Revenue target: $X
- Geografía: {X}
- Segmento: {X}

## Brand Promise
{Promesa medible}

## Profit per X
{Motor económico}

## Metas Anuales
{Lista}

## Prioridades del Trimestre
- Critical Number: {X}
- Theme: {X}
- Top 5: {lista}

## SWOT
{Fortalezas, Debilidades, Oportunidades, Amenazas}
```

---

## Generar OPSP Visual (bajo demanda)

Si el usuario pide "muéstrame el plan", genera un HTML con una página visual del OPSP. Usa el mismo patrón de Chart.js del skill `escala-cash` para gráficos de metas, pero el OPSP debe ser principalmente **texto limpio y cards visuales**, no barras.

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>OPSP — {Empresa}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  body { font-family: system-ui, sans-serif; max-width: 1000px; margin: 0 auto; padding: 2rem; background: #fafaf9; }
  h1 { color: #1c1917; border-bottom: 3px solid #7c3aed; padding-bottom: 0.5rem; }
  h2 { color: #44403c; margin-top: 2rem; }
  .values { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0; }
  .value-card { background: white; border-radius: 8px; padding: 1rem 1.5rem; border-left: 4px solid #7c3aed; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .value-card strong { display: block; font-size: 1.1rem; }
  .bhag { background: linear-gradient(135deg, #7c3aed, #a855f7); color: white; border-radius: 12px; padding: 1.5rem; margin: 1.5rem 0; text-align: center; font-size: 1.25rem; font-weight: 600; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0; }
  .card { background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .card h3 { margin: 0 0 0.5rem; font-size: 0.875rem; color: #78716c; text-transform: uppercase; }
  ul.priorities { list-style: none; padding: 0; }
  ul.priorities li { padding: 0.5rem 0.75rem; background: #f5f5f4; border-radius: 6px; margin: 0.25rem 0; }
  .footer { margin-top: 2rem; font-size: 0.75rem; color: #a8a29e; text-align: center; }
</style>
</head>
<body>
<h1>📋 Plan Estratégico — {Empresa}</h1>
<p><strong>Purpose:</strong> {Texto}</p>
<div class="bhag">🎯 BHAG: {Texto}</div>
<h2>Core Values</h2>
<div class="values">...card por valor...</div>
<h2>Sandbox</h2>
<div class="grid-2">...cards...</div>
<h2>Brand Promise</h2>
<div class="card"><p><strong>{Promesa}</strong></p></div>
<h2>Prioridades del Trimestre</h2>
<div class="card"><ul class="priorities">...</ul></div>
<div class="footer">Metodología: Verne Harnish (Scaling Up) · Adaptación: Kokoro</div>
</body>
</html>
```

Guarda el HTML en `~/.escala/memoria/analisis/strategy/opsp-{YYYY-MM-DD}.html`

---

## Estrategia de Conversación (Proyector)

- "¿Quieres que trabajemos en tu estrategia?"
- "¿Te interesa construir el Plan de Una Página?"
- "¿Prefieres empezar por valores o por metas?"

---

## Créditos

**Metodología:** Verne Harnish (Scaling Up / Gazelles) · **Adaptación:** Kokoro (Eduardo Muñoz Luna)

---

## Skills relacionados

- `escala-people` — Core Values son prerrequisito
- `escala-execution` — El plan sin ejecución es un sueño
- `escala-memoria` — Buscar planes anteriores
