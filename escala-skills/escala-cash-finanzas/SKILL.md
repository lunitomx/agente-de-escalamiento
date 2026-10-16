---
description: 'Pásame tus estados financieros como los tengas (PDF, Excel, foto). ESCALA los lee, revisa que cuadren y saca con su calculadora tu ciclo de efectivo y tu Power of One, cada número con su fórmula y de dónde sale.'
name: escala-cash-finanzas
---

# Escalamiento Cash — De tus Estados Financieros al Power of One

## Purpose

El dueño no llena el Power of One a mano. Pasa su estado de resultados y su
balance como los tenga. ESCALA los lee, pone cada cuenta en su caja, revisa
que cuadren y la calculadora saca los números del curso.

## Steps

Cuando el dueño dice «analiza mi balance general y mi estado de resultados» (o
manda sus estados), todo pasa por una sola entrada de ESCALA, el escenario. El
escenario lee los archivos, arma la lista ✔ lo tengo · ? no me queda claro ·
✘ me falta, hace las preguntas (máximo 3 por mensaje, de la más importante a la
menos importante), revisa que todo cuadre, dice qué va a calcular y qué no, y
calcula. Tú sólo lo corres y muestras lo que dice.

### Step 1: Recibir los estados financieros

Pregunta: "¿Me pasas tu balance general y tu estado de resultados como los
tengas (PDF, Excel o foto)?"

- Si tiene el balance del cierre anterior, pídelo también: con él sale el flujo.
- **De cabeza**: sin estados no hay cuentas que revisar. Pide al dueño que se
  los pida a su contador. No calcules con cifras sueltas.

### Step 2: Correr el escenario

- En la copia de ESCALA, desde su carpeta:
  `python3 escala_server/cash/calcular.py escenario --empresa "<empresa>" --archivo <balance> --archivo <resultados> --formato json`
- En un paquete, junto a la puerta de ESCALA:
  `python3 references/calculadora/escala_server/cash/calcular.py escenario --empresa "<empresa>" --archivo <balance> --archivo <resultados> --formato json`

Usa siempre el mismo `--empresa`: con él, el escenario recuerda los archivos y
las respuestas entre mensajes. Para un archivo nuevo o corregido, agrega
`--archivo <ruta>`; para quitar uno, `--quita-archivo <ruta>`.

Devuelve JSON. Muestra el campo `mensaje` tal cual, completo. Ahí vienen la
lista, las preguntas, el anuncio («Con esto voy a calcular… No puedo calcular…
porque…») y el resumen con el origen de cada número.

### Step 3: Pasar las respuestas del dueño

Cada pregunta del JSON trae su `clave`. Repite las preguntas como vienen en
`mensaje`, sin cambiarlas ni agregar otras. Cuando el dueño conteste, corre otra
vez el escenario con una `--responde <clave>=<lo que dijo>` por respuesta, por
ejemplo `--responde "C10=acumulado del año"`.

- Si una pregunta trae `clave` vacía, no se contesta con palabras: el dueño
  tiene que mandar el archivo corregido.
- Si el escenario no entiende una respuesta, lo dice en `mensaje` y la vuelve a
  preguntar. Tú no la interpretas.

### Step 4: Los números

Tú no haces ninguna cuenta, ni de memoria ni a mano.
Nunca escribas un número que no venga en `mensaje`. Cada número del resumen trae su fórmula y «sale de:
…», y lo que no se pudo calcular dice «no calculable» con su razón. Nunca pongas
0 en su lugar.

Si el escenario responde sólo `{"no_calculable": …}` porque falta Python o
pydantic, o Python ni siquiera arranca, di exactamente:

> "Para calcular necesito Python en tu computadora y no lo encontré. No voy a hacer las cuentas de memoria."

y no des ningún número.

### Step 5: Guardar, sólo con «sí»

Al final, `mensaje` pregunta si guarda los estados revisados en
`work/cash/<empresa>/`. Sin su «sí» no guardes nada. Si dice «sí», corre otra
vez el escenario con `--guardar sí` y muestra `mensaje`. Así puede seguir otro
día donde se quedó.

Pregunta después: "¿Qué quieres revisar primero: tus días, tu capital de
trabajo o tu flujo?"

## Output

- Números de la calculadora, cada uno con fórmula, origen y lámina.
- Lo que no se pudo calcular, con su razón.
- Con «sí»: estados revisados guardados en `work/cash/<empresa>/`.

## Notas

- Este procedimiento no hace cuentas: corre el escenario y muestra su mensaje.
- Las cifras leídas se validan con el dueño dentro del escenario, antes de calcular.
