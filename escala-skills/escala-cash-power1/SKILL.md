     1|---
     2|description: 'Análisis Análisis Power of One: impacto de mejorar 1% cada palanca de cash flow.'
     3|name: escala-cash-power1
     4|---
     5|
     6|# Escalamiento Cash — Análisis Power of One
     7|
     8|## Purpose
     9|
    10|Calcular el impacto en cash flow de mejorar 1% (o 1 día) cada una de las 7 palancas. Identificar las de mayor impacto.
    11|
    12|## Steps
    13|
    14|### Step 1: Load Context
    15|
    16|Leer `.escala/knowledge/cash/tools/power-of-one.md`.
    17|Cargar template `templates/power-of-one.md`.
    18|
    19|### Step 2: Gather Current Numbers
    20|
    21|Pedir datos actuales: precio promedio, volumen, COGS, OpEx, días de cobro, inventario, días de pago.
    22|
    23|### Step 3: Calculate Impact
    24|
    25|Para cada palanca, calcular impacto anual en cash de mejorar 1%/1 día.
    26|
    27|### Step 4: Prioritize
    28|
    29|Ordenar por impacto vs dificultad. Seleccionar top 3 palancas a accionar.
    30|
    31|### Step 5: Action Plan & Save
    32|
    33|Crear plan de acción para las 3 palancas prioritarias. Guardar en `work/cash/power-of-one.md`.
    34|
    35|## Output
    36|
    37|| Item | Destination |
    38||------|-------------|
    39|| Análisis Power of One analysis | `work/cash/power-of-one.md` |
    40|| Next | `/escala-cash-acceleration` |
    41|

---
*> Esta herramienta está inspirada en el análisis Power of One, desarrollado por Verne Harnish. Ver [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) para la referencia completa.
