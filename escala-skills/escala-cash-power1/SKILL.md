---
description: >-
  Power of One: impacto de mejorar 1% (o 1 día) en cada una de las 7 palancas de
  cash flow. Basado en Alan Miltz.
name: escala-cash-power1
---

# Escalamiento Cash — Power of One (7 Palancas)

## Purpose

Calcular el impacto en cash flow de mejorar 1% (o 1 día) cada una de las 7 palancas
financieras. Identificar las de mayor impacto y generar recomendaciones accionables.

## Créditos

- **Metodología:** Alan Miltz
- **Motor backend:** `escala_server/cash/__init__.py`

## ⚠️ Reglas de Cálculo (NO improvisar)

NO usar sliders continuos. NO calcular Volumen con precio completo. NO usar 30 días.

### Las 7 Palancas

| Palanca | Tipo | +1% significa | Utilidad (antes de ISR) | Flujo (antes de ISR) |
|---------|------|---------------|-------------------------|----------------------|
| Precio | % | Subir precio 1% | Ventas × 1% | Ventas × 1% − Clientes × 1% |
| Volumen | % | Vender 1% más | Utilidad bruta × 1% | Utilidad bruta × 1% − Capital de trabajo × 1% (clientes + inventario − proveedores) |
| COGS | % | Reducir costo 1% | COGS × 1% | COGS × 1% + (Inventario − Proveedores) × 1% |
| OPEX | % | Gastar 1% menos | OPEX × 1% | OPEX × 1% |
| AR (cobrar) | día | Cobrar 1 día antes | 0 | Ventas ÷ 365 |
| INV (inventario) | día | 1 día menos almacén | 0 | COGS ÷ 365 |
| AP (pagar) | día | Pagar 1 día después | 0 | COGS ÷ 365 |

Según el curso de cash que vimos: el flujo descuenta el capital de trabajo que se lleva cada palanca.
Tú no haces estas cuentas: las hace `POST /api/cash/power-of-one`, que devuelve cada número con su fórmula.

### Diseño UI

- **Botones +1 / -1** — NO sliders
- +1 = mejora, -1 = empeoramiento (para TODAS las palancas)
- Toggle "Antes / Después"
- Tooltips en idioma humano: "Lo que te cuesta hacer tu producto" no "COGS"

### Métricas (base 365 días)

DSO = AR / (Ventas/365). DIO = Inv / (COGS/365). DPO = AP / (COGS/365). CCC = DSO + DIO - DPO.

## Steps

### Step 1: Gather Numbers (humano)

Preguntar en lenguaje coloquial. No usar COGS, DSO, CCC. Usar "costo de producto", "días en cobrar".

### Step 2: Calculate Impact

Usar `POST /api/cash/power-of-one`. No calcules a mano: muestra el número y la fórmula que devuelve (`cash_formula`, `ebit_formula`).

### Step 3: Prioritize

Score = Impacto ÷ Dificultad. Incluir: impacto ($), dificultad (1-5), tiempo, principio Rockefeller.

### Step 4: Recomendación priorizada

Decir prioridad #1, por qué, y "¿Qué vas a hacer al respecto?"

## Benchmarks

| Industria | Margen | CCC | DSO |
|-----------|:------:|:---:|:---:|
| Retail | 5% | 10-30d | 7-15d |
| Manufactura | 10% | 30-60d | 30-45d |
| Servicios | 15% | -15-15d | 15-30d |
| SaaS | 25% | -30 a -10d | 7-15d |
| Alimentos | 8% | 5-15d | 3-7d |

## References

- Backend: `escala_server/cash/__init__.py`
- Dashboard: `static/dashboards/cash/power-of-one.html`
- Tests: `tests/test_cash_engine.py`, `tests/test_s86_13_power_of_one_cash.py` (Mi Empresa al centavo)

---

*Metodología: Alan Miltz. Adaptación: Kokoro.*
