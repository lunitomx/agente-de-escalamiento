---
description: >-
  Muestra el ciclo de efectivo (días de clientes, de inventario y de
  proveedores) que saca la calculadora de ESCALA. Identifica qué aprieta el
  efectivo. Basado en Alan Miltz.
name: escala-cash-ccc
---

# Escalamiento Cash — CCC (Ciclo de Efectivo)

## Purpose

Mostrar el ciclo de efectivo: los días que tarda el dinero en regresar como
efectivo. Identificar si lo que aprieta es el cobro, el inventario o los pagos.

## Quién hace las cuentas

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

## Qué te da la calculadora

Claves del JSON (una por fecha del balance, con el año anterior para comparar):

- `dias_clientes`: cuántos días tarda tu cliente en pagarte.
- `dias_inventario`: cuántos días se queda tu mercancía en el almacén.
- `dias_proveedores`: cuántos días tardas en pagarle a tu proveedor.
- `ciclo`: cuántos días tarda en regresar tu peso.

Cada clave trae su fórmula en el campo `formula` del JSON: explícala con esas
palabras. Las fórmulas viven sólo en la calculadora; aquí no se repiten.
Los días del periodo los confirma el dueño al revisar sus estados: 365 si es
un año, los días del mes si es un mes. Nunca uses 30 ni 360 por costumbre.

## Steps

1. Si no hay estados revisados, pídelos con el procedimiento interno
   `escala-cash-finanzas`. No pidas números sueltos para calcular.
2. Corre la calculadora y muestra los cuatro números con fórmula y origen.
3. Compara con el año anterior: di cuál de los tres días creció más.
   No lo califiques contra un límite: no hay un límite que valga para todos.
4. Recomienda una acción sobre ese componente y pregunta qué va a hacer.
5. Guarda en `work/cash/ccc-analysis.md` el JSON de la calculadora y tu
   recomendación.

---

*Metodología: Alan Miltz. Adaptación: Kokoro.*
