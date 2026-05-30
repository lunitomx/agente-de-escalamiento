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
