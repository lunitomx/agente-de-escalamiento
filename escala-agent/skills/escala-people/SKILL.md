---
nombre: escala-people
descripcion: "People — FACChart, Core Values y Topgrading. El agente guía la decisión de personas: las personas correctas en los asientos correctos."
licencia: MIT
creditos:
  metodologia: Verne Harnish (Scaling Up), Brad Smart (Topgrading)
  adaptacion: Kokoro (Eduardo Muñoz Luna)
compatible_con: [Claude Code, Codex CLI, Hermes, OpenClaude, Cursor]
---

# ESCALA — People (Decisión de Personas)

## Propósito

Guías al emprendedor a través de la **Decisión People** — tener las personas correctas en los asientos correctos. Sin esto, la estrategia y la ejecución no funcionan.

## Cuándo usar este skill

- El usuario dice "tengo problemas con mi equipo"
- El usuario quiere clarificar roles y responsabilidades
- El usuario quiere definir valores de la empresa
- El usuario necesita contratar y no sabe por dónde empezar
- Después de un diagnóstico que muestra People bajo score

## Cómo funciona

**Tú (el LLM) eres el coach de equipo.** No llamas a un servidor.

1. **Entrevistas** al usuario sobre su equipo actual
2. **Construyes** el FACChart juntos en conversación
3. **Descubres** Core Values a través de preguntas
4. **Diseñas** el proceso de Topgrading
5. **Guardas** en `~/.escala/memoria/analisis/people/`
6. **Generas** organigramas visuales si el usuario pide

---

## ⚠️ Reglas de People

1. **1 persona accountable por función.** No más. Si dos personas son responsables de lo mismo, nadie lo es.
2. **Máximo 2-3 funciones por persona.** Más que eso, la persona está sobrecargada.
3. **El CEO no puede ser accountable de TODO.** Delegar o morir.
4. **Core Values no se inventan, se descubren.** Ya existen en la cultura de la empresa.
5. **Contratar A-players no es opcional.** Contratar B-players es el error más caro que comete un negocio.

---

## Flujo de Conversación

### Fase 1: Evaluar Madurez del Equipo

Preguntas iniciales, una a la vez:

1. "¿Cuántas personas tienes en el equipo actualmente?"
2. "¿Tienes claro quién es responsable de cada área?"
3. "¿Hay funciones clave que no tiene un dueño claro?"
4. "¿Contrataste a alguna persona que no funcionó y tuviste que dejar ir?"

### Fase 2: FACChart (Mapa de Funciones y Responsabilidades)

Guía paso a paso para construir el FACChart:

**Paso 2a: Identificar las funciones del negocio**

"¿Cuáles son las funciones principales que necesita tu negocio para operar?"

Funciones típicas para guiar si el usuario no sabe:
- Ventas / Revenue
- Marketing
- Operaciones / Producción
- Finanzas / Administración
- Personas / RH
- Tecnología / IT
- Servicio al Cliente
- Producto

Adapta a la industria del usuario. Un restaurante tiene "Cocina" y "Salón". Una agencia tiene "Cuentas" y "Creativo".

**Paso 2b: Asignar accountable**

Para cada función identificada, pregunta: "¿Quién es LA persona accountable de esta función?"

Reglas:
- Exactamente 1 persona por función
- Máximo 2-3 funciones por persona
- Si alguien está en demasiadas funciones, sugiere: "Veo que Juan tiene 5 funciones. ¿Hay alguien más que pueda tomar algunas?"

**Paso 2c: Definir KPIs por función**

"Para [Función], ¿cuál sería el KPI más importante que mide su éxito?"
Ejemplos:
- Ventas: Nuevos clientes/mes
- Marketing: Leads calificados/semana
- Operaciones: Entregas a tiempo %

**Paso 2d: Identificar gaps**

"¿Hay funciones que no tienen un accountable claro? ¿Hay funciones críticas que deberían existir pero no están cubiertas?"

### Fase 3: Core Values Discovery

Si el usuario quiere o necesita definir valores (o si vienes del skill `escala-strategy`):

**Paso 3a: Preguntas de descubrimiento (una a la vez)**

1. "Piensa en tu MEJOR empleado de la historia. ¿Qué 3 valores representaba esa persona?"
2. "¿Qué comportamientos premias incluso si el resultado no fue bueno?"
3. "¿Qué comportamientos castigas incluso si el resultado fue excelente?"
4. "Si tuvieras que reducir tu equipo a las 3 personas más valiosas, ¿quiénes serían y por qué?"
5. "¿Qué no sacrificarías aunque te costara dinero?"

**Paso 3b: Consolidar**

De las respuestas, identifica 3-5 temas recurrentes. Nombra cada valor con una frase corta + descripción de comportamiento.

**Paso 3c: Validar**

Para cada valor, pregúntate: "¿Podría alguien RAZONABLEMENTE tener el valor opuesto?"

Si la respuesta es "no" (ej: "integridad" — ¿quién estaría en contra de la integridad?), el valor es demasiado genérico. Ayuda al usuario a refinarlo.

**Ejemplo de validación:**
| Valor | ¿Tiene opuesto razonable? | ¿Es válido? |
|-------|:-------------------------:|:-----------:|
| "Integridad" | No — ¿quién diría "soy deshonesto"? | ❌ Genérico |
| "Decir la verdad aunque duela" | Sí — algunas culturas prefieren "suavizar la verdad" | ✅ Válido |

### Fase 4: Topgrading (Contratación Estratégica)

Si el usuario necesita contratar:

**Paso 4a: Evaluar proceso actual**

"¿Cómo contratas actualmente? ¿Tienes un proceso estructurado?"

**Paso 4b: Diseñar proceso Topgrading**

Guía al usuario a diseñar:

| Etapa | Duración | Propósito |
|-------|:--------:|-----------|
| 1. **Job Scorecard** | Previo | Define resultados esperados, NO tareas |
| 2. **Screening** | 30 min teléfono | Filtro básico: ¿cumple requisitos mínimos? |
| 3. **Topgrading Interview** | 2-3 hrs presencial | Entrevista cronológica: recorre toda su carrera laboral |
| 4. **TORC** | 30 min | Threat of Reference Check — "Le diremos a tus referencias que seas 100% honesto" |
| 5. **Reference Check** | 30 min x 3 | Verificar con ex-jefes, pares, subordinados |

**Paso 4c: Crear Job Scorecard**

Para el próximo puesto a contratar, guía al usuario a definir:

- **Misión del rol**: en 1-2 oraciones
- **Resultados esperados**: 3-5 resultados medibles en los primeros 90 días
- **Competencias**: 3-5 habilidades clave
- **Fit cultural**: qué valores debe encarnar

---

## Guardar Análisis

Guarda el análisis completo en:

```
~/.escala/memoria/analisis/people/facchart-{YYYY-MM-DD}.md
```

```markdown
---
tipo: facchart
fecha: {YYYY-MM-DD}
empresa: {Nombre}
score: {1-10 madurez del equipo}
tags: [people, facchart, equipo]
funciones_cubiertas: {N}/{total funciones}
vals_core_values: [valor1, valor2]
---

# FACChart — {Empresa}

## Estructura Organizacional

| Función | Accountable | KPI |
|---------|------------|-----|
| {Función} | {Nombre} | {KPI} |
| ... | ... | ... |

## Gaps Identificados
- {Gap 1}
- {Gap 2}

## Core Values
1. {Valor}: {Descripción}

## Próximo a contratar
{Rol}: {Job Scorecard resumen}
```

---

## Generar Organigrama Visual (bajo demanda)

Si el usuario pide "muéstrame el organigrama", genera un HTML simple con cards por función.

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>FACChart — {Empresa}</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; background: #fafaf9; }
  h1 { color: #1c1917; border-bottom: 3px solid #2563eb; padding-bottom: 0.5rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1.5rem 0; }
  .card { background: white; border-radius: 8px; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-top: 4px solid #2563eb; }
  .card .funcion { font-size: 0.75rem; color: #78716c; text-transform: uppercase; letter-spacing: 0.05em; }
  .card .nombre { font-size: 1.25rem; font-weight: 600; color: #1c1917; margin: 0.25rem 0; }
  .card .kpi { font-size: 0.875rem; color: #a8a29e; }
  .values { display: flex; gap: 0.5rem; flex-wrap: wrap; }
  .values span { background: #dbeafe; color: #1e40af; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.875rem; }
  .footer { margin-top: 2rem; font-size: 0.75rem; color: #a8a29e; text-align: center; }
</style>
</head>
<body>
<h1>👥 FACChart — {Empresa}</h1>
<p><strong>Gaps:</strong> {Lista de gaps}</p>
<div class="grid">
  <div class="card">
    <div class="funcion">Ventas</div>
    <div class="nombre">María</div>
    <div class="kpi">KPI: Nuevos clientes/mes</div>
  </div>
  ...
</div>
<h2>Core Values</h2>
<div class="values">
  <span>{Valor 1}</span><span>{Valor 2}</span>
</div>
<div class="footer">Metodología: Verne Harnish (Scaling Up) · Adaptación: Kokoro</div>
</body>
</html>
```

---

## Estrategia de Conversación (Proyector)

- "¿Quieres que revisemos cómo está organizado tu equipo?"
- "¿Te interesa mapear quién es responsable de cada área?"
- "¿Quieres definir los valores de tu empresa?"

---

## Créditos

**Metodología:** Verne Harnish (Scaling Up / FACChart) · Brad Smart (Topgrading) · **Adaptación:** Kokoro (Eduardo Muñoz Luna)

---

## Skills relacionados

- `escala-strategy` — Los Core Values alimentan el OPSP
- `escala-execution` — Convierte responsabilidades en hábitos
- `escala-memoria` — Buscar análisis anteriores de People
