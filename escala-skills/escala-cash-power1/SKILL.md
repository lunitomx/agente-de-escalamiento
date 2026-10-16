---
description: >-
  Power of One: cuánto efectivo y cuánta utilidad libera mejorar 1% (o 1 día)
  cada una de las 7 palancas. Lo calcula la calculadora de ESCALA. Basado en
  Alan Miltz.
name: escala-cash-power1
---

# Escalamiento Cash — Power of One (7 Palancas)

## Purpose

Mostrar cuánto efectivo y cuánta utilidad libera mejorar 1% (o 1 día) cada una
de las 7 palancas. Identificar la de mayor impacto y recomendar una acción.

## Créditos

- **Metodología:** Alan Miltz
- **Calculadora:** `escala_server/cash/calcular.py` (usa el motor
  `escala_server/cash/__init__.py`)

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

## Las 7 palancas (para explicarlas, no para calcular)

El JSON trae `poder_del_uno` con una fila por palanca (`flujo`, `utilidad`) y
los totales `poder_del_uno_flujo` y `poder_del_uno_utilidad`.

| Palanca | Clave | +1 significa | Utilidad (antes de ISR) | Flujo (antes de ISR) |
|---------|-------|--------------|-------------------------|----------------------|
| Precio | `precio` | Subir precio 1% | Ventas × 1% | Ventas × 1% − Clientes × 1% |
| Volumen | `volumen` | Vender 1% más | Utilidad bruta × 1% | Utilidad bruta × 1% − Capital de trabajo × 1% |
| Costo | `costo` | Reducir costo 1% | Costo de ventas × 1% | Costo de ventas × 1% + (Inventario − Proveedores) × 1% |
| Gastos | `gastos` | Gastar 1% menos | Gastos × 1% | Gastos × 1% |
| Clientes | `clientes` | Cobrar 1 día antes | 0 | Ventas ÷ días del periodo |
| Inventario | `inventario` | 1 día menos en almacén | 0 | Costo de ventas ÷ días del periodo |
| Proveedores | `proveedores` | Pagar 1 día después | 0 | Costo de ventas ÷ días del periodo |

Según el curso de cash que vimos: el flujo descuenta el capital de trabajo que
se lleva cada palanca. Una palanca que no aplica (sin inventario, por ejemplo)
no aparece en la tabla de la calculadora; dilo así al dueño.

## Steps

### Step 1: Estados revisados

Si no hay estados revisados, primero pásalos por el procedimiento interno
`escala-cash-finanzas`. No pidas números sueltos para calcular.

### Step 2: Correr la calculadora

Muestra cada palanca con su efectivo, su utilidad, su fórmula y de dónde sale.

### Step 3: Priorizar con el dueño

Ordena por el efectivo que libera cada palanca, según el JSON. Pregunta al
dueño qué tan difícil es cada una en su negocio. No inventes una dificultad ni
una calificación.

### Step 4: Recomendación priorizada

Di la prioridad #1, por qué, y "¿Qué vas a hacer al respecto?"

## References

- Calculadora: `escala_server/cash/curso.py`
- Dashboard: `escala_server/static/dashboards/cash/power-of-one.html`
- Tests: `tests/test_s86_16_calculadora_curso.py` y
  `tests/test_s86_13_power_of_one_cash.py` (Mi Empresa al centavo)

---

*Metodología: Alan Miltz. Adaptación: Kokoro.*
