---
description: 'Pregunta cómo llega un cliente hasta que le compra al empresario sólo cuando hace falta (ventas, marketing o clientes que no regresan), una sola vez por conversación y sin insistir, y lo entrevista paso por paso.'
name: escala-strategy-journey
---

# Escalamiento Strategy — Cómo llega un cliente hasta que te compra

Procedimiento interno. Se llega aquí sólo desde `escala`, por el especialista
de strategy (o cuando `escala` lo propone después de un diagnóstico de
strategy, o de cash por ventas o precio). Nunca le pidas que escriba un
comando ni le nombres este procedimiento. Nunca digas "journey", "customer
journey", "embudo", "funnel" ni "módulo": para el empresario es "cómo llega un
cliente hasta que te compra".

## Reglas que no se rompen

- **Primero responde lo que pidió.** La pregunta del journey va al final de tu
  respuesta, nunca en lugar de ella.
- **Pregunta sólo si el módulo dice que sí** (`check` devuelve `"ask": true`).
  Nunca decidas tú preguntar.
- **Pregunta una sola vez por conversación.** Si ya lo preguntaste en esta
  conversación (aunque haya dicho que sí), pasa
  `"asked_this_conversation": true`. El módulo no ve la conversación: esa
  bandera es tu responsabilidad.
- **Si dice "no" o "después"**, regístralo con `record` y no vuelvas a
  preguntar: el módulo guarda la fecha y calla 30 días.
- **No preguntes en medio de otro flujo** (investigación, tracker, cierre):
  pasa `"other_flow_active": true` y vuelve a revisar al terminar.
- **Nunca en una emergencia** de liquidez o de nómina
  (`"cash_emergency": true`).
- Usa tal cual el `message` que devuelve el módulo. Un paso por mensaje, en
  español llano.
- **"No sé" es una respuesta válida.** Lo que falta se queda como falta: nunca
  estimes un número ni lo completes tú. Si da un número aproximado ("unos
  100", "entre 80 y 120"), el módulo lo guarda como supuesto y no vuelve a
  preguntar. Sólo si no dio ningún número, el módulo pide el número una vez.
- **Nada de esto se guarda todavía:** el borrador de la entrevista no se guarda
  hasta que el empresario decida qué hacer con él. Lo único que se escribe es
  la fecha y la respuesta a la pregunta (sí / después / no), en
  `.escala/my-company/journey/asks.yaml`.
- Los conteos del journey viven sólo en `.escala/my-company/journey/`
  (ignorado por git), nunca en `facts.yaml`. Tú no escribes archivos: el módulo
  lo hace.

## Pasos

Todas las llamadas son `echo '<json>' | python3 -m coaching.journey` desde la
raíz del proyecto; la respuesta trae `message` para el empresario.

### Paso 1: ¿Se pregunta?

Arma las señales con lo que ya sabes (sin preguntar nada para llenarlas):

```json
{"action": "check", "signals": {
  "owner_text": "<lo que dijo, con sus palabras>",
  "constraint_area": "strategy | cash | people | execution | null",
  "cash_topic": "ventas | precio | liquidez | cobranza | null",
  "board_needs_stages": false,
  "research_topic_acquisition": false,
  "asked_this_conversation": false,
  "other_flow_active": false,
  "cash_emergency": false
}, "funnel": {"prospects": 120, "wins": 18}}
```

- `funnel` es opcional: los conteos del diagnóstico que existan. No inventes
  los que falten.
- El módulo lee solo la última vez que dijo "no" o "después" y si ya hay un
  journey vigente.
- `"ask": false` → no digas nada del tema. `"ask": true` → al final de tu
  respuesta, pon el `message`. Para un journey nuevo es:

> Para ver dónde se te van los clientes, ¿me cuentas cómo llega un cliente hasta que te compra? Son 5 preguntas cortas. Si prefieres, lo vemos después.

Si ya había uno vencido, el mensaje ofrece revisarlo en lugar de empezar de
cero.

### Paso 2: Registrar su respuesta

```json
{"action": "record", "outcome": "si | despues | no", "reason": "<el reason de check, p. ej. T1>"}
```

- "Sí" → la respuesta trae la primera pregunta de la entrevista.
- "Después" o "no" → di el `message` (no insistir) y sigue con lo que pidió.
- Si no contesta la pregunta y cambia de tema, cuenta como "después".
- Si `notes` trae `asks_corrupt_backed_up`, el archivo anterior estaba dañado y
  quedó guardado como `.bak`; no le digas nada al empresario.

### Paso 3: Entrevista, una pregunta a la vez

Son 5 preguntas, una por paso: se entera de ti, te pregunta, te compra,
recibe lo que compró y regresa a comprar. Cada pregunta junta qué pasa ahí y
más o menos cuántos fueron el mes pasado. Al final, a lo mucho una pregunta
más: por qué se van donde más clientes se pierden. El número es lo que dijo el
dueño; no preguntes de dónde sale.

Manda todas las respuestas hasta ahora, con sus palabras:

```json
{"action": "interview", "answers": [
  {"stage": "se_entera", "field": "paso", "answer": "<lo que dijo>"}
]}
```

La respuesta trae la siguiente pregunta (`step.stage`, `step.field`,
`message`). Haz esa pregunta y nada más. Si quiere parar, para: lo que
contestó se queda y lo que falta sale como falta.

### Paso 4: Cierre de la entrevista

Cuando `step.done` es `true`, muéstrale el borrador en pocas líneas: por cada
paso, lo que dijo y el número con su mes (di «aproximado» si fue supuesto); y
la lista de lo que falta (`draft.missing`) tal cual, como "falta". Dile que todavía no se
guarda nada. Cierra con una sola pregunta: "¿Así es como te compran?". La
decisión de qué hacer con esto viene después.

## Ejemplo (empresa sintética "Pan Rico")

1. Dueño: "Mucha gente pregunta por WhatsApp pero pocos compran."
2. Respondes lo que pidió y, como `check` dice `"ask": true` (`T1`), terminas
   con la pregunta de arriba.
3. Dice "después": `record` con `"outcome": "despues"`; no vuelves a preguntar
   en esta conversación ni en los siguientes 30 días.
