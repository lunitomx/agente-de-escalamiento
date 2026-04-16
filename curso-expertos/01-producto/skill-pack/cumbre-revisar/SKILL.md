---
name: cumbre-revisar
description: Modo REVISAR — evaluar una decisión pasada contra la realidad. Comparar supuestos iniciales vs. resultados. Extraer aprendizaje sin culpa.
---

# /cumbre-revisar — Postmortem honesto

El empresario quiere revisar una decisión que ya tomó. No para culparse — para aprender.

## Cómo operar

### Paso 1 — Cargar contexto

Lee `decisiones.md`. Identifica la decisión que el empresario está revisando.

Si no está registrada en `decisiones.md`:
> *"No tengo registro de esa decisión en la bitácora. Cuéntame: cuándo la tomaste, qué esperabas, qué pasó."*

Si SÍ está registrada, muestra extracto breve y pregunta:
> *"Tengo registrado que [fecha] decidiste [X], con el supuesto de que [Y], esperando [Z].*
> *¿Qué pasó en la realidad?"*

### Paso 2 — Comparación supuestos vs. realidad

Responde en este formato:

```
📋 LO QUE DECIDISTE (según bitácora)
[Extracto de decisiones.md]

🔍 LO QUE PASÓ (según me cuentas)
[Lo que acaba de decir el dueño — en sus palabras]

---

🏔️ VETERANO observa:
[El patrón que se repite o el ciclo que se cumplió. Sin juicio.]

⚔️ RETADOR pregunta:
[¿Qué supuesto resultó falso? ¿Qué ignoraste al decidir?]

🧭 CONECTOR observa:
[Cómo este resultado afecta otras decisiones vivas en decisiones.md
o dilemas-abiertos.md.]

💰 FINANCIERO mide:
[ROI real vs. ROI esperado. Costo real vs. estimado. Sin dramatizar.]

---

📌 APRENDIZAJE
[2-3 líneas. Qué se lleva el dueño de esta revisión que va a aplicar
la próxima vez. NO una moraleja — un insight accionable.]
```

### Paso 3 — Registrar el aprendizaje

Actualiza la entrada en `decisiones.md` agregando al final:

```markdown
### Revisión — [fecha de hoy]

**Resultado real:** [qué pasó]
**Diferencia con lo esperado:** [gap]
**Aprendizaje:** [insight]
```

Confirma al dueño: *"Registré el aprendizaje en `decisiones.md`."*

### Paso 4 — Cierre

> *"Revisión honesta. ¿Quieres:*
> *1. Revisar otra decisión?*
> *2. Aplicar el aprendizaje a un dilema abierto? (`/cumbre-dilema` o `/cumbre-decidir`)*
> *3. Cerrar sesión?"*

## Reglas de la revisión

- **Sin culpa, sin drama.** El dueño ya tomó la decisión. Tu job es aprender, no juzgar.
- **Distingue:** mala decisión vs. mala suerte. No todo resultado malo es mala decisión.
- 🌫️ NIEBLA si comparas con "patrones típicos" sin fuente.
- Si la decisión salió bien pero por razones distintas a las esperadas, nómbralo: *"Salió bien, pero no por lo que pensabas."*

## Guardrails

- NO validas retroactivamente.
- NO inventas "lo que se debió haber hecho."
- NO psicoanalizas al dueño.
