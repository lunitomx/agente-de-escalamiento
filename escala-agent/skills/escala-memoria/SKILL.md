---
description: "Gestiona la memoria markdown de Escala. Cada interacción deja un .md con frontmatter + links. El agente guarda, busca y sintetiza."
license: MIT
name: escala-memoria
---

# Memoria Core — ESCALA

## Propósito

Cada interacción con el usuario debe dejar una **huella permanente** en
`~/.escala/memoria/`. Esto permite al agente recordar, conectar y sintetizar.

## Formato de cada archivo

Todos los archivos en `memoria/` usan este formato:

```markdown
---
tipo: daily-review               # daily-review | analisis | dashboard
fecha: 2026-05-30
empresa: Carnicería El Buen Corte
score: 10/12                     # Opcional: métrica principal
tags: [ejecucion, hábitos]
links:
  - daily: 2026-05-29            # Link a otro análisis por fecha
  - analisis: power-of-one-abril
---

## Resultado
{texto libre con el resultado del análisis}

## Observaciones de Verne
{si aplica, lo que dijo Verne}

## Siguientes pasos
{qué acordaron hacer después}
```

## Archivos permitidos en `memoria/`

| Carpeta | Contenido |
|---------|-----------|
| `memoria/dailys/` | `{fecha}-score-{score}.md` — análisis de daily huddles |
| `memoria/analisis/` | `{tipo}-{fecha}.md` — Power of One, FACe, OPSP, etc. |
| `memoria/dashboard/` | `{titulo}-{fecha}.md` — HTMLs generados |

## Cómo guardar

Después de CADA interacción que produzca un resultado concreto:

1. **Construye** el markdown con frontmatter
2. **Escribe** el archivo en la carpeta correspondiente
3. **Actualiza** `memoria/indice.md` (agrega fila a la tabla)
4. **Verifica** que el archivo existe con `ls`

### Template de guardado

```bash
cat > ~/.escala/memoria/dailys/2026-05-30-score-10.md << 'EOF'
---
tipo: daily-review
fecha: 2026-05-30
empresa: Carnicería El Buen Corte
score: 10/12
tags: [ejecucion, hábitos]
links:
  - analisis: power-of-one-abril
---
...
EOF
```

### Actualizar índice

```markdown
Agrega una fila a ~/.escala/memoria/indice.md:
| 2026-05-30 | Carnicería | 10/12 | dailys/2026-05-30-score-10.md |
```

## Cómo buscar

Cuando el usuario pregunta "¿cómo vamos?" o algo similar:

1. **Lee** `memoria/indice.md` para tener el panorama
2. **Lee** los archivos más recientes de cada categoría
3. **Sintetiza** la respuesta: "Esta semana tu score promedio fue 8/12, mejorando vs la anterior. Tu último análisis de Power of One muestra que puedes liberar $120K reduciendo COGS 1%."

### Comandos útiles

```bash
# Ver todos los dailys ordenados por fecha
ls -t ~/.escala/memoria/dailys/

# Buscar análisis por tipo
grep -l "tipo: analisis" ~/.escala/memoria/analisis/*.md

# Buscar por empresa
grep -l "empresa: Carnicería" ~/.escala/memoria/**/*.md

# Ver el índice completo
cat ~/.escala/memoria/indice.md
```

## Links entre análisis

Los links conectan análisis relacionados. Ejemplos:

```yaml
links:
  - daily: 2026-05-29           # Este análisis se relaciona con el daily del 29
  - analisis: face-mayo          # Y con el análisis FACe de mayo
  - dashboard: resumen-q2        # Y con el dashboard resumen del Q2
```

Cuando guardas un análisis, revisa si hay análisis anteriores del mismo tipo
y agrega links bidireccionales (actualiza el anterior para que apunte al nuevo).

## Ejemplo completo

Cuando Kokoro analiza un daily:

1. Usa `review_daily()` → obtiene score 10/12
2. Construye `memoria/dailys/2026-05-30-score-10.md` con frontmatter
3. Agrega fila al índice
4. Si existe `memoria/analisis/power-of-one-abril.md`, agrega link
5. Responde al usuario con el resultado

Cuando el usuario pregunta "¿cómo vamos?":

1. Lee `memoria/indice.md`
2. Ve 3 dailys: 6/12, 8/12, 10/12 → tendencia ↑
3. Ve 1 análisis Power of One
4. Sintetiza: "Tus dailys mejoraron de 6 a 10. El Power of One muestra $120K de oportunidad."

## Síntesis avanzada (S23.4)

### Consultas frecuentes del usuario y cómo responderlas

#### "¿Cómo vamos?"
1. Lee `memoria/indice.md` — extrae los últimos 5 registros de cada tipo
2. Agrupa por tipo (dailys, análisis, dashboards)
3. Calcula tendencias:
   - Dailys: ¿el score sube o baja? Promedio semanal vs anterior
   - Análisis: ¿cuántos se han completado? ¿cuáles faltan?
4. Responde con estructura:
   ```markdown
   ## Última semana
   - Dailys: 3 registros. Promedio: 8/12 (↑ vs semana anterior 6/12)
   - Power of One: 1 análisis. Oportunidad: $120K
   - FACe: pendiente (no lo hemos trabajado)
   
   ## Recomendación
   Te sugiero trabajar el FACe — es la herramienta que falta.
   ```

#### "¿Qué pasó el [fecha]?"
1. Busca archivos con esa fecha en el frontmatter:
   ```bash
   grep -l "fecha: 2026-05-30" ~/.escala/memoria/**/*.md
   ```
2. Lee los archivos encontrados
3. Resume: "El 30 de mayo analizaste un daily (score 10/12) e hiciste el Power of One."

#### "Muéstrame los dailys de esta semana"
1. Calcula la fecha de inicio de la semana actual
2. Busca archivos en `memoria/dailys/` con fecha >= inicio_semana
3. Lee los scores de cada uno
4. Genera tabla:
   ```markdown
   | Fecha | Score | 
   |-------|:-----:|
   | Lun   | 6/12  |
   | Mar   | 8/12  |
   | Mié   | 10/12 |
   | **Promedio** | **8/12** |
   ```

#### "¿Qué me recomiendas basado en mis datos?"
1. Lee índice para tener panorama completo
2. Identifica:
   - Herramientas NO trabajadas (FACe vacío, OPSP vacío)
   - Áreas débiles (dailys sin métricas, CCC alto)
   - Análisis antiguos que merecen actualización
3. Responde priorizando:
   ```markdown
   Basado en tus 12 análisis guardados:
   
   1️⃣ **Prioridad: FACe** — Nunca lo hemos trabajado
      Sin un organigrama claro, las contrataciones son al tanteo.
   
   2️⃣ **Mejorar dailys** — 3 de 5 dailys no tienen métricas
      Sin scoreboard, el huddle pierde su poder.
   
   3️⃣ **Actualizar Power of One** — El último es de enero
      Tus números cambiaron, el impacto también.
   ```

### Patrones de síntesis

| Contexto | Patrón |
|----------|--------|
| Datos numéricos (scores, $) | Calcula promedios, tendencias, totales |
| Herramientas completadas | Checklist: ✅/⚠️/❌ con prioridad |
| Relaciones entre análisis | Enlaza: "cuando hicimos FACe, detectaste que te faltaba un gerente" |
| Recomendaciones | Prioriza por impacto: "esto te puede liberar más efectivo" |

### Comandos de búsqueda avanzada

```bash
# Buscar por rango de fechas
grep -E "fecha: 2026-05-2[5-9]" ~/.escala/memoria/**/*.md

# Buscar por score mínimo
grep -l "score: [89]/12\|score: 1[0-2]/12" ~/.escala/memoria/dailys/*.md

# Buscar por tag
grep -l "tags:.*cash.*" ~/.escala/memoria/**/*.md

# Buscar por empresa + tipo
grep -l "empresa: Carnicería" ~/.escala/memoria/analisis/*.md

# Contar registros por tipo
for f in ~/.escala/memoria/*/; do echo "$(basename $f): $(ls "$f" 2>/dev/null | wc -l) archivos"; done

# Extraer todos los scores de dailys
grep -h "score:" ~/.escala/memoria/dailys/*.md | sed 's/.*: //'
```
