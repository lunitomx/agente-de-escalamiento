# Epic Scope: E32 — Onboarding Conversacional

**Status:** Draft
**Dependencies:** E30 (skills de lectura disponibles)
**Tamaño:** M (3 historias, ~4h)
**Origen:** Visión de coach — si el usuario no pasa de los primeros 10 minutos, no importa qué tan bueno sea el agente.

## Visión

"Hola, soy Escala. ¿Qué te preocupa hoy?" Sin comandos. Sin skills. Sin documentación. El agente detecta dónde está parado el empresario, qué datos tiene disponibles, y lo guía a su primer dashboard en menos de 10 minutos. Si el empresario está trabado, el agente diagnostica. Si ya tiene datos, el agente acelera.

## Stories

| Story | Size | Qué |
|-------|:----:|-----|
| **S32.1 — Rediseño de welcome: detección sin comandos** | M | Reescribir `coaching/welcome/`. La conversación detecta madurez: ¿primera vez? ¿ya tiene datos? ¿viene de un daily? Sin preguntar "elige un comando". |
| **S32.2 — Discovery de fuentes de datos** | S | "¿Dónde están tus datos?" El agente sugiere opciones: Google Drive, Excel local, CRM (exporta CSV), foto del pizarrón. Según lo que elija, sugiere skills de E30. |
| **S32.3 — Primer diagnóstico en 10 minutos** | M | Flujo guiado de inicio a fin: "Empecemos por lo que más te duele." El agente elige la decisión correcta (People/Strategy/Execution/Cash), aplica el skill adecuado, y termina con un dashboard y una recomendación concreta. |

## Done Criteria

- [ ] S32.1: usuario nuevo llega, conversa 2 min, y ya está en un diagnóstico sin elegir comandos
- [ ] S32.2: agente sabe sugerir E30 si el usuario menciona "tengo un Excel"
- [ ] S32.3: de "hola" a dashboard con recomendación en < 10 min
