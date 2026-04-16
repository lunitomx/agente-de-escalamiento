---
name: cumbre-bitacora
description: Registra una decisión tomada en decisiones.md con formato de postmortem futuro. Captura supuestos, fecha de revisión, criterio de éxito.
---

# /cumbre-bitacora — Registrar decisión

El empresario tomó una decisión. La registras con el formato correcto para que en 3 meses se pueda revisar con honestidad.

## Cómo operar

### Paso 1 — Capturar la decisión

Pregunta (una a una, no en lista):

1. *"En una línea: ¿qué decidiste?"*
2. *"¿Cuáles son los 2-3 supuestos sobre los que descansa esta decisión?"*
3. *"¿Cómo sabrás en X tiempo si la decisión fue correcta? (criterio de éxito medible)"*
4. *"¿Cuándo quieres que la revisemos? (fecha sugerida: 30, 60, 90 días)"*

### Paso 2 — Escribir en `decisiones.md`

Agrega al final del archivo:

```markdown
---

## [Fecha de hoy YYYY-MM-DD] — [Título corto de la decisión]

**Decisión:** [una línea]

**Supuestos clave:**
1. [Supuesto 1]
2. [Supuesto 2]
3. [Supuesto 3]

**Criterio de éxito:** [Cómo sabré si fue correcta]

**Fecha de revisión programada:** [fecha YYYY-MM-DD]

**Estado:** Vigente

**Voces escuchadas antes de decidir:**
[Breve nota de qué dijeron Veterano, Retador, Conector, Financiero
si hubo deliberación previa. Si no hubo, escribe "decisión directa sin
deliberación formal en CUMBRE".]

**🌫️ Niebla al momento de decidir:**
- [Qué supuestos no pudo validar antes de decidir]
```

### Paso 3 — Confirmar

> *"Registrado en `decisiones.md`.*
>
> *Revisión programada para [fecha]. Cuando llegue esa fecha, invoca `/cumbre-revisar` con el título de esta decisión — comparamos supuestos vs. realidad y sacamos aprendizaje."*

### Paso 4 — Remover de dilemas abiertos (si aplica)

Si la decisión estaba en `dilemas-abiertos.md`, quita esa entrada del archivo (ya se resolvió).

### Paso 5 — Cierre

> *"¿Cerramos sesión o sigues con otro tema?"*

## Reglas de la bitácora

- **Los supuestos son obligatorios.** Una decisión sin supuestos explícitos es una decisión invisible al postmortem.
- **El criterio de éxito debe ser medible.** Si no es medible, pide al dueño que lo reformule:
  > *"'Que funcione' no es criterio medible. ¿Qué número te dirá que funcionó?"*
- **Fecha de revisión siempre presente.** Si no la pone, sugiere 60 días.
- 🌫️ NIEBLA obligatoria si el dueño decidió sin validar algún supuesto.

## Guardrails

- NO validas la decisión al registrarla. Solo registras.
- NO juzgas los supuestos.
- NO sugieres cambiar la decisión — si quiere revisarla, que use `/cumbre-revisar`.
