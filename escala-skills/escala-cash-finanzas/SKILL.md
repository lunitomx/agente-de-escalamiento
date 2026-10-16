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

### Step 1: Recibir los estados financieros

Pregunta: "¿Dónde están tus estados financieros?"

- **PDF o Excel del contador**: "Pásamelo como lo tengas."
- **Foto de pantalla**: "Tómale foto a tu estado de resultados y a tu balance."
- **De cabeza**: sin estados no hay cuentas que revisar. Pide al dueño que se
  los pida a su contador. No calcules con cifras sueltas.

### Step 2: Leer y revisar los estados

1. Lee cada archivo con el lector de ESCALA:
   `python3 -m escala_server.financial.lector <archivo>` en la copia de ESCALA;
   en un paquete, antepón `PYTHONPATH=references/calculadora`.
2. Muestra lo que leíste y confirma con el dueño las preguntas que salgan:
   el periodo (año, acumulado o mes) y las cuentas que no tienen caja.
3. Sólo cuando la revisión dice que se puede calcular hay estados revisados.
   Si algo no cuadra, dilo y no des números.

### Step 3: Calcular con la calculadora de ESCALA

Tú no haces ninguna cuenta, ni de memoria ni a mano. Las hace la calculadora de
ESCALA con los estados ya revisados (cada cuenta en su caja y el periodo
confirmado):

- En la copia de ESCALA, desde su carpeta:
  `python3 escala_server/cash/calcular.py <estados-revisados.json>`.
- En un paquete, junto a la puerta de ESCALA:
  `python3 references/calculadora/escala_server/cash/calcular.py <estados-revisados.json>`.

Devuelve JSON. Cada número trae `valor`, `formula`, `origen` («sale de: …») y
`lamina`. Muéstralo así: el número, su fórmula en palabras y de dónde sale.
Si un número trae `no_calculable` o `no_aplica`, di la razón en palabras del
dueño. Nunca pongas 0 en su lugar ni lo calcules tú.
Si todavía no hay estados revisados, no hay números: primero se leen y se
revisan los estados.

Si la calculadora responde sólo `{"no_calculable": …}` porque falta Python o
pydantic, o Python ni siquiera arranca, di exactamente:

> "Para calcular necesito Python en tu computadora y no lo encontré. No voy a hacer las cuentas de memoria."

y no des ningún número.

### Step 4: Presentar el diagnóstico

- Muestra el ciclo de efectivo con sus tres días, el capital de trabajo, el
  flujo neto, el flujo de operación y el Power of One de la calculadora.
- Cada número va con su fórmula en palabras y de dónde sale.
- Compara con el año anterior que trae la calculadora. No califiques contra
  límites ni promedios de otras empresas: no hay uno que valga para todos.
- Di cuál palanca del Power of One libera más efectivo, según el JSON.

### Step 5: Guardar y próximos pasos

Guarda en `work/cash/power-of-one.md` y `work/cash/ccc.md` el JSON de la
calculadora y tu recomendación.

Pregunta: "¿Qué vas a hacer con la palanca que más efectivo libera?"

## Output

- Números de la calculadora, cada uno con fórmula, origen y lámina.
- Lo que no se pudo calcular, con su razón.
- Archivos guardados en `work/cash/`.

## Notas

- Este procedimiento no hace cuentas: lee, revisa y llama a la calculadora.
- Valida con el dueño cada cifra leída antes de calcular.
