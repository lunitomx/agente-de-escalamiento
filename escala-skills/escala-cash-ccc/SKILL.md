     1|---
     2|description: 'Mapea el Ciclo de Conversión de Efectivo (CCC) completo: sales cycle, delivery cycle
     3|  y collection cycle en días.'
     4|name: escala-cash-ccc
     5|---
     6|
     7|# Escalamiento Cash — Ciclo de Conversión de Efectivo (CCC)
     8|
     9|## Purpose
    10|
    11|Mapear el CCC completo de la empresa: cuántos días tarda un peso invertido en regresar como cash cobrado.
    12|
    13|## Steps
    14|
    15|### Step 1: Load Context
    16|
    17|Leer `.escala/knowledge/cash/tools/cash-conversion-cycle.md`.
    18|Cargar template `templates/cash-conversion-cycle.md`.
    19|
    20|### Step 2: Map Sales Cycle
    21|
    22|Cuántos días desde primer contacto hasta contrato firmado. Desglosar etapas.
    23|
    24|### Step 3: Map Delivery Cycle
    25|
    26|Cuántos días desde contrato hasta entrega completada.
    27|
    28|### Step 4: Map Collection Cycle
    29|
    30|Cuántos días desde facturación hasta dinero en banco.
    31|
    32|### Step 5: Calculate & Identify Opportunities
    33|
    34|CCC = Sales + Delivery + Collection. Identificar qué componente es más largo y dónde hay oportunidades de reducción.
    35|
    36|### Step 6: Save
    37|
    38|Guardar en `work/cash/ccc-analysis.md`.
    39|
    40|## Output
    41|
    42|| Item | Destination |
    43||------|-------------|
    44|| CCC Analysis | `work/cash/ccc-analysis.md` |
    45|| Next | `/escala-cash-power1` |
    46|

---
*> El Ciclo de Conversión de Efectivo (CCC) es un principio de finanzas corporativas. Ver [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) para la referencia completa.
