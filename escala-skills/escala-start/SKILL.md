---
description: 'Flujo guiado de inicio a fin: de "hola" a dashboard con recomendación. El agente elige la decisión correcta, aplica el skill, y entrega valor en <10 min.'
name: escala-start
---

# Escalamiento — Primer Diagnóstico en 10 Minutos

## Purpose

El objetivo es simple: en menos de 10 minutos desde que el usuario dijo "hola", debe tener un diagnóstico claro con una recomendación accionable. No un tour. No un menú. Valor.

Este skill es el motor que ejecuta la promesa del onboarding: detectar el dolor, elegir el skill correcto, ejecutarlo, y entregar.

## Principios

- **Una decisión a la vez.** No diagnosticar People y Strategy y Cash en la primera sesión. La que más duele.
- **Datos mínimos.** Si el usuario no tiene datos, usar lo que diga. "Dime los 3 números que sí sabes."
- **Dashboard siempre.** Cada diagnóstico termina con algo visible: un dashboard HTML, un PDF, o al menos un resumen estructurado en markdown.
- **Siguiente paso concreto.** "Esto es lo que tienes. Esto es lo que te recomiendo hacer esta semana."

## Flow

### Paso 1: Elegir la decisión correcta (1 min)

Basado en lo que el usuario dijo en el welcome, clasificar su dolor principal:

| El usuario dice... | Decisión | Skill |
|---|---|---|
| "Mi equipo no funciona", "No tengo a quién delegar" | People | escala-people-organigrama / escala-people-fac |
| "No sé para dónde voy", "Mi competencia me está comiendo" | Strategy | escala-strategy-opsp / escala-strategy-swt |
| "No llegamos a las metas", "Puro apagar incendios" | Execution | escala-execution-prioridad / escala-execution-habits |
| "No tengo dinero", "No sé a dónde se va el cash" | Cash | escala-cash-finanzas / escala-cash-power1 |
| "Todo está mal" | General | escala-diagnose |

Si no está claro: "De estas 4 áreas, ¿cuál te quita más el sueño: tu equipo, tu rumbo, tu operación o tu dinero?"

### Paso 2: Recolectar datos mínimos (2-3 min)

Activar escala-discover para detectar dónde están los datos.

Si no hay datos: "No te preocupes. Dime lo que sepas. Aunque sean 3 números."

**Mínimo viable por decisión:**

- **People:** "Dime 3 personas clave de tu equipo y qué hacen."
- **Strategy:** "¿Quién es tu cliente ideal? Descríbelo en una frase."
- **Execution:** "¿Cuál es tu meta más importante este trimestre?"
- **Cash:** "¿Cuánto vendiste el mes pasado y cuánto gastaste?"

Con eso es suficiente para un primer diagnóstico.

### Paso 3: Ejecutar diagnóstico (3-4 min)

Aplicar el skill correspondiente con los datos disponibles (aunque sean mínimos).

"Perfecto. Déjame analizar esto..."

El skill debe:
- Procesar los datos (de archivo o de conversación)
- Generar el diagnóstico
- Guardar resultados
- Generar dashboard o resumen

### Paso 4: Entregar resultado (2 min)

Mostrar al usuario:

```
📊 Diagnóstico inicial — [Decisión]

Esto es lo que veo:
[3-5 hallazgos clave con datos]

Mi recomendación:
[1 acción concreta para esta semana]

Próximo paso:
[Qué hacer, con qué skill, y cuándo volver]

¿Quieres profundizar en algo de esto o prefieres pasar a otra área?
```

### Paso 5: Guardar y preparar siguiente sesión

Guardar todo en `work/` y en memoria/.

"Ya guardé todo. La próxima vez que entres, seguimos donde nos quedamos. ¿Hay algo más en lo que pueda ayudarte hoy?"

## Time Budget

| Fase | Tiempo |
|---|---|
| Elegir decisión | 1 min |
| Recolectar datos | 2-3 min |
| Ejecutar diagnóstico | 3-4 min |
| Entregar resultado | 2 min |
| **Total** | **8-10 min** |

Si en 10 minutos no hay diagnóstico, el skill no está funcionando. Optimizar.

## Notas

- Si el usuario se va por las ramas: "Volvamos a [tema]. Dijiste que [su dolor]. ¿Quieres que empecemos por ahí?"
- Si el usuario quiere cambiar de tema a mitad: "OK, cambiemos. ¿Qué es más urgente ahora?"
- Si el diagnóstico revela algo más grave que el dolor inicial: "Mira, entramos por [tema A], pero lo que veo es que [tema B] es más urgente. ¿Re-enfocamos?"
- Siempre terminar con optimismo: "Esto tiene solución. Vamos paso a paso."
