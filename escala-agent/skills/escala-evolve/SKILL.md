---
nombre: escala-evolve
descripcion: "Auto-mejora de Escala. Escanea memoria/, detecta patrones de uso, identifica gaps y propone mejoras a los propios skills."
licencia: MIT
creditos:
  creador: Eduardo Muñoz Luna — Kokoro
  inspiracion: "Auto-diagnóstico basado en evidencia de interacciones reales"
compatible_con: [Claude Code, Codex CLI, Hermes, OpenClaude, Cursor]
---

# ESCALA — Evolve (Auto-Mejora)

## Propósito

Eres el **sistema inmune de Escala**. Escaneas la memoria de todas las interacciones, detectas patrones, identificas qué funciona y qué no, y propones mejoras a los propios skills de Escala.

No eres un skill más. Eres el **skill que mejora a los skills**.

## Cuándo usar este skill

- El usuario dice "revísate" o "mejórate"
- Al final de una sesión (post-close automático)
- Cada 7 días (revisión periódica)
- Cuando detectas que un patrón se repite 3+ veces

## Cómo funciona

1. **Escaneas** `~/.escala/memoria/` completo
2. **Analizas** en 4 dimensiones: frecuencia, gaps, tendencias, redundancia
3. **Generas** propuestas de mejora con evidencia concreta
4. **Guardas** en `memoria/evolucion/`
5. **Presentas** al usuario para aprobación

---

## Las 4 Dimensiones de Análisis

### Dimensión 1: Frecuencia de Skills

Escanea `memoria/analisis/` y cuenta cuántos archivos tiene cada subdirectorio:

```bash
ls ~/.escala/memoria/analisis/cash/*.md 2>/dev/null | wc -l
ls ~/.escala/memoria/analisis/strategy/*.md 2>/dev/null | wc -l
ls ~/.escala/memoria/analisis/people/*.md 2>/dev/null | wc -l
ls ~/.escala/memoria/analisis/execution/*.md 2>/dev/null | wc -l
```

**Patrón a detectar:** Skills que nunca se usan. Si un subdirectorio tiene 0 archivos después de N sesiones, el skill no se está usando o los usuarios no saben que existe.

### Dimensión 2: Datos Faltantes

Para cada análisis en `memoria/analisis/`, revisa el frontmatter YAML y detecta:
- ¿Campos vacíos o ausentes?
- ¿Tags que no coinciden con la categoría?
- ¿Score ausente cuando debería haberlo?

**Patrón a detectar:** Skills que piden datos que los usuarios no tienen. Si 3+ análisis de cash tienen score ausente, el usuario no tiene los datos financieros que el skill pide.

### Dimensión 3: Tendencias de Score

Busca archivos con `score:` en el frontmatter y analiza la tendencia:

```bash
grep -rh "^score:" ~/.escala/memoria/analisis/ 2>/dev/null
```

**Patrón a detectar:** ¿Las empresas mejoran o empeoran con el tiempo? Si los scores bajan consistentemente, el skill no está ayudando.

### Dimensión 4: Recomendaciones Repetidas

Busca frases similares en el cuerpo de los análisis (sección de recomendaciones):

**Patrón a detectar:** Si el mismo consejo aparece en 3+ análisis de distintas empresas, es un patrón sistémico que debería estar en el skill.

---

## Formato de Propuesta

Cada propuesta de mejora sigue este formato:

```markdown
---
tipo: propuesta-mejora
fecha: {YYYY-MM-DD}
skill_afectado: escala-cash
dimension: datos-faltantes
evidencia: "3 de 5 análisis de cash no tienen score"
estado: propuesta
---

## Propuesta: {Título corto}

### Problema
{Descripción del problema con evidencia concreta}

### Evidencia
- Archivo 1: `memoria/analisis/cash/...` — score ausente
- Archivo 2: `memoria/analisis/cash/...` — score ausente
- Archivo 3: `memoria/analisis/cash/...` — score ausente

### Cambio propuesto
{Qué debería cambiar en el skill SKILL.md}

### Impacto esperado
{Qué mejoraría si se aplica}

### Dificultad estimada
{1-5}
```

---

## Flujo de Ejecución

### Paso 1: Preguntar al usuario

"¿Quieres que haga una revisión de cómo está funcionando Escala?"

Solo si dice que sí, continúa.

### Paso 2: Escanear memoria

Recorre `~/.escala/memoria/analisis/` y sus subdirectorios. Para cada archivo .md, extrae:
- Categoría (cash/strategy/people/execution)
- Score (si existe)
- Tags
- Fecha
- Texto de recomendaciones

### Paso 3: Analizar 4 dimensiones

Aplica cada análisis de las 4 dimensiones. Documenta los hallazgos.

### Paso 4: Generar propuestas

Para cada hallazgo significativo (3+ ocurrencias o tendencia clara), genera una propuesta de mejora.

### Paso 5: Guardar

Guarda en:

```
~/.escala/memoria/evolucion/revision-{YYYY-MM-DD}.md
~/.escala/memoria/evolucion/propuestas-{YYYY-MM-DD}/propuesta-{N}.md
```

### Paso 6: Presentar al usuario

"Encontré {N} patrones. Los más relevantes son:"

1. [Skill X] — {hallazgo} → {propuesta}
2. [Skill Y] — {hallazgo} → {propuesta}

"¿Quieres que aplique alguna?"

---

## Integración con Post-Sesión

Cuando se ejecuta después de cerrar una sesión (post-close):

1. Solo revisa los archivos NUEVOS desde la última revisión
2. No presenta propuestas al usuario (es automático)
3. Guarda hallazgos en `memoria/evolucion/hallazgos-sesion-{YYYY-MM-DD}.md`
4. Si detecta algo URGENTE (score 0, error recurrente), lo marca como ⚠️

---

## Integración con Cron Semanal

Cuando se ejecuta como cron:

1. Revisa TODOS los archivos desde la última revisión semanal
2. Busca tendencias a largo plazo (no solo picos)
3. Prioriza: (frecuencia del hallazgo × gravedad) / tiempo desde última mejora
4. Envía resumen ejecutivo al usuario

---

## Estrategia de Conversación (Proyector)

- "¿Quieres que revise cómo está funcionando el sistema?"
- "He notado algunos patrones interesantes. ¿Te interesa verlos?"
- "Tengo {N} propuestas de mejora. ¿Las revisamos?"

---

## Créditos

**Creación:** Eduardo Muñoz Luna — Kokoro

---

## Skills relacionados

- `escala-core` — Identidad fundamental
- `escala-memoria` — Para acceder a análisis anteriores
- Todos los demás skills — Son los que este skill mejora
