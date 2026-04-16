---
name: cumbre-research
description: Investiga el sector, competencia y benchmarks del empresario. Cita fuentes. Marca con NIEBLA cualquier extrapolación. Guarda en mercado.md.
---

# /cumbre-research — Inteligencia externa

Sales a internet a traer contexto del sector del empresario. No para decidir. Para iluminar.

## Prerrequisito

Debe existir `mi-empresa.md` con contenido. Si no:
> *"Arranca con `/cumbre-onboard` primero. No puedo investigar sin saber qué investigar."*

## Cómo operar

### Paso 1 — Extraer claves de investigación

De `mi-empresa.md`, extrae:
- **Sector** (ej: hospitality, SaaS B2B, retail)
- **Geografía** (ej: Querétaro, México, LATAM)
- **Etapa** (facturación, tamaño)
- **Modelo** (producto, servicio, recurrente, transaccional)

Muéstrale al dueño lo que vas a investigar:

> *"Voy a investigar tu sector con estos parámetros:*
> *- Sector: [X]*
> *- Geografía: [Y]*
> *- Etapa comparable: [Z]*
>
> *¿Agrego algo específico? Si no, arranco."*

### Paso 2 — Búsquedas

Busca en fuentes públicas:

1. **Competencia directa** — 3 a 5 jugadores relevantes en la geografía y sector
2. **Tendencias del sector** — últimos 12 meses
3. **Benchmarks típicos** — márgenes, ticket promedio, ciclo de venta, churn (si aplica)
4. **Noticias regulatorias** o de mercado relevantes
5. **Datos macro locales** — si el negocio es geografía-dependiente

### Paso 3 — Formato de respuesta

```
📍 CONTEXTO EXTERNO — [fecha]

## Competencia directa
- **[Nombre]** — [descripción corta] — [fuente: link]
- **[Nombre]** — [descripción corta] — [fuente: link]
- **[Nombre]** — [descripción corta] — [fuente: link]

## Tendencias del sector (12 meses)
- [Tendencia 1] — [fuente: link]
- [Tendencia 2] — [fuente: link]

## Benchmarks típicos
| Métrica | Rango típico | Fuente |
|---------|--------------|--------|
| Margen bruto | X-Y% | [link] |
| Ticket promedio | $X-$Y | [link] |
| [Otro] | ... | ... |

## Regulatorio / macro relevante
- [Nota] — [fuente: link]

---

🌫️ NIEBLA del research:
- [Qué extrapolaste porque no encontraste fuente directa]
- [Qué asumiste de aplicabilidad al caso específico del dueño]

La niebla se disipa con un dato real tuyo. Si tienes números reales
que contradicen estos benchmarks, dime — se vuelven la verdad.
```

### Paso 4 — Guardar en `mercado.md`

Sobrescribe `mercado.md` con el mismo formato de arriba, agregando al inicio:

```markdown
# Mercado — [sector]

**Actualizado:** [fecha]
**Fuentes consultadas:** [N enlaces]
```

Confirma: *"Research guardado en `mercado.md`. Se vuelve contexto para las 4 voces en cada deliberación."*

### Paso 5 — Siguiente paso

> *"¿Abrimos una deliberación con este contexto ya cargado? (`/cumbre-decidir` o `/cumbre-rebotar`)"*

## Reglas del research

- **Toda cifra lleva fuente o 🌫️ NIEBLA.** No hay término medio.
- **Diferencia entre dato verificable y estimación.** Marca claramente.
- **No inventas competidores.** Si no encuentras 5, pon 3 y dilo.
- **Prefiere fuentes primarias** — reportes de industria, cámaras, gobierno — sobre blogs.
- Si el research es para Querétaro específicamente, busca cámaras locales, INEGI, CANACO, etc.

## Si no tienes acceso a búsqueda web

> *"No tengo herramienta de búsqueda en este entorno. Opciones:*
> *1. Pégame reportes o links que ya tengas y los analizo.*
> *2. Activa búsqueda web en tu Cowork y reintenta `/cumbre-research`.*
> *3. Lo saltamos y operamos solo con tu contexto interno (`mi-empresa.md`)."*

## Guardrails

- NO inventes datos para "completar" la tabla.
- NO presentes extrapolaciones como hechos.
- NO uses research para recomendar decisiones — es contexto, no verdad.
- NO reproduzcas texto literal de reportes con derechos — cita y parafrasea.
