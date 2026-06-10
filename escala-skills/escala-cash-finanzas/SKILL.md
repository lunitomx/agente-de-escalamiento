---
description: 'Pásame tu P&L y balance (PDF, Excel, foto) y calculo tu Power of One y CCC automáticamente. Sin fórmulas, sin Excel manual.'
name: escala-cash-finanzas
---

# Escalamiento Cash — De tus Estados Financieros al Power of One

## Purpose

No me pidas que llenes el Power of One a mano. Pásame tu Estado de Resultados y Balance — el que ya tienes en PDF, Excel, Google Sheets, o hasta una foto de tu pantalla. Yo extraigo los números, calculo tu CCC, y te digo exactamente cuánto cash genera cada palanca del Power of One.

## Steps

### Step 1: Recibir los estados financieros

Preguntar al usuario: "¿Dónde están tus estados financieros?"

Opciones:
- **PDF del contador** — "Súbelo, extraigo los números clave."
- **Excel / Google Sheets** — "Compártelo, yo leo las celdas."
- **Foto de pantalla** — "Tómale foto a tu P&L y balance, yo identifico las cifras."
- **De cabeza** — "Dame los 6 números clave y yo hago el resto."

### Step 2: Extraer los números clave

Del P&L extraer:
- Ingresos totales (último trimestre o año)
- Costo de ventas (COGS)
- Gastos operativos
- Utilidad neta

Del Balance extraer:
- Cuentas por cobrar (Accounts Receivable)
- Inventario
- Cuentas por pagar (Accounts Payable)

Validar con el usuario: "Esto es lo que extraje. ¿Son correctos estos números?"

### Step 3: Calcular métricas Scaling Up

**Power of One — 7 palancas:**
1. Precio (+1%) → impacto en EBIT y Cash
2. Volumen (+1%) → impacto
3. Costo variable (-1%) → impacto
4. Costo fijo (-1%) → impacto
5. Días de cuentas por cobrar (-1 día) → impacto
6. Días de inventario (-1 día) → impacto
7. Días de cuentas por pagar (+1 día) → impacto

**Cash Conversion Cycle:**
- DSO = (Cuentas por cobrar / Ingresos) × 365
- DIO = (Inventario / COGS) × 365
- DPO = (Cuentas por pagar / COGS) × 365
- CCC = DSO + DIO - DPO

### Step 4: Presentar el diagnóstico

Mostrar tabla Power of One con impacto en cash de cada palanca.

Mostrar CCC: "Tu ciclo de efectivo es de X días. Tardas Y días en cobrar, Z días en vender inventario, y W días en pagar a proveedores."

**Diagnóstico automático:**
- Si CCC > 90 días: "ALERTA: Tu ciclo de efectivo es muy largo. Estás financiando a tus clientes."
- Si DSO > 60 días: "ALERTA: Tus clientes te pagan muy lento. Cada día que reduces DSO libera $X."
- Si Margen Bruto < 30%: "ALERTA: Margen bajo. La palanca de precio es tu mayor oportunidad."
- Si la palanca #1 (precio) genera más cash que las otras 6 juntas: "Tu mayor oportunidad está en el precio. Un 1% de aumento te da $X."

### Step 5: Guardar y próximos pasos

Guardar en `work/cash/power-of-one.md` y `work/cash/ccc.md`.

Preguntar: "¿Quieres que simulemos escenarios? Puedo calcular qué pasa si mejoras 5% en precio o reduces 10 días tu DSO."

## Output

- Power of One calculado con las 7 palancas
- CCC desglosado (DSO, DIO, DPO)
- Diagnóstico automático con alertas
- Archivos guardados en work/cash/

## Notas

- Este skill NO programa nada. Usa las capacidades nativas de Claude Code/Codex para leer documentos, extraer números y hacer cálculos.
- Si el usuario no tiene estados financieros formales, guiarlo con preguntas simples: "¿Cuánto vendiste el mes pasado? ¿Cuánto te costó? ¿Cuánto tienes en caja?"
- Los cálculos del Power of One siguen la metodología de Alan Miltz tal como está en el libro Scaling Up.
